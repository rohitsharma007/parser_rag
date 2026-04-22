"""
Stage 2: Feature Clustering (structural / Option A)
Groups TestCase objects by the primary page objects they touch.
Returns named feature buckets used by Stage 3 for User Story synthesis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from tc_extractor import TestCase, PAGE_OBJECT_TO_FEATURE


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class FeatureCluster:
    """A named group of test cases that share a common page-object domain."""
    feature_name: str        # e.g. "Login", "Navigation"
    test_cases: list[TestCase] = field(default_factory=list)

    # Derived properties used by US synthesiser
    @property
    def tc_ids(self) -> list[str]:
        return [tc.tc_id for tc in self.test_cases]

    @property
    def all_page_objects(self) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for tc in self.test_cases:
            for po in tc.page_objects_used:
                if po not in seen:
                    seen.add(po)
                    result.append(po)
        return result

    @property
    def all_groups(self) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for tc in self.test_cases:
            for g in tc.groups:
                if g not in seen:
                    seen.add(g)
                    result.append(g)
        return result


# ---------------------------------------------------------------------------
# Cluster priority order (determines which bucket a TC falls into first)
# ---------------------------------------------------------------------------

FEATURE_PRIORITY: list[str] = [
    "Login",
    "User Registration",
    "Home Page",
    "Navigation",
    "Account Management",
    "Application Management",
    "Azure Cloud",
    "Financial Calculators",
    "Playwright Integration",
    "Reliability",
]

# Fallback feature for TCs that don't use any mapped page objects
_FALLBACK = "General"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_clusters(test_cases: list[TestCase]) -> list[FeatureCluster]:
    """
    Assign each TestCase to exactly one FeatureCluster (its primary feature).

    Primary feature = the feature of the first page object the test instantiates,
    ranked by FEATURE_PRIORITY so that higher-priority features win when a test
    spans multiple features (e.g. Login + Navigation → Login).
    """
    bucket: dict[str, FeatureCluster] = {}

    for tc in test_cases:
        feature = _primary_feature(tc)
        if feature not in bucket:
            bucket[feature] = FeatureCluster(feature_name=feature)
        bucket[feature].test_cases.append(tc)

    # Return clusters in the canonical priority order
    ordered: list[FeatureCluster] = []
    for name in FEATURE_PRIORITY:
        if name in bucket:
            ordered.append(bucket.pop(name))
    # Append any remaining clusters (shouldn't happen but just in case)
    ordered.extend(bucket.values())
    return ordered


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _primary_feature(tc: TestCase) -> str:
    """
    Return the highest-priority feature bucket for a test case.

    Strategy:
    1. Collect all features implied by the TC's page objects.
    2. Return the one that appears earliest in FEATURE_PRIORITY.
    3. Fall back to class-name heuristic, then _FALLBACK.
    """
    candidate_features: list[str] = [
        PAGE_OBJECT_TO_FEATURE[po]
        for po in tc.page_objects_used
        if po in PAGE_OBJECT_TO_FEATURE
    ]

    if not candidate_features:
        # Derive from class / area path when no page objects found
        candidate_features = _infer_from_class(tc.class_name)

    if not candidate_features:
        return _FALLBACK

    # Pick the one with the smallest index in FEATURE_PRIORITY
    def rank(f: str) -> int:
        try:
            return FEATURE_PRIORITY.index(f)
        except ValueError:
            return len(FEATURE_PRIORITY)

    return min(set(candidate_features), key=rank)


def _infer_from_class(class_name: str) -> list[str]:
    mapping = {
        "ATR_Portal_Tests": ["Login"],
        "ATR_Portal_POC_Tests": ["Login"],
        "ATR_Portal_POC_Retry_Tests": ["Reliability"],
        "ATR_Application_Regression_Tests": ["Account Management"],
        "ATR_Web_Portal_Tests": ["Navigation"],
        "Azure_Public_Cloud_Tests": ["Azure Cloud"],
    }
    return mapping.get(class_name, [])
