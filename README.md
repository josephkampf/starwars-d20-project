# Star Wars D20 Revival Project

A community effort to revive the **Star Wars D20 Tabletop RPG** — the out-of-print roleplaying game
originally published by Wizards of the Coast.

---

## About

The Star Wars D20 TTRPG has been out of print for years, making it difficult for new and returning
players to access the rules. This project aims to change that by converting the original rulebooks
into a searchable, linkable [Obsidian](https://obsidian.md) vault — free and open for the community.

## How It Works

1. **Extract** — Scanned PDFs of the out-of-print rulebooks are processed using AI-assisted OCR to
   extract the text into markdown files.
2. **Review** — Pull requests are opened for community volunteers to review and correct the
   extracted content, fixing OCR errors, formatting, and layout issues.
3. **Publish** — The cleaned-up markdown files live in this repo as an Obsidian vault, ready to
   download and use at your table.

## How to Contribute

We welcome volunteers of all skill levels. No coding experience required — if you can read Star Wars
D20 and spot a typo, you can contribute.

1. **Fork** this repository
2. **Open** the vault in Obsidian (point Obsidian at your fork's root folder)
3. **Pick a chapter** — find an open pull request or browse the files in `SWD20 Core Rulebook/`
4. **Edit** — fix OCR errors, restore formatting, correct tables
5. **Submit a pull request** with your corrections

All pull requests require a review before merging, so your changes will be checked before they go in.

## Repository Structure

```
StarwarsD20/
├── SWD20 Core Rulebook/     # Chapter markdown files (the Obsidian vault content)
├── convert_pdf_to_vault.sh  # OCR pipeline: PDF → markdown
├── convert_tables.py        # Converts OCR text tables to markdown pipe tables
├── format_vault.py          # Initial formatting pass (run once on fresh OCR output)
├── improve_formatting.py    # Idempotent post-processing improvements
├── revert_bad_tables.py     # Reverts incorrectly converted tables
└── CLAUDE.md                # AI assistant instructions and project conventions
```

## Getting Started (Using the Vault)

1. Install [Obsidian](https://obsidian.md) (free)
2. Clone or download this repository
3. In Obsidian, choose **Open folder as vault** and select the `StarwarsD20` folder
4. Start with `SWD20 Core Rulebook/Index.md` for the chapter list

## License & Legal

This project contains community-contributed editorial work (formatting corrections, OCR cleanup)
and tooling scripts. The original Star Wars D20 rules are the intellectual property of their
respective owners. This project does not distribute scanned PDFs or reproduce content beyond what
is necessary for accessibility and preservation of an out-of-print work.

---

*May the Force be with you — and your saving throws.*
