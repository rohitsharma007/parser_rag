"""
Stage 3: User Story Synthesiser
Each FeatureCluster → one Claude API call → one UserStory.
"""

from __future__ import annotations

import os
import json
import re
import textwrap
from dataclasses import dataclass, field

import anthropic

from cluster_builder import FeatureCluster
from tc_extractor import TestCase


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class UserStory:
    us_id: str               # e.g. "US-001"
    us_type: str = "User Story"
    title: str = ""
    state: str = "Active"
    area_path: str = ""
    description: str = ""    # "As a … I want … So that …"
    acceptance_criteria: str = ""  # bullet list with TC references
    parent_id: str = ""
    url: str = ""
    linked_tc_ids: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Area path mapping (cluster → Azure DevOps area)
# ---------------------------------------------------------------------------

CLUSTER_AREA_PATH: dict[str, str] = {
    "Login":                   r"ATR Portal\Authentication",
    "User Registration":       r"ATR Portal\User Management",
    "Home Page":               r"ATR Portal\User Management",
    "Navigation":              r"ATR Portal\Navigation",
    "Account Management":      r"ATR Portal\Application Management",
    "Application Management":  r"ATR Portal\Application Management",
    "Azure Cloud":             r"ATR Portal\Cloud Integration",
    "Financial Calculators":   r"ATR Portal\Financial Services",
    "Playwright Integration":  r"ATR Portal\Test Infrastructure",
    "Reliability":             r"ATR Portal\Test Infrastructure",
    "General":                 r"ATR Portal\General",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def synthesise_user_stories(
    clusters: list[FeatureCluster],
    model: str = "claude-sonnet-4-6",
) -> list[UserStory]:
    """Call Claude API once per cluster and return a list of UserStory objects."""
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

    # System prompt — sent with prompt caching so it is only billed once
    system_prompt = textwrap.dedent("""
        You are a senior business analyst converting automated test cases into
        Agile User Stories.  For each cluster of test cases you receive, produce
        exactly ONE User Story in this JSON format (no markdown, no prose outside
        the JSON):

        {
          "title": "<concise US title, ≤ 10 words>",
          "description": "As a <role>,\\nI want <goal>,\\nSo that <benefit>.",
          "acceptance_criteria": [
            {"text": "<criterion>", "tc_id": "<TC-XXXXXXXX>"},
            ...
          ]
        }

        Rules:
        - Role must be inferred from the feature (e.g. "registered user", "admin",
          "cloud operator").
        - Each acceptance criterion must map to exactly one TC-ID from the input.
        - Criteria must be concrete and testable (✓ Valid credentials grant access).
        - Keep the description to 3 lines exactly.
        - Do NOT invent TC IDs; use only the ones provided.
    """).strip()

    stories: list[UserStory] = []

    for idx, cluster in enumerate(clusters, start=1):
        us_id = f"US-{idx:03d}"
        area_path = CLUSTER_AREA_PATH.get(cluster.feature_name, r"ATR Portal\General")

        user_message = _build_user_message(cluster)

        try:
            response = client.messages.create(
                model=model,
                max_tokens=1024,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": user_message}],
            )
            raw = response.content[0].text.strip()
            story = _parse_response(raw, us_id, cluster, area_path)
        except Exception as exc:
            print(f"  [WARN] Claude API call failed for {cluster.feature_name}: {exc}")
            story = _fallback_story(us_id, cluster, area_path)

        stories.append(story)
        print(f"  [{us_id}] {story.title}")

    return stories


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_user_message(cluster: FeatureCluster) -> str:
    tc_lines = []
    for tc in cluster.test_cases:
        steps_text = "; ".join(
            f"Step {s.step_number}: {s.action}"
            + (f" → {s.expected_result}" if s.expected_result else "")
            for s in tc.steps
        )
        tc_lines.append(
            f"TC-ID: {tc.tc_id}\n"
            f"  Title: {tc.title}\n"
            f"  Page Objects: {', '.join(tc.page_objects_used) or 'N/A'}\n"
            f"  Groups: {', '.join(tc.groups) or 'N/A'}\n"
            f"  Steps: {steps_text}"
        )

    return (
        f"Feature cluster: {cluster.feature_name}\n"
        f"Page objects involved: {', '.join(cluster.all_page_objects)}\n\n"
        "Test cases:\n"
        + "\n\n".join(tc_lines)
    )


def _parse_response(
    raw: str, us_id: str, cluster: FeatureCluster, area_path: str
) -> UserStory:
    # Strip markdown code fences if present
    raw = re.sub(r"```(?:json)?", "", raw).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON object with regex
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
        else:
            return _fallback_story(us_id, cluster, area_path)

    criteria_lines: list[str] = []
    linked: list[str] = []
    for ac in data.get("acceptance_criteria", []):
        text = ac.get("text", "")
        tc_id = ac.get("tc_id", "")
        criteria_lines.append(f"✓ {text}  ← {tc_id}")
        if tc_id:
            linked.append(tc_id)

    return UserStory(
        us_id=us_id,
        title=data.get("title", cluster.feature_name),
        state="Active",
        area_path=area_path,
        description=data.get("description", ""),
        acceptance_criteria="\n".join(criteria_lines),
        linked_tc_ids=linked,
    )


_FALLBACK_METADATA: dict[str, dict] = {
    "Login": {
        "title": "Secure Login to ATR Portal",
        "role": "registered user",
        "goal": "authenticate to the ATR Portal with my credentials",
        "benefit": "access my account and the portal features securely",
    },
    "User Registration": {
        "title": "New User Self-Registration",
        "role": "new user",
        "goal": "register an account on the ATR Portal",
        "benefit": "gain access to portal services without administrator intervention",
    },
    "Home Page": {
        "title": "Portal Home Page Overview",
        "role": "logged-in user",
        "goal": "see a personalised home page with quick-access links after login",
        "benefit": "navigate to key portal areas efficiently",
    },
    "Navigation": {
        "title": "Portal Menu and Navigation",
        "role": "portal user",
        "goal": "navigate between portal sections via the menu",
        "benefit": "quickly reach any area of the application",
    },
    "Account Management": {
        "title": "Account Creation and Verification",
        "role": "account administrator",
        "goal": "create and verify accounts via API and the UI",
        "benefit": "manage account lifecycle end-to-end within the portal",
    },
    "Application Management": {
        "title": "Application Grid and Provisioning",
        "role": "application administrator",
        "goal": "create and manage applications through the ATR Application page",
        "benefit": "keep the application inventory accurate and up to date",
    },
    "Azure Cloud": {
        "title": "Azure Cloud Deployment and SaaS Configuration",
        "role": "cloud operator",
        "goal": "configure Azure deployments and manage ADU SaaS instances",
        "benefit": "provision and monitor cloud resources from within the portal",
    },
    "Financial Calculators": {
        "title": "Financial Calculator Accessibility",
        "role": "financial analyst",
        "goal": "use interest and other financial calculators in the portal",
        "benefit": "perform accurate financial computations without leaving the platform",
    },
    "Playwright Integration": {
        "title": "Headless Browser Login via Playwright",
        "role": "QA engineer",
        "goal": "run portal login flows using the Playwright automation framework",
        "benefit": "validate portal behaviour in a fast, headless browser environment",
    },
    "Reliability": {
        "title": "Flaky Test Retry and Recovery",
        "role": "QA engineer",
        "goal": "have intermittent test failures retried automatically",
        "benefit": "reduce false-negative results and maintain pipeline stability",
    },
}


def _fallback_story(us_id: str, cluster: FeatureCluster, area_path: str) -> UserStory:
    """Template-based fallback used when Claude API is unavailable."""
    meta = _FALLBACK_METADATA.get(cluster.feature_name, {
        "title": f"{cluster.feature_name} Feature",
        "role": "user",
        "goal": f"use {cluster.feature_name.lower()} functionality",
        "benefit": "complete my tasks efficiently",
    })

    description = (
        f"As a {meta['role']},\n"
        f"I want to {meta['goal']},\n"
        f"So that I can {meta['benefit']}."
    )

    criteria_lines = []
    linked = []
    for tc in cluster.test_cases:
        criteria_lines.append(f"✓ {tc.title}  ← {tc.tc_id}")
        linked.append(tc.tc_id)

    return UserStory(
        us_id=us_id,
        title=meta["title"],
        state="Active",
        area_path=area_path,
        description=description,
        acceptance_criteria="\n".join(criteria_lines),
        linked_tc_ids=linked,
    )
