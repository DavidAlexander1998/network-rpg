# Network+ RPG - Content Specification
## Version 1.1 - Data Schema (Revised)

---

## 1. Content Architecture

All game content is stored in JSON files. Decoupled from the engine — easy to update, audit, or port to web.

### File Structure
`/content/zone-X.json` (where X is 1-5)

---

## 2. Minimum Question Counts Per Zone (REVISED)

Based on exam domain weights. More questions = more coverage = fewer surprises on exam day.

| Zone | Domain | Exam Weight | Min Questions | Reason |
|------|--------|-------------|---------------|--------|
| Zone 1 | Networking Concepts | 23% | **80 questions** | Highest weight, foundational — everything builds on this |
| Zone 2 | Network Implementation | 20% | **70 questions** | Routing/switching depth needed |
| Zone 3 | Network Operations | 19% | **65 questions** | Monitoring/DR/services coverage |
| Zone 4 | Network Security | 14% | **55 questions** | PKI, IAM, 802.1X, attacks — deceptively deep |
| Zone 5 | Network Troubleshooting | 24% | **80 questions** | Highest weight, most scenario-heavy |
| **Total** | | **100%** | **~350 questions** | Roughly 70 per zone on average |

> Zone 4 minimum raised from 30 to 55. The original 30 was too thin for content that includes PKI, IAM, RADIUS/TACACS+, 802.1X, DoS/DDoS types, ARP spoofing, device hardening, ACLs, and NAC. You would have had gaps.

### Distribution Per Zone (Per Node)
Each node within a zone must have:
- Minimum 8 easy questions
- Minimum 5 medium questions  
- Minimum 3 hard questions
- At least 1 scenario/mini-boss question

---

## 3. The Encounter Schema

```json
{
  "encounters": [
    {
      "id": "z1-n1-001",
      "zone": 1,
      "node": 1.1,
      "difficulty": "easy",
      "type": "mob",
      "question": "Which OSI layer is responsible for routing packets across different networks?",
      "options": [
        "Layer 2 - Data Link",
        "Layer 3 - Network",
        "Layer 4 - Transport",
        "Layer 7 - Application"
      ],
      "correct_index": 1,
      "explanation": "Layer 3 (Network) handles logical addressing and routing (e.g., IP addresses). Layer 2 handles MAC addresses, Layer 4 handles TCP/UDP, and Layer 7 is the user interface.",
      "xp_reward": 20,
      "bits_reward": 10,
      "tags": ["OSI", "Routing", "Layer 3"]
    }
  ]
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Unique identifier (Zone-Node-Index) |
| `zone` | Int | 1-5 mapping to Domain |
| `node` | Float | Mapping to specific objective (e.g., 1.1) |
| `difficulty` | String | `easy` \| `medium` \| `hard` \| `boss` |
| `type` | String | `mob` \| `mini-boss` \| `guardian` |
| `question` | String | The core prompt |
| `options` | Array | 4 possible answers |
| `correct_index`| Int | Index of the correct option (0-3) |
| `explanation` | String | The "Learning Moment" shown after answering |
| `xp_reward` | Int | XP given on correct answer |
| `bits_reward` | Int | BITS given on correct answer |
| `tags` | Array | Used for targeted review/spaced repetition |

---

## 4. PBQ (Performance Based Question) Schema

Used for Mini-Bosses and Guardians. Terminal version simulates via "Configuration Menus."

```json
{
  "id": "z2-pbq-001",
  "type": "config_simulation",
  "scenario": "You need to configure a VLAN for the HR department. The switch is currently on the default VLAN 1.",
  "steps": [
    {
      "step_id": 1,
      "prompt": "Enter the command to create VLAN 10",
      "correct_answer": "vlan 10",
      "hint": "Use the standard Cisco-style command: vlan [ID]"
    },
    {
      "step_id": 2,
      "prompt": "Name the VLAN 'HR'",
      "correct_answer": "name HR",
      "hint": "The command is 'name [String]'"
    }
  ],
  "success_condition": "all_steps_correct"
}
```

> **Note on PBQs**: The terminal step-prompt format trains the underlying knowledge. For actual drag-and-drop familiarity, use CompTIA's official practice exam tool in the final week. Don't skip that.

---

## 5. Acronym Library Schema

```json
[
  {
    "acronym": "SLA",
    "full_name": "Service-level Agreement",
    "definition": "A contract between a service provider and a customer that defines the expected level of service."
  }
]
```

The N10-009 acronym list has 100+ entries. Acronym flashcard mode should cycle through ALL of them, weighted toward ones the player has missed.

---

## 6. Validation Rules

- **No Duplicate Questions**: IDs must be unique across all zones.
- **Balanced Distribution**: Each node must meet minimum counts above before a Guardian is unlockable.
- **Correctness**: Every question must have exactly one correct answer.
- **Explanation Required**: No question ships without an explanation — this is where the learning happens.
- **Tag Coverage**: Every exam objective sub-bullet must be covered by at least 2 questions.

---

*Last Updated: 2026-05-29 (v1.1)*
*Next: 03-TECH-ARCHITECTURE.md*
