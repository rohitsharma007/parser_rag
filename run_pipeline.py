"""
run_pipeline.py — Orchestrates all 3 stages and writes output files.

Usage:
    python run_pipeline.py [--java-root <path>] [--out-root <path>]

Defaults:
    java-root : dummy_test/src/test/java/com/ntrs/demoapp/testcases/web
    out-root  : current directory  (creates Test_cases/ and UserStory/ here)
"""

from __future__ import annotations

import argparse
import pathlib
import sys

_HERE = str(pathlib.Path(__file__).parent.resolve())
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from tc_extractor import extract_all_test_cases
from cluster_builder import build_clusters
from us_synthesizer import synthesise_user_stories
from csvparser import (
    write_test_cases_json,
    write_test_cases_csv,
    write_user_stories_json,
    write_user_stories_csv,
)

DEFAULT_JAVA_ROOT = pathlib.Path(_HERE) / "dummy_test/src/test/java/com/ntrs/demoapp/testcases/web"
DEFAULT_OUT_ROOT  = pathlib.Path(_HERE)


def main() -> None:
    args     = _parse_args()
    java_root = pathlib.Path(args.java_root)
    out_root  = pathlib.Path(args.out_root)

    tc_dir = out_root / "Test_cases"
    us_dir = out_root / "UserStory"
    tc_dir.mkdir(parents=True, exist_ok=True)
    us_dir.mkdir(parents=True, exist_ok=True)

    # ── Stage 1 ──────────────────────────────────────────────────────────────
    print("\n─── Stage 1: Extracting test cases ───────────────────────────────")
    java_files = sorted(java_root.glob("*.java"))
    if not java_files:
        sys.exit(f"No Java files found in {java_root}")

    test_cases = extract_all_test_cases([str(f) for f in java_files])
    print(f"  Extracted {len(test_cases)} test cases from {len(java_files)} files")

    # ── Stage 2 ──────────────────────────────────────────────────────────────
    print("\n─── Stage 2: Building feature clusters ───────────────────────────")
    clusters = build_clusters(test_cases)
    for cl in clusters:
        tc_ids = ", ".join(tc.tc_id for tc in cl.test_cases)
        print(f"  [{cl.feature_name}] ({len(cl.test_cases)} TCs)  →  {tc_ids}")

    # ── Stage 3 ──────────────────────────────────────────────────────────────
    print("\n─── Stage 3: Synthesising User Stories via Claude API ─────────────")
    user_stories = synthesise_user_stories(clusters)

    # Build tc_id → us_id lookup used by both writers
    tc_to_us: dict[str, str] = {}
    for i, cl in enumerate(clusters, start=1):
        for tc in cl.test_cases:
            tc_to_us[tc.tc_id] = f"US-{i:03d}"

    # ── Write output ─────────────────────────────────────────────────────────
    print("\n─── Writing Test_cases/ ──────────────────────────────────────────")
    write_test_cases_json(test_cases, tc_to_us, tc_dir)
    write_test_cases_csv(test_cases, tc_to_us, tc_dir)

    print("\n─── Writing UserStory/ ───────────────────────────────────────────")
    write_user_stories_json(user_stories, us_dir)
    write_user_stories_csv(user_stories, us_dir)

    print(f"\n✓  Test cases → {tc_dir}")
    print(f"✓  User stories → {us_dir}")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TC → Cluster → UserStory pipeline")
    p.add_argument("--java-root", default=str(DEFAULT_JAVA_ROOT))
    p.add_argument("--out-root",  default=str(DEFAULT_OUT_ROOT))
    return p.parse_args()


if __name__ == "__main__":
    main()
