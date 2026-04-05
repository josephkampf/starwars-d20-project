#!/usr/bin/env bash
# SWD20 PDF → Obsidian Vault Converter (Generic)
# Converts any Star Wars D20 PDF into chapter markdown files.
#
# Usage:
#   bash scripts/convert_pdf_to_vault_generic.sh \
#     "/path/to/pdf" "Output Dir Name" 2>&1 | tee convert-book.log
#
# Example:
#   bash scripts/convert_pdf_to_vault_generic.sh \
#     "/Users/josephkampf/Downloads/SWD20 - Core - Heros Guide.pdf" \
#     "SWD20 Heros Guide"

set -euo pipefail

# ──────────────────────────────────────────────
# Phase 0: Setup & Validation
# ──────────────────────────────────────────────

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <pdf_path> <output_dir_name>"
  echo "Example: $0 '/Users/josephkampf/Downloads/SWD20 - Core - Heros Guide.pdf' 'SWD20 Heros Guide'"
  exit 1
fi

PDF="$1"
OUTPUT_NAME="$2"

VAULT="/Users/josephkampf/code/StarwarsD20"
TMPDIR_WORK="$VAULT/.convert_tmp_generic"
IMGDIR="$TMPDIR_WORK/img"
OCRDIR="$TMPDIR_WORK/ocr"
OUTDIR="$VAULT/$OUTPUT_NAME"
PDFTOPPM=/opt/homebrew/bin/pdftoppm
TESSERACT=/opt/homebrew/bin/tesseract

if [[ ! -f "$PDF" ]]; then
  echo "ERROR: PDF not found at: $PDF"
  exit 1
fi

# Get page count
PAGE_COUNT=$(pdfinfo "$PDF" 2>/dev/null | grep Pages | awk '{print $2}' || echo "384")

mkdir -p "$IMGDIR" "$OCRDIR" "$OUTDIR"
echo "[$(date)] Starting PDF → Vault conversion..."
echo "[$(date)] PDF: $PDF"
echo "[$(date)] Pages: $PAGE_COUNT"
echo "[$(date)] Output: $OUTDIR"
echo ""

# ──────────────────────────────────────────────
# Phase 1: Rasterize all pages
# ──────────────────────────────────────────────

TOC_PAGES=$((PAGE_COUNT < 50 ? PAGE_COUNT : 50))
echo "[$(date)] Phase 1: Rasterizing first $TOC_PAGES pages for TOC at 150 DPI..."
"$PDFTOPPM" -r 150 -f 1 -l "$TOC_PAGES" "$PDF" "$IMGDIR/toc"

echo "[$(date)] Phase 1: OCR of TOC pages..."
for i in $(seq -w 1 "$TOC_PAGES"); do
  src="$IMGDIR/toc-$i.ppm"
  if [[ -f "$src" ]]; then
    "$TESSERACT" "$src" "$OCRDIR/toc-$i" -l eng 2>/dev/null
  fi
done
echo "[$(date)] Phase 1 complete."

# ──────────────────────────────────────────────
# Phase 2: Rasterize all pages
# ──────────────────────────────────────────────

echo "[$(date)] Phase 2: Rasterizing all $PAGE_COUNT pages at 150 DPI (this may take a few minutes)..."
"$PDFTOPPM" -r 150 "$PDF" "$IMGDIR/page"
RASTERIZED=$(ls "$IMGDIR"/page-*.ppm 2>/dev/null | wc -l | tr -d ' ')
echo "[$(date)] Phase 2 complete. $RASTERIZED page images created."

# ──────────────────────────────────────────────
# Phase 3: Parallel OCR (4 workers)
# ──────────────────────────────────────────────

echo "[$(date)] Phase 3: OCR with 4 parallel workers..."
ls "$IMGDIR"/page-*.ppm | \
  xargs -P 4 -I{} bash -c \
    'f="{}"; b="${f%.ppm}"; /opt/homebrew/bin/tesseract "$f" "$b" -l eng 2>/dev/null && echo "  OCR: $(basename $f)"'
OCR_COUNT=$(ls "$IMGDIR"/page-*.txt 2>/dev/null | wc -l | tr -d ' ')
echo "[$(date)] Phase 3 complete. $OCR_COUNT pages OCR'd."

# ──────────────────────────────────────────────
# Phase 4: Assemble Markdown file
# ──────────────────────────────────────────────

echo "[$(date)] Phase 4: Assembling markdown file..."
export IMGDIR OUTDIR

python3 << 'PYEOF'
import os

img_dir = os.environ['IMGDIR']
out_dir = os.environ['OUTDIR']

# Find actual page count from OCR files
pages = []
for fn in sorted(os.listdir(img_dir)):
    if fn.startswith('page-') and fn.endswith('.txt'):
        num = int(fn.replace('page-', '').replace('.txt', ''))
        pages.append(num)

if not pages:
    print("ERROR: No OCR'd pages found")
    exit(1)

min_page = min(pages)
max_page = max(pages)
display_name = os.path.basename(out_dir)

# Create single assembled markdown file
lines = []
lines.append(f"# {display_name}\n\n")
lines.append(f"*Pages 1–{max_page - min_page + 1} (PDF)*\n\n")
lines.append("---\n\n")

for pg in range(min_page, max_page + 1):
    txt_path = os.path.join(img_dir, f"page-{pg:03d}.txt")
    if os.path.exists(txt_path):
        content = open(txt_path).read().strip()
        if content:
            lines.append(f"<!-- page {pg - min_page + 1} -->\n\n")
            lines.append(content + "\n\n")

output_file = os.path.join(out_dir, "content.md")
with open(output_file, 'w') as f:
    f.write("".join(lines))

print(f"  Written: content.md ({max_page - min_page + 1} pages)")
PYEOF

echo "[$(date)] Phase 4 complete."

# ──────────────────────────────────────────────
# Phase 5: Cleanup
# ──────────────────────────────────────────────

echo "[$(date)] Phase 5: Cleaning up temp files..."
rm -rf "$TMPDIR_WORK"
echo "[$(date)] Done."
echo ""
echo "Files created in: $OUTDIR"
ls -lh "$OUTDIR"
