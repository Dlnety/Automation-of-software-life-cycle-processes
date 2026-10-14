#!/usr/bin/env bash
set -euo pipefail

mkdir -p analysis-reports

docker build -f ci/Dockerfile.secrets \
  -t studentprogress-secrets .

docker run --rm studentprogress-secrets \
  dir /scan --verbose --redact=100 \
  2>&1 | tee analysis-reports/gitleaks.log
