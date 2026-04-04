# CLAUDE.md — StarwarsD20 Project

This file captures all conventions and hard-won learnings for working in this repository.
It is read automatically by Claude Code at the start of every session.

---

## Project Overview

This repository is an **Obsidian vault** containing the *Star Wars D20 Revised Core Rulebook (2002)*,
converted from a scanned PDF into chapter-level markdown files.

- `SWD20 Core Rulebook/` — generated chapter markdown files (the vault content)
- `scripts/` — utility scripts for OCR processing and formatting
  - `convert_pdf_to_vault.sh` — full pipeline: rasterize → OCR → assemble markdown
  - `convert_tables.py` — converts plain-text table data into markdown pipe tables
  - `format_vault.py` — initial formatting pass on fresh OCR output; **run once, not idempotent**
  - `improve_formatting.py` — post-processing formatting improvements; **idempotent**, safe to re-run
  - `revert_bad_tables.py` — reverts tables that were converted incorrectly
  - `unwrap_paragraphs.py` — joins lines within paragraphs; **idempotent**

---

## Git Workflow

**All changes must be made on a feature branch and submitted as a pull request before merging to main.**

- Create a feature branch: `git checkout -b descriptive-branch-name`
- Make changes and commit: `git commit -m "Clear, descriptive commit message"`
- Push to remote: `git push -u origin descriptive-branch-name`
- Create a PR on GitHub with a clear summary of changes
- PRs are reviewed before merging to main
- Never commit directly to main

---

## PDF Extraction Workflow

When working with large PDFs that cannot be read directly:

- Use `pdftotext` to extract to `~/Data` as a `.txt` file before reading
- Binary is at `/opt/homebrew/bin/pdftotext`
- Command: `pdftotext "/path/to/file.pdf" ~/Data/filename.txt`
- Output filename should match the PDF base name with `.txt` extension
- Check `~/Data` first — the file may already have been extracted in a prior session
- The Read tool has a 100 MB size limit and a 20-page limit per call — `pdftotext` handles large files reliably

---

## PDF → Obsidian Vault Conversion (OCR Pipeline)

### Tool versions / paths (this machine)

| Tool | Path |
|------|------|
| `pdftoppm` | `/opt/homebrew/bin/pdftoppm` |
| `tesseract` | `/opt/homebrew/bin/tesseract` |

### Critical constraints

- **`pdftoppm` format:** Use default PPM format — **do NOT pass `-png`**. Tesseract cannot open PNG on
  this system (Leptonica error).
- **Temp directory:** Must be inside `$HOME`, not `/tmp`. Tesseract silently fails on `/tmp` files
  due to a macOS SIP interaction.
- **DPI:** 150 DPI is the right balance of speed vs. accuracy for scanned rulebooks.
- **Parallel OCR:** Use `xargs -P 4` for 4-worker parallelism.
- **Extension stripping in xargs:** Use `bash -c` wrapper with `${f%.ppm}` to correctly strip the
  `.ppm` extension before passing to Tesseract.
- **Zero-padding:** `pdftoppm` zero-pads filenames to 3 digits (`page-001.ppm`). Use `{pg:03d}` in
  Python loops when building filenames.

### Chapter map rules

- **Exclude** the "INDEX" / "Alphabetical Index" appendix from the chapter map.
  - Why: macOS has a case-insensitive filesystem. `Index.md` (the master nav file) and `index.md`
    (a chapter file) collide, silently overwriting content.
  - The Obsidian search function makes a book index unnecessary anyway.
- The master nav file is `SWD20 Core Rulebook/Index.md` and contains wiki-links to all chapters.
- Other low-value appendices (playtesters, character sheets) can be included or skipped.

### Hardcoded chapter page ranges (PDF page numbers, verified)

| Chapter | Start | End |
|---------|-------|-----|
| INTRODUCTION | 7 | 16 |
| ABILITIES | 17 | 20 |
| SPECIES | 21 | 34 |
| CLASSES | 35 | 66 |
| SKILLS | 67 | 102 |
| FEATS | 103 | 118 |
| HEROIC_CHARACTERISTICS | 119 | 128 |
| EQUIPMENT | 129 | 144 |
| COMBAT | 145 | 172 |
| THE_FORCE | 173 | 184 |
| VEHICLES | 185 | 202 |
| STARSHIPS | 203 | 238 |
| GAMEMASTERING | 239 | 292 |
| ERAS_OF_PLAY | 293 | 318 |
| ALLIES_AND_OPPONENTS | 319 | 358 |
| DROIDS | 359 | 376 |
| APPENDIX_PLAYTESTERS | 377 | 377 |
| APPENDIX_TERMS | 378 | 379 |
| CHARACTER_SHEET | 383 | 384 |

*(INDEX 380–382 is intentionally excluded — see Chapter map rules above.)*

---
