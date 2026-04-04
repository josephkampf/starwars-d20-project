# Star Wars D20 Revival Project

A community effort to revive the **Star Wars D20 Tabletop RPG** — the out-of-print roleplaying game
originally published by Wizards of the Coast.

---

## About

The Star Wars D20 TTRPG has been out of print for years, making it difficult for new and returning
players to access the rules. This project aims to change that by converting the full library of
out-of-print rulebooks, sourcebooks, adventures, and supplements into a searchable, linkable
[Obsidian](https://obsidian.md) vault — free and open for the community.

## How It Works

1. **Extract** — Scanned PDFs of the out-of-print books are processed using AI-assisted OCR to
   extract the text into markdown files.
2. **Review** — Pull requests are opened for community volunteers to review and correct the
   extracted content, fixing OCR errors, formatting, and layout issues.
3. **Publish** — The cleaned-up markdown files live in this repo as an Obsidian vault, ready to
   download and use at your table.

## Books Included

### Core Books

| Book |
|------|
| Revised Core Rulebook |
| Hero's Guide |
| GM Screen |

### Sourcebooks

| Book |
|------|
| Alien Anthology |
| Arms and Equipment Guide |
| Dark Side Sourcebook |
| Galactic Campaign Guide |
| Geonosis and the Outer Rim Worlds |
| Coruscant and the Core Worlds |
| Knights of the Old Republic Sourcebook |
| Living Force Campaign Guide |
| New Jedi Order Sourcebook |
| Power of the Jedi Sourcebook |
| Rebellion Era Sourcebook |
| Secrets of Naboo |
| Secrets of Tatooine |
| Starships of the Galaxy |
| Tales of the Jedi Companion |
| The Clone Wars Sourcebook |
| Ultimate Adversaries |
| Ultimate Alien Anthology |
| Galactic Gazetteer: Hoth and the Greater Javin |

### Adventures

| Adventure | Level |
|-----------|-------|
| Damsel in Distress | 1 |
| Signal Interruption | 1 |
| Rendezvous at Ord Mantell | 1–2 |
| High Alert | 2 |
| Gun Nut | 3 |
| Last Call at Leatherbacks | 3 |
| Talnar's Rescue | 3–4 |
| Cat and Mouse | 3–5 |
| Kashyyyk in Flames | 3–6 |
| Steal of a Deal | 4 |
| The Rycar Run | 4–6 |
| Head Trip | 5 |
| The Crypt of Saalo Morn | 5–6 |
| Death, Dirt, and the Nerf Rancher's Daughter | 6 |
| Positive ID | 6 |
| The Kitonak Connection | 6 |
| The Storm's Edge | 6 |
| Put Up Your Dukes | 6–7 |
| Mission to Myrkr | 6–8 |
| Art for Art's Sake | 7 |
| Beneath Aucellis Park | 7–9 |
| Masquerade | 7–9 |
| Yavin: Rough and Tundra | 8–10 |
| Zygerrian Takedown | 8–10 |
| Tempest Feud | 9 |
| Triplet Threat | 9 |
| With the Band | 9 |
| Bloodhawk Down | 9–11 |
| Horning In | 10 |
| The Nebula Assassin | 10 |
| Hunger | 10–12 |
| The Wellspring | 11 |
| Swim Meet | 12 |
| Rebel Jedi | 15 |
| Rebel Jedi Part 2: Nightsaber | 15 |
| Unifying Force Adventure 1: The Fall of Eraydia | — |
| Coruscani Dawn (Living Force) | 1–9 |


---

## How to Contribute

We welcome volunteers of all skill levels. No coding experience required — if you can read Star Wars
D20 and spot a typo, you can contribute.

1. **Request access** — open an issue titled "Contributor Access Request" and we'll add you as a collaborator
2. **Clone** the repository once access is granted
3. **Open** the vault in Obsidian (point Obsidian at the cloned folder)
4. **Pick a book** — find an open issue or browse the files in the vault
5. **Edit** — fix OCR errors, restore formatting, correct tables
6. **Submit a pull request** with your corrections

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
is necessary for accessibility and preservation of out-of-print works.

---

*May the Force be with you — and your saving throws.*
