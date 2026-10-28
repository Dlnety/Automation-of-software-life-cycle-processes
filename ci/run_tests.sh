#!/usr/bin/env bash
# Работает и внутри TeamCity Agent с Docker socket: bind mount не нужен.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
suite="${1:-all}"
case "$suite" in
  unit) target="tests/unit" ;;
  integration) target="tests/integration" ;;
  all) target="tests" ;;
  *) echo "Usage: bash ci/run_tests.sh [unit|integration|all]" >&2; exit 2 ;;
esac
report_dir="test-reports/$suite"
mkdir -p "$report_dir"
# Стираем только предыдущие результаты выбранного набора.
rm -f "$report_dir/junit.xml" "$report_dir/coverage.xml"
iid_file=$(mktemp)
container_id=""
cleanup() {
  if [[ -n "$container_id" ]]; then
    docker rm -f "$container_id" >/dev/null 2>&1 || true
  fi
  rm -f "$iid_file"
}
trap cleanup EXIT
docker build --iidfile "$iid_file" -f ci/Dockerfile.tests .
container_id=$(docker create "$(cat "$iid_file")" \
  python -m pytest "$target" -v \
  --junitxml="/app/$report_dir/junit.xml" \
  --cov=app --cov=db --cov-report=term-missing \
  --cov-report="xml:/app/$report_dir/coverage.xml")
status=0
docker start -a "$container_id" || status=$?
# Копируем отчёты даже после упавшего теста, затем возвращаем его код ошибки.
docker cp "$container_id:/app/$report_dir/." "$report_dir/"
exit "$status"
