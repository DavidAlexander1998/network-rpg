# Network+ RPG - UI Specification
## Version 1.0 - Terminal Edition

---

## 1. Visual Aesthetic

**Theme**: "Cyber-Terminal" / "Hacker"
**Color Palette (Rich Library)**:
- **Primary**: Neon Green (`#00FF00`) - Success, XP, Health
- **Secondary**: Neon Cyan (`#00FFFF`) - Questions, UI Borders
- **Warning**: Amber/Yellow (`#FFBF00`) - Hints, Time warnings
- **Danger**: Neon Red (`#FF0000`) - Wrong answers, HP loss, Boss warnings
- **Background**: Black (`#000000`)

---

## 2. Key Screen Layouts

### A. The World Map (Main Menu)
The map is represented as an ASCII flowchart showing the Bastions.

```
    [START]
       |
       v
  ( Zone 1 ) --- [OSI Overlord] --- [UNLOCKED]
       |
       v
  ( Zone 2 ) --- [Routing Warden] -- [LOCKED]
       |
       v
  ( Zone 3 ) --- [Sentinel of Ops] - [LOCKED]
       |
       v
  ( Zone 4 ) --- [Shadow Firewall] - [LOCKED]
       |
       v
  ( Zone 5 ) --- [Chaos Engineer] -- [LOCKED]
```

### B. Combat Screen (Encounter)
The screen is divided into a header, a content area, and a footer.

**Header**:
- Player Name | Level | XP Bar | HP Bar | BITS
- Example: `David | Lvl 3 | XP: [████░░] 450/500 | HP: [██████░] 60/100 | 💰 120`

**Content**:
- **Question**: (Cyan bold text)
- **Options**: (Numbered list with selectable highlight)
- **Explanation**: (Appears *after* answer, Green if correct, Red if wrong)

**Footer**:
- **Action Menu**: `[A] Answer | [S] Use Skill | [I] Inventory | [Q] Quit`

---

## 3. Animations & Visual Feedback

Since it's a terminal, "animations" are simulated via rapid print updates:

- **Damage Shake**: Flash the screen red and print "!!! CRITICAL HIT !!!" when HP drops.
- **Level Up**: Clear screen and print a massive ASCII "LEVEL UP!" banner with a gold color.
- **XP Gain**: Print `+50 XP` floating upwards (simulated by printing it on a new line then clearing).
- **Loading Screens**: Use a `rich.progress` bar when "Entering Zone..." or "Loading Save...".

---

## 4. ASCII Art Assets

The game includes a library of ASCII art for key events:

- **The OSI Overlord**: A massive, floating geometric cube of layers.
- **The Routing Warden**: A complex web of interconnected lines and nodes.
- **The Shadow Firewall**: A solid wall of `#` characters with gaps.
- **The Chaos Engineer**: A glitchy, fragmented skull made of random characters.

---

## 5. User Input Flow

All inputs are handled via `questionary` for a modern CLI feel:

1. **Multiple Choice**: Arrow keys to select $\rightarrow$ Enter to confirm.
2. **Text Input**: For "Braindumps" or "Config Simulations."
3. **Menu Selection**: Select from list $\rightarrow$ Execute action.

---

*Last Updated: 2026-05-29*
*Next: 05-IMPLEMENTATION-PHASES.md*
