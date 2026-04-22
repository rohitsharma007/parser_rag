"""
Stage 1: Test Case Extractor
Java @Test method → structured TestCase with steps, assertions, page objects.
"""

from __future__ import annotations

import hashlib
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

_HERE = str(pathlib.Path(__file__).parent.resolve())
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from enhanced_parser import EnhancedJavaParser


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class TestStep:
    step_number: int
    action: str
    expected_result: str = ""


@dataclass
class TestCase:
    tc_id: str
    title: str
    method_name: str
    class_name: str
    file_path: str
    layer: str = "test"
    page_objects_used: list[str] = field(default_factory=list)
    steps: list[TestStep] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)
    description: str = ""
    area_path: str = ""
    priority: int = 2
    assigned_to: str = "QA Team"
    state: str = "Design"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Maps page object class name → feature bucket name
PAGE_OBJECT_TO_FEATURE: dict[str, str] = {
    "Login_Page": "Login",
    "Login_Playwright_Page": "Login",
    "ATR_Portal_Playwright_Page": "Playwright Integration",
    "Navigation_Page": "Navigation",
    "Menu_Page": "Navigation",
    "ATR_HomePage": "Home Page",
    "RegisterUser_Page": "User Registration",
    "MyAccount_Page": "Account Management",
    "ATR_Application_Page": "Application Management",
    "Accounts_Page": "Account Management",
    "Azure_Cloud_Page": "Azure Cloud",
    "Adu_Saas_Page": "Azure Cloud",
    "Core_Reference_Page": "Azure Cloud",
    "FinancialCalculators_Perfecto_Page": "Financial Calculators",
    "InterestCalculator_Perfecto_Page": "Financial Calculators",
    "RetryAnalyzer": "Reliability",
}

PRIORITY_BY_GROUP: dict[str, int] = {
    "smoke": 1,
    "login": 1,
    "regression": 2,
    "navigation": 2,
    "accounts": 2,
    "api": 2,
    "cloud": 2,
    "homepage": 2,
    "registration": 2,
    "poc": 3,
    "retry": 3,
    "playwright": 3,
    "perfecto": 3,
    "utility": 3,
    "negative": 2,
}

AREA_PATH_BY_CLASS: dict[str, str] = {
    "ATR_Portal_Tests": r"ATR Portal\Authentication",
    "ATR_Portal_POC_Tests": r"ATR Portal\POC",
    "ATR_Portal_POC_Retry_Tests": r"ATR Portal\Reliability",
    "ATR_Application_Regression_Tests": r"ATR Portal\Application Management",
    "ATR_Web_Portal_Tests": r"ATR Portal\Navigation",
    "Azure_Public_Cloud_Tests": r"ATR Portal\Cloud Integration",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_all_test_cases(java_files: list[str]) -> list[TestCase]:
    """Parse every file and return a flat list of all TestCases found."""
    all_tcs: list[TestCase] = []
    parser = EnhancedJavaParser()
    for path in java_files:
        all_tcs.extend(_extract_from_file(path, parser))
    return all_tcs


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_from_file(java_file: str, parser: EnhancedJavaParser) -> list[TestCase]:
    source_text = pathlib.Path(java_file).read_text(encoding="utf-8")
    result = parser.parse_file_enhanced(java_file, layer="test")
    test_cases: list[TestCase] = []

    for cls in result.classes:
        area_path = AREA_PATH_BY_CLASS.get(cls.name, r"ATR Portal\General")

        for method in cls.methods:
            # Only process @Test / @TestNG annotated methods
            if not any(a.startswith("@Test") or a.startswith("@TestNG") for a in method.annotations):
                continue

            description, groups = _parse_test_annotation(source_text, method.name)
            page_objects = _find_page_objects(method.code)
            steps = _build_steps(method.code, method.name)
            priority = _calc_priority(groups)
            tc_id = _make_tc_id(cls.name, method.name)

            test_cases.append(TestCase(
                tc_id=tc_id,
                title=description or _humanize(method.name),
                method_name=method.name,
                class_name=cls.name,
                file_path=java_file,
                layer=cls.layer,
                page_objects_used=page_objects,
                steps=steps,
                tags=groups,
                groups=groups,
                description=description,
                area_path=area_path,
                priority=priority,
            ))

    return test_cases


def _make_tc_id(class_name: str, method_name: str) -> str:
    digest = hashlib.sha256(f"{class_name}::{method_name}".encode()).hexdigest()
    return f"TC-{digest[:8].upper()}"


def _calc_priority(groups: list[str]) -> int:
    best = 3
    for g in groups:
        best = min(best, PRIORITY_BY_GROUP.get(g.lower(), 3))
    return best


# ---------------------------------------------------------------------------
# @Test annotation parsing
# ---------------------------------------------------------------------------

def _parse_test_annotation(source: str, method_name: str) -> tuple[str, list[str]]:
    """
    Find the @Test / @TestNG block immediately preceding `method_name`
    and return (description, [groups...]).
    """
    # Capture the annotation block that precedes the method declaration
    pattern = (
        r'@(?:Test|TestNG)\s*\(([^)]*)\)'          # annotation + params
        r'(?:\s*@\w+(?:\([^)]*\))?\s*)*'           # optional other annotations
        r'\s*(?:public|protected|private)\s+'
        r'\w+\s+' + re.escape(method_name) + r'\s*\('
    )
    m = re.search(pattern, source, re.DOTALL)
    if not m:
        return "", []

    params = m.group(1)
    description = _extract_string_param(params, "description")
    groups = _extract_list_param(params, "groups")
    return description, groups


def _extract_string_param(params: str, key: str) -> str:
    m = re.search(rf'{key}\s*=\s*"([^"]*)"', params)
    return m.group(1) if m else ""


def _extract_list_param(params: str, key: str) -> list[str]:
    m = re.search(rf'{key}\s*=\s*\{{([^}}]*)\}}', params)
    if not m:
        return []
    return [g.strip().strip('"') for g in m.group(1).split(',') if g.strip()]


# ---------------------------------------------------------------------------
# Page object detection
# ---------------------------------------------------------------------------

def _find_page_objects(code: str) -> list[str]:
    """Return ordered, deduplicated list of page object class names instantiated in code."""
    hits = re.findall(r'new\s+([A-Z][A-Za-z0-9_]*)\s*\(', code)
    seen: set[str] = set()
    result: list[str] = []
    for h in hits:
        if h in PAGE_OBJECT_TO_FEATURE and h not in seen:
            result.append(h)
            seen.add(h)
    return result


# ---------------------------------------------------------------------------
# Step extraction
# ---------------------------------------------------------------------------

def _build_steps(code: str, method_name: str) -> list[TestStep]:
    """Convert method body into ordered TestStep list."""
    # Strip method signature — keep only the body content
    body_match = re.search(r'\{(.*)\}\s*$', code, re.DOTALL)
    body = body_match.group(1) if body_match else code

    # Extract all Assert.* blocks from the entire body (handles multi-line assertions)
    assertions = _extract_all_assertions(body)

    raw_steps: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line in ('{', '}'):
            continue
        if line.startswith('//'):
            continue
        if 'System.out.println' in line:
            continue
        if 'Assert.fail(' in line:
            continue
        # Skip Assert lines — handled separately above
        if line.startswith('Assert.'):
            continue

        action = _line_to_action(line)
        if action:
            raw_steps.append(action)

    steps: list[TestStep] = []
    for i, action in enumerate(raw_steps, start=1):
        # Attach all assertions as expected result on the last step
        expected = "; ".join(assertions) if i == len(raw_steps) and assertions else ""
        steps.append(TestStep(step_number=i, action=action, expected_result=expected))

    # If there were assertions but no steps, synthesise a verify step
    if assertions and not steps:
        steps.append(TestStep(
            step_number=1,
            action=f"Execute {_humanize(method_name)}",
            expected_result="; ".join(assertions),
        ))

    if not steps:
        steps.append(TestStep(
            step_number=1,
            action=f"Execute {_humanize(method_name)}",
            expected_result="Test completes without errors",
        ))

    return steps


def _line_to_action(line: str) -> Optional[str]:
    """Convert a single Java statement into a plain-English step action."""
    # new ClassName(driver) initialisation
    m = re.match(r'(?:\w+\s+)?(\w+)\s*=\s*new\s+([A-Z][A-Za-z0-9_]*)\s*\(', line)
    if m:
        return f"Initialize {m.group(2)}"

    # Direct new ClassName() without assignment
    m = re.match(r'new\s+([A-Z][A-Za-z0-9_]*)\s*\(', line)
    if m:
        return f"Initialize {m.group(1)}"

    # object.method(args) or var = object.method(args)
    m = re.match(r'(?:\w[\w.<>]*\s+\w+\s*=\s*)?(\w+)\.(\w+)\(([^)]*)\)\s*;?$', line)
    if m:
        obj, method, args = m.group(1), m.group(2), m.group(3).strip()
        return _format_call(obj, method, args)

    # try { ... } — keep opening line
    if line.startswith('try {') or line == 'try {':
        return None

    # navigateTo(url)
    m = re.match(r'navigateTo\((.+)\)\s*;?$', line)
    if m:
        url = m.group(1).strip().strip('"')
        return f"Navigate to {url}"

    return None


def _format_call(obj: str, method: str, args: str) -> str:
    method_words = _humanize(method)
    if not args or args == 'driver':
        return f"{method_words} on {obj}"
    # Trim long arg strings
    args_display = args if len(args) <= 60 else args[:57] + "..."
    return f"{method_words} [{args_display}] via {obj}"


def _extract_all_assertions(body: str) -> list[str]:
    """
    Find every Assert.* call in the full method body (handles multi-line calls)
    and return a list of human-readable assertion messages.
    """
    results: list[str] = []
    # Collapse whitespace/newlines inside parentheses by joining the body
    collapsed = ' '.join(body.split())

    # Find all Assert.XXX(...) blocks
    for m in re.finditer(r'Assert\.\w+\(([^;]+);', collapsed):
        args = m.group(1).strip()
        # Skip simulated failures
        if 'Assert.fail' in m.group(0):
            continue
        # Prefer the last quoted string (human message)
        msgs = re.findall(r'"([^"]+)"', args)
        if msgs:
            results.append(msgs[-1])
        else:
            # Use condition text (first argument)
            cond = re.match(r'([^,)]+)', args)
            if cond:
                results.append(cond.group(1).strip())
    return results


def _assertion_message(line: str) -> str:
    # Prefer the human message parameter (last quoted string)
    msgs = re.findall(r'"([^"]+)"', line)
    if msgs:
        return msgs[-1]
    # Fallback: condition text
    m = re.search(r'Assert\.\w+\(([^,)]+)', line)
    return m.group(1).strip() if m else ""


def _humanize(name: str) -> str:
    """camelCase / snake_case → Title Case words."""
    # Insert space before uppercase letters
    spaced = re.sub(r'([A-Z])', r' \1', name).strip()
    # Remove leading 'test' word (common in TestNG methods)
    words = spaced.split()
    if words and words[0].lower() == 'test':
        words = words[1:]
    return ' '.join(words).title() if words else name.title()
