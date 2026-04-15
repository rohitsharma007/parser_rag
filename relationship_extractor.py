"""
relationship_extractor.py — Extracts typed cross-class relationships from parsed AST data.

Relationship types (weakest → strongest signal):
  USES         — class A has an import statement for class B
  IMPLEMENTS   — class A implements interface B
  EXTENDS      — class A extends class B
  USES_STRONG  — class A instantiates B with `new B()`  (strongest coupling)

These map directly to foreign-key rows in a relational table or graph edges
in a knowledge graph.  They are also injected into chunk metadata for richer
vector-based retrieval.

Usage:
    from relationship_extractor import RelationshipExtractor, Relationship

    extractor = RelationshipExtractor(symbol_table)
    rels = extractor.extract(file_result)   # file_result: EnhancedFileResult
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Relationship:
    """A directed, typed dependency between two Java classes."""

    # Source side
    source_class: str   # fully-qualified name (or simple name if pkg unknown)
    source_simple: str  # simple (short) name
    source_layer: str
    source_file: str

    # Target side
    target_class: str   # FQN when resolvable; simple name otherwise
    target_simple: str
    target_layer: str   # "external" if target not in repo
    target_file: str

    # Relationship kind
    relation_type: str  # USES | IMPLEMENTS | EXTENDS | USES_STRONG

    # Optional context
    method_context: str = ""  # which method triggered the relationship


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------

class RelationshipExtractor:
    """
    Second-pass extractor.

    Uses an EnhancedFileResult (produced by EnhancedJavaParser) together
    with the SymbolTable from Pass 1 to produce typed Relationship objects.

    Processing order per class:
      1. EXTENDS      (superclass field)
      2. IMPLEMENTS   (interfaces field)
      3. USES_STRONG  (object_creations: new ClassName())
      4. USES         (imports that map to known project classes)
    """

    # Java standard library and framework types that add no useful signal.
    # Extend this set if you see noise from other libraries.
    NOISE_CLASSES: frozenset[str] = frozenset({
        # Java primitives and wrappers
        "String", "Integer", "Long", "Boolean", "Double", "Float",
        "Object", "Class", "Enum",
        # Collections
        "List", "Map", "Set", "HashMap", "ArrayList", "LinkedList",
        "HashSet", "Optional", "Arrays", "Collections",
        # Threading / IO
        "Thread", "Runnable", "Exception", "RuntimeException",
        "IOException", "System", "Math",
        # JUnit / TestNG annotations and base types
        "Test", "Before", "After", "BeforeClass", "AfterClass",
        "BeforeEach", "AfterEach", "BeforeAll", "AfterAll",
        "Assert", "Assertions",
        # Selenium types
        "WebDriver", "WebElement", "By", "Actions", "JavascriptExecutor",
        "ChromeDriver", "FirefoxDriver", "EdgeDriver",
        # Java / Spring annotations
        "Override", "SuppressWarnings", "Deprecated",
        # Void / primitives in type position
        "void", "int", "long", "boolean", "double", "float", "char", "byte",
    })

    def __init__(self, symbol_table) -> None:
        self._st = symbol_table  # SymbolTable instance

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, file_result) -> list[Relationship]:
        """
        Extract all relationships from one EnhancedFileResult.

        Returns a deduplicated list ordered by (source, target, type).
        """
        rels: list[Relationship] = []

        for cls in file_result.classes:
            src = self._resolve_source(cls)
            rels.extend(self._extends_rels(cls, src))
            rels.extend(self._implements_rels(cls, src))
            rels.extend(self._uses_strong_rels(cls, src))
            rels.extend(self._uses_rels(cls, src))

        return self._deduplicate(rels)

    # ------------------------------------------------------------------
    # A. EXTENDS
    # ------------------------------------------------------------------

    def _extends_rels(self, cls, src: _SourceCtx) -> list[Relationship]:
        if not cls.extends or cls.extends in self.NOISE_CLASSES:
            return []
        rel = self._build_rel(
            src, cls.extends, "EXTENDS", cls.imports
        )
        return [rel] if rel else []

    # ------------------------------------------------------------------
    # B. IMPLEMENTS
    # ------------------------------------------------------------------

    def _implements_rels(self, cls, src: _SourceCtx) -> list[Relationship]:
        rels = []
        for iface in cls.implements:
            if iface not in self.NOISE_CLASSES:
                rel = self._build_rel(src, iface, "IMPLEMENTS", cls.imports)
                if rel:
                    rels.append(rel)
        return rels

    # ------------------------------------------------------------------
    # C. USES_STRONG  (new ClassName())
    # ------------------------------------------------------------------

    def _uses_strong_rels(self, cls, src: _SourceCtx) -> list[Relationship]:
        rels = []
        for created in cls.object_creations:
            if created in self.NOISE_CLASSES:
                continue
            rel = self._build_rel(src, created, "USES_STRONG", cls.imports)
            if rel:
                rels.append(rel)
        return rels

    # ------------------------------------------------------------------
    # D. USES  (import-level, project classes only)
    # ------------------------------------------------------------------

    def _uses_rels(self, cls, src: _SourceCtx) -> list[Relationship]:
        """
        Only emit a USES relationship when the imported class is actually
        in our repository (i.e. resolvable in the symbol table).
        This avoids hundreds of noisy entries for JUnit / Selenium imports.
        """
        rels = []
        for imp in cls.imports:
            simple = imp.split(".")[-1]
            if simple in self.NOISE_CLASSES or simple == cls.name:
                continue
            # Try FQN lookup first (most precise)
            target_sym = self._st.resolve_with_imports(simple, [imp])
            if target_sym and target_sym.class_name != cls.name:
                rels.append(Relationship(
                    source_class=src.fqn,
                    source_simple=cls.name,
                    source_layer=src.layer,
                    source_file=src.file,
                    target_class=target_sym.fully_qualified_name,
                    target_simple=target_sym.class_name,
                    target_layer=target_sym.layer,
                    target_file=target_sym.file_path,
                    relation_type="USES",
                ))
        return rels

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_source(self, cls) -> "_SourceCtx":
        """Build a lightweight source-side context struct."""
        sym = self._st.resolve(cls.name)
        fqn   = sym.fully_qualified_name if sym else (
            f"{cls.package}.{cls.name}" if cls.package else cls.name
        )
        layer = sym.layer if sym else cls.layer
        file  = sym.file_path if sym else cls.file_path
        return _SourceCtx(fqn=fqn, layer=layer, file=file, simple=cls.name)

    def _build_rel(
        self,
        src: "_SourceCtx",
        target_simple: str,
        rel_type: str,
        imports: list[str],
    ) -> Optional[Relationship]:
        """
        Resolve `target_simple` using the symbol table and construct a
        Relationship.  If the target is not in the repo, still record it
        with target_layer="external" so the full dependency picture is
        preserved — callers can filter externals out if desired.
        """
        target_sym = self._st.resolve_with_imports(target_simple, imports)

        if target_sym:
            return Relationship(
                source_class=src.fqn,
                source_simple=src.simple,
                source_layer=src.layer,
                source_file=src.file,
                target_class=target_sym.fully_qualified_name,
                target_simple=target_sym.class_name,
                target_layer=target_sym.layer,
                target_file=target_sym.file_path,
                relation_type=rel_type,
            )

        # Target not in repo — record as external dependency
        return Relationship(
            source_class=src.fqn,
            source_simple=src.simple,
            source_layer=src.layer,
            source_file=src.file,
            target_class=target_simple,
            target_simple=target_simple,
            target_layer="external",
            target_file="",
            relation_type=rel_type,
        )

    @staticmethod
    def _deduplicate(rels: list[Relationship]) -> list[Relationship]:
        """Remove exact (source, target, type) duplicates."""
        seen: set[tuple[str, str, str]] = set()
        result: list[Relationship] = []
        for r in rels:
            key = (r.source_class, r.target_class, r.relation_type)
            if key not in seen:
                seen.add(key)
                result.append(r)
        return result


# ---------------------------------------------------------------------------
# Internal helper struct (not exported)
# ---------------------------------------------------------------------------

@dataclass
class _SourceCtx:
    """Lightweight source-side context used during extraction."""
    fqn: str
    layer: str
    file: str
    simple: str
