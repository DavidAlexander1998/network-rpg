# Network+ RPG - Implementation Phases
## Revised Schedule: 4-Week Exam Prep Window (End of June Target)

---

## Reality Check

You have ~4 weeks to exam. Claude helps with implementation — this cuts build time to a fraction. Plan is:
- **Weekend 1 (Days 1-2)**: Terminal app built and playable
- **Week 2 (Days 3-7)**: Web app + content population
- **Weeks 3-4**: Playing the game IS the studying

**Do not let building the app eat into study time beyond week 2.**

---

## Phase 1: Terminal MVP (Weekend — ~2 days with Claude)

**Goal**: Playable terminal app with Zone 1 content, Story Mode + Free Study Mode.

### Day 1: Core Engine
- [ ] Project skeleton from `03-TECH-ARCHITECTURE.md`
- [ ] Python environment + dependencies (`rich`, `questionary`, `pyyaml`)
- [ ] `Player` class with all stats + `free_study_mode` flag
- [ ] `SaveManager` — YAML save/load, 3 slots, `.bak` on overwrite
- [ ] `ZoneManager` with `is_zone_accessible()` (respects free_study flag)
- [ ] Basic combat loop: load JSON → display question → handle answer → show explanation → save
- [ ] Main menu: Story Mode / Free Study Mode / Acronym Drill / Study Report

### Day 2: Content + Polish
- [ ] Zone 1 fully loaded and tested (all 8 nodes, 80 questions)
- [ ] Guardian system: 20-question exam, 75% pass requirement, braindump ritual
- [ ] Spaced repetition: wrong answer IDs queued, re-served after 10 correct answers
- [ ] Level-up logic with XP thresholds
- [ ] Study Report screen: % correct per zone, weakest tags, estimated readiness
- [ ] Basic `rich` UI: HP/XP bars, colour theming, clean layout

**Milestone**: `python main.py` → answer questions in Zone 1 → save/load works → Free Study Mode accessible.

---

## Phase 2: Web App (Week 2 — with Claude)

**Goal**: Browser-based version using the same JSON content files.

### Stack
- React + Vite
- Tailwind CSS (glassmorphism/cyberpunk terminal aesthetic)
- Same `/content/zone-X.json` files — no content rewrite
- localStorage for save data

### Features to port
- [ ] All 5 zones accessible (Free Study Mode default in web)
- [ ] Story Mode campaign tracker
- [ ] Guardian battle with timer
- [ ] Drag-and-drop PBQ simulation (actual diagrams — this is the upgrade from terminal)
- [ ] Skill tree visualization
- [ ] Study Report with visual charts (recharts)
- [ ] Sound effects (correct/wrong answer feedback)

**Milestone**: Web app running locally, all zones playable, PBQs working.

---

## Phase 3: Content Population (Parallel to Phase 2 — ongoing)

This is the most important phase and the most underestimated one.

### Target Question Counts

| Zone | Target | Notes |
|------|--------|-------|
| Zone 1 | 80 | Foundation — OSI, ports, protocols, subnetting, cloud |
| Zone 2 | 70 | Routing (BGP/OSPF/EIGRP), VLANs, STP, wireless |
| Zone 3 | 65 | SNMP, Syslog, DHCP/DNS, VPNs, DR/HA |
| Zone 4 | 55 | PKI, IAM, 802.1X, RADIUS/TACACS+, attack types, ACLs |
| Zone 5 | 80 | Troubleshooting methodology, tools, scenarios |
| Acronyms | 100+ | Full N10-009 acronym list |
| **Total** | **~350+** | |

### Content Creation Strategy
- Use Claude to generate questions in bulk from the exam objectives PDF
- You validate accuracy (you have the study guide — cross-check)
- Write JSON directly — don't create a "question generator tool" first, that's scope creep

### Batch generation approach:
Tell Claude: *"Generate 15 questions for Network+ Zone 4 Node 4.2 covering DoS/DDoS, ARP spoofing, and phishing. Use the encounter JSON schema from 02-CONTENT-SPEC.md. Vary difficulty (5 easy, 7 medium, 3 hard)."*

---

## Phase 4: Active Study Mode (Weeks 3-4)

**This is the actual exam prep. Stop building, start playing.**

### Week 3 Focus
- [ ] Play through all zones in Story Mode once
- [ ] Note your worst zones from Study Report
- [ ] Flip to Free Study Mode and grind weak zones
- [ ] Acronym Drill daily for 10 minutes

### Week 4 Focus (Final Push)
- [ ] Guardian exams only — test yourself under 25-minute time pressure
- [ ] Run Free Study on every tag you've failed more than twice
- [ ] Take CompTIA's official practice exam (separate from the game — mandatory for PBQ format familiarity)
- [ ] Final day: Acronym Drill + braindump practice (write out key port tables from memory)

---

## What NOT To Do

- **Don't add features in weeks 3-4.** If you're adding sound effects in week 4, you're procrastinating.
- **Don't chase perfection on the UI.** Terminal version ugly? Good. Use it anyway.
- **Don't skip Free Study Mode drilling.** Story Mode completion ≠ exam ready. The grind on weak areas is what moves the needle.
- **Don't rely only on the game for PBQs.** Use the official CompTIA practice exam at least twice.

---

## Exam Day Checklist
- [ ] Scored ≥80% on all 5 Guardian exams
- [ ] Study Report shows no zone below 70% accuracy
- [ ] Completed all acronym flashcards at least twice
- [ ] Done at least 1 full CompTIA practice exam
- [ ] Know your port numbers cold (FTP 20/21, SSH 22, Telnet 23, SMTP 25, DNS 53, DHCP 67/68, HTTP 80, HTTPS 443, etc.)
- [ ] Can explain the OSI model, subnetting, and the 6-step troubleshooting methodology from memory

---

*Last Updated: 2026-05-29 (v1.1)*
