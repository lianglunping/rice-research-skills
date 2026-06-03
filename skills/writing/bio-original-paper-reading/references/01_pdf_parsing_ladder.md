# PDF Parsing Ladder

PDF parsing improves navigation; it does not replace original PDF inspection.

## Parser Choice

1. **Born-digital, ordinary layout**
   - Try PyMuPDF4LLM or equivalent lightweight local extraction for Markdown/page chunks.
   - Use GROBID or equivalent when metadata, references, and section hierarchy matter.
2. **Complex multi-column, tables, formulas, images**
   - Try Docling, Marker, MinerU, or a comparable structure-aware parser if available.
   - Compare section order, captions, tables, and formulas against the PDF.
3. **Scanned or OCR-heavy PDF**
   - Use OCR-capable tools only if available and permitted.
   - If OCR quality is low, switch to page-image reading and mark confidence as low.
4. **Figure/caption extraction**
   - Use PDFFigures2, Marker, MinerU, or page screenshots only as candidate extraction.
   - Always verify panel boundaries and captions against original PDF pages.
5. **Cloud parsers**
   - Use only when the user allows cloud processing and privacy constraints are acceptable.

## Parse Manifest

Record:

```yaml
pdf_path:
engines_used:
engine_versions:
pages_total:
sections_detected:
figures_detected:
tables_detected:
supplement_detected:
ocr_used:
layout_confidence: high|medium|low
known_parse_errors:
manual_verification_required:
```

Every extracted section, caption, table, and figure candidate should keep source provenance when feasible:

```yaml
source_type: original_pdf|parser_markdown|parser_json|ocr|page_screenshot|external
source_engine:
source_page:
source_confidence: high|medium|low
visual_verified: true|false
```

## Evidence Confidence

- `high`: section order, figures, captions, and tables match PDF spot checks.
- `medium`: text mostly usable but captions, tables, or figure locations need manual verification.
- `low`: OCR, page order, formulas, tables, or figures are unreliable. Reduce conclusion strength.
