# Findings Schema

Return findings first. Keep them concrete.

## Required Fields Per Finding

- `severity`: `critical`, `major`, `moderate`, or `minor`
- `location`: section title, paragraph opener, table, figure, or file path
- `problem`: one-sentence statement of the issue
- `why_it_matters`: what risk this creates
- `minimum_fix`: smallest useful correction

## Ordering

1. issues that can invalidate the argument
2. issues that weaken the main line
3. issues that create defense or review vulnerability
4. cosmetic issues

## Example Shape

```text
1. [major] Section 2.3 gap statement is still generic.
Why it matters: an outside reviewer can read this as a broad topic motivation rather than a research gap.
Minimum fix: rewrite the closing paragraph to distinguish what prior rice mutagenesis studies established from what they still do not connect.
```

## Optional Closing Sections

- `Open Questions`: unresolved ambiguity that needs user input
- `Priority Order`: the first three fixes to make
- `Residual Risk`: what remains risky even after the obvious fixes
