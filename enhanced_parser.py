"""
enhanced_parser.py — Extends JavaSeleniumParser for repository-level AST extraction.

Adds extraction on top of the base parser (parser.py) without modifying it:
  - package_declaration      → package name
  - import_declaration       → all imported class/package names
  - superclass field         → EXTENDS target (class name)
  - interfaces field         → IMPLEMENTS targets
  - field_declaration        → field types and variable names
  - object_creation_expression → class names instantiated with `new`
  - method_invocation        → (object, method) call pairs (best-effort)

Usage:
    from enhanced_parser import EnhancedJavaParser
    parser = EnhancedJavaParser()
    result = parser.parse_file_enhanced("LoginTest.java", layer="test")

    for cls in result.classes:
        print(cls.name, "extends", cls.extends)
        print("instantiates:", cls.object_creations)
"""

from __future__ import annotations

import logging
import pathlib
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Bootstrap sys.path so 'parser' resolves to our local parser.py, not the
# deprecated stdlib parser module that still exists on Python 3.9–3.11.
# ---------------------------------------------------------------------------
_HERE = str(pathlib.Path(__file__).parent.resolve())
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from parser import JavaSeleniumParser, MethodInfo  # noqa: E402

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enhanced data models
# ---------------------------------------------------------------------------

@dataclass
class FieldInfo:
    """A single field declaration inside a class body."""
    type_name: str       # e.g. "Login_Page", "WebDriver", "String"
    variable_name: str   # e.g. "loginPage", "driver"


@dataclass
class EnhancedMethodInfo:
    """Method info extended with instantiation and call-site data."""
    name: str
    annotations: list[str] = field(default_factory=list)
    code: str = ""
    comments: str = ""
    selenium_actions: list[str] = field(default_factory=list)
    # new ClassName() expressions found inside this method
    object_creations: list[str] = field(default_factory=list)
    # Structured call records: {object, method, full_call, arguments}
    method_calls: list[dict] = field(default_factory=list)


@dataclass
class EnhancedClassInfo:
    """Class info extended with import/inheritance/field/instantiation data."""
    name: str
    file_path: str = ""
    package: str = ""
    layer: str = "unknown"
    annotations: list[str] = field(default_factory=list)
    extends: str = ""                            # single superclass name
    implements: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)  # file-level imports
    fields: list[FieldInfo] = field(default_factory=list)
    methods: list[EnhancedMethodInfo] = field(default_factory=list)
    # Deduplicated list of all class names instantiated anywhere in this class
    object_creations: list[str] = field(default_factory=list)


@dataclass
class EnhancedFileResult:
    """Top-level result of parsing one Java file with the enhanced parser."""
    file_path: str
    package: str = ""
    imports: list[str] = field(default_factory=list)
    classes: list[EnhancedClassInfo] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Enhanced parser — inherits ALL existing extraction; adds new layers
# ---------------------------------------------------------------------------

class EnhancedJavaParser(JavaSeleniumParser):
    """
    Extends JavaSeleniumParser with cross-file relationship data.

    Inherits unchanged:
        parse_file(), parse_source()  → produce ParseResult (base format)
        _extract_class(), _extract_method(), _extract_selenium_actions() …

    Adds new public methods:
        parse_file_enhanced()   → EnhancedFileResult
        parse_source_enhanced() → EnhancedFileResult
    """

    # ------------------------------------------------------------------
    # Public enhanced API
    # ------------------------------------------------------------------

    def parse_file_enhanced(
        self, path: str | Path, layer: str = "unknown"
    ) -> EnhancedFileResult:
        """Read a Java file and return an EnhancedFileResult."""
        path = Path(path)
        source = path.read_bytes()
        return self.parse_source_enhanced(
            source, filename=str(path), layer=layer
        )

    def parse_source_enhanced(
        self,
        source: bytes | str,
        filename: str = "<string>",
        layer: str = "unknown",
    ) -> EnhancedFileResult:
        """Parse Java source (bytes or str) and return an EnhancedFileResult."""
        if isinstance(source, str):
            source = source.encode("utf-8")

        tree = self._parser.parse(source)
        root = tree.root_node

        if root.has_error:
            logger.warning("AST has parse errors in %s — output may be incomplete.", filename)

        result = EnhancedFileResult(file_path=filename)
        result.package = self._extract_package(root, source)
        result.imports = self._extract_imports(root, source)

        for node in root.children:
            if node.type == "class_declaration":
                cls = self._extract_enhanced_class(
                    node, source, filename, layer, result.imports
                )
                cls.package = result.package
                result.classes.append(cls)

        return result

    # ------------------------------------------------------------------
    # Package extraction
    # ------------------------------------------------------------------

    def _extract_package(self, root, source: bytes) -> str:
        """
        Extract the package name from a package_declaration node.

        AST shape:
            package_declaration
              "package"
              scoped_identifier | identifier   ← the package string
              ";"
        """
        for child in root.children:
            if child.type == "package_declaration":
                for c in child.children:
                    if c.type in ("scoped_identifier", "identifier"):
                        return self._node_text(c, source)
        return ""

    # ------------------------------------------------------------------
    # Import extraction
    # ------------------------------------------------------------------

    def _extract_imports(self, root, source: bytes) -> list[str]:
        """
        Collect all import statements at the file level.

        AST shape:
            import_declaration
              "import" ["static"]
              scoped_identifier | identifier
              ";"

        Returns simple strings like "org.junit.Test" or "com.ntrs.demoapp.pages.atrwebportal.Login_Page".
        Wildcard imports (import foo.*) are kept as-is.
        """
        imports: list[str] = []
        for child in root.children:
            if child.type == "import_declaration":
                for c in child.children:
                    if c.type in ("scoped_identifier", "identifier", "asterisk"):
                        imports.append(self._node_text(c, source))
        return imports

    # ------------------------------------------------------------------
    # Enhanced class extraction
    # ------------------------------------------------------------------

    def _extract_enhanced_class(
        self,
        node,
        source: bytes,
        file_path: str,
        layer: str,
        file_imports: list[str],
    ) -> EnhancedClassInfo:
        """
        Build an EnhancedClassInfo from a class_declaration node.

        Extracts everything the base parser extracts PLUS:
          - extends (superclass field in the grammar)
          - implements (interfaces field)
          - field declarations
          - object instantiations (new ClassName())
          - enhanced method info
        """
        name = self._get_identifier(node)
        annotations = self._extract_annotations_from_modifiers(node, source)

        # ── Superclass (extends) ──────────────────────────────────────
        extends = ""
        superclass_node = node.child_by_field_name("superclass")
        if superclass_node:
            extends = self._first_type_identifier(superclass_node, source)

        # ── Implemented interfaces ────────────────────────────────────
        implements: list[str] = []
        interfaces_node = node.child_by_field_name("interfaces")
        if interfaces_node:
            # interfaces field → super_interfaces node
            # super_interfaces → "implements" interface_type_list
            # interface_type_list → type_identifier ("," type_identifier)*
            for c in interfaces_node.children:
                if c.type == "interface_type_list":
                    for t in c.children:
                        if t.type == "type_identifier":
                            implements.append(self._node_text(t, source))

        cls = EnhancedClassInfo(
            name=name,
            file_path=file_path,
            layer=layer,
            annotations=annotations,
            extends=extends,
            implements=implements,
            imports=file_imports,
        )

        # ── Class body ────────────────────────────────────────────────
        body = self._child_by_type(node, "class_body")
        if body:
            for child in body.children:
                if child.type == "field_declaration":
                    fi = self._extract_field(child, source)
                    if fi:
                        cls.fields.append(fi)
                elif child.type == "method_declaration":
                    method = self._extract_enhanced_method(child, source)
                    cls.methods.append(method)
                    cls.object_creations.extend(method.object_creations)

        # Deduplicate object_creations while preserving first-seen order
        seen: set[str] = set()
        deduped: list[str] = []
        for oc in cls.object_creations:
            if oc not in seen:
                seen.add(oc)
                deduped.append(oc)
        cls.object_creations = deduped

        return cls

    # ------------------------------------------------------------------
    # Field declaration extraction
    # ------------------------------------------------------------------

    def _extract_field(self, node, source: bytes) -> Optional[FieldInfo]:
        """
        Extract the type and first variable name from a field_declaration.

        AST shape:
            field_declaration
              modifiers?
              type: type_identifier | generic_type | array_type
              variable_declarator
                name: identifier
                ["=" initializer]
        """
        type_name = ""
        var_name = ""

        for child in node.children:
            if not type_name and child.type in (
                "type_identifier", "generic_type", "array_type",
                "integral_type", "floating_point_type", "boolean_type",
            ):
                raw = self._node_text(child, source).strip()
                # Strip generic parameters: List<String> → List
                type_name = raw.split("<")[0].strip()

            elif child.type == "variable_declarator":
                for c in child.children:
                    if c.type == "identifier" and not var_name:
                        var_name = self._node_text(c, source)

        if type_name and var_name:
            return FieldInfo(type_name=type_name, variable_name=var_name)
        return None

    # ------------------------------------------------------------------
    # Enhanced method extraction
    # ------------------------------------------------------------------

    def _extract_enhanced_method(self, node, source: bytes) -> EnhancedMethodInfo:
        """
        Build an EnhancedMethodInfo by calling the base _extract_method()
        then appending object-creation and method-call data.
        """
        base: MethodInfo = self._extract_method(node, source)

        return EnhancedMethodInfo(
            name=base.name,
            annotations=base.annotations,
            code=base.code,
            comments=base.comments,
            selenium_actions=base.selenium_actions,
            object_creations=self._extract_object_creations(node, source),
            method_calls=self._extract_method_calls(node, source),
        )

    # ------------------------------------------------------------------
    # Object creation extraction  (new ClassName(...))
    # ------------------------------------------------------------------

    def _extract_object_creations(self, node, source: bytes) -> list[str]:
        """
        DFS walk to collect every `new ClassName()` expression.

        AST shape:
            object_creation_expression
              "new"
              type: type_identifier | generic_type
              arguments: argument_list
        """
        found: list[str] = []
        self._walk_object_creations(node, source, found)
        # Deduplicate preserving order
        seen: set[str] = set()
        return [x for x in found if not (x in seen or seen.add(x))]  # type: ignore[func-returns-value]

    def _walk_object_creations(self, node, source: bytes, found: list[str]) -> None:
        if node.type == "object_creation_expression":
            # Prefer field-name access; fall back to iterating children
            type_node = node.child_by_field_name("type")
            if type_node is None:
                for c in node.children:
                    if c.type in ("type_identifier", "generic_type"):
                        type_node = c
                        break
            if type_node:
                raw = self._node_text(type_node, source).strip()
                type_name = raw.split("<")[0].strip()  # strip generics
                if type_name:
                    found.append(type_name)
        for child in node.children:
            self._walk_object_creations(child, source, found)

    # ------------------------------------------------------------------
    # Method call extraction
    # ------------------------------------------------------------------

    def _extract_method_calls(self, node, source: bytes) -> list[dict]:
        """
        Extract structured call records from simple method invocations.

        loginPage.enterUsername("admin")  →
            {
              "object":    "loginPage",
              "method":    "enterUsername",
              "full_call": "loginPage.enterUsername",
              "arguments": ['"admin"']
            }

        Chained receivers (foo.bar().baz()) are skipped to avoid noise; only
        calls where the receiver is a plain identifier are captured.
        """
        found: list[dict] = []
        self._walk_method_calls(node, source, found)
        # Deduplicate by (full_call, arguments) fingerprint
        seen: set[str] = set()
        deduped: list[dict] = []
        for call in found:
            key = f"{call['full_call']}({','.join(call['arguments'])})"
            if key not in seen:
                seen.add(key)
                deduped.append(call)
        return deduped

    def _walk_method_calls(self, node, source: bytes, found: list[dict]) -> None:
        if node.type == "method_invocation":
            obj_node  = node.child_by_field_name("object")
            name_node = node.child_by_field_name("name")
            if obj_node and name_node and obj_node.type == "identifier":
                receiver  = self._node_text(obj_node, source).strip()
                method    = self._node_text(name_node, source).strip()
                arguments = self._extract_argument_list(node, source)
                found.append({
                    "object":    receiver,
                    "method":    method,
                    "full_call": f"{receiver}.{method}",
                    "arguments": arguments,
                })
        for child in node.children:
            self._walk_method_calls(child, source, found)

    def _extract_argument_list(self, invocation_node, source: bytes) -> list[str]:
        """
        Extract the textual arguments from a method_invocation's argument_list.

        RestAssuredAPI.setDefaultHeader("Authorization", token)
          →  ['"Authorization"', 'token']
        """
        args: list[str] = []
        arg_list = invocation_node.child_by_field_name("arguments")
        if arg_list is None:
            return args
        for child in arg_list.children:
            # Skip punctuation; keep all expression nodes
            if child.type not in ("(", ")", ","):
                args.append(self._node_text(child, source).strip())
        return args

    # ------------------------------------------------------------------
    # Shared helper
    # ------------------------------------------------------------------

    def _first_type_identifier(self, node, source: bytes) -> str:
        """Return text of the first type_identifier child, recursively."""
        for c in node.children:
            if c.type == "type_identifier":
                return self._node_text(c, source)
        # One level deeper (e.g. scoped_type_identifier wrapping type_identifier)
        for c in node.children:
            result = self._first_type_identifier(c, source)
            if result:
                return result
        return ""
