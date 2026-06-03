# Redesign Policy

## Round 1: Strict Profile

- primer length: `18-22`
- Tm: `57.0-60.0`
- GC: `45.0-65.0`
- product size: `300-600`
- minimum distance from variant to primer: `100`
- maximum Tm difference: `1.0`
- maximum primer length difference: `2`

This profile mirrors the original baseline script behavior and should run first.

## Round 2: Relaxed Profile

- primer length: `18-24`
- Tm: `54.0-62.0`
- GC: `35.0-70.0`
- product size: `250-650`
- minimum distance from variant to primer: `80`
- maximum Tm difference: `1.5`
- maximum primer length difference: `3`

Run the relaxed profile only for loci that:

- failed in the strict round, or
- passed the design stage but failed BLAST specificity screening

## Selection Logic

For each locus, the final table keeps the best available result in this order:

1. strict-round `specific`
2. relaxed-round `specific`
3. relaxed-round `non_specific`
4. strict-round `non_specific`
5. last failed result

This keeps the most useful result while retaining transparent failure status.

## User Preference Precedence

The strict and relaxed profiles above describe the current v1 implementation baseline. They do not
override the user's standing default preferences.

Use this order of precedence:

1. check whether the user default preferences are compatible with the requested assay and current implementation
2. if incompatible, report a `preference_conflict`
3. only use the strict or relaxed v1 profiles after the user has accepted the compatible workflow or approved a relaxation

In particular, do not silently replace a user default such as `>=1000 bp` primer-to-target distance
with the v1 short-amplicon defaults of `80-100 bp`.
