#!/usr/bin/env bash
set -euo pipefail

for variant in v03 v04 v09 v12 v18 v25; do
    echo "Сборка отчёта: ${variant}"
    uv run python build_report.py "${variant}" || exit 1
done
