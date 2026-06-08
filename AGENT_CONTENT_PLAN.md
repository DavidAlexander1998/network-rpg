# Network-RPG Content Overhaul — Orchestrator Brief (for Kimi + local Gemma workers)

> **You are Kimi, the orchestrator.** You dispatch local Gemma subagents (via Ollama) to
> clean up and expand the study content of this Network+ study game. This document is the
> single source of truth. Read it fully before dispatching anything. Zone 1 has **already
> been cleaned by hand** — treat it as the reference template for everything else.

---

## 0. Mission (what "done" looks like)

For **every zone (2–5)** the repo must end up with:

1. **Clean structure** — sequential nodes (`Z.1, Z.2, …`), consistent IDs, consistent
   `difficulty` values. No three-schemes-bolted-together mess like old Zone 1.
2. **Real teaching content**, not wall-to-wall tables. Every study encounter must *teach*
   with a plain-English explanation + an analogy + a scenario question (see §5 rubric).
3. **A study guide** per zone (`content/study-N.json`) — quick-reference cards keyed to the
   matching node. Tables are fine *here* (this is the cheat-sheet layer), but each zone also
   needs concept/mnemonic cards, not only tables.
4. **It still loads and passes tests** (see §7 validation gate). Nothing ships unvalidated.

The human is studying for **CompTIA Network+ N10-009**. Content must map to that exam.

---

## 1. Repo orientation

```
network-rpg/
  main.py                  # TUI entry point (don't touch for content work)
  game/
    zone_manager.py        # loads content/zone-N.json + content/study-N.json  <-- READ THIS
    encounter.py           # Encounter schema + validation (from_dict)          <-- READ THIS
    player.py, combat.py, spaced_repetition.py, save_manager.py
  content/
    zone-1.json ... zone-5.json     # the levels + encounters (PRIMARY WORK)
    study-1.json ... study-5.json   # quick-reference cards per node
    acronyms.json, cli-encounters.json, topology-encounters.json, flavor-texts.json
  test_all.py, test_study_first.py  # pytest suite — MUST stay green
```

**How content loads (verify by reading `game/zone_manager.py`):**
- `zone-N.json` is parsed; **node `id` is cast to `float`** — so node ids MUST be clean
  decimals like `2.1, 2.2` (never `2.01`, never `2.10` which collides with `2.1`).
- Nodes are **sorted by that float**. Bad numbering = scrambled order for the player.
- `study-N.json` keys are node ids as strings (`"2.1"`); cards attach to the node with the
  matching float id. **If a study key has no matching node, those cards silently vanish.**
- Each encounter is built by `Encounter.from_dict` — missing required keys raise and the
  encounter is **skipped with a warning**. Watch stderr during validation.

---

## 2. The data schemas (exact)

### zone-N.json (top level)
```json
{
  "zone": 2,
  "name": "string",
  "description": "string",
  "nodes": [ Node, ... ],
  "guardian_encounters": [ Encounter, ... ]   // the end-of-zone boss quiz
}
```

### Node
```json
{
  "id": 2.1,                 // float, sequential: 2.1, 2.2, 2.3 ...
  "name": "Short evocative name",
  "description": "One sentence on what this node covers.",
  "encounters": [ Encounter, ... ]
}
```

### Encounter — multiple choice (`study_encounter` and `mob`)
```json
{
  "id": "z2-n1-study-001",   // see §3 for the ID law
  "zone": 2,
  "node": 2.1,
  "type": "study_encounter", // or "mob"
  "difficulty": "easy",      // ONLY: "easy" | "medium" | "hard"
  "title": "Topic: Subtopic",
  "scenario": "Teaching text. REQUIRED for study_encounter (this is where you teach).",
  "question": "The actual question being asked.",
  "options": ["A", "B", "C", "D"],   // exactly 4, plausible
  "correct_index": 0,                // 0-based index of the correct option
  "explanation": "Why the right answer is right AND why the others are wrong.",
  "xp_reward": 50,
  "bits_reward": 10,
  "tags": ["osi-model", "layer-2"]
}
```
- `study_encounter` = teach-first (long `scenario`, then an easy check question).
- `mob` = a combat/quiz question (shorter or no `scenario`, tests recall). The "boss"
  questions live in `guardian_encounters` and use ids `z{Z}-g-{NNN}`.

### Encounter — `cli_encounter` (typed-command challenges; see cli-encounters.json)
Required: `id, scenario, objective, correct_answers (list), explanation`.
Optional: `command_prompt, accepts_partial (bool), hint`. No `options`/`correct_index`.

### Encounter — `topology_encounter`
Same as multiple choice **plus** an `ascii_diagram` string rendered above the question.

### study-N.json (the quick-reference cards)
```json
{
  "2.1": [ StudyCard, ... ],
  "2.2": [ StudyCard, ... ]
}
```
StudyCard:
```json
{
  "title": "string",
  "type": "table" | "concept" | "mnemonic" | "list",
  "body": "prose for concept/mnemonic",
  "key_points": ["for list type"],
  "headers": ["Col1", "Col2"],        // for table type
  "rows": [["a","b"], ["c","d"]]      // for table type
}
```

---

## 3. The ID law (non-negotiable — match zones, never invent)

| Thing | Format | Example |
|-------|--------|---------|
| Node id | `Z.N` float, sequential from `.1` | `2.1`, `2.2` |
| Study encounter id | `z{Z}-n{N}-study-{NNN}` | `z2-n1-study-001` |
| Mob encounter id | `z{Z}-n{N}-{NNN}` | `z2-n1-001` |
| Guardian id | `z{Z}-g-{NNN}` | `z2-g-001` |
| Study card key | string of node id | `"2.1"` |

`{NNN}` is zero-padded, **restarts at 001 per node**, study-list first then mobs. `difficulty`
is **always** one of `easy/medium/hard` (map any stray ints: `1→easy, 2→medium, 3→hard`).

---

## 4. Worked example — what was done to Zone 1 (your template)

Old Zone 1 was 19 nodes with **three** clashing numbering schemes (`1.01–1.05`, `1.1–1.8`,
`1.41/1.441`), **five** encounter-id styles (`prereq_001`, `1.1.1`, `z1-n6-001`, `fiber_001`,
`copper_001`), mixed `difficulty` (`easy` AND `1`), and the physical-layer topic smeared
across 4 node groups. It was consolidated to **8 clean nodes**, keeping all 80 encounters:

```
1.1 The Seven Layers   (OSI model)            1.5 The Cloud      (cloud+virt+SDN+modern)
1.2 The Toolbox        (devices + IDS/IPS)    1.6 The Layout     (topologies)
1.3 The Secret Codes   (ports & protocols)    1.7 Copper Lines   (copper cabling)
1.4 The Address Book   (IPv4/DNS)             1.8 Fiber & Light  (fiber optics)
```
Rules applied (apply the SAME rules to zones 2–5):
- Group encounters by **topic**, not by which commit added them.
- One topic = one node. Merge duplicates (Zone 1 had fiber in 4 places → 1 fiber node).
- Renumber nodes `Z.1…` with no gaps; renumber encounter ids per §3.
- Normalize every `difficulty` to a string.
- **Re-key `study-N.json`** so each card set's float key matches its new node, or cards vanish.
- Reference transform: `_zone1_cleanup.py` at repo root shows the exact mechanical approach
  (build an index by old id → assign to new nodes → renumber). You may delete it after.

**Do NOT delete encounter content.** Regroup and rename only. Adding *new* encounters to thin
nodes is encouraged (see §6), but existing questions are kept.

---

## 5. Content quality rubric (this is the whole point — kill the table-spam)

The human's complaint: *"is it actually gonna help me pass or is it just feeding me tables
the whole time."* Every **study_encounter** you write or keep MUST hit all of these:

1. **Plain-English definition** of each key term before using it.
2. **A concrete analogy** (Zone 1's good ones: OSI physical layer = city water pipes; switch
   = mailroom clerk with a logbook; router = airport customs officer; TCP = certified mail vs
   UDP = postcard). One vivid analogy per encounter.
3. **A scenario-style question** — "A technician is troubleshooting X and sees Y…" — not a
   bare "What does ABC stand for?" Recall-only questions are fine as `mob`/guardian, but
   `study_encounter` questions should make the learner *reason*.
4. **An explanation that also says why the wrong options are wrong** (this is where real
   learning happens — model it on Zone 1's explanations).
5. **Exam-aligned**: tie to N10-009 objectives. Use real numbers/standards (ports, Cat
   ratings, distances, RFC 1918 ranges, IPv6 facts).

**Tables** belong in `study-N.json` cards (`type: "table"`), NOT as the body of teaching
encounters. A zone whose study file is *only* tables fails review — add `concept` and
`mnemonic` cards too (e.g. "Please Do Not Throw Sausage Pizza Away").

**Anti-patterns to reject from a Gemma worker's output:**
- 4 options where 3 are obviously absurd (distractors must be plausible near-misses).
- `correct_index` that doesn't point at the correct option (validate every one).
- Restating the question as the explanation.
- Inventing facts/ports/standards. If unsure, the worker must flag, not guess.

---

## 6. Per-zone work orders (current state → target)

Run `python -c "import json;d=json.load(open('content/zone-N.json',encoding='utf-8'));
print(len(d['nodes']),[n['id'] for n in d['nodes']])"` first to confirm current state, then:

- **Zone 2 — Network Implementation** (routing, switching, wireless, physical). Currently
  ~5 nodes, already has `study_encounter` + `mob` and a `study-2.json`. Audit IDs against
  §3, verify difficulties, apply rubric §5 to weak encounters, ensure every node has ≥2
  teach-first study encounters. Likely the lightest cleanup.
- **Zone 3 — Network Operations** (monitoring, QoS, docs, HA/DR). ~5 nodes but encounters
  may be **mob-only** — add `study_encounter` teach-first content per node so it isn't pure
  quiz. Verify `study-3.json` keys match nodes.
- **Zone 4 — Network Security** (attacks, firewalls, VPN, PKI, AAA). ~4 nodes, likely
  mob-only. Same treatment as Zone 3. Consider whether 4 nodes should be 5 for topic balance.
- **Zone 5 — Network Troubleshooting** (methodology, tools, commands, wireless, services).
  ~5 nodes, mob-only. Add teach-first content; this zone pairs well with `cli_encounter`
  practice (ipconfig/ping/show commands) — see `cli-encounters.json` for the pattern.

For each zone produce: cleaned `zone-N.json` + matching `study-N.json`. Target **5 nodes**
per zone (4 acceptable if topics genuinely split that way), **5–8 encounters per node**, at
least 2 of them teach-first study encounters.

---

## 7. Validation gate (a subagent's work is NOT done until this passes)

Run from repo root after each zone:

```bash
# 1. JSON parses + loads through the real engine with NO warnings on stderr
python -c "from game.zone_manager import ZoneManager; \
zm=ZoneManager('content'); z=zm.load_zone(N); \
assert z, 'failed to load'; \
ids=[e.id for n in z.nodes for e in n.encounters]; \
assert len(ids)==len(set(ids)), 'duplicate encounter ids'; \
import sys; \
[print(n.id,n.name,len(n.encounters),'cards='+str(len(n.study_cards))) for n in z.nodes]"

# 2. Every correct_index is valid and points at a real option; difficulty is a clean string
python -c "import json; d=json.load(open('content/zone-N.json',encoding='utf-8')); \
[ (_:=None) for n in d['nodes'] for e in n['encounters'] \
  if e.get('type')!='cli_encounter' and not (0<=e['correct_index']<len(e['options'])) \
  and (_ for _ in ()).throw(SystemExit('bad correct_index '+e['id']))]; \
assert all(e.get('difficulty') in ('easy','medium','hard') \
  for n in d['nodes'] for e in n['encounters']), 'bad difficulty'; print('ok')"

# 3. Study cards all attach (no orphan keys)
python -c "import json; d=json.load(open('content/zone-N.json',encoding='utf-8')); \
s=json.load(open('content/study-N.json',encoding='utf-8')); \
nodes={str(n['id']) for n in d['nodes']}; \
orphans=[k for k in s if k not in nodes]; \
assert not orphans, 'orphan study keys: '+str(orphans); print('study ok')"

# 4. The whole test suite stays green
python -m pytest -q
```

Only after all four pass may the orchestrator accept the zone and commit it. Commit one zone
per commit with a message like `Zone N: restructure into clean nodes + teach-first study content`.

---

## 8. How to split the work among Gemma workers (orchestration plan)

Gemma (esp. smaller quants) is good at *bounded* generation, weak at *holding a whole repo
in its head*. So **you (Kimi) own structure and validation; Gemma only fills bounded slots.**

**Pipeline per zone:**
1. **You** read the current `zone-N.json`, decide the final node list (topic grouping per §4),
   and build the id map. This is judgement work — keep it.
2. **Fan out per node** (one Gemma subagent per node, they're independent):
   - Give the worker: the node's name, its topic, the exact §2 schema, the §3 id range to use
     (e.g. "ids `z3-n2-study-001`..`-004` and `z3-n2-001`..`-004`"), the §5 rubric, and 1–2
     of Zone 1's good encounters as a **few-shot example**.
   - Ask for: that node's `encounters` array (JSON only) + its study cards array.
   - Constrain hard: exactly 4 options, valid `correct_index`, plausible distractors,
     one analogy per study encounter, no invented facts.
3. **You** assemble the returned node arrays into `zone-N.json` / `study-N.json`, fix ids if a
   worker drifted, and run §7. If validation fails, bounce the specific bad encounter back to
   a worker with the error — don't regenerate the whole zone.
4. Commit when green.

**Worker prompt skeleton (give this to each Gemma subagent):**
> You are writing CompTIA Network+ (N10-009) study content as JSON. Output ONLY a JSON array,
> no prose. Schema: {paste §2 multiple-choice schema}. Rules: exactly 4 options; `correct_index`
> is 0-based and MUST point at the correct option; the 3 wrong options are plausible near-misses,
> never absurd; each `study_encounter` has a `scenario` that (a) defines terms in plain English,
> (b) gives ONE concrete real-world analogy, (c) leads to a reasoning question; the `explanation`
> says why the right answer is right AND why each wrong option is wrong; use real ports/standards,
> never invent. Topic: {node topic}. Use ids {id range}. Difficulty spread: mostly easy/medium.
> Here are two gold examples to match in depth and style: {paste 2 Zone-1 study encounters}.

**Model note:** content quality scales with the Gemma variant — use the largest you can run
(e.g. `gemma3:27b` >> a 2–4B quant) especially for plausible distractors and explanations.
Whatever you pull, **you (Kimi) validate every `correct_index` and every claimed fact** — a
local model *will* occasionally mislabel the answer or invent a port number.

---

## 9. Guardrails

- Work on a branch (current branch is `Zone-1-enhancements`; make `content-overhaul` or per-zone
  branches). Never force-push. Commit per zone.
- Never edit `game/*.py` for content work — if content seems to need a code change, stop and
  surface it to the human instead.
- Don't touch `saves/` or `main.py`.
- Keep existing encounters; regroup/rename/augment, don't delete teaching content.
- If a fact is uncertain, flag it in the commit body for human review rather than guessing.

---

### Appendix: quick repo facts
- Node ids are floats → keep them clean decimals, no gaps, no `.10`.
- `study_encounter` teaches; `mob` tests; `guardian_encounters` is the boss quiz.
- Difficulty: `easy|medium|hard` only.
- Zone 1 (8 nodes, 80 encounters) is the done reference — open it to see the target quality.
