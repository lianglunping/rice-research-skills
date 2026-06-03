#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-primer-design}"

if ! command -v mamba >/dev/null 2>&1; then
  echo "mamba not found in PATH" >&2
  exit 1
fi

if ! mamba env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
  mamba create -y -n "${ENV_NAME}" \
    python=3.11 \
    pandas \
    openpyxl \
    xlrd \
    pyfaidx \
    blast \
    xlsxwriter \
    pytest \
    ruff
fi

mamba run -n "${ENV_NAME}" python - <<'PY'
import pandas
import pyfaidx
import openpyxl
import xlrd
import xlsxwriter
print("python-ok")
print(f"pandas={pandas.__version__}")
print(f"pyfaidx={pyfaidx.__version__}")
print(f"openpyxl={openpyxl.__version__}")
print(f"xlrd={xlrd.__version__}")
print(f"xlsxwriter={xlsxwriter.__version__}")
PY

mamba run -n "${ENV_NAME}" blastn -version | head -n 1
mamba run -n "${ENV_NAME}" makeblastdb -version | head -n 1
