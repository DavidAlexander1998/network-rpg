# Network+ RPG - Technical Architecture
## Version 1.1 - Terminal Edition (Revised)

---

## 1. Technology Stack

### Core Language: Python 3.10+

### Key Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| `rich` | Terminal UI (colors, tables, progress bars) | `pip install rich` |
| `questionary` | Interactive prompts (menus, select boxes) | `pip install questionary` |
| `pyyaml` | Save file format (human-readable) | `pip install pyyaml` |

> `typer` removed — adds complexity without value for this scope. `rich` + `questionary` is sufficient for the terminal version.

---

## 2. Project Structure

```
network-rpg/
├── main.py                 # Entry point
├── game/
│   ├── __init__.py
│   ├── engine.py           # Core game loop
│   ├── player.py           # Player class (stats, inventory)
│   ├── combat.py           # Encounter/combat logic
│   ├── zones.py            # Zone/Node management
│   ├── free_study.py       # Free Study Mode logic (zone-lock bypass)
│   └── save_manager.py     # Load/save functionality
├── content/
│   ├── zone-1.json
│   ├── zone-2.json
│   ├── zone-3.json
│   ├── zone-4.json
│   ├── zone-5.json
│   └── acronyms.json
├── ui/
│   ├── __init__.py
│   ├── screens.py          # Screen rendering (Rich)
│   ├── ascii_art.py        # Boss art, banners
│   └── themes.py           # Color schemes
├── utils/
│   ├── __init__.py
│   ├── validators.py
│   └── helpers.py
├── saves/
│   └── save-1.yaml
└── requirements.txt
```

---

## 3. Core Classes

### Player
```python
class Player:
    def __init__(self, name: str):
        self.name = name
        self.hp = 100
        self.max_hp = 100
        self.xp = 0
        self.level = 1
        self.bits = 0
        self.skills = []
        self.inventory = {}
        self.completed_nodes = []
        self.guardian_defeated = [False] * 5
        self.wrong_answer_ids = []        # For spaced repetition queue
        self.free_study_mode = False      # Toggle for Free Study Mode
```

### Encounter
```python
class Encounter:
    def __init__(self, data: dict):
        self.id = data['id']
        self.question = data['question']
        self.options = data['options']
        self.correct = data['correct_index']
        self.explanation = data['explanation']
        self.difficulty = data['difficulty']
        self.rewards = {
            'xp': data['xp_reward'],
            'bits': data['bits_reward']
        }
```

### Zone Manager
```python
class ZoneManager:
    def __init__(self):
        self.zones = self._load_zones()
    
    def get_encounters(self, zone: int, node: float, free_study: bool = False) -> List[Encounter]:
        """Get all encounters for a specific zone/node.
        In free_study mode, zone lock is bypassed entirely."""
        pass
    
    def get_guardian(self, zone: int) -> List[Encounter]:
        """Get the guardian exam for a zone."""
        pass

    def is_zone_accessible(self, zone: int, player: Player) -> bool:
        """Story mode: check if zone is unlocked. Free Study: always True."""
        if player.free_study_mode:
            return True
        if zone == 1:
            return True
        return player.guardian_defeated[zone - 2]
```

---

## 4. Data Flow

### Main Menu
```
[Start] → [Load Save / New Game]
   ↓
[Main Menu]
   ├── [Story Mode]   → [World Map (locked zones)] → [Select Zone] → ...
   ├── [Free Study]   → [Zone Select (ALL unlocked)] → [Node Select] → ...
   ├── [Acronym Drill]→ [Flashcard loop]
   └── [Study Report] → [Show weak areas + estimated readiness %]
```

### Encounter Loop
```
[Select Zone/Node] → [Start Encounter]
   ↓
[Show Question] → [Player Answers]
   ↓
[Calculate Result] → [Award XP/BITS or Deduct HP]
   ↓
[Show Explanation] → [Save Progress]
   ↓
[Level Up?] → [Queue wrong answer for spaced repetition?] → [Next Encounter]
```

---

## 5. Save System

- **Format**: YAML (human-readable, editable if needed)
- **Location**:
  - Windows: `%APPDATA%/NetworkRPG/saves/`
  - Linux/Mac: `~/.local/share/network-rpg/saves/`
- **Auto-save**: After every encounter completion
- **Slots**: 3 save slots
- **Backup**: Keep previous save before overwriting (save-1.yaml → save-1.yaml.bak)

---

## 6. Terminal UI Components (Rich)

### Screen Layout
```
┌─────────────────────────────────────────────────┐
│  NETWORK+ RPG - Zone 1: The Plains of Concepts  │
├─────────────────────────────────────────────────┤
│  HP: ████████░░ 80/100    XP: 450/500          │
│  Level: 3    Zone: 1/5    Mode: [STORY]         │
├─────────────────────────────────────────────────┤
│  Question:                                       │
│  Which OSI layer handles logical addressing?    │
│                                                  │
│  1) Layer 2 - Data Link                         │
│  2) Layer 3 - Network                           │
│  3) Layer 4 - Transport                         │
│  4) Layer 7 - Application                       │
└─────────────────────────────────────────────────┘
```

---

## 7. Error Handling

| Error | Handling |
|-------|----------|
| Missing content file | Show error, exit gracefully with message |
| Corrupt save file | Offer to create new save or restore .bak |
| Invalid user input | Re-prompt with error message |
| Keyboard interrupt (Ctrl+C) | Save state, exit cleanly |

---

## 8. Web Migration Path

To port to web later:
1. Content JSON files remain 100% unchanged
2. Replace `rich`/`questionary` with React components
3. Keep Python backend with FastAPI (optional) or go full client-side
4. Save system moves from YAML to browser localStorage or SQLite

---

*Last Updated: 2026-05-29 (v1.1)*
*Next: 04-UI-SPEC.md*
