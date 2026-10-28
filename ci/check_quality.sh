#!/usr/bin/env bash
set -euo pipefail

mkdir -p analysis-reports

docker build -f ci/Dockerfile.quality \
  -t studentprogress-quality .

docker run --rm studentprogress-quality \
  2>&1 | tee analysis-reports/pylint.log
