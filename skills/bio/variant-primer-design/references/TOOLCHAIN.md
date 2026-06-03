# Toolchain

## Dedicated Environment

The skill ships a dedicated environment bootstrap script:

```bash
cd /path/to/codex/skills/variant-primer-design
bash scripts/bootstrap_env.sh
```

Default environment name:

- `primer-design`

## Package Policy

The bootstrap script prefers `mamba` and creates a conda-style named environment with:

- `python=3.11`
- `pandas`
- `openpyxl`
- `xlrd`
- `pyfaidx`
- `blast`
- `xlsxwriter`
- `pytest`
- `ruff`

## Verification Commands

```bash
mamba run -n primer-design python -m pytest -q
mamba run -n primer-design ruff check .
mamba run -n primer-design python -m compileall scripts tests
```

## Reproducibility

The workflow report records:

- input path
- reference FASTA or BLAST DB prefix
- assay mode
- flank-size assumptions
- selected output directory
- Python version
- command line

If package-level version pinning becomes critical later, add a lock file or explicit export from the dedicated environment.
