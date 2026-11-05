# Compatibility notice

This legacy guide is intentionally retired because it encoded a fixed caller set, merge distance, and minimum caller count that are not portable across SV classes or datasets.

Use `SKILL.md` as the canonical entry point. Load:

- `references/evidence-and-design.md` for the 2026 benchmark evidence and limitations;
- `references/workflow-contract.md` for manifests, output layout, matching policy, benchmarking, and failure gates;
- `scripts/validate_ensemble_manifest.py` for read-only ensemble preflight.

Historical commands are not production defaults and must not be reconstructed from this compatibility file.
