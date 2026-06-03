# Boundary Edge Cases — Spec §8.2
<!-- Plan Section: Chunk 7, Task 4-5 — Examples -->
<!-- Plan Version: 2026-04-30-provenance-doc-plan.md -->

Three mini cases illustrating how to handle common boundary situations
when writing or updating a provenance document.

---

## Case 1: Parameter Change Between Versions

**Situation**: Between v1.0 and v2.0 of a pipeline, the quality threshold
changes from 20 to 25. This affects the record count in the output.

**Documents to update**:
1. `archive/legacy_results/v2.0/provenance.md` — new version document
2. `DECISION_LOG.md` — record why the threshold was changed

**What each document should say**:
- `provenance.md §6.4` (Parameter Deltas): list `quality_threshold: 20 → 25`
  and give a one-line rationale (e.g., "raised to reduce false-positive rate
  based on audit findings in `audit_threshold_20260501.md`").
- `provenance.md §8` (Delta Table): compare `record_count` old vs. new,
  with delta and change reason in the `reason` column.
- `DECISION_LOG.md`: one appended entry with the decision date, old value,
  new value, and the evidence that justified the change.

---

## Case 2: Adding a Caveat After Analysis

**Situation**: After completing analysis, the analyst discovers that a subset
of records had a labeling inconsistency not caught at filtering time. The
analysis is already in `verified` state.

**Documents to update**:
1. `provenance.md §0.4` (Known Caveats) — add a one-line caveat summary
2. `audit_label_inconsistency_20260502.md` — full description of the finding

**What each document should say**:
- `provenance.md §0.4`: "Label inconsistency in ~5% of Category B records;
  does not affect aggregate totals; see `audit_label_inconsistency_20260502.md`."
- `audit_*.md`: full description of which records were affected, how the
  inconsistency was detected, and what downstream impact (if any) it has.
- Do **not** revert the document to `draft` for a caveat addition — caveats
  are narrative and do not invalidate existing verified claims.

---

## Case 3: Correcting a Number After Verification

**Situation**: A verified claim `c02` asserted record count = 182, but a
subsequent check found the correct value is 180 (two duplicate IDs were
counted twice).

**Documents to update**:
1. `provenance.md §5` (Claim Verification Registry) — update `value` and
   `observed_result` for `c02`; revert status to `unverified` then re-run

**What each document should say**:
- `provenance.md §5 / c02`: correct `value` from `182` to `180`;
  set `status` to `unverified`; re-run `verify_claims.py` to repopulate
  `observed_result`; confirm `status` returns to `verified`.
- `provenance.md §7.2` (Version Lineage): note the correction if this is
  a new version bump; otherwise add a one-line note in `§5.2` Change Summary.
- `evolution.md` (if the error affects downstream conclusions): record
  old conclusion, new conclusion, and the trigger event that revealed the error.
- The document should be taken back through the state machine:
  `verified → numbers-pending → verification-ready → verified`.
