"""
repo_scanner.py — Walks a Java repository and assigns semantic layer tags.

Layer assignment is purely path-based (no parsing required) so this runs
in milliseconds even on large repositories.

Layer rules (first match wins):
  Path contains …                 → layer
  ─────────────────────────────────────────
  testcases/                      → test
  pages/api/  or  pages\\api\\    → api
  pages/atrwebportal/             → ui
  businessfunctions/              → service
  retryanalyzer/                  → utility
  pages/  (catch-all for pages)  → page
  File stem starts with "Base"   → base
  (no match)                      → unknown

Usage:
    from repo_scanner import RepoScanner

    scanner = RepoScanner()
    files = scanner.scan("/path/to/apm001302-atr-enterpriseautomationframework-3.0-testing")

    for f in files:
        print(f.layer, f.relative_path)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ScannedFile:
    """Metadata about one discovered Java file."""
    absolute_path: str    # full OS path for reading
    relative_path: str    # path relative to repo root (for display / metadata)
    layer: str            # semantic layer tag
    file_name: str        # e.g. "Login_Page.java"
    class_name: str       # stem of the file, assumed to match the public class name


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

class RepoScanner:
    """
    Discovers all .java files under a repository root and assigns each a
    semantic layer tag based on its directory path.

    The rules list is ordered — first match wins — and can be customised by
    subclassing or by passing a custom `layer_rules` list at construction time.
    """

    #: Default ordered rules: (path-fragment-lowercase, layer-name)
    DEFAULT_LAYER_RULES: list[tuple[str, str]] = [
        ("testcases",           "test"),
        ("pages/api",           "api"),
        ("pages\\api",          "api"),      # Windows path separator
        ("pages/atrwebportal",  "ui"),
        ("pages\\atrwebportal", "ui"),
        ("businessfunctions",   "service"),
        ("retryanalyzer",       "utility"),
        ("pages",               "page"),     # catch-all for other page dirs
    ]

    #: File-stem prefixes that override path-based rules (e.g. BaseTest.java)
    BASE_PREFIXES: tuple[str, ...] = ("Base",)

    def __init__(
        self,
        layer_rules: list[tuple[str, str]] | None = None,
        exclude_dirs: set[str] | None = None,
    ) -> None:
        """
        layer_rules  — custom ordered rules (overrides DEFAULT_LAYER_RULES)
        exclude_dirs — directory names to skip entirely (default: .git, target, build)
        """
        self._rules = layer_rules if layer_rules is not None else self.DEFAULT_LAYER_RULES
        self._exclude = exclude_dirs or {".git", "target", "build", ".idea", "node_modules"}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self, repo_root: str) -> list[ScannedFile]:
        """
        Recursively find every *.java file under repo_root.

        Returns a list of ScannedFile objects sorted by relative_path so
        that downstream processing is deterministic.
        """
        root = Path(repo_root).resolve()
        files: list[ScannedFile] = []

        for java_file in self._iter_java_files(root):
            try:
                rel = java_file.relative_to(root)
            except ValueError:
                rel = java_file  # shouldn't happen but be safe

            rel_str = rel.as_posix()  # always forward slashes for consistency
            stem = java_file.stem

            files.append(ScannedFile(
                absolute_path=str(java_file),
                relative_path=rel_str,
                layer=self._get_layer(rel_str, stem),
                file_name=java_file.name,
                class_name=stem,
            ))

        return sorted(files, key=lambda f: f.relative_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _iter_java_files(self, root: Path):
        """Walk the tree, yielding .java files while skipping excluded dirs."""
        for item in root.iterdir():
            if item.is_dir():
                if item.name not in self._exclude:
                    yield from self._iter_java_files(item)
            elif item.is_file() and item.suffix.lower() == ".java":
                yield item

    def _get_layer(self, rel_path: str, stem: str) -> str:
        """
        Assign a layer to a file.

        Priority order:
          1. Base-prefix check (BaseTest.java → "base")
          2. Path-fragment rules (ordered, first match wins)
          3. Default "unknown"
        """
        # 1. Stem-prefix rules take priority over path rules
        for prefix in self.BASE_PREFIXES:
            if stem.startswith(prefix):
                return "base"

        # 2. Path-fragment matching (case-insensitive, forward-slash normalised)
        norm = rel_path.lower()
        for fragment, layer in self._rules:
            if fragment.lower() in norm:
                return layer

        return "unknown"

    # ------------------------------------------------------------------
    # Convenience: group by layer
    # ------------------------------------------------------------------

    @staticmethod
    def group_by_layer(files: list[ScannedFile]) -> dict[str, list[ScannedFile]]:
        """Return a dict mapping layer → list of ScannedFile."""
        groups: dict[str, list[ScannedFile]] = {}
        for f in files:
            groups.setdefault(f.layer, []).append(f)
        return groups
