#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# push_to_rag_script_test.sh
# Copies the Java TestNG automation framework into rohitsharma007/rag_script_test
# and pushes it.
#
# Usage:
#   bash push_to_rag_script_test.sh
#
# Prerequisites: git, GitHub credentials configured (PAT / SSH)
# ─────────────────────────────────────────────────────────────────────────────
set -e

FRAMEWORK_SRC="$(cd "$(dirname "$0")/samples/java_automation_framework" && pwd)"
TARGET_REPO="https://github.com/rohitsharma007/rag_script_test.git"
TMP_DIR="/tmp/rag_script_test_push"

echo "==> Cloning rag_script_test..."
rm -rf "$TMP_DIR"
git clone "$TARGET_REPO" "$TMP_DIR"

echo "==> Copying framework files..."
cp -r "$FRAMEWORK_SRC"/. "$TMP_DIR"/

echo "==> Committing..."
cd "$TMP_DIR"
git add .
git commit -m "Add Java TestNG automation framework

Fully connected 37-file TestNG framework with 5 automation flows:
- Flow 1: Login + Navigation (Login_Page → Get_CertificateToken_Page)
- Flow 2: Account Creation  (Accounts_Page API + MyAccount_Page UI)
- Flow 3: Menu Navigation   (Menu_Page + Navigation_Page)
- Flow 4: Retry Scenario    (RetryAnalyzer implements IRetryAnalyzer)
- Flow 5: Cloud Validation  (Azure_Cloud_Page → Adu_Saas_Page API)

Layers: testcases/ | businessfunctions/ | pages/api/ | pages/atrwebportal/ | retryanalyzer/"

echo "==> Pushing to rag_script_test..."
git push

echo ""
echo "Done! Framework pushed to: $TARGET_REPO"
