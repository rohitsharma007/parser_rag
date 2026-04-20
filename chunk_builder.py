"""
chunk_builder.py — Converts parsed Java class data into PGVector-ready chunks.

Each chunk is a self-contained dict with:
  - chunk_id     : deterministic SHA-256 fingerprint (16-char hex)
  - chunk_type   : "class" or "method"
  - content      : the text to embed
  - metadata     : structured dict for filtering / relational joins

Chunk content strategy
───────────────────────
CLASS chunk
  Captures the class's identity, structure, and dependency surface.
  Does NOT include full method bodies (those go in METHOD chunks) so the
  class chunk stays focused on "what this class IS and USES".

  Content includes:
    • Class name, layer, package, annotations
    • Extends / implements
    • Field inventory (type + variable name)
    • Method name list with their annotations
    • Object instantiations (new ClassName() anywhere in the class)

METHOD chunk
  Captures one method in full context.
  Content includes:
    • Header: class, layer, method name, annotations, comment
    • Full method source code
  Metadata includes:
    • Selenium actions, object creations, method calls

Why keep them separate?
  Retrieval queries split naturally:
    "What test classes use Login_Page?"  → CLASS chunks (metadata filter)
    "How does testSuccessfulLogin work?" → METHOD chunks (semantic similarity)

Usage:
    from chunk_builder import ChunkBuilder

    builder = ChunkBuilder(symbol_table=st, relationships=all_rels)
    class_chunk  = builder.build_class_chunk(cls)
    method_chunks = builder.build_method_chunks(cls)
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    """
    One embedding-ready unit.

    Store `content` in the pgvector column.
    Store `metadata` in a JSONB column alongside the vector.
    Use `chunk_id` as the primary key.
    """
    chunk_id: str         # 16-char deterministic hex fingerprint
    chunk_type: str       # "class" | "method"
    class_name: str
    method_name: str = "" # empty for class-level chunks

    # ── Text to embed ────────────────────────────────────────────────
    content: str = ""

    # ── Structured metadata for filtering / joins ────────────────────
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

class ChunkBuilder:
    """
    Builds Chunk objects from EnhancedClassInfo data.

    Accepts an optional SymbolTable and pre-computed relationships list so
    that each chunk's metadata can include resolved dependency info.
    """

    def __init__(
        self,
        symbol_table=None,
        relationships=None,   # list[Relationship]
    ) -> None:
        self._st = symbol_table

        # Build relationship index keyed by source FQN for O(1) lookup.
        # rel_index[fqn] = [Relationship, ...]
        self._rel_index: dict[str, list] = {}
        if relationships:
            for r in relationships:
                self._rel_index.setdefault(r.source_class, []).append(r)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_class_chunk(
        self,
        cls,              # EnhancedClassInfo
        file_path: str = "",
    ) -> Chunk:
        """
        One chunk per class — structure + dependency summary.

        Avoids embedding full method bodies so the class vector stays
        focused on the class's role, not its implementation details.
        """
        fp   = file_path or cls.file_path
        fqn  = f"{cls.package}.{cls.name}" if cls.package else cls.name
        rels = self._rel_index.get(fqn, [])

        # ── Derived dependency lists ──────────────────────────────────
        extends_list    = [r.target_simple for r in rels if r.relation_type == "EXTENDS"]
        uses_pages      = sorted({
            r.target_simple for r in rels
            if r.relation_type == "USES_STRONG"
            and r.target_layer in ("ui", "api", "page", "service")
        })
        all_strong_deps = sorted({
            r.target_simple for r in rels
            if r.relation_type == "USES_STRONG"
        })
        all_dep_meta    = [
            {"target": r.target_simple, "type": r.relation_type, "layer": r.target_layer}
            for r in rels
            if r.relation_type in ("EXTENDS", "IMPLEMENTS", "USES_STRONG")
        ]

        # ── Content text (what gets embedded) ────────────────────────
        lines: list[str] = [
            f"Class: {cls.name}",
            f"Layer: {cls.layer}",
        ]
        if cls.package:
            lines.append(f"Package: {cls.package}")
        if cls.annotations:
            lines.append(f"Annotations: {', '.join(cls.annotations)}")
        if cls.extends:
            lines.append(f"Extends: {cls.extends}")
        if cls.implements:
            lines.append(f"Implements: {', '.join(cls.implements)}")
        if cls.fields:
            field_strs = [f"{f.type_name} {f.variable_name}" for f in cls.fields]
            lines.append(f"Fields: {', '.join(field_strs)}")
        if cls.methods:
            lines.append("")
            lines.append("Methods:")
            for m in cls.methods:
                ann_str = f"  [{', '.join(m.annotations)}]" if m.annotations else ""
                lines.append(f"  - {m.name}{ann_str}")
        if cls.object_creations:
            lines.append("")
            lines.append(f"Instantiates: {', '.join(cls.object_creations)}")
        if uses_pages:
            lines.append(f"Uses pages/services: {', '.join(uses_pages)}")

        content = "\n".join(lines).strip()

        # ── Metadata ─────────────────────────────────────────────────
        metadata: dict = {
            "chunk_type":       "class",
            "layer":            cls.layer,
            "package":          cls.package,
            "file_path":        fp,
            "extends":          cls.extends or None,
            "implements":       cls.implements,
            "annotations":      cls.annotations,
            "fields": [
                {"type": f.type_name, "name": f.variable_name}
                for f in cls.fields
            ],
            "method_names":     [m.name for m in cls.methods],
            "object_creations": cls.object_creations,
            "uses_pages":       uses_pages,
            "dependencies":     all_dep_meta,
        }

        return Chunk(
            chunk_id=_make_id(fp, cls.name),
            chunk_type="class",
            class_name=cls.name,
            content=content,
            metadata=metadata,
        )

    def build_method_chunks(
        self,
        cls,              # EnhancedClassInfo
        file_path: str = "",
    ) -> list[Chunk]:
        """
        One chunk per method — full source code in context.

        Each chunk includes a class-context header so the embedding captures
        both WHAT the method does and WHERE it lives (which class, layer).
        """
        fp = file_path or cls.file_path
        chunks: list[Chunk] = []

        for method in cls.methods:
            # ── Content ──────────────────────────────────────────────
            header_lines: list[str] = [
                f"Class: {cls.name}  |  Layer: {cls.layer}",
                f"Method: {method.name}",
            ]
            if method.annotations:
                header_lines.append(f"Annotations: {', '.join(method.annotations)}")
            if method.comments:
                header_lines.append(f"Comment: {method.comments}")
            if method.selenium_actions:
                header_lines.append(
                    f"Selenium actions: {', '.join(method.selenium_actions)}"
                )
            # Include each call with its actual arguments so the embedding
            # captures WHAT was called and WITH WHAT VALUES (not just a label).
            if method.method_calls:
                call_strs = [
                    f"{c['full_call']}({', '.join(c['arguments'])})"
                    for c in method.method_calls
                ]
                header_lines.append(f"Method calls: {'; '.join(call_strs)}")

            # Raw code is always preserved — never replaced with a summary.
            content = "\n".join(header_lines) + "\n\n" + method.code

            # ── Metadata ─────────────────────────────────────────────
            # method_calls is now a list of structured dicts:
            #   {object, method, full_call, arguments}
            # This gives downstream consumers both human-readable and
            # machine-parseable call detail without losing argument values.
            metadata: dict = {
                "chunk_type":       "method",
                "layer":            cls.layer,
                "class_name":       cls.name,
                "package":          cls.package,
                "file_path":        fp,
                "annotations":      method.annotations,
                "selenium_actions": method.selenium_actions,
                "object_creations": method.object_creations,
                "method_calls":     method.method_calls,
                "comments":         method.comments,
            }

            chunks.append(Chunk(
                chunk_id=_make_id(fp, cls.name, method.name),
                chunk_type="method",
                class_name=cls.name,
                method_name=method.name,
                content=content.strip(),
                metadata=metadata,
            ))

        return chunks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_id(*parts: str) -> str:
    """
    Build a deterministic 16-char hex chunk ID from its identifying parts.

    Using SHA-256 means:
      - Same file + class + method always produces the same ID
      - IDs survive reruns → safe for upserts in pgvector
    """
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
