#!/usr/bin/env bash
# SWD20 PDF → Obsidian Vault Converter
# Converts Star Wars D20 Revised Core Rulebook (scanned PDF) into chapter markdown files.
#
# Usage: cd ~/code/StarwarsD20 && nohup bash convert_pdf_to_vault.sh 2>&1 | tee convert.log &

set -euo pipefail

# ──────────────────────────────────────────────
# Phase 0: Setup
# ──────────────────────────────────────────────

VAULT="/Users/josephkampf/code/StarwarsD20"
PDF="/Users/josephkampf/Downloads/SWD20 - Core - Revised Core Rulebook.pdf"
TMPDIR_WORK="$VAULT/.convert_tmp"
IMGDIR="$TMPDIR_WORK/img"
OCRDIR="$TMPDIR_WORK/ocr"
OUTDIR="$VAULT/SWD20 Core Rulebook"
PDFTOPPM=/opt/homebrew/bin/pdftoppm
TESSERACT=/opt/homebrew/bin/tesseract

if [[ ! -f "$PDF" ]]; then
  echo "ERROR: PDF not found at: $PDF"
  exit 1
fi

mkdir -p "$IMGDIR" "$OCRDIR" "$OUTDIR"
echo "[$(date)] Starting SWD20 PDF → Vault conversion..."

# ──────────────────────────────────────────────
# Phase 1: Rasterize + OCR TOC pages (1–25)
# ──────────────────────────────────────────────

echo "[$(date)] Phase 1: Rasterizing TOC pages 1–25 at 150 DPI..."
"$PDFTOPPM" -r 150 -f 1 -l 25 "$PDF" "$IMGDIR/toc"

echo "[$(date)] Phase 1: OCR of TOC pages..."
for i in $(seq -w 1 25); do
  src="$IMGDIR/toc-$i.ppm"
  if [[ -f "$src" ]]; then
    "$TESSERACT" "$src" "$OCRDIR/toc-$i" -l eng 2>/dev/null
  fi
done
echo "[$(date)] Phase 1 complete."

# ──────────────────────────────────────────────
# Phase 2: Parse TOC → chapters.txt
# ──────────────────────────────────────────────

echo "[$(date)] Phase 2: Parsing TOC..."
export TMPDIR_WORK OCRDIR

python3 << 'PYEOF'
import re, os

ocr_dir = os.environ['OCRDIR']
tmp_dir = os.environ['TMPDIR_WORK']

# Read all TOC OCR pages
text = ""
for i in range(1, 26):
    fn = os.path.join(ocr_dir, f"toc-{i:02d}.txt")
    if not os.path.exists(fn):
        fn = os.path.join(ocr_dir, f"toc-{i}.txt")
    if os.path.exists(fn):
        text += open(fn).read() + "\n"

CHAPTER_KEYWORDS = [
    'ABILIT', 'SPECIES', 'CLASS', 'SKILL', 'FEAT', 'HEROIC', 'EQUIP',
    'COMBAT', 'FORCE', 'VEHICLE', 'STARSHIP', 'GAMEMASTER', 'ERAS',
    'ALLIES', 'DROID'
]

entry_re = re.compile(
    r'^.{0,20}(' + '|'.join(CHAPTER_KEYWORDS) + r').{0,40}\b(\d{1,3})\s*$',
    re.IGNORECASE
)

entries = []
for line in text.splitlines():
    m = entry_re.match(line.strip())
    if m:
        keyword = m.group(1).upper()
        page = int(m.group(2))
        entries.append((keyword, page))

# Remove duplicates (keep last occurrence per keyword, highest page wins)
seen = {}
for kw, pg in entries:
    if kw not in seen or pg > seen[kw]:
        seen[kw] = pg
deduped = sorted(seen.items(), key=lambda x: x[1])

# Hardcoded fallback (PDF page numbers, verified)
FALLBACK = [
    ("INTRODUCTION",              7,   16),
    ("ABILITIES",                17,   20),
    ("SPECIES",                  21,   34),
    ("CLASSES",                  35,   66),
    ("SKILLS",                   67,  102),
    ("FEATS",                   103,  118),
    ("HEROIC_CHARACTERISTICS",  119,  128),
    ("EQUIPMENT",               129,  144),
    ("COMBAT",                  145,  172),
    ("THE_FORCE",               173,  184),
    ("VEHICLES",                185,  202),
    ("STARSHIPS",               203,  238),
    ("GAMEMASTERING",           239,  292),
    ("ERAS_OF_PLAY",            293,  318),
    ("ALLIES_AND_OPPONENTS",    319,  358),
    ("DROIDS",                  359,  376),
    ("APPENDIX_PLAYTESTERS",    377,  377),
    ("APPENDIX_TERMS",          378,  379),
    ("INDEX",                   380,  382),
    ("CHARACTER_SHEET",         383,  384),
]

if len(deduped) >= 10:
    print(f"  Parsed {len(deduped)} chapter entries from TOC — using parsed data")
    # Apply +1 PDF offset, compute end pages
    chapters_with_ends = []
    for i, (kw, toc_pg) in enumerate(deduped):
        start = toc_pg + 1  # TOC page number + 1 = PDF page number
        if i + 1 < len(deduped):
            end = deduped[i+1][1]  # next chapter's toc page = this chapter's last PDF page
        else:
            end = 384
        chapters_with_ends.append((kw, start, end))
    use = chapters_with_ends
else:
    print(f"  WARNING: only {len(deduped)} entries found — using hardcoded fallback")
    use = FALLBACK

out_path = os.path.join(tmp_dir, "chapters.txt")
with open(out_path, "w") as f:
    for name, start, end in use:
        f.write(f"{name}|{start}|{end}\n")
print(f"  Written: {out_path} ({len(use)} chapters)")
PYEOF

echo "[$(date)] Phase 2 complete."

# ──────────────────────────────────────────────
# Phase 3: Rasterize all 387 pages
# ──────────────────────────────────────────────

echo "[$(date)] Phase 3: Rasterizing all 387 pages at 150 DPI (this takes ~60–90s)..."
"$PDFTOPPM" -r 150 "$PDF" "$IMGDIR/page"
PAGE_COUNT=$(ls "$IMGDIR"/page-*.ppm 2>/dev/null | wc -l | tr -d ' ')
echo "[$(date)] Phase 3 complete. ${PAGE_COUNT} page images created."

# ──────────────────────────────────────────────
# Phase 4: Parallel OCR (4 workers)
# ──────────────────────────────────────────────

echo "[$(date)] Phase 4: OCR with 4 parallel workers..."
ls "$IMGDIR"/page-*.ppm | \
  xargs -P 4 -I{} bash -c \
    'f="{}"; b="${f%.ppm}"; /opt/homebrew/bin/tesseract "$f" "$b" -l eng 2>/dev/null && echo "  OCR: $(basename $f)"'
OCR_COUNT=$(ls "$IMGDIR"/page-*.txt 2>/dev/null | wc -l | tr -d ' ')
echo "[$(date)] Phase 4 complete. ${OCR_COUNT} pages OCR'd."

# ──────────────────────────────────────────────
# Phase 5: Assemble Markdown files
# ──────────────────────────────────────────────

echo "[$(date)] Phase 5: Assembling markdown files..."
export IMGDIR OUTDIR TMPDIR_WORK

python3 << 'PYEOF'
import os, re

img_dir   = os.environ['IMGDIR']
out_dir   = os.environ['OUTDIR']
tmp_dir   = os.environ['TMPDIR_WORK']

chapters = []
with open(os.path.join(tmp_dir, "chapters.txt")) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split('|')
        if len(parts) == 3:
            name, start, end = parts[0], int(parts[1]), int(parts[2])
            chapters.append((name, start, end))

def sanitize_display(name):
    return name.replace('_', ' ').title()

def make_slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

toc_links = []

for name, start, end in chapters:
    display = sanitize_display(name)
    slug    = make_slug(name)
    filename = f"{slug}.md"
    filepath = os.path.join(out_dir, filename)

    lines = []
    lines.append(f"# {display}\n\n")
    lines.append(f"*Pages {start}–{end} (PDF)*\n\n")
    lines.append("---\n\n")

    for pg in range(start, end + 1):
        txt_path = os.path.join(img_dir, f"page-{pg:03d}.txt")
        if os.path.exists(txt_path):
            content = open(txt_path).read().strip()
            if content:
                lines.append(f"<!-- page {pg} -->\n\n")
                lines.append(content + "\n\n")

    with open(filepath, 'w') as f:
        f.write("".join(lines))

    toc_links.append((display, slug, filename))
    print(f"  Written: {filename} (pp {start}–{end})")

# Write Index.md
index_path = os.path.join(out_dir, "Index.md")
with open(index_path, 'w') as f:
    f.write("# SWD20 Core Rulebook\n\n")
    f.write("*Star Wars D20 Revised Core Rulebook (2002)*\n\n")
    f.write("---\n\n")
    f.write("## Chapters\n\n")
    for display, slug, filename in toc_links:
        f.write(f"- [[{slug}|{display}]]\n")
    f.write("\n---\n\n")
    f.write("*Generated by `convert_pdf_to_vault.sh`*\n")

print(f"  Written: Index.md ({len(toc_links)} entries)")
PYEOF

echo "[$(date)] Phase 5 complete."

# ──────────────────────────────────────────────
# Phase 6: Cleanup
# ──────────────────────────────────────────────

echo "[$(date)] Phase 6: Cleaning up temp files..."
rm -rf "$TMPDIR_WORK"
echo "[$(date)] Done."
echo ""
echo "Files created in: $OUTDIR"
ls -1 "$OUTDIR"
