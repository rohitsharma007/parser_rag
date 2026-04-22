"""
run_pipeline.py — Orchestrates all 3 stages and writes output CSV files.

Usage:
    python run_pipeline.py [--java-root <path>] [--out-root <path>]

Defaults:
    java-root : dummy_test/src/test/java/com/ntrs/demoapp/testcases/web
    out-root  : current directory  (creates Test_cases/ and UserStory/ here)
"""

from __future__ import annotations

import argparse
import csv
import os
import pathlib
import sys
import textwrap

_HERE = str(pathlib.Path(__file__).parent.resolve())
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from tc_extractor import extract_all_test_cases, TestCase
from cluster_builder import build_clusters, FeatureCluster
from us_synthesizer import synthesise_user_stories, UserStory


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_JAVA_ROOT = pathlib.Path(_HERE) / "dummy_test/src/test/java/com/ntrs/demoapp/testcases/web"
DEFAULT_OUT_ROOT = pathlib.Path(_HERE)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = _parse_args()
    java_root = pathlib.Path(args.java_root)
    out_root = pathlib.Path(args.out_root)

    tc_dir = out_root / "Test_cases"
    us_dir = out_root / "UserStory"
    tc_dir.mkdir(parents=True, exist_ok=True)
    us_dir.mkdir(parents=True, exist_ok=True)

    # ── Stage 1: Extract test cases ─────────────────────────────────────────
    print("\n─── Stage 1: Extracting test cases ───────────────────────────────")
    java_files = sorted(java_root.glob("*.java"))
    if not java_files:
        sys.exit(f"No Java files found in {java_root}")

    test_cases = extract_all_test_cases([str(f) for f in java_files])
    print(f"  Extracted {len(test_cases)} test cases from {len(java_files)} files")

    # ── Stage 2: Cluster by page objects ────────────────────────────────────
    print("\n─── Stage 2: Building feature clusters ───────────────────────────")
    clusters = build_clusters(test_cases)
    for cl in clusters:
        tc_ids = ", ".join(tc.tc_id for tc in cl.test_cases)
        print(f"  [{cl.feature_name}] ({len(cl.test_cases)} TCs)  →  {tc_ids}")

    # ── Stage 3: Synthesise User Stories ────────────────────────────────────
    print("\n─── Stage 3: Synthesising User Stories via Claude API ─────────────")
    user_stories = synthesise_user_stories(clusters)

    # ── Write output ─────────────────────────────────────────────────────────
    print("\n─── Writing output files ─────────────────────────────────────────")
    _write_test_cases(test_cases, clusters, tc_dir)
    _write_user_stories(user_stories, clusters, us_dir)

    print(f"\n✓  Test cases → {tc_dir}")
    print(f"✓  User stories → {us_dir}")


# ---------------------------------------------------------------------------
# Test Case CSV writers
# ---------------------------------------------------------------------------

def _write_test_cases(
    test_cases: list[TestCase],
    clusters: list[FeatureCluster],
    out_dir: pathlib.Path,
) -> None:
    """
    Write one CSV per source test class, plus a combined file.

    Columns (Azure DevOps test case import format):
    Title | AssignedTo | Tags | State | AreaPath | Priority | Test Step |
    Step Action | Expected Result
    """
    # Build tc_id → us_id mapping for back-reference
    tc_to_us: dict[str, str] = {}
    for i, cl in enumerate(clusters, start=1):
        us_id = f"US-{i:03d}"
        for tc in cl.test_cases:
            tc_to_us[tc.tc_id] = us_id

    headers = [
        "Title", "AssignedTo", "Tags", "State", "AreaPath",
        "Priority", "Test Step", "Step Action", "Expected Result",
    ]

    # Group by class name
    by_class: dict[str, list[TestCase]] = {}
    for tc in test_cases:
        by_class.setdefault(tc.class_name, []).append(tc)

    all_rows: list[list[str]] = []

    for class_name, tcs in by_class.items():
        class_rows: list[list[str]] = []
        for tc in tcs:
            tags_str = ", ".join(tc.tags) if tc.tags else ""
            us_ref = tc_to_us.get(tc.tc_id, "")
            title_with_id = f"[{tc.tc_id}] {tc.title}"
            if us_ref:
                title_with_id += f" ({us_ref})"

            for step in tc.steps:
                row = [
                    title_with_id,
                    tc.assigned_to,
                    tags_str,
                    tc.state,
                    tc.area_path,
                    str(tc.priority),
                    str(step.step_number),
                    step.action,
                    step.expected_result,
                ]
                class_rows.append(row)

        # Per-class file
        class_file = out_dir / f"{class_name}.csv"
        _write_csv(class_file, headers, class_rows)
        print(f"  Written: {class_file.name}  ({len(tcs)} TCs)")
        all_rows.extend(class_rows)

    # Combined file
    combined_file = out_dir / "ALL_TestCases.csv"
    _write_csv(combined_file, headers, all_rows)
    print(f"  Written: {combined_file.name}  ({len(test_cases)} TCs total)")


# ---------------------------------------------------------------------------
# User Story CSV writers
# ---------------------------------------------------------------------------

def _write_user_stories(
    user_stories: list[UserStory],
    clusters: list[FeatureCluster],
    out_dir: pathlib.Path,
) -> None:
    """
    Write one CSV per user story (named US-NNN_<feature>.csv) plus a combined file.

    Columns:
    id | type | title | state | areaPath | description |
    acceptanceCriteria | parentId | url
    """
    headers = [
        "id", "type", "title", "state", "areaPath",
        "description", "acceptanceCriteria", "parentId", "url",
    ]

    all_rows: list[list[str]] = []

    for us, cluster in zip(user_stories, clusters):
        row = [
            us.us_id,
            us.us_type,
            us.title,
            us.state,
            us.area_path,
            us.description,
            us.acceptance_criteria,
            us.parent_id,
            us.url,
        ]
        all_rows.append(row)

        # Per-US file
        safe_name = cluster.feature_name.replace(" ", "_").replace("/", "-")
        us_file = out_dir / f"{us.us_id}_{safe_name}.csv"
        _write_csv(us_file, headers, [row])
        print(f"  Written: {us_file.name}")

    # Combined file
    combined_file = out_dir / "ALL_UserStories.csv"
    _write_csv(combined_file, headers, all_rows)
    print(f"  Written: {combined_file.name}  ({len(user_stories)} stories total)")


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _write_csv(path: pathlib.Path, headers: list[str], rows: list[list[str]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        writer.writerows(rows)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TC → Cluster → UserStory pipeline")
    p.add_argument("--java-root", default=str(DEFAULT_JAVA_ROOT),
                   help="Directory containing Java test class files")
    p.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT),
                   help="Root directory where Test_cases/ and UserStory/ will be created")
    return p.parse_args()


if __name__ == "__main__":
    main()
