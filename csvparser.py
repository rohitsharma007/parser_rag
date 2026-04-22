"""
csvparser.py — Output writer for the TC → US pipeline.

Writes test cases as:
  - JSON  : one object per TC, steps nested under a "steps" array
  - CSV   : one row per TC, steps formatted as a numbered text block
             (no row-per-step explosion)

Also writes User Story JSON and CSV (unchanged format from pipeline).
"""

from __future__ import annotations

import csv
import json
import pathlib

from tc_extractor import TestCase
from us_synthesizer import UserStory


# ---------------------------------------------------------------------------
# Test Case writers
# ---------------------------------------------------------------------------

def write_test_cases_json(
    test_cases: list[TestCase],
    tc_to_us: dict[str, str],
    out_dir: pathlib.Path,
) -> None:
    """
    Write one JSON file per source class + one combined ALL_TestCases.json.
    Each TC is a single object; steps are a nested list.
    """
    by_class: dict[str, list[dict]] = {}

    for tc in test_cases:
        obj = _tc_to_dict(tc, tc_to_us)
        by_class.setdefault(tc.class_name, []).append(obj)

    for class_name, objs in by_class.items():
        path = out_dir / f"{class_name}.json"
        _write_json(path, objs)
        print(f"  Written: {path.name}  ({len(objs)} TCs)")

    combined = out_dir / "ALL_TestCases.json"
    all_objs = [obj for objs in by_class.values() for obj in objs]
    _write_json(combined, all_objs)
    print(f"  Written: {combined.name}  ({len(all_objs)} TCs total)")


def write_test_cases_csv(
    test_cases: list[TestCase],
    tc_to_us: dict[str, str],
    out_dir: pathlib.Path,
) -> None:
    """
    Write one CSV file per source class + one combined ALL_TestCases.csv.
    Each TC occupies exactly ONE row; steps are packed into the Steps column
    as a numbered text block.
    """
    headers = [
        "TC_ID",
        "Title",
        "AssignedTo",
        "Tags",
        "State",
        "AreaPath",
        "Priority",
        "LinkedUserStory",
        "PageObjectsUsed",
        "Steps",
    ]

    by_class: dict[str, list[list[str]]] = {}

    for tc in test_cases:
        row = _tc_to_csv_row(tc, tc_to_us)
        by_class.setdefault(tc.class_name, []).append(row)

    for class_name, rows in by_class.items():
        path = out_dir / f"{class_name}.csv"
        _write_csv(path, headers, rows)
        print(f"  Written: {path.name}  ({len(rows)} TCs)")

    combined = out_dir / "ALL_TestCases.csv"
    all_rows = [row for rows in by_class.values() for row in rows]
    _write_csv(combined, headers, all_rows)
    print(f"  Written: {combined.name}  ({len(all_rows)} TCs total)")


# ---------------------------------------------------------------------------
# User Story writers
# ---------------------------------------------------------------------------

def write_user_stories_json(
    user_stories: list[UserStory],
    out_dir: pathlib.Path,
) -> None:
    """Write one JSON file per US + combined ALL_UserStories.json."""
    all_objs: list[dict] = []

    for us in user_stories:
        obj = _us_to_dict(us)
        all_objs.append(obj)

        safe = us.title.replace(" ", "_").replace("/", "-")[:40]
        path = out_dir / f"{us.us_id}_{safe}.json"
        _write_json(path, obj)
        print(f"  Written: {path.name}")

    combined = out_dir / "ALL_UserStories.json"
    _write_json(combined, all_objs)
    print(f"  Written: {combined.name}  ({len(all_objs)} stories total)")


def write_user_stories_csv(
    user_stories: list[UserStory],
    out_dir: pathlib.Path,
) -> None:
    """Write one CSV per US + combined ALL_UserStories.csv (one row per story)."""
    headers = [
        "id", "type", "title", "state", "areaPath",
        "description", "acceptanceCriteria", "parentId", "url",
    ]
    all_rows: list[list[str]] = []

    for us in user_stories:
        row = [
            us.us_id, us.us_type, us.title, us.state, us.area_path,
            us.description, us.acceptance_criteria, us.parent_id, us.url,
        ]
        all_rows.append(row)

        safe = us.title.replace(" ", "_").replace("/", "-")[:40]
        path = out_dir / f"{us.us_id}_{safe}.csv"
        _write_csv(path, headers, [row])
        print(f"  Written: {path.name}")

    combined = out_dir / "ALL_UserStories.csv"
    _write_csv(combined, headers, all_rows)
    print(f"  Written: {combined.name}  ({len(all_rows)} stories total)")


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _tc_to_dict(tc: TestCase, tc_to_us: dict[str, str]) -> dict:
    return {
        "tc_id": tc.tc_id,
        "title": tc.title,
        "method_name": tc.method_name,
        "class_name": tc.class_name,
        "assigned_to": tc.assigned_to,
        "tags": tc.tags,
        "state": tc.state,
        "area_path": tc.area_path,
        "priority": tc.priority,
        "linked_us_id": tc_to_us.get(tc.tc_id, ""),
        "page_objects_used": tc.page_objects_used,
        "steps": [
            {
                "step_number": s.step_number,
                "action": s.action,
                "expected_result": s.expected_result,
            }
            for s in tc.steps
        ],
    }


def _tc_to_csv_row(tc: TestCase, tc_to_us: dict[str, str]) -> list[str]:
    # Pack steps into a numbered text block
    step_lines: list[str] = []
    for s in tc.steps:
        line = f"{s.step_number}. {s.action}"
        if s.expected_result:
            line += f"\n   → Expected: {s.expected_result}"
        step_lines.append(line)
    steps_block = "\n".join(step_lines)

    return [
        tc.tc_id,
        tc.title,
        tc.assigned_to,
        ", ".join(tc.tags),
        tc.state,
        tc.area_path,
        str(tc.priority),
        tc_to_us.get(tc.tc_id, ""),
        ", ".join(tc.page_objects_used),
        steps_block,
    ]


def _us_to_dict(us: UserStory) -> dict:
    return {
        "id": us.us_id,
        "type": us.us_type,
        "title": us.title,
        "state": us.state,
        "area_path": us.area_path,
        "description": us.description,
        "acceptance_criteria": [
            line.strip() for line in us.acceptance_criteria.splitlines() if line.strip()
        ],
        "linked_tc_ids": us.linked_tc_ids,
        "parent_id": us.parent_id,
        "url": us.url,
    }


# ---------------------------------------------------------------------------
# Low-level I/O
# ---------------------------------------------------------------------------

def _write_json(path: pathlib.Path, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _write_csv(path: pathlib.Path, headers: list[str], rows: list[list[str]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        writer.writerows(rows)
