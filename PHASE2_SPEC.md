# Phase 2 Specification - Network+ RPG
## Combat Loop, Zone Manager, and Free Study Mode

---

## Deliverables

### 1. Combat Loop (`game/combat.py`)
```python
class Combat:
    def __init__(self, player: Player, encounter: Encounter)
    def start(self) -> CombatResult
    # Displays question, handles answer, updates player stats
    # Returns: xp_gained, bits_gained, hp_lost, is_correct
```

### 2. Zone Manager (`game/zone_manager.py`)
```python
class ZoneManager:
    def __init__(self, content_dir: str)
    def load_zone(self, zone_number: int) -> Zone
    def get_available_nodes(self, zone_number: int, player: Player) -> List[Node]
    def is_zone_accessible(self, zone_number: int, player: Player) -> bool
    # Free Study Mode: all zones always accessible
    # Story Mode: zone N+1 locked until guardian N defeated
```

### 3. Zone/Node/Data Classes
```python
@dataclass
class Zone:
    number: int
    name: str
    nodes: List[Node]
    guardian: Encounter

@dataclass  
class Node:
    id: float  # e.g., 1.1
    name: str
    encounters: List[Encounter]
    is_completed: bool
```

### 4. Spaced Repetition (`game/spaced_repetition.py`)
```python
class SpacedRepetition:
    def __init__(self)
    def add_failed(self, encounter_id: str)
    def get_next_review(self) -> Optional[str]
    def should_review_before_new(self) -> bool
    # After 10 correct answers, serve failed encounter
```

### 5. UI Screens (`ui/screens.py`)
```python
def show_main_menu(player: Player) -> str  # Returns choice
def show_zone_select(zones: List[Zone], player: Player) -> int
def show_node_map(zone: Zone, player: Player) -> str
def show_encounter(encounter: Encounter, player: Player) -> int  # Returns selected index
def show_combat_result(result: CombatResult)
def show_level_up(player: Player)
def show_save_slots(saves: List[Dict]) -> int
```

### 6. Main Game Loop (`main.py` - REPLACE existing)
```
Main Menu:
  [S] Story Mode
  [F] Free Study Mode
  [A] Acronym Drill
  [R] Study Report
  [Q] Quit

Story Mode:
  - Show zones 1-5, locked/unlocked status
  - Select zone → Show node map
  - Select node → Combat loop
  - After guardian defeated, unlock next zone

Free Study Mode:
  - All zones available immediately
  - Select any zone/node
  - No HP penalty (or minimal)
  - Focus on weak areas
```

### 7. Content Loader
- Load from `content/zone-1.json` (already exists)
- Validate against schema
- Graceful error handling for missing/corrupt files

---

## Constraints

- DO NOT create zone-2.json, zone-3.json etc (content comes later)
- DO make zone-1.json load and playable
- DO implement Free Study Mode fully
- DO implement spaced repetition queue
- DO use `rich` for all UI (tables, panels, colors)
- DO handle keyboard interrupts (Ctrl+C) gracefully
- DO NOT build Guardian battle timer yet (Phase 3)

---

## Testing Requirements

After implementation, these must work:
1. `python main.py` → Shows main menu
2. Select Free Study Mode → Shows all 5 zones
3. Select Zone 1 → Shows node map with 8 nodes
4. Select Node 1.1 → Shows encounter question
5. Answer question → Shows result, updates XP/HP/BITS
6. Wrong answer → Queue for spaced repetition
7. Save game → YAML file created
8. Load game → Progress restored
9. Study Report → Shows % correct per zone

---

## File Structure to Create

```
network-rpg/
├── main.py (replace)
├── game/
│   ├── combat.py (new)
│   ├── zone_manager.py (new)
│   ├── spaced_repetition.py (new)
│   └── (existing: player.py, encounter.py, save_manager.py)
├── ui/
│   ├── screens.py (new)
│   └── themes.py (new - colors/constants)
└── content/
    └── zone-1.json (use existing)
```

---

## Acceptance Criteria

- [ ] Main menu displays with Rich styling
- [ ] Can start Free Study Mode from day one
- [ ] Can complete encounters in Zone 1
- [ ] XP/BITS/HP update correctly
- [ ] Spaced repetition queues failed questions
- [ ] Can save and load game
- [ ] Study Report shows accuracy stats
- [ ] Graceful error handling throughout
