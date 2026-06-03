# User Default Preferences

These defaults apply to all future primer design tasks for this user unless the user explicitly asks
to relax them.

## Pair-Level Defaults

- primer length: `18-22 bp`
- primer Tm: `58-60 C`
- each primer should be at least `1000 bp` away from the target site when feasible under the
  requested assay design
- forward and reverse primers in the same pair should ideally have identical length
- forward and reverse primers in the same pair should ideally have identical or nearly identical Tm
- specificity is mandatory

## Panel-Level Preferences

- different primer pairs should ideally have similar Tm
- product sizes across the panel should ideally be similar

## Conflict Handling

These defaults can conflict with the current v1 short-amplicon workflow, especially when a task
implicitly becomes a long-amplicon design because both primers are expected to stay at least
`1000 bp` away from the target site.

When that conflict exists:

- do not silently fall back to shorter-distance defaults such as `80-100 bp`
- do not present the v1 short-amplicon workflow as if it already satisfies these defaults
- explicitly report the conflict
- either switch to a compatible custom workflow or get approval to relax the defaults
