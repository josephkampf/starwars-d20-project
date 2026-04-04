#!/usr/bin/env python3
"""
Format OCR markdown files in the SWD20 Obsidian vault.
Run ONCE on fresh OCR output. Not idempotent.
"""
import re, os, sys, glob

VAULT = "/Users/josephkampf/code/StarwarsD20/SWD20 Core Rulebook"

CHAPTER_ORD_RE = re.compile(
    r'^CHAPTER\s+(?:ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|'
    r'ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN)\s*$',
    re.IGNORECASE
)
PAGE_MARKER_RE = re.compile(r'^<!-- page \d+ -->$')

# Words that only start sentences, never headings
SENTENCE_STARTERS = {
    'if','when','while','once','since','because','although','unless',
    'such','after','before','during','though','even','just','not'
}

def has_garbled_word(s):
    """Returns True if any word has uppercase embedded after position 0 (garbled OCR)."""
    for word in s.split():
        alpha = re.sub(r'[^a-zA-Z]', '', word)
        if len(alpha) < 3:
            continue
        if alpha == alpha.upper() or alpha == alpha.lower():
            continue   # ALL-CAPS abbreviations or normal words are fine
        # Mixed case: uppercase after position 0 → garbled (e.g. "WadtHes", "LIVawood")
        if any(c.isupper() for c in alpha[1:]):
            return True
    return False

def word_ratio(s):
    if not s:
        return 0
    return len(re.findall(r'[a-zA-Z0-9 ]', s)) / len(s)

def is_garbled(s):
    """Short OCR noise strings — running headers, decorative elements, etc."""
    s = s.strip()
    if not s or len(s) > 25 or ' ' in s:
        return False
    # Mixed-case with high transition count → garbled (e.g. "SAILIMeaVv", "LNAWdInNDA")
    has_up = any(c.isupper() for c in s)
    has_lo = any(c.islower() for c in s)
    if has_up and has_lo:
        transitions = sum(1 for i in range(len(s)-1) if s[i].isupper() != s[i+1].isupper())
        if transitions >= 2:
            return True
        # Uppercase letters embedded mid-word (not first char) → likely garbled
        # e.g. "LIVawood" (V is uppercase mid-word)
        if any(c.isupper() for c in s[1:]):
            return True
    # All-caps short fragment with no vowels or implausible combo → garbled chapter slug
    # e.g. "STUAS", "IVEW", "SKILS"
    if has_up and not has_lo and len(s) <= 8 and s.isalpha():
        vowels = len(re.findall(r'[AEIOU]', s))
        if vowels == 0 or vowels / len(s) < 0.2:
            return True
    # Pipe-containing OCR artefacts like "species|2"
    if '|' in s:
        return True
    return False

def heading_level(s):
    """
    Returns 2 or 3 if line looks like a section heading, else 0.
    Only called when line is isolated between blank lines.
    Conservative: rejects anything that looks like body text or table data.
    """
    if not s or len(s) > 75 or len(s) < 3:
        return 0
    # Must start with a capital letter
    if not s[0].isupper():
        return 0
    # No trailing sentence-ending punctuation or lead-in colon
    if s[-1] in (',', ';', ':'):
        return 0
    if s[-1] == '.' and not s.rstrip('.').endswith('etc'):
        return 0
    # No pipe characters (table rows / OCR artefacts)
    if '|' in s:
        return 0
    # Must be mostly word characters
    if word_ratio(s) < 0.78:
        return 0
    # Skip chapter ordinals
    if CHAPTER_ORD_RE.match(s):
        return 0

    words = s.split()

    # Stat adjustment rows: "Bothan +2 Dex, -2 Con" etc.
    if re.search(r'[+\-]\d+\s+[A-Z][a-z]', s):
        return 0

    # Lines with comma + lowercase continuation are sentence fragments
    if re.search(r',\s+[a-z]', s):
        return 0

    # First word is a sentence-only function word (body text, never a heading start)
    if words[0].lower() in SENTENCE_STARTERS:
        return 0

    # Words with uppercase letters embedded mid-word → garbled OCR
    if has_garbled_word(s):
        return 0

    # Count lowercase-starting interior words (heading words are Title Cased)
    inner_lower = sum(1 for w in words[1:] if w and w[0].islower() and len(w) > 2)
    if inner_lower >= 2:
        return 0

    # "Name (Abbrev)" pattern → h3, e.g. "Strength (Str)", "Wisdom (Wis)"
    if re.match(r'^[A-Z][a-z]+(?:\s[A-Za-z]+)?\s+\([A-Za-z]{2,4}\)$', s):
        return 3

    # Table captions "Table N-N: Title" → h4 (represented as bold, not heading)
    if re.match(r'^Table\s+[\dIiVv]', s):
        return 4  # caller converts to bold text

    # ALL CAPS multi-word lines → h2 (e.g. "HOW COMBAT WORKS")
    if s == s.upper() and re.match(r'^[A-Z][A-Z\s\'\-]+$', s) and len(words) >= 2:
        return 2

    # Title Case multi-word line → h2 (e.g. "How Combat Works", "What's New?")
    if len(words) >= 2:
        cap_words = sum(1 for w in words if not w[0].isalpha() or w[0].isupper())
        if cap_words >= len(words) * 0.65 and len(s) <= 65:
            return 2

    # Single Title-Cased word (e.g. "Rerolling", "Setup")
    if len(words) == 1 and s[0].isupper() and s[1:].islower() and len(s) >= 4:
        return 2

    return 0

def process(filepath):
    with open(filepath) as f:
        lines = f.read().split('\n')

    out = []
    i = 0
    after_marker = False

    while i < len(lines):
        raw = lines[i]
        s = raw.strip()

        # Preserve file header (first 5 lines: # title, blank, *, ---, blank)
        if i < 5:
            out.append(raw)
            i += 1
            continue

        # Page markers pass through unchanged
        if PAGE_MARKER_RE.match(s):
            out.append(raw)
            after_marker = True
            i += 1
            continue

        # Right after a page marker: remove chapter cover lines + garbled noise
        if after_marker and s:
            if CHAPTER_ORD_RE.match(s) or is_garbled(s):
                i += 1
                # Also skip any following blank lines + garbled continuation
                while i < len(lines):
                    ns = lines[i].strip()
                    if not ns:
                        i += 1
                        continue
                    if is_garbled(ns) or CHAPTER_ORD_RE.match(ns):
                        i += 1
                        continue
                    break
                continue
            after_marker = False

        if s:
            after_marker = False

        # @ bullet → - bullet
        if re.match(r'^@\s', raw):
            raw = re.sub(r'^@\s+', '- ', raw)
            s = raw.strip()

        # (@) sidebar icon → blockquote bold heading
        if re.match(r'^\(@\)', raw):
            raw = re.sub(r'^\(@\)\s*', '> **', raw).rstrip() + '**'
            s = raw.strip()

        # Hyphenated line-break join: "compart-" + next line "ment ..."
        if (s.endswith('-') and
                i + 1 < len(lines) and
                lines[i + 1].strip() and
                lines[i + 1].strip()[0].islower() and
                not PAGE_MARKER_RE.match(lines[i + 1].strip())):
            tail = lines[i + 1].strip()
            raw = raw.rstrip()[:-1] + tail
            s = raw.strip()
            i += 1

        # Section heading promotion
        prev_blank = (not out or not out[-1].strip() or PAGE_MARKER_RE.match(out[-1].strip()))
        next_blank  = (i + 1 >= len(lines) or not lines[i + 1].strip())

        if prev_blank and next_blank:
            lvl = heading_level(s)
            if lvl == 4:
                raw = '**' + s + '**'   # table caption → bold
            elif lvl:
                raw = '#' * lvl + ' ' + s
        elif prev_blank:
            # "Name (Abbrev)" headings appear directly before their paragraph
            if re.match(r'^[A-Z][a-z]+(?:\s[A-Za-z]+)?\s+\([A-Za-z]{2,4}\)$', s):
                raw = '### ' + s

        out.append(raw)
        i += 1

    return '\n'.join(out)

# ── Main ──
files = sorted(glob.glob(os.path.join(VAULT, '[0-9]*.md')))
if not files:
    print(f"No chapter files found in: {VAULT}")
    sys.exit(1)

for fp in files:
    name = os.path.basename(fp)
    new_content = process(fp)
    with open(fp, 'w') as f:
        f.write(new_content)
    print(f"  Formatted: {name}")

print(f"\nDone. {len(files)} files updated.")
