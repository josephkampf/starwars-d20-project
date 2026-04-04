#!/usr/bin/env python3
"""
Unwrap paragraphs by joining lines within them.
Preserves blank lines, headings, lists, code blocks, and other formatting.
"""

import os
import re
from pathlib import Path


def unwrap_paragraphs(text):
    """
    Join lines within paragraphs while preserving structure.
    """
    lines = text.split('\n')
    result = []
    current_paragraph = []
    in_code_block = False

    for line in lines:
        # Track code blocks
        if line.startswith('```'):
            in_code_block = not in_code_block
            if current_paragraph:
                result.append(' '.join(current_paragraph))
                current_paragraph = []
            result.append(line)
            continue

        # If in code block, preserve as-is
        if in_code_block:
            result.append(line)
            continue

        # Blank line ends paragraph
        if not line.strip():
            if current_paragraph:
                result.append(' '.join(current_paragraph))
                current_paragraph = []
            result.append('')
            continue

        # Heading, list, table, or HTML comment - ends paragraph
        if (line.startswith('#') or
            line.startswith('- ') or
            line.startswith('* ') or
            line.startswith('+ ') or
            line.startswith('|') or
            line.startswith('<!--') or
            line.startswith('>')):
            if current_paragraph:
                result.append(' '.join(current_paragraph))
                current_paragraph = []
            result.append(line)
            continue

        # Regular text - accumulate for paragraph joining
        current_paragraph.append(line)

    # Handle remaining paragraph
    if current_paragraph:
        result.append(' '.join(current_paragraph))

    return '\n'.join(result)


def process_file(filepath):
    """Process a single markdown file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = unwrap_paragraphs(content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✓ {filepath.name}")


def main():
    """Process all chapter files in the SWD20 directory."""
    chapter_dir = Path('/Users/josephkampf/code/StarwarsD20/SWD20 Core Rulebook')

    # Get all markdown files, sorted
    md_files = sorted(chapter_dir.glob('*.md'))

    if not md_files:
        print(f"No markdown files found in {chapter_dir}")
        return

    print(f"Processing {len(md_files)} files...\n")

    for filepath in md_files:
        process_file(filepath)

    print(f"\n✓ All files processed!")


if __name__ == '__main__':
    main()
