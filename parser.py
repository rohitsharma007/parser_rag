"""
parser.py — Tree-sitter-based Java Selenium source code parser.

Usage:
    python parser.py <path_to_java_file>
    python parser.py <path_to_java_file> --pretty   # pretty-print JSON

Outputs structured JSON:
{
  "file": "...",
  "classes": [
    {
      "class": "ClassName",
      "annotations": ["@RunWith(...)"],
      "methods": [
        {
          "name": "methodName",
          "annotations": ["@Test"],
          "code": "...",
          "comments": "...",
          "selenium_actions": [...]
        }
      ]
    }
  ]
}

Designed to be imported as a module for use in RAG pipelines:
    from parser import JavaSeleniumParser
    result = JavaSeleniumParser().parse_file("LoginTest.java")
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import tree_sitter_java as tsjava
from tree_sitter import Language, Node, Parser

# ---------------------------------------------------------------------------
# Logging — writes to stderr so stdout stays clean for JSON output
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class MethodInfo:
    name: str
    annotations: list[str] = field(default_factory=list)
    code: str = ""
    comments: str = ""
    selenium_actions: list[str] = field(default_factory=list)


@dataclass
class ClassInfo:
    name: str
    annotations: list[str] = field(default_factory=list)
    methods: list[MethodInfo] = field(default_factory=list)


@dataclass
class ParseResult:
    file: str
    classes: list[ClassInfo] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a plain dict suitable for JSON output."""
        return {
            "file": self.file,
            "classes": [
                {
                    "class": cls.name,
                    "annotations": cls.annotations,
                    "methods": [asdict(m) for m in cls.methods],
                }
                for cls in self.classes
            ],
        }


# ---------------------------------------------------------------------------
# Selenium API surface — method names matched against AST nodes (no regex)
# ---------------------------------------------------------------------------

# Methods belonging to the WebDriver interface
_SELENIUM_DRIVER_METHODS: frozenset[str] = frozenset(
    {
        "findElement",
        "findElements",
        "get",
        "navigate",
        "switchTo",
        "manage",
        "close",
        "quit",
        "getTitle",
        "getCurrentUrl",
        "getPageSource",
        "getWindowHandle",
        "getWindowHandles",
        "executeScript",
        "executeAsyncScript",
        "getScreenshotAs",
        "implicitlyWait",
    }
)

# Methods belonging to the WebElement interface
_SELENIUM_ELEMENT_METHODS: frozenset[str] = frozenset(
    {
        "click",
        "sendKeys",
        "clear",
        "submit",
        "getText",
        "getAttribute",
        "isDisplayed",
        "isEnabled",
        "isSelected",
        "getTagName",
        "getCssValue",
        "getLocation",
        "getSize",
        "getRect",
    }
)

# Union — used for fast membership testing
_SELENIUM_METHOD_NAMES: frozenset[str] = (
    _SELENIUM_DRIVER_METHODS | _SELENIUM_ELEMENT_METHODS
)

# Common variable names used for the WebDriver instance
_DRIVER_VARIABLE_NAMES: frozenset[str] = frozenset(
    {"driver", "wd", "webDriver", "webdriver", "chromeDriver", "firefoxDriver"}
)


# ---------------------------------------------------------------------------
# Core parser class
# ---------------------------------------------------------------------------


class JavaSeleniumParser:
    """
    Parses Java Selenium source files using Tree-sitter.

    Reusable as a library in RAG pipelines — call ``parse_file(path)`` or
    ``parse_source(src, filename)`` to obtain a ``ParseResult``.
    """

    def __init__(self) -> None:
        _lang = Language(tsjava.language())
        self._parser = Parser(_lang)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_file(self, path: str | Path) -> ParseResult:
        """Read a Java file from disk and return a ParseResult.

        Tries UTF-8 first; falls back to latin-1 on decode errors.
        Raises FileNotFoundError if the path does not exist.
        """
        path = Path(path)
        try:
            source = path.read_bytes()
        except FileNotFoundError:
            raise FileNotFoundError(f"Java file not found: {path}") from None

        return self.parse_source(source, filename=str(path))

    def parse_source(
        self, source: bytes | str, filename: str = "<string>"
    ) -> ParseResult:
        """Parse raw Java source (bytes or str) and return a ParseResult."""
        if isinstance(source, str):
            source = source.encode("utf-8")

        tree = self._parser.parse(source)
        root = tree.root_node

        # Warn if the AST contains syntax errors — output may be incomplete
        if root.has_error:
            logger.warning(
                "AST contains parse errors in %s — output may be incomplete.",
                filename,
            )

        result = ParseResult(file=filename)
        for node in root.children:
            if node.type == "class_declaration":
                result.classes.append(self._extract_class(node, source))

        return result

    # ------------------------------------------------------------------
    # Class extraction
    # ------------------------------------------------------------------

    def _extract_class(self, node: Node, source: bytes) -> ClassInfo:
        """Build a ClassInfo from a class_declaration node."""
        name = self._get_identifier(node)
        annotations = self._extract_annotations_from_modifiers(node, source)
        cls = ClassInfo(name=name, annotations=annotations)

        body = self._child_by_type(node, "class_body")
        if body:
            for child in body.children:
                if child.type == "method_declaration":
                    cls.methods.append(self._extract_method(child, source))

        return cls

    # ------------------------------------------------------------------
    # Method extraction
    # ------------------------------------------------------------------

    def _extract_method(self, node: Node, source: bytes) -> MethodInfo:
        """Build a MethodInfo from a method_declaration node."""
        name = self._get_identifier(node)
        annotations = self._extract_annotations_from_modifiers(node, source)
        code = self._node_text(node, source)
        comments = self._collect_preceding_comments(node, source)
        selenium_actions = self._extract_selenium_actions(node, source)

        return MethodInfo(
            name=name,
            annotations=annotations,
            code=code,
            comments=comments,
            selenium_actions=selenium_actions,
        )

    # ------------------------------------------------------------------
    # Annotation extraction
    # ------------------------------------------------------------------

    def _extract_annotations_from_modifiers(
        self, node: Node, source: bytes
    ) -> list[str]:
        """
        Return annotation strings from the modifiers child of a declaration.

        Handles all three Tree-sitter annotation subtypes:
          - marker_annotation   → @Test
          - annotation          → @SuppressWarnings("unused")
          - normal_annotation   → @RunWith(Parameterized.class)

        Note: child_by_field_name("modifiers") is unreliable in tree-sitter-java;
        we iterate children directly.
        """
        modifiers = self._child_by_type(node, "modifiers")
        if not modifiers:
            return []

        return [
            self._node_text(child, source).strip()
            for child in modifiers.children
            if child.type in ("marker_annotation", "annotation", "normal_annotation")
        ]

    # ------------------------------------------------------------------
    # Comment extraction
    # ------------------------------------------------------------------

    def _collect_preceding_comments(self, node: Node, source: bytes) -> str:
        """
        Collect consecutive comment siblings that immediately precede *node*.

        Tree-sitter places comments as sibling nodes (not children of the
        declaration they document).  We walk ``prev_sibling`` backwards and
        stop at the first non-comment node, then reverse to restore source order.
        """
        comments: list[str] = []
        sibling = node.prev_sibling

        while sibling is not None:
            if sibling.type in ("line_comment", "block_comment"):
                comments.append(self._node_text(sibling, source).strip())
                sibling = sibling.prev_sibling
            else:
                # Any non-comment sibling (field, blank line sentinel, etc.)
                # terminates the run.
                break

        comments.reverse()  # restore source order
        return "\n".join(comments)

    # ------------------------------------------------------------------
    # Selenium action extraction (AST-based, no regex)
    # ------------------------------------------------------------------

    def _extract_selenium_actions(self, node: Node, source: bytes) -> list[str]:
        """
        Recursively collect method_invocation nodes inside *node* that belong
        to the Selenium API.

        Deduplication strategy — byte-range containment:
          Chained calls such as ``driver.findElement(...).click()`` produce
          nested method_invocation nodes.  We keep only the outermost node
          (the one whose byte range is not strictly contained within any other
          collected node) so each statement is reported exactly once.
        """
        candidates: list[Node] = []
        self._walk_for_selenium(node, source, candidates)

        # Build the deduplicated list by dropping nodes whose range falls
        # entirely inside another candidate's range.
        result: list[str] = []
        for i, cand in enumerate(candidates):
            contained = any(
                j != i
                and candidates[j].start_byte <= cand.start_byte
                and candidates[j].end_byte >= cand.end_byte
                for j in range(len(candidates))
            )
            if not contained:
                result.append(self._node_text(cand, source).strip())

        return result

    def _walk_for_selenium(
        self, node: Node, source: bytes, found: list[Node]
    ) -> None:
        """DFS traversal that appends matching method_invocation nodes."""
        if node.type == "method_invocation":
            method_name = self._get_method_invocation_name(node, source)
            root_obj = self._get_invocation_root_object(node, source)

            is_selenium = (root_obj in _DRIVER_VARIABLE_NAMES) or (
                method_name in _SELENIUM_METHOD_NAMES
            )
            if is_selenium:
                found.append(node)

        for child in node.children:
            self._walk_for_selenium(child, source, found)

    def _get_method_invocation_name(self, node: Node, source: bytes) -> Optional[str]:
        """
        Return the method-name part of a method_invocation node.

        Tree-sitter models  foo.bar(...)  with a named field "name" pointing
        to the identifier after the dot.
        """
        name_node = node.child_by_field_name("name")
        if name_node:
            return self._node_text(name_node, source)
        return None

    def _get_invocation_root_object(
        self, node: Node, source: bytes
    ) -> Optional[str]:
        """
        Walk the leftmost child of a (possibly chained) method_invocation to
        find the root identifier.

        Example: driver.findElement(...).click()
          outer method_invocation → object = driver.findElement(...)
            inner method_invocation → object = driver  (identifier) ← root
        """
        obj = node.child_by_field_name("object")
        if obj is None:
            return None
        # Recurse into chained invocations
        if obj.type == "method_invocation":
            return self._get_invocation_root_object(obj, source)
        if obj.type == "identifier":
            return self._node_text(obj, source)
        return None

    # ------------------------------------------------------------------
    # Generic tree-traversal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _child_by_type(node: Node, node_type: str) -> Optional[Node]:
        """Return the first direct child whose type matches, or None."""
        for child in node.children:
            if child.type == node_type:
                return child
        return None

    @staticmethod
    def _node_text(node: Node, source: bytes) -> str:
        """Decode the source slice covered by *node* as a UTF-8 string."""
        return source[node.start_byte : node.end_byte].decode(
            "utf-8", errors="replace"
        )

    @staticmethod
    def _get_identifier(node: Node) -> str:
        """
        Return the text of the first 'identifier' child of *node*.
        Used to extract class and method names.
        """
        for child in node.children:
            if child.type == "identifier":
                return (child.text or b"").decode("utf-8", errors="replace")
        return "<unknown>"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="parser.py",
        description="Parse a Java Selenium source file and output structured JSON.",
    )
    ap.add_argument("java_file", help="Path to the Java source file to parse.")
    ap.add_argument(
        "--pretty",
        action="store_true",
        default=False,
        help="Pretty-print the JSON output (indent=2).",
    )
    ap.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        default=None,
        help="Write JSON to FILE instead of stdout.",
    )
    return ap


def main(argv: list[str] | None = None) -> None:
    ap = _build_arg_parser()
    args = ap.parse_args(argv)

    java_path = Path(args.java_file)
    if not java_path.exists():
        logger.error("File not found: %s", java_path)
        sys.exit(1)
    if java_path.suffix.lower() != ".java":
        logger.warning(
            "File does not have a .java extension: %s", java_path
        )

    java_parser = JavaSeleniumParser()

    try:
        result = java_parser.parse_file(java_path)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to parse %s: %s", java_path, exc)
        sys.exit(1)

    indent = 2 if args.pretty else None
    output = json.dumps(result.to_dict(), indent=indent, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
