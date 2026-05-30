# Network+ RPG - Game Design Document
## Version 1.1 - Terminal Edition (Revised)

---

## 1. Core Concept

**"The Grid"** has collapsed. You are a Network Initiate tasked with restoring connectivity by conquering the 5 Bastions of Networking. Each bastion corresponds to a CompTIA Network+ exam domain.

**Win Condition**: Defeat all 5 Domain Guardians and achieve a combined score of ≥75% across all domains (720/900 equivalent).

**Lose Condition**: Run out of HP (study stamina) before defeating all guardians. HP resets daily — you cannot permanently "lose."

---

## 2. Player Stats

| Stat | Description | Starting Value |
|------|-------------|----------------|
| **HP** (Health Points) | Study stamina. Wrong answers cost HP. Resets each session. | 100 |
| **XP** (Experience Points) | Earned from correct answers. Levels up character. | 0 |
| **Level** | Determines max HP and available skills | 1 |
| **BITS** (In-game currency) | Earned from encounters, spent on consumables | 0 |

### Level Progression

| Level | XP Required | Max HP | Unlock |
|-------|-------------|--------|--------|
| 1 | 0 | 100 | Zone 1 + Free Study Mode |
| 2 | 500 | 120 | Skill: Double XP (15 min) |
| 3 | 1200 | 140 | Consumable: Health Potion |
| 4 | 2500 | 160 | Zone 2 Access (story mode) |
| 5 | 4500 | 180 | Skill: Answer Shield (1 wrong→right) |

---

## 3. The 5 Zones (Exam Domains)

Each zone contains:
- **Mobs**: 10-15 bite-sized encounters (quick multiple-choice)
- **Mini-Boss**: 5 medium questions (scenario-based)
- **Guardian**: 20-question domain exam (must score ≥75% to pass)

| Zone | Domain | Weight | Theme | Boss Name |
|------|--------|--------|-------|-----------| 
| 1 | Networking Concepts (23%) | Highest | The Plains of Concepts | The OSI Overlord |
| 2 | Network Implementation (20%) | High | The Forge of Implementation | The Routing Warden |
| 3 | Network Operations (19%) | High | The Engine Room | The Sentinel of Ops |
| 4 | Network Security (14%) | Medium | The Security Citadel | The Shadow Firewall |
| 5 | Network Troubleshooting (24%) | Highest | The Abyss of Debugging | The Chaos Engineer |

---

## 4. Two Play Modes

### Mode A: Story Mode (Structured)
- Zones unlock sequentially after defeating each Guardian
- Recommended for first playthrough
- Tracks overall campaign progress

### Mode B: Free Study Mode (Exam Prep) ⭐ IMPORTANT
- **All zones accessible from day one, regardless of story progress**
- Choose any zone, any node, any difficulty
- No HP penalty — wrong answers show explanation, then move on
- Designed for targeted weak-area drilling before the exam
- **This is what you use in the final week before the exam**

> **Why this matters**: The real exam doesn't care if you've "unlocked" troubleshooting. Zone 5 is 24% of the exam. You need to be able to drill it on day 1 if needed.

---

## 5. Combat System

### Encounter Types

#### A. Mob Encounter (The Grind)
- **Format**: 1 multiple-choice question
- **Time Limit**: 30 seconds (optional, adds pressure/excitement)
- **Rewards**:
  - Correct: +20-50 XP, +10 BITS, HP stays
  - Wrong: -10 HP, +5 XP (encouragement), explanation shown immediately
- **Difficulty Scaling**: Easy → Medium → Hard as player levels

#### B. Mini-Boss Encounter
- **Format**: 3-5 questions back-to-back
- **Theme**: Scenario-based ("You have a VLAN loop. What do you check first?")
- **Rewards**:
  - All correct: +200 XP, +50 BITS, Skill Point
  - 1+ wrong: +100 XP, explanation for wrong answers

#### C. Guardian Battle (Domain Exam)
- **Format**: 20 questions, 25-minute timer
- **Pass Requirement**: ≥15/20 correct (75%)
- **Pre-Battle Ritual**: "Braindump" — Player types key formulas/ports for bonus XP
- **Rewards**:
  - Pass: +1000 XP, +200 BITS, Zone Complete Badge, Unlock Next Zone
  - Fail: Can retry after completing 10 more mob encounters (spaced repetition) or spend BITS for instant retry

---

## 6. Skills & Consumables

### Active Skills (Unlock via Leveling)

| Skill | Level | Effect | Cooldown |
|-------|-------|--------|----------|
| **50/50** | 1 | Removes 2 wrong answers | 3 encounters |
| **Time Freeze** | 3 | +15 seconds on timed questions | 2 encounters |
| **Reveal Intent** | 5 | Shows what concept is being tested | 3 encounters |
| **Second Wind** | 7 | Restores 50 HP once per day | Daily |

### Consumables (Purchase with BITS)

| Item | Cost | Effect |
|------|------|--------|
| **Health Packet** | 50 BITS | +25 HP |
| **Golden RJ45** | 100 BITS | Skip 1 question (auto-correct) |
| **Packet Sniffer** | 75 BITS | Highlight the distractor answer |
| **Energy Drink** | 150 BITS | Double XP for next 3 encounters |

---

## 7. Progression Mechanics

### Daily Streaks
- Study for 3+ days in a row → Streak bonus (+10% XP)
- Miss a day → Streak resets (no penalty, just no bonus)

### Achievements (Badges)

| Badge | Requirement |
|-------|-------------|
| **First Blood** | Answer first question correctly |
| **Speed Demon** | Answer 10 questions in <10 seconds each |
| **Perfectionist** | Clear a zone with 100% on Guardian |
| **Comeback Kid** | Defeat a Guardian on 3rd+ attempt |
| **Network God** | Defeat all 5 Guardians |

---

## 8. Save System

- **Format**: YAML files
- **Location**:
  - Windows: `%APPDATA%/NetworkRPG/saves/`
  - Linux/Mac: `~/.local/share/network-rpg/saves/`
- **Auto-save**: After every encounter completion (atomic saves)
- **Slots**: 3 save slots

---

## 9. Difficulty Scaling

Based on player accuracy in last 10 questions:
- **<40% correct**: Drop to easier questions
- **40-75% correct**: Maintain current difficulty
- **>75% correct**: Increase difficulty, increase XP rewards

---

## 10. Anti-Boredom Mechanics

1. **Session Timer**: Recommend 20-25 min sessions
2. **Session Boss**: Every 5 encounters, face a "session boss" (mini-review)
3. **Random Encounters**: Occasional "loot goblins" (bonus BITS questions)
4. **Break Reminders**: After 20 min, suggest a 5-min break (pomodoro style)

---

## 11. PBQ Supplement Note

The terminal version simulates PBQs via CLI-step prompts. This is useful but not a full substitute for the actual drag-and-drop format on the exam. **Supplement with CompTIA's official practice exam tool for PBQ exposure** — the game covers the knowledge, the official tool covers the interface familiarity.

---

## 12. Design Principles

1. **Progress, Not Perfection**: Wrong answers teach, don't punish heavily
2. **Immediate Feedback**: Show correct answer + explanation instantly
3. **Spaced Repetition**: Failed questions reappear in future encounters
4. **Visible Growth**: XP bar, level ups, skill unlocks = dopamine hits
5. **Agency**: Player chooses which zone to tackle at all times (Free Study Mode)
6. **Exam-Weight Aware**: More grind content in Zones 1 and 5 (highest exam %)

---

*Last Updated: 2026-05-29 (v1.1)*
*Next: 01-DOMAIN-MAPPING.md*
