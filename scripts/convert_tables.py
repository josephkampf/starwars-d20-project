#!/usr/bin/env python3
"""
Convert plain-text table data to markdown pipe tables in SWD20 vault files.

Strategy:
- Detect **Table N-N:** captions
- Collect the table block (stop aggressively at body-text indicators)
- Detect header (short lines with no value tokens, max 2 lines)
- Detect column count via trailing-value-token counting
- Split each row and build a pipe table
- Only write if result passes quality checks
"""
import re, os, glob
from collections import Counter

VAULT = "/Users/josephkampf/code/StarwarsD20/SWD20 Core Rulebook"
PAGE_RE    = re.compile(r'^<!-- page \d+ -->')
HEAD_RE    = re.compile(r'^#{1,6} ')
BOLD_RE    = re.compile(r'^\*\*[^*]')   # **Some text  (not **Table)
CAPTION_RE = re.compile(r'^\*\*Table \d')

# ── Value-token detection ─────────────────────────────────────────────────────
VALUE_RE = re.compile(
    r'^[+\-]?\d+\.?\d*$'           # plain numbers: -8, +2, 0, 3.5
    r'|^`[^`]+`$'                   # inline code (dice already wrapped)
    r'|^\d+[dk]\d+([+\-]\d+)?$'    # bare dice: 2d6, 1d4+2
    r'|^x\d+(/\d+)?\.?$'           # multipliers: x1, x3/4
    r'|^\*\d+(\/\d+)?\.?$'         # OCR: *1/2
    r'|^«\d+(\/\d+)?\.?$'          # OCR: «1/2
    r'|^~\d+(\/\d+)?\.?$'          # OCR: ~3/4
    r'|^«?\d+/\d+\.?$'             # fractions: 3/4
    r'|^[+\-]?\d+[mk]m?\.?$'       # measurements: 10m, 2km
    r'|^(Yes|No|None|Free|Move|Full[- ]round|Standard|Swift|Immediate|Varies)$'
    r'|^[-—=~«»]+\.?$'             # dashes / OCR artifacts
    r'|^\d+-\d+$'                   # ranges: 1-5, 6-10
    r'|^[A-Z][+\-]\d+$',            # ability adjustments in specific contexts
    re.IGNORECASE
)

def is_value(tok):
    t = re.sub(r'^[\'"""''`*]|[\'"""''`*.,;]$', '', tok)
    return bool(VALUE_RE.match(t))

def trailing_value_count(tokens):
    count = 0
    for tok in reversed(tokens):
        if is_value(tok):
            count += 1
        else:
            break
    return count

def looks_like_body_text(line):
    """True if a line is clearly body text (not a table row)."""
    s = line.strip()
    if not s:
        return False
    # Very long lines are body text
    if len(s) > 120:
        return True
    # Starts with lowercase and has no values = likely a continuation sentence
    toks = s.split()
    if toks and toks[0][0].islower() and trailing_value_count(toks) == 0:
        if len(toks) > 6:
            return True
    # Lines ending in common sentence punctuation with many words
    if s.endswith(('.', ',', ';')) and len(toks) > 8 and trailing_value_count(toks) == 0:
        return True
    return False

# ── Table block collector ─────────────────────────────────────────────────────
def collect_table_block(lines, start):
    """
    Collect lines belonging to this table.
    Stops at: heading, page marker, another **Table caption,
               2 consecutive blank lines, or clear body text.
    Returns (collected_lines, end_index).
    """
    block = []
    i = start
    consecutive_blanks = 0

    while i < len(lines):
        raw  = lines[i]
        s    = raw.strip()

        # Hard stops
        if HEAD_RE.match(s) or PAGE_RE.match(s):
            break
        if CAPTION_RE.match(s) and i != start:
            break
        # A **Bold** line that isn't a table caption = new section header
        if BOLD_RE.match(s) and not CAPTION_RE.match(s):
            break

        if not s:
            consecutive_blanks += 1
            if consecutive_blanks >= 2:
                break
            block.append(raw)
        else:
            consecutive_blanks = 0
            if looks_like_body_text(raw):
                break
            block.append(raw)
        i += 1

    # Trim trailing blanks
    while block and not block[-1].strip():
        block.pop()

    return block, i

# ── Header extraction ─────────────────────────────────────────────────────────
def extract_header(rows, n_cols):
    """
    Find header rows at the top (lines with no or few value tokens).
    Max 2 header lines. Skips if header line is > 100 chars (garbled).
    Returns (header_cells, remaining_data_rows).
    """
    header_parts = []
    data_start   = 0

    for i, row in enumerate(rows):
        s    = row.strip()
        if not s:
            continue
        # Too long → garbled, treat as data
        if len(s) > 100:
            break
        toks = s.split()
        vc   = trailing_value_count(toks)
        # Header: no values at all (or line is very short = column-name continuation)
        all_non_value = (vc == 0)
        if all_non_value and len(header_parts) < 2:
            header_parts.append(s)
            data_start = i + 1
        else:
            break

    if not header_parts:
        return [f'Col {j+1}' for j in range(n_cols)], rows

    # Build cells from merged header
    merged = ' '.join(header_parts)
    # Try 2+ space split
    cells = re.split(r' {2,}', merged)
    if len(cells) >= n_cols:
        return [c.strip() for c in cells[:n_cols]], rows[data_start:]
    # Otherwise split on single spaces and group into n_cols buckets
    words = merged.split()
    if len(words) <= n_cols:
        cells = words + [f'Col {j+len(words)+1}' for j in range(n_cols - len(words))]
        return cells[:n_cols], rows[data_start:]
    # Group: last n_cols-1 words are last n_cols-1 column names; rest = col1 name
    cells = [' '.join(words[:len(words)-(n_cols-1)])] + words[-(n_cols-1):]
    return [c.strip() for c in cells[:n_cols]], rows[data_start:]

# ── Column count detection ─────────────────────────────────────────────────────
def detect_ncols(rows):
    counts = []
    for row in rows:
        s    = row.strip()
        if not s or len(s) > 100:
            continue
        toks = s.split()
        if len(toks) < 2:
            continue
        vc = trailing_value_count(toks)
        if 1 <= vc <= 7:
            counts.append(vc + 1)

    if not counts:
        return 0
    c = Counter(counts)
    top_n, top_freq = c.most_common(1)[0]
    total_counted = len(counts)
    total_rows    = sum(1 for r in rows if r.strip() and len(r.strip()) <= 100)
    # Must cover at least 40% of counted rows AND at least 2 rows
    if top_freq < 2 or top_freq < total_counted * 0.40:
        return 0
    return top_n

# ── Row splitting ─────────────────────────────────────────────────────────────
def split_data_row(row, n_cols):
    toks = row.strip().split()
    if len(toks) < n_cols:
        return None
    if len(toks) == n_cols:
        return toks
    tail = toks[-(n_cols - 1):]
    head = ' '.join(toks[:len(toks) - (n_cols - 1)])
    return [head] + tail

# ── Quality validation ────────────────────────────────────────────────────────
def validate_split_rows(split_rows, n_cols):
    """
    Check that:
    - At least 2 rows were successfully split
    - Last cell of most rows is value-like (not a random word)
    """
    if not split_rows:
        return False
    good = [cells for cells in split_rows if cells is not None and len(cells) >= n_cols]
    if len(good) < 2:
        return False
    # Check last cell of each good row
    last_col_value = sum(1 for cells in good if is_value(cells[-1].split()[-1]) if cells[-1])
    # At least 50% of rows should have a value-like last cell
    if last_col_value < len(good) * 0.50:
        return False
    return True

# ── Pipe table builder ────────────────────────────────────────────────────────
def build_pipe_table(header_cells, split_rows):
    n = len(header_cells)
    widths = [max(3, len(h)) for h in header_cells]
    for cells in split_rows:
        if cells is None:
            continue
        for j, c in enumerate(cells[:n]):
            widths[j] = max(widths[j], len(str(c)))

    def fmt(cells):
        padded = [str(cells[j] if j < len(cells) else '').ljust(widths[j]) for j in range(n)]
        return '| ' + ' | '.join(padded) + ' |'

    lines = [fmt(header_cells),
             '| ' + ' | '.join('-' * w for w in widths) + ' |']
    for cells in split_rows:
        if cells is not None:
            lines.append(fmt(cells))
    return lines

# ── Per-file processing ───────────────────────────────────────────────────────
def process_file(fp):
    original = open(fp).read()
    lines    = original.split('\n')
    out      = []
    i        = 0
    stats    = {'converted': 0, 'skipped': 0}

    while i < len(lines):
        raw = lines[i]
        s   = raw.strip()

        if not CAPTION_RE.match(s):
            out.append(raw)
            i += 1
            continue

        out.append(raw)
        i += 1

        block, end_i = collect_table_block(lines, i)

        # Skip if already pipe table
        if any(l.strip().startswith('|') for l in block):
            out.extend(lines[i:end_i])
            i = end_i
            continue

        # Non-blank candidate rows
        candidate_rows = [l for l in block if l.strip()]

        n_cols = detect_ncols(candidate_rows)
        if n_cols < 2:
            stats['skipped'] += 1
            out.extend(lines[i:end_i])
            i = end_i
            continue

        header_cells, data_rows = extract_header(candidate_rows, n_cols)

        # If no data rows remain after header extraction, skip
        if not data_rows:
            stats['skipped'] += 1
            out.extend(lines[i:end_i])
            i = end_i
            continue

        split_rows = []
        for row in data_rows:
            s2 = row.strip()
            if not s2:
                continue
            cells = split_data_row(row, n_cols)
            split_rows.append(cells)

        if not validate_split_rows(split_rows, n_cols):
            stats['skipped'] += 1
            out.extend(lines[i:end_i])
            i = end_i
            continue

        table_lines = build_pipe_table(header_cells, split_rows)
        out.append('')
        out.extend(table_lines)
        out.append('')
        stats['converted'] += 1
        i = end_i

    new_content = '\n'.join(out)
    if new_content != original:
        open(fp, 'w').write(new_content)
    return stats

# ── Main ──────────────────────────────────────────────────────────────────────
files = sorted(glob.glob(os.path.join(VAULT, '[0-9]*.md')))
totals = {'converted': 0, 'skipped': 0}
for fp in files:
    name  = os.path.basename(fp)
    stats = process_file(fp)
    if stats['converted'] or stats['skipped']:
        print(f"  {name}: {stats['converted']} converted, {stats['skipped']} skipped")
    totals['converted'] += stats['converted']
    totals['skipped']   += stats['skipped']
print(f"\nTotal: {totals['converted']} converted, {totals['skipped']} skipped")
