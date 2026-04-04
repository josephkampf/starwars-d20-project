#!/usr/bin/env python3
"""
Revert pipe tables that have "Col 2" / "Col 3" etc. in their header row —
those are the ones convert_tables.py got wrong.
Restores them to plain text by joining the pipe-table cell content.
"""
import re, os, glob

VAULT = "/Users/josephkampf/code/StarwarsD20/SWD20 Core Rulebook"
CAPTION_RE = re.compile(r'^\*\*Table \d')

def is_bad_header(line):
    """True if this pipe-table header was auto-generated with 'Col N' fallbacks."""
    return bool(re.search(r'\| Col \d', line))

def is_separator(line):
    """True for a pipe-table separator row like | ----- | ----- |"""
    s = line.strip()
    return s.startswith('|') and all(c in '| -' for c in s)

def extract_plain_text(pipe_lines):
    """Convert a pipe table back to plain text by joining cells per row."""
    result = []
    for raw in pipe_lines:
        s = raw.strip()
        if not s:
            result.append('')
            continue
        if is_separator(s):
            continue  # drop separator rows
        if s.startswith('|'):
            # Split on | and gather non-empty, non-"Col N" cells
            cells = [c.strip() for c in s.split('|')]
            cells = [c for c in cells if c and not re.match(r'^Col \d+$', c)]
            if cells:
                result.append(' '.join(cells))
        else:
            result.append(raw)
    return result

def process_file(fp):
    original = open(fp).read()
    lines = original.split('\n')
    out = []
    i = 0
    reverted = 0

    while i < len(lines):
        raw = lines[i]
        s = raw.strip()

        if not CAPTION_RE.match(s):
            out.append(raw)
            i += 1
            continue

        # Found a **Table caption — look ahead for a pipe table
        out.append(raw)
        i += 1

        # Skip any blank lines right after caption
        while i < len(lines) and not lines[i].strip():
            out.append(lines[i])
            i += 1

        # Is the next content a pipe table?
        if i >= len(lines) or not lines[i].strip().startswith('|'):
            continue  # No pipe table, carry on

        # Read the pipe table block
        table_start = i
        while i < len(lines) and (lines[i].strip().startswith('|') or not lines[i].strip()):
            i += 1
        table_end = i

        table_lines = lines[table_start:table_end]

        # Determine if this is a bad auto-conversion
        header_line = next((l for l in table_lines if l.strip().startswith('|') and not is_separator(l.strip())), '')

        if is_bad_header(header_line):
            # Revert: extract plain text from the pipe table
            plain = extract_plain_text(table_lines)
            # Remove leading/trailing blanks in the extracted block
            while plain and not plain[0]:
                plain.pop(0)
            while plain and not plain[-1]:
                plain.pop()
            out.extend(plain)
            reverted += 1
        else:
            # Good table — keep it
            out.extend(table_lines)

    new_content = '\n'.join(out)
    if new_content != original:
        open(fp, 'w').write(new_content)

    return reverted

files = sorted(glob.glob(os.path.join(VAULT, '[0-9]*.md')))
total = 0
for fp in files:
    n = process_file(fp)
    if n:
        print(f"  {os.path.basename(fp)}: {n} tables reverted")
    total += n
print(f"\nTotal reverted: {total}")
