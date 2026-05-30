# Network+ RPG - Documentation Index
## v1.1 — Revised for 4-Week Exam Window

---

## Quick Start

**This is a gamified study app for CompTIA Network+ (N10-009) certification.**

Start here: `00-GAME-DESIGN.md` for the big picture.

---

## File Structure

| File | Purpose | What Changed in v1.1 |
|------|---------|----------------------|
| `00-GAME-DESIGN.md` | Core game mechanics, combat system, XP/leveling | Added Free Study Mode (all zones accessible always) |
| `01-DOMAIN-MAPPING.md` | How exam domains map to game zones/nodes | No changes |
| `02-CONTENT-SPEC.md` | JSON schemas + minimum question counts | Question minimums raised; Zone 4 from 30→55 |
| `03-TECH-ARCHITECTURE.md` | Python stack, class structure, data flow | Added `free_study_mode` flag, `is_zone_accessible()`, removed `typer` |
| `04-UI-SPEC.md` | Terminal UI design, colors, ASCII art | No changes |
| `05-IMPLEMENTATION-PHASES.md` | Revised 4-week build + study schedule | Completely rewritten for realistic timeline |
| `content/zone-1.json` | Sample content file with real questions | No changes |

---

## Key Decisions (Locked)

1. **Stack**: Python 3.10+ with `rich`, `questionary`, `pyyaml`
2. **Save Format**: YAML files (consistent across all docs now)
3. **Content Format**: JSON files in `/content/zone-X.json`
4. **Pass Threshold**: 75% on Guardian exams (matches real exam — 720/900)
5. **Session Length**: 20-25 minute sessions
6. **Free Study Mode**: All zones accessible from session 1, no story lock

---

## What Changed from v1.0 (Summary)

| Issue | Fix |
|-------|-----|
| Zone lock prevented drilling high-weight zones early | Free Study Mode bypasses all zone locks |
| Question counts too low (Zone 4 had only 30 planned) | Minimums raised to ~350 total across all zones |
| Save format inconsistency (JSON vs YAML) | Standardised to YAML everywhere |
| Timeline assumed solo dev, didn't account for Claude | Rewritten as 2-day terminal build, week 2 web build |
| No exam readiness checklist | Added to Phase 4 |

---

## Content Sources

All questions derived from:
- CompTIA Network+ N10-009 Exam Objectives (in `CompTIA_Network_resources/`)
- CompTIA Network+ Study Guide (in `CompTIA_Network_resources/`)
- Official N10-009 acronym list (100+ terms)
- Port/protocol reference tables

---

## User Context

**Player**: Davido  
**Constraint**: Historically bad at sitting down to study — needs gamification and short feedback loops  
**Goal**: Pass N10-009 before end of June 2026  
**Timeline**: Build this weekend + next week → study weeks 3-4  
**Philosophy**: Build it fast, use it hard, pass the exam

---

*Library Version: 1.1*  
*Revised: 2026-05-29*  
*Status: Ready for Implementation*
