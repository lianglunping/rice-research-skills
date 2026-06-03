# DOCX Markdown Bridge

Use this module when the working document is a Word file or when the user needs a Word-facing output.

## Supported V1 Operations

- extract `.docx` into Markdown and JSON
- extract one section from a larger `.docx`
- render Markdown back to `.docx`
- create a paragraph-level patch pack between original and revised text

## Not In V1

- Word tracked changes
- comments balloons
- style-preserving in-place XML surgery
- equation or citation-field round-trip guarantees

## Commands

### Extract

```bash
micromamba run -n py3 python scripts/docx_extract.py input.docx --output-dir /tmp/docx_extract
```

### Extract One Section

```bash
micromamba run -n py3 python scripts/docx_extract.py input.docx --output-dir /tmp/docx_extract --section "相关工作"
```

### Render Markdown To Word

```bash
micromamba run -n py3 python scripts/docx_render.py input.md output.docx
```

### Render With Reference Template

```bash
micromamba run -n py3 python scripts/docx_render.py input.md output.docx --reference-doc template.docx
```

### Build Patch Pack

```bash
micromamba run -n py3 python scripts/section_patch_pack.py --original original.md --revised revised.md --output-dir /tmp/patch_pack
```

## Workflow Recommendation

1. Extract `.docx` to Markdown/JSON.
2. Revise the Markdown or a section subset.
3. If the user wants a clean Word output, render the revised Markdown to `.docx`.
4. If the user wants a reviewable change bundle, produce a patch pack.

## Heading Mapping

- `Heading 1` -> `#`
- `Heading 2` -> `##`
- `Heading 3` -> `###`
- `Heading 4` -> `####`

If the extracted document uses nonstandard style names, rely on text structure conservatively and do not invent heading levels.

## Safety Rules

- Treat extracted Markdown as a working surface, not the ground truth of formatting.
- Preserve tables as faithfully as feasible, but if the table is too complex, keep the text and note the limitation.
- For thesis work, keep the Word version and intermediate Markdown aligned in section logic.
