#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

mapfile -d '' -t sql_files < <(git ls-files -z -- '*.sql')
if (( ${#sql_files[@]} == 0 )); then
    echo "В репозитории не найдены SQL-файлы."
    exit 1
fi

printf 'SQL-файлы для проверки:\n'
printf '  %s\n' "${sql_files[@]}"

tar -cf - -- ci/semgrep-sql.yml "${sql_files[@]}" |
    docker run --rm -i --entrypoint sh semgrep/semgrep:latest -ec '
        mkdir -p /tmp/sql-check
        cd /tmp/sql-check
        tar -xf -
        semgrep scan --config ci/semgrep-sql.yml \
            --include "*.sql" --metrics=off --error .
    '
