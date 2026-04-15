"""
repo_parser.py — Orchestrates the full two-pass repository parse.

Architecture (incremental, built on top of existing parser.py):

  ┌──────────────────────────────────────────────────────────────┐
  │                        repo_parser.py                        │
  │                    (you are here — glue)                     │
  └──┬──────────┬──────────┬───────────────┬────────────────────┘
     │          │          │               │
     ▼          ▼          ▼               ▼
  repo_     symbol_   relationship_    chunk_
  scanner   table     extractor        builder
  (paths)   (Pass 1)  (Pass 2)         (Pass 2)
     │
     └──► enhanced_parser
              │
              └──► parser.py  ← UNCHANGED base

Two-pass strategy
─────────────────
  Pass 1  (fast)
    Scan every .java file, run EnhancedJavaParser.parse_file_enhanced(),
    register class name + package + layer in the SymbolTable.
    No method bodies read; purpose is symbol discovery only.

  Pass 2  (full)
    Re-parse every file (full AST) to extract relationships and build chunks.
    The SymbolTable from Pass 1 is used to resolve class references.

CLI usage:
    python repo_parser.py /path/to/repo
    python repo_parser.py /path/to/repo --pretty
    python repo_parser.py /path/to/repo --output result.json
    python repo_parser.py /path/to/repo --no-method-chunks
    python repo_parser.py /path/to/repo --include-external

Module usage:
    from repo_parser import RepoParser

    result = RepoParser().parse("/path/to/repo")
    print(result.summary())

    for chunk in result.chunks:
        embed_and_upsert(chunk.content, chunk.metadata, id=chunk.chunk_id)

    for rel in result.relationships:
        insert_relationship_row(rel)
"""

from __future__ import annotations

import argparse
import json
import logging
import pathlib
import sys
import time
from dataclasses import asdict, dataclass, field

# ── Bootstrap local import path ────────────────────────────────────────────
_HERE = str(pathlib.Path(__file__).parent.resolve())
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from repo_scanner         import RepoScanner, ScannedFile
from enhanced_parser      import EnhancedJavaParser, EnhancedFileResult
from symbol_table         import SymbolTable, ClassSymbol
from relationship_extractor import RelationshipExtractor, Relationship
from chunk_builder        import ChunkBuilder, Chunk

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------

@dataclass
class RepoParseResult:
    """Complete output of parsing a repository."""
    repo_root: str
    total_files: int = 0
    total_classes: int = 0
    chunks: list[Chunk] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    elapsed_ms: float = 0.0

    # ── Serialisation ────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """
        Return a JSON-serialisable dict.

        Shape:
        {
          "summary": { ... },
          "chunks":  [ { chunk_id, chunk_type, class_name, content, metadata } ],
          "relationships": [ { source_class, target_class, relation_type, ... } ],
          "errors": [ { "file": ..., "error": ... } ]
        }
        """
        return {
            "repo_root": self.repo_root,
            "summary": {
                "total_files":         self.total_files,
                "total_classes":       self.total_classes,
                "total_chunks":        len(self.chunks),
                "class_chunks":        sum(1 for c in self.chunks if c.chunk_type == "class"),
                "method_chunks":       sum(1 for c in self.chunks if c.chunk_type == "method"),
                "total_relationships": len(self.relationships),
                "by_relation_type": {
                    rtype: sum(1 for r in self.relationships if r.relation_type == rtype)
                    for rtype in ("EXTENDS", "IMPLEMENTS", "USES_STRONG", "USES")
                },
                "errors":              len(self.errors),
                "elapsed_ms":          round(self.elapsed_ms, 2),
            },
            "chunks":        [c.to_dict() for c in self.chunks],
            "relationships": [asdict(r) for r in self.relationships],
            "errors":        self.errors,
        }

    def summary(self) -> str:
        """Human-readable one-page summary."""
        rel_counts = {
            rtype: sum(1 for r in self.relationships if r.relation_type == rtype)
            for rtype in ("EXTENDS", "IMPLEMENTS", "USES_STRONG", "USES")
        }
        class_chunks  = sum(1 for c in self.chunks if c.chunk_type == "class")
        method_chunks = sum(1 for c in self.chunks if c.chunk_type == "method")
        lines = [
            f"Repository : {self.repo_root}",
            f"Files      : {self.total_files}",
            f"Classes    : {self.total_classes}",
            f"Chunks     : {len(self.chunks)}  (class={class_chunks}, method={method_chunks})",
            f"Relationships:",
            *[f"  {k:12s}: {v}" for k, v in rel_counts.items()],
            f"Errors     : {len(self.errors)}",
            f"Time       : {self.elapsed_ms:.1f} ms",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class RepoParser:
    """
    Full two-pass repository parser.

    Pass 1 — Symbol table (fast, lightweight)
        Scan all .java files, extract class names + packages → SymbolTable.

    Pass 2 — Full AST + Relationships + Chunks
        Re-parse each file with EnhancedJavaParser.
        Use SymbolTable to resolve cross-class references.
        Build Relationship objects and PGVector-ready Chunks.
    """

    def __init__(
        self,
        build_method_chunks: bool = True,
        include_external_rels: bool = False,
        layer_rules: list[tuple[str, str]] | None = None,
    ) -> None:
        """
        build_method_chunks    — also emit per-method chunks (default: True)
        include_external_rels  — keep rels to external/stdlib classes (default: False)
        layer_rules            — custom layer rules for RepoScanner (default: built-in)
        """
        self._build_method_chunks   = build_method_chunks
        self._include_external_rels = include_external_rels
        self._scanner = RepoScanner(layer_rules=layer_rules)
        self._ep      = EnhancedJavaParser()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, repo_root: str) -> RepoParseResult:
        """
        Parse a repository root directory and return a RepoParseResult.

        Safe to call on any directory — files that fail to parse are
        recorded in result.errors and skipped (never aborts the whole run).
        """
        t0 = time.perf_counter()
        result = RepoParseResult(repo_root=repo_root)

        # ── Pass 1: Discover files + build symbol table ───────────────
        logger.info("Pass 1 — Scanning repository: %s", repo_root)
        scanned: list[ScannedFile] = self._scanner.scan(repo_root)
        result.total_files = len(scanned)

        if not scanned:
            logger.warning("No Java files found under %s", repo_root)
            return result

        layer_counts = {}
        for f in scanned:
            layer_counts[f.layer] = layer_counts.get(f.layer, 0) + 1
        logger.info(
            "Found %d Java files: %s",
            len(scanned),
            ", ".join(f"{l}={n}" for l, n in sorted(layer_counts.items())),
        )

        symbol_table: SymbolTable = SymbolTable.build(scanned, self._ep)

        # ── Pass 2: Full parse → relationships + chunks ───────────────
        logger.info("Pass 2 — Full AST parse (%d files) …", len(scanned))
        extractor     = RelationshipExtractor(symbol_table)
        all_results:  list[EnhancedFileResult] = []

        for sf in scanned:
            try:
                file_result = self._ep.parse_file_enhanced(
                    sf.absolute_path, layer=sf.layer
                )
                all_results.append(file_result)
                result.total_classes += len(file_result.classes)

                rels = extractor.extract(file_result)
                if not self._include_external_rels:
                    rels = [r for r in rels if r.target_layer != "external"]
                result.relationships.extend(rels)

            except Exception as exc:
                logger.warning("Parse failed: %s — %s", sf.relative_path, exc)
                result.errors.append({"file": sf.relative_path, "error": str(exc)})

        # ── Build chunks (needs full relationship set for metadata) ───
        logger.info(
            "Building chunks for %d classes …", result.total_classes
        )
        builder = ChunkBuilder(
            symbol_table=symbol_table,
            relationships=result.relationships,
        )

        for file_result in all_results:
            for cls in file_result.classes:
                fp = file_result.file_path
                result.chunks.append(builder.build_class_chunk(cls, fp))
                if self._build_method_chunks:
                    result.chunks.extend(builder.build_method_chunks(cls, fp))

        result.elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "Done: %d chunks, %d relationships in %.1f ms",
            len(result.chunks),
            len(result.relationships),
            result.elapsed_ms,
        )
        return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="repo_parser.py",
        description=(
            "Parse a Java repository with Tree-sitter and output "
            "PGVector-ready chunks + relationship graph as JSON."
        ),
    )
    ap.add_argument(
        "repo_root",
        help="Path to the root of the Java repository.",
    )
    ap.add_argument(
        "--output", "-o",
        metavar="FILE",
        default=None,
        help="Write JSON output to FILE (default: stdout).",
    )
    ap.add_argument(
        "--pretty",
        action="store_true",
        default=False,
        help="Pretty-print JSON output (indent=2).",
    )
    ap.add_argument(
        "--no-method-chunks",
        action="store_true",
        default=False,
        help="Omit per-method chunks (only emit class-level chunks).",
    )
    ap.add_argument(
        "--include-external",
        action="store_true",
        default=False,
        help="Include relationships to external/stdlib classes.",
    )
    ap.add_argument(
        "--summary-only",
        action="store_true",
        default=False,
        help="Print a human-readable summary instead of JSON.",
    )
    return ap


def main(argv: list[str] | None = None) -> None:
    ap = _build_arg_parser()
    args = ap.parse_args(argv)

    repo_root = pathlib.Path(args.repo_root)
    if not repo_root.is_dir():
        print(f"[ERROR] Not a directory: {repo_root}", file=sys.stderr)
        sys.exit(1)

    parser = RepoParser(
        build_method_chunks=not args.no_method_chunks,
        include_external_rels=args.include_external,
    )
    result = parser.parse(str(repo_root))

    if args.summary_only:
        print(result.summary())
        return

    indent = 2 if args.pretty else None
    output_str = json.dumps(result.to_dict(), indent=indent, ensure_ascii=False)

    if args.output:
        pathlib.Path(args.output).write_text(output_str, encoding="utf-8")
        print(f"Output written to: {args.output}", file=sys.stderr)
    else:
        print(output_str)


if __name__ == "__main__":
    main()
