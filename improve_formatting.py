#!/usr/bin/env python3
"""
Post-processing formatting improvements for SWD20 vault markdown files.
Safe to run on already-formatted files (idempotent).

Applies:
1. Bullet continuation indentation (2 spaces for wrapped bullet text)
2. Dice notation → inline code (1d20, 4d6, d8, etc.)
3. Simple two-column tables (Commodity / Cost format)
"""
import re, os, glob

VAULT = "/Users/josephkampf/code/StarwarsD20/SWD20 Core Rulebook"
PAGE_RE = re.compile(r'^<!-- page \d+ -->')
HEADING_RE = re.compile(r'^#{1,6} ')
BULLET_RE = re.compile(r'^- ')
SPECIAL_START = re.compile(r'^(- |#{1,6} |> |<!--|\*\*|\||\d+\. |  )')

# ── 1. Bullet continuation indentation ─────────────────────────────────────────

def fix_bullet_continuations(lines):
    """Indent bare continuation lines under bullet items with 2 spaces."""
    result = []
    in_bullet = False

    for i, raw in enumerate(lines):
        s = raw.strip()

        # Page markers and headings always reset bullet state
        if PAGE_RE.match(s) or HEADING_RE.match(s):
            in_bullet = False
            result.append(raw)
            continue

        if not s:
            # Blank line ends the bullet
            in_bullet = False
            result.append(raw)
            continue

        # New bullet item
        if BULLET_RE.match(raw):
            in_bullet = True
            result.append(raw)
            continue

        # Already indented (previous pass or original) — keep as-is, maintain state
        if raw.startswith('  ') and in_bullet:
            result.append(raw)
            continue

        # Continuation candidate: in_bullet and starts with lowercase, '(', or
        # is indented continuation of a parenthetical (prev was indented continuation)
        prev_is_cont = result and result[-1].startswith('  ') and not result[-1].startswith('   ')
        if in_bullet and (s[0].islower() or s[0] == '(' or prev_is_cont):
            result.append('  ' + raw)
            continue

        # Anything else resets bullet state
        in_bullet = False
        result.append(raw)

    return result


# ── 2. Dice notation → inline code ─────────────────────────────────────────────

DICE_RE = re.compile(
    r'(?<!`)'           # not already inside backtick
    r'\b(\d*d\d+(?:[+\-]\d+)?)\b'
    r'(?!`)',           # not followed by backtick (already wrapped)
    re.IGNORECASE
)

def fix_dice_notation(lines):
    """Wrap dice expressions in backticks."""
    result = []
    for raw in lines:
        s = raw.strip()
        # Don't modify headings, page markers, or already-code lines
        if PAGE_RE.match(s) or HEADING_RE.match(s) or s.startswith('```'):
            result.append(raw)
            continue
        new = DICE_RE.sub(r'`\1`', raw)
        result.append(new)
    return result


# ── 3. Two-column commodity tables ─────────────────────────────────────────────

# Matches "Name (with spaces/commas/numbers)  cost_digits credits"
COMMODITY_ROW_RE = re.compile(
    r'^(.+?)\s+([\d,]+\s+credits?)$',
    re.IGNORECASE
)

def try_convert_commodity_block(block):
    """
    Convert plain-text rows to a markdown table.
    block = list of stripped non-blank non-footnote lines (data rows only, no header).
    Returns list of markdown table lines, or None if not confident.
    """
    rows = []
    for line in block:
        s = line.strip()
        if not s or s.startswith('*') or s.startswith('Commodity'):
            continue
        m = COMMODITY_ROW_RE.match(s)
        if not m:
            return None
        rows.append((m.group(1).strip(), m.group(2).strip()))
    if len(rows) < 3:
        return None
    col1_w = max(len(r[0]) for r in rows)
    col2_w = max(len(r[1]) for r in rows)
    out = []
    out.append(f"| {'Commodity':{col1_w}} | {'Cost':{col2_w}} |")
    out.append(f"| {'-'*col1_w} | {'-'*col2_w} |")
    for name, cost in rows:
        out.append(f"| {name:{col1_w}} | {cost:{col2_w}} |")
    return out

def fix_simple_tables(lines):
    """
    Convert plain two-column "Name   cost credits" tables to markdown pipe tables.
    Only activates after a **Table N-N: ...** bold caption.
    Collects data across blank lines within the table block.
    """
    result = []
    i = 0
    while i < len(lines):
        raw = lines[i]
        s = raw.strip()

        # Deduplicate consecutive identical table captions (OCR double-print)
        if re.match(r'^\*\*Table ', s) and result and result[-1].strip() == s:
            i += 1
            continue

        if re.match(r'^\*\*Table ', s):
            result.append(raw)
            i += 1

            # Gather all lines until we hit a heading or page marker
            # (blank lines inside the table are ok — skip them when collecting rows)
            block = []
            footnotes = []
            j = i
            while j < len(lines):
                rs = lines[j].strip()
                if HEADING_RE.match(rs) or PAGE_RE.match(rs):
                    break
                if BULLET_RE.match(rs):
                    break
                if rs.startswith('*') and len(rs) < 60:
                    footnotes.append(rs)
                else:
                    block.append(lines[j])
                j += 1

            table_lines = try_convert_commodity_block(block)
            if table_lines:
                result.append('')
                result.extend(table_lines)
                for fn in footnotes:
                    result.append('')
                    result.append(fn)
                result.append('')
                i = j
                continue
            # else: fall through — emit block lines as-is
            result.extend(block)
            result.extend(footnotes)
            i = j
            continue

        result.append(raw)
        i += 1

    return result


# ── Main ────────────────────────────────────────────────────────────────────────

files = sorted(glob.glob(os.path.join(VAULT, '[0-9]*.md')))
stats = {'bullet_cont': 0, 'dice': 0, 'tables': 0}

for fp in files:
    name = os.path.basename(fp)
    original = open(fp).read()
    lines = original.split('\n')

    # Pass 1: bullet continuations
    before = sum(1 for l in lines if l.startswith('  ') and not l.startswith('   '))
    lines = fix_bullet_continuations(lines)
    after = sum(1 for l in lines if l.startswith('  ') and not l.startswith('   '))
    bc = after - before
    stats['bullet_cont'] += bc

    # Pass 2: dice notation
    dice_before = sum(1 for l in lines if '`' in l)
    lines = fix_dice_notation(lines)
    dice_after = sum(1 for l in lines if '`' in l)
    dc = dice_after - dice_before
    stats['dice'] += dc

    # Pass 3: simple tables
    table_before = sum(1 for l in lines if l.startswith('| '))
    lines = fix_simple_tables(lines)
    table_after = sum(1 for l in lines if l.startswith('| '))
    tc = table_after - table_before
    stats['tables'] += tc

    # Pass 4: deduplicate table captions that appear multiple times
    seen_captions = set()
    deduped = []
    k = 0
    while k < len(lines):
        s = lines[k].strip()
        if re.match(r'^\*\*Table ', s):
            if s in seen_captions:
                # Skip this duplicate caption and any immediately-following footnotes/blanks
                k += 1
                while k < len(lines) and (not lines[k].strip() or lines[k].strip().startswith('*')):
                    k += 1
                continue
            seen_captions.add(s)
        deduped.append(lines[k])
        k += 1
    lines = deduped

    new_content = '\n'.join(lines)
    if new_content != original:
        open(fp, 'w').write(new_content)
        print(f"  {name}: +{bc} bullet-cont, +{dc} dice, +{tc} table-rows")

print(f"\nTotals — bullet continuations: {stats['bullet_cont']}, "
      f"dice wrapped: {stats['dice']}, table rows: {stats['tables']}")
