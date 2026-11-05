#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export PYTHONDONTWRITEBYTECODE=1
python3 -B skills/workflow/job-monitor-loop/scripts/test_next_check.py
python3 -B skills/workflow/job-monitor-loop/scripts/test_monitor_repair_budget.py
python3 -B skills/workflow/provenance-doc/scripts/test_smoke.py
python3 -B skills/workflow/provenance-doc/tests/test_state_machine.py
python3 -B skills/workflow/provenance-doc/tests/check_v132_mapping.py
bash skills/workflow/provenance-doc/tests/check_contract.sh
python3 -B -m pytest -p no:cacheprovider skills/bio/variant-primer-design/tests
