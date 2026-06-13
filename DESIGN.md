---
format: google-stitch-design-md
version: 1
project: APO
register: product
---

# DESIGN.md

## Overview

**Creative North Star:** "The Fiduciary Ledger"

Structured like a clinical chart — numbered priorities, timestamped agent actions, annotated decisions. Warm paper surfaces, ink typography, one committed teal accent. Flat by default; elevation only on interactive focus and the charter-check hero block.

Layout philosophy: three columns on desktop (charter | activity | plan), single column on mobile. Spacing follows an 8px rhythm. The charter-check section is visually heaviest in the plan panel — it is the demo's proof point.

Motion: subtle opacity fade for new feed entries. No bounce, spring, or pulse except a single slow breathe on "live" status.

## Colors

| Token | Value | Name |
|-------|-------|------|
| `--bg` | `#f3f0e8` | Warm Chart Paper |
| `--surface` | `#fefcf8` | Ledger Page |
| `--surface-muted` | `#ebe6dc` | Margin Rule |
| `--border` | `#d4cfc4` | Rule Line |
| `--text` | `#1a2420` | Clinical Ink |
| `--text-muted` | `#5c6a64` | Annotation Gray |
| `--accent` | `#1a6b5c` | Fiduciary Teal |
| `--accent-hover` | `#145549` | Deep Teal |
| `--aligned` | `#2a7d52` | Clear Pass |
| `--aligned-bg` | `#e8f3ec` | Pass Tint |
| `--flagged` | `#9a5b14` | Review Amber |
| `--flagged-bg` | `#f9eed9` | Review Tint |
| `--running` | `#1a6b5c` | Active Teal |
| `--error` | `#b53d3d` | Alert Red |

Neutrals are tinted toward warm green-gray, never cool blue-gray. Never use purple, violet, or gradient text.

## Typography

| Role | Family | Weight | Size |
|------|--------|--------|------|
| Wordmark | Newsreader | 500 | 1.75rem |
| Panel title | IBM Plex Sans | 600 | 0.9375rem |
| Body | IBM Plex Sans | 400 | 0.9375rem |
| Label | IBM Plex Sans | 500 | 0.8125rem |
| Mono/time | IBM Plex Mono | 400 | 0.75rem |

Type scale: 12 / 13 / 15 / 17 / 28px. Line height 1.5 body, 1.35 headings. Sentence case labels — never ALL CAPS except status pills.

## Elevation

Flat surfaces with 1px `--border` rules. No drop shadows on cards. Focus ring: 2px `--accent` at 30% opacity. Charter-check flagged items get a 2px `--flagged` border, no shadow.

## Components

**Button primary:** Filled `--accent`, white text, 6px radius, 0.5rem 1rem padding.

**Button secondary:** Transparent, `--border` outline, `--text` label.

**Panel:** `--surface` background, 1px border, 8px radius, no shadow.

**Feed entry:** No left stripe. Agent name in `--accent` semibold; action in `--text-muted`; output in `--text`. Separated by bottom border, not nested cards.

**Charter item:** Rank in small square badge. Highlighted state uses `--flagged-bg` border.

**Charter check (hero):** Full-width blocks. Aligned = `--aligned-bg` + checkmark label. Flagged = `--flagged-bg` + "Review required" label. Never duplicate emoji in badge and message.

**Voice bubble:** APO right-aligned teal tint; clinic left-aligned `--surface-muted`.

**Status pill:** Rounded full, small caps avoided — use "Running", "Complete".

## Do's and Don'ts

**Do**
- Tint neutrals toward warm green-gray
- Make charter-check the visual climax of the plan panel
- Use IBM Plex Mono for timestamps
- Keep agent differentiation typographic, not rainbow

**Don't**
- Use Inter, purple, gradients, or glassmorphism
- Add side-stripe borders to feed entries
- Nest identical rounded cards inside panels
- Use pulse animations on multiple elements simultaneously
- Write vague empty states — name the next action ("Press Run APO to start")
