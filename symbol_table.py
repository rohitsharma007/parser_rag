"""
symbol_table.py — Global symbol registry built from a first-pass repository scan.

The symbol table maps class names (simple and fully-qualified) to their
location, layer, and package.  It is built once in Pass 1 and then used
during Pass 2 to resolve class references found in imports, `extends`,
`implements`, and `new` expressions.

Two-level index:
  _by_name[simple_name]  → list[ClassSymbol]   (may have >1 entry if same
                                                 name in different packages)
  _by_fqn[fqn]           → ClassSymbol          (always unique)

Ambiguity resolution:
  1. If only one class has that simple name → return it.
  2. If multiple → try to narrow down using the file's import list.
  3. If still ambiguous → return the first candidate and log a debug warning.

Usage:
    from symbol_table import SymbolTable
    from enhanced_parser import EnhancedJavaParser
    from repo_scanner import RepoScanner

    files   = RepoScanner().scan(repo_root)
    parser  = EnhancedJavaParser()
    table   = SymbolTable.build(files, parser)

    sym = table.resolve("Login_Page")
    print(sym.fully_qualified_name, sym.layer)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ClassSymbol:
    """One entry in the symbol table — represents a single Java class/interface."""
    class_name: str           # simple name:  "Login_Page"
    file_path: str            # absolute OS path
    relative_path: str        # relative to repo root (for display)
    package: str              # e.g. "com.ntrs.demoapp.pages.atrwebportal"
    layer: str                # e.g. "ui", "test", "service"
    fully_qualified_name: str # package + "." + class_name  (or just class_name if no pkg)
    class_type: str = "class" # "class" | "abstract" | "interface" | "enum"


# ---------------------------------------------------------------------------
# Symbol table
# ---------------------------------------------------------------------------

class SymbolTable:
    """
    In-memory registry of all classes discovered in the repository.

    Built in a single fast first pass that only needs package + class name
    (no full method/field extraction required).
    """

    def __init__(self) -> None:
        # simple name → list of ClassSymbol  (one-to-many for same-name classes)
        self._by_name: dict[str, list[ClassSymbol]] = {}
        # fully-qualified name → ClassSymbol  (always unique)
        self._by_fqn:  dict[str, ClassSymbol] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, symbol: ClassSymbol) -> None:
        """Register a symbol in both indexes."""
        self._by_name.setdefault(symbol.class_name, []).append(symbol)
        fqn = symbol.fully_qualified_name
        if fqn in self._by_fqn:
            logger.debug("Duplicate FQN '%s' — keeping first registration.", fqn)
        else:
            self._by_fqn[fqn] = symbol

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def resolve(self, name: str) -> Optional[ClassSymbol]:
        """
        Resolve a class name to its symbol.

        - `name` may be a simple name ("Login_Page") or a FQN
          ("com.ntrs.demoapp.pages.atrwebportal.Login_Page").
        - If the simple name is ambiguous, returns the first candidate
          and emits a debug log.  Use `resolve_with_imports` for better
          disambiguation.
        """
        if "." in name:
            return self._by_fqn.get(name)

        candidates = self._by_name.get(name, [])
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]

        # Ambiguous — return first but warn
        logger.debug(
            "Ambiguous simple name '%s': %d candidates (%s). Returning first.",
            name,
            len(candidates),
            ", ".join(c.fully_qualified_name for c in candidates),
        )
        return candidates[0]

    def resolve_with_imports(
        self, name: str, imports: list[str]
    ) -> Optional[ClassSymbol]:
        """
        Resolve using the file's import list for disambiguation.

        Strategy:
          1. If `name` is a FQN, look up directly.
          2. Scan `imports` for an entry whose last segment matches `name`
             — if found, look up by that FQN.
          3. Fall back to simple-name lookup (may be ambiguous).
        """
        if "." in name:
            return self._by_fqn.get(name)

        # Try to find a matching import
        for imp in imports:
            last_segment = imp.split(".")[-1]
            if last_segment == name:
                sym = self._by_fqn.get(imp)
                if sym:
                    return sym

        return self.resolve(name)

    def all_symbols(self) -> list[ClassSymbol]:
        """Return every symbol registered in the table."""
        return list(self._by_fqn.values())

    def symbols_for_layer(self, layer: str) -> list[ClassSymbol]:
        """Return all symbols belonging to a specific layer."""
        return [s for s in self._by_fqn.values() if s.layer == layer]

    # ------------------------------------------------------------------
    # Class method — build from a scan
    # ------------------------------------------------------------------

    @classmethod
    def build(
        cls,
        scanned_files,      # list[ScannedFile]
        enhanced_parser,    # EnhancedJavaParser instance
    ) -> "SymbolTable":
        """
        First-pass builder.

        Parses every scanned file just enough to extract package name and
        class name(s).  Full method/field extraction is deferred to Pass 2.

        Errors on individual files are logged as warnings and skipped so
        that a single bad file never aborts the whole scan.
        """
        table = cls()
        ok = 0
        failed = 0

        for sf in scanned_files:
            try:
                # parse_file_enhanced does a full parse, but we only USE the
                # package + class names here.  The result is discarded after
                # symbol registration so memory stays bounded.
                result = enhanced_parser.parse_file_enhanced(
                    sf.absolute_path, layer=sf.layer
                )
                pkg = result.package or ""

                for class_info in result.classes:
                    fqn = (
                        f"{pkg}.{class_info.name}" if pkg else class_info.name
                    )
                    symbol = ClassSymbol(
                        class_name=class_info.name,
                        file_path=sf.absolute_path,
                        relative_path=sf.relative_path,
                        package=pkg,
                        layer=sf.layer,
                        fully_qualified_name=fqn,
                    )
                    table.add(symbol)
                ok += 1

            except Exception as exc:
                logger.warning(
                    "Symbol table: skipping %s (%s)", sf.relative_path, exc
                )
                failed += 1

        logger.info(
            "Symbol table built: %d classes from %d files (%d failed).",
            len(table),
            ok,
            failed,
        )
        return table

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._by_fqn)

    def __contains__(self, name: str) -> bool:
        if "." in name:
            return name in self._by_fqn
        return name in self._by_name

    def __repr__(self) -> str:
        return (
            f"SymbolTable("
            f"{len(self._by_fqn)} classes, "
            f"{len(self._by_name)} unique simple names)"
        )
