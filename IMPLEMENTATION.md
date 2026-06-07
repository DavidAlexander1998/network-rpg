# Network+ RPG Enhancement Implementation Guide

## Overview
Integrate AI-generated content (from local Gemma4 26B) into the existing codebase.

---

## 1. CLI ENCOUNTERS (5 New Encounters)

New encounter type: `cli_encounter` - accepts text input instead of multiple choice.

### Encounter 1: Interface Status Check
```json
{
  "id": "z1-cli-001",
  "zone": 1,
  "node": 1.1,
  "type": "cli_encounter",
  "scenario": "The server room is freezing. You plug in your console cable, and the terminal blinks rhythmically. The local workstation reports 'No Internet,' and the link light on the main router's GigabitEthernet0/0 port is dark. You need to see the status of all interfaces to confirm if the port is administratively down or physically disconnected.",
  "objective": "Check the status and IP address of all interfaces.",
  "command_prompt": "Router>",
  "correct_answers": ["show ip interface brief", "sh ip int br", "show ip interface"],
  "accepts_partial": true,
  "hint": "Try using the 'show' command followed by 'ip interface brief' to get a summary table.",
  "explanation": "The 'show ip interface brief' command provides a concise summary of the IP address and the current status (up/down) of all interfaces on the device.",
  "xp_reward": 50,
  "bits_reward": 25,
  "tags": ["CLI", "Cisco", "Verification", "Interface Status"]
}
```

### Encounter 2: Running Configuration
```json
{
  "id": "z1-cli-002",
  "zone": 1,
  "node": 1.2,
  "type": "cli_encounter",
  "scenario": "You've bypassed the security gate and accessed the core switch. The previous admin left the configuration in a mess. You need to see exactly how the device is currently operating—including the assigned IP addresses and VLAN settings—to find where the misconfiguration lies.",
  "objective": "Display the current active configuration in the volatile memory.",
  "command_prompt": "Switch#",
  "correct_answers": ["show running-config", "sh run"],
  "accepts_partial": true,
  "hint": "You need to view the 'running' configuration, not the startup one.",
  "explanation": "The 'show running-config' command displays the configuration currently active in the device's RAM.",
  "xp_reward": 60,
  "bits_reward": 30,
  "tags": ["CLI", "Cisco", "Configuration", "Layer 2"]
}
```

### Encounter 3: Connectivity Test
```json
{
  "id": "z1-cli-003",
  "zone": 1,
  "node": 1.3,
  "type": "cli_encounter",
  "scenario": "The terminal scrolls with error logs. A remote sensor at 192.168.50.10 is failing to report data. You can reach the local gateway, but you aren't sure if the path to the sensor is actually open. You need to send a test packet to see if the remote host responds.",
  "objective": "Test connectivity to the IP address 192.168.50.10.",
  "command_prompt": "Router#",
  "correct_answers": ["ping 192.168.50.10"],
  "accepts_partial": false,
  "hint": "Use the standard ICMP echo request command followed by the target IP.",
  "explanation": "The 'ping' command uses ICMP Echo Request and Echo Reply messages to verify end-to-end connectivity between two hosts.",
  "xp_reward": 40,
  "bits_reward": 20,
  "tags": ["CLI", "Cisco", "ICMP", "Connectivity"]
}
```

### Encounter 4: ARP Table
```json
{
  "id": "z1-cli-004",
  "zone": 1,
  "node": 1.4,
  "type": "cli_encounter",
  "scenario": "The switch is receiving frames, but the packets are being dropped at the MAC layer. You suspect a duplicate IP address or an ARP mismatch. You need to see the mapping between the Layer 3 IP addresses and the Layer 2 MAC addresses to identify the intruder.",
  "objective": "View the Address Resolution Protocol (ARP) table.",
  "command_prompt": "Router#",
  "correct_answers": ["show arp", "sh arp"],
  "accepts_partial": true,
  "hint": "Search for the protocol that maps IP addresses to MAC addresses.",
  "explanation": "The 'show arp' command displays the ARP cache, which maps IP addresses to physical MAC addresses on the local network segment.",
  "xp_reward": 70,
  "bits_reward": 35,
  "tags": ["CLI", "Cisco", "ARP", "Layer 2/3"]
}
```

### Encounter 5: Routing Table
```json
{
  "id": "z1-cli-005",
  "zone": 1,
  "node": 1.5,
  "type": "cli_encounter",
  "scenario": "The router is humming, but it's behaving like a brick. It has multiple interfaces, but it seems to have no idea where to send traffic destined for the 10.0.0.0/24 subnet. You need to inspect the router's internal map to see if a route even exists.",
  "objective": "View the IP routing table.",
  "command_prompt": "Router#",
  "correct_answers": ["show ip route", "sh ip route"],
  "accepts_partial": true,
  "hint": "Look for the command that displays the IP routing table.",
  "explanation": "The 'show ip route' command displays the routing table, which tells the router which interface or next-hop to use for specific destination networks.",
  "xp_reward": 80,
  "bits_reward": 40,
  "tags": ["CLI", "Cisco", "Routing", "Layer 3"]
}
```

---

## 2. NARRATIVE FLAVOR TEXTS

### Zone Entry Texts
```json
{
  "zone_entries": {
    "zone1": "The architecture here is a fractured stack of seven collapsing realities. You navigate the Physical layer's rusted ruins, feeling the abstraction of the higher layers peeling away like dead skin.",
    "zone2": "Neon-lit gateways flicker with incorrect destination headers, bleeding data into the void. Every hop through this district feels like a gamble against a corrupted routing table.",
    "zone3": "The air is thick with the static of endless syslog streams, a constant, low-frequency scream of system telemetry. Latency hangs in the smog like heavy rain, slowing every breath and every movement.",
    "zone4": "Razor-wire ACLs slice through the darkness, guarding the perimeter with cold, mathematical indifference. Everything here is shrouded in black-ice encryption, a cipher that kills anyone without the proper handshake.",
    "zone5": "This is the graveyard of discarded packets, where checksum errors rot in the gutters. The signal is lost here, a fractured, broken trace of what was once a coherent stream."
  }
}
```

### Node Transition Texts
```json
{
  "node_transitions": [
    "Squeezing through a choked bundle of frayed Cat6, the copper bites at your skin.",
    "A violent, jagged SYN/ACK handshake forces your consciousness into the next sector.",
    "Sliding through the crystalline, blinding light of a fiber-optic conduit.",
    "The heavy, rhythmic thrum of a dying switchboard vibrates through your boots as you jump the gap.",
    "Leaping through a burst of unencrypted wireless noise, the air screams with interference."
  ]
}
```

### Encounter Intros
```json
{
  "encounter_intros": [
    "A rogue DHCP daemon materializes, attempting to assign you a soul it does not own.",
    "Packet loss corruption seeps from the walls, eroding the reality of your very existence.",
    "A massive, churning Spanning Tree loop begins to swallow the light.",
    "The silence is shattered by the deafening, rhythmic roar of a localized broadcast storm.",
    "A Time-to-Live expiration shadow looms, ready to prune your existence from the Grid."
  ]
}
```

---

## 3. ASCII TOPOLOGY DIAGRAMS (5 New Encounters)

New encounter type: `topology_encounter` - displays ASCII art diagram + multiple choice question.

### Diagram 1: Single Point of Failure
```json
{
  "id": "topo-001",
  "name": "The Lonely Hub",
  "difficulty": "easy",
  "ascii_diagram": "      ┌───┐\n      │H1 │\n      └───┘\n        │\n  ┌─────┴─────┐\n  │   [S1]    │\n  └─────┬─────┘\n        │\n      ┌─┴─┐\n      │H2 │\n      └───┘",
  "question": "What is the single point of failure in this topology?",
  "options": ["The Router", "The Central Switch [S1]", "The Host H1", "The Ethernet Cables"],
  "correct_index": 1,
  "explanation": "In a star topology, if the central switch fails, all connected nodes lose connectivity to each other.",
  "xp_reward": 40,
  "bits_reward": 20,
  "tags": ["topology", "single-point-of-failure"]
}
```

### Diagram 2: VLAN Trunk Misconfiguration
```json
{
  "id": "topo-002",
  "name": "The Trunk Trap",
  "difficulty": "medium",
  "ascii_diagram": "┌─────────┐         ┌─────────┐\n│ [S1]    │         │ [S2]    │\n│ VLAN 10 │ ~~~~~~~ │ VLAN 10 │\n└────┬────┘         └────┬────┘\n     │                  │\n   ┌─┴─┐              ┌─┴─┐\n   │H1 │              │H2 │\n   └─┬─┘              └─┬─┘\n     └───[VLAN 10]──────┘",
  "question": "Why are H1 and H2 unable to communicate on VLAN 10?",
  "options": ["The cable is broken", "The switch is powered off", "The link is an access port instead of a trunk", "VLAN 10 is disabled"],
  "correct_index": 2,
  "explanation": "To carry traffic for multiple VLANs between switches, the link must be configured as a Trunk port. The '~~~' indicates a misconfiguration where it is acting as a single access port.",
  "xp_reward": 60,
  "bits_reward": 30,
  "tags": ["vlan", "trunking", "misconfiguration"]
}
```

### Diagram 3: STP Loop
```json
{
  "id": "topo-003",
  "name": "The Infinite Loop",
  "difficulty": "hard",
  "ascii_diagram": "┌─────────┐      ┌─────────┐\n│ [S1]    │======│ [S2]    │\n│         │      │         │\n│         └======┘         │\n└─────────┘      └─────────┘",
  "question": "What is causing the broadcast storm in this network?",
  "options": ["A faulty router", "Lack of Spanning Tree Protocol (STP)", "Too many hosts on the segment", "A wireless interference"],
  "correct_index": 1,
  "explanation": "Redundant links between switches without STP enabled create a switching loop, causing broadcast packets to circulate infinitely.",
  "xp_reward": 80,
  "bits_reward": 40,
  "tags": ["stp", "loop", "switching"]
}
```

### Diagram 4: Subnet Mask Mismatch
```json
{
  "id": "topo-004",
  "name": "The Mask Mismatch",
  "difficulty": "medium",
  "ascii_diagram": "┌─────────┐\n│ [S1]    │\n└─┬───┬───┘\n  │   │\n┌─┴─┐ ┌─┴─┐\n│H1 │ │H2 │\n└───┘ └─┬─┘\nH1: 10.0.0.5/24\nH2: 10.0.0.6/30",
  "question": "Why can't Host 2 (10.0.0.6/30) communicate with a host at 10.0.0.8/24?",
  "options": ["The cable is bad", "The IP address is duplicate", "The subnet mask is too restrictive", "The switch is full"],
  "correct_index": 2,
  "explanation": "A /30 mask means Host 2 only considers the range 10.0.0.4 to 10.0.0.7 as local. It will attempt to send traffic for 10.0.0.8 to its default gateway instead of directly to the host.",
  "xp_reward": 50,
  "bits_reward": 25,
  "tags": ["subnetting", "ip-addressing"]
}
```

### Diagram 5: DMZ Bypass
```json
{
  "id": "topo-005",
  "name": "The Leaky DMZ",
  "difficulty": "hard",
  "ascii_diagram": "      ☁ (Internet)\n        │\n      ┌─┴─┐\n      │ F1│\n      └─┬─┘\n        ├──────────────┐\n      ┌─┴─┐          ┌─┴─┐\n      │S1 │          │S2 │\n      └─┬─┘          └─┬─┘\n        │ (Int)        │ (DMZ)\n      ┌─┴─┐          ┌─┴─┐\n      │H_I│ ~~~~~~~~ │H_D│\n      └─┬─┘          └─┬─┘",
  "question": "Why is the Internal Host (H_I) vulnerable to the DMZ Host (H_D)?",
  "options": ["The firewall is powered off", "There is an unauthorized direct link bypassing the firewall", "The DMZ is too large", "The cloud is compromised"],
  "correct_index": 1,
  "explanation": "A secure DMZ should force all traffic between the DMZ and the Internal network through the firewall. The '~~~' link shows a direct connection that bypasses security inspection.",
  "xp_reward": 100,
  "bits_reward": 50,
  "tags": ["firewall", "dmz", "security"]
}
```

---

## 4. ZONE 3 CONTENT (64 Questions, 8 Nodes)

**Zone 3: The Engine Room** - Network Operations domain (19% of exam)

Topics covered:
- Node 3.1: Documentation & Change Management (SLAs, CAB, rollback plans)
- Node 3.2: Monitoring (SNMP v1/v2c/v3, Syslog levels, SIEM)
- Node 3.3: Disaster Recovery (RPO, RTO, backup types, HA)
- Node 3.4: IPv4 Services (DHCP DORA, DNS records, NAT/PAT)
- Node 3.5: IPv6 Services (address types, SLAAC, DHCPv6, NDP)
- Node 3.6: Time Services (NTP stratum, PTP precision)
- Node 3.7: Remote Access (SSH, VPN types, jump boxes, MFA)
- Node 3.8: Network Management (IPAM, CMDB, patching lifecycle, EOL/EOS)

### Sample Questions:

**Node 3.1 - Change Management:**
```json
{
  "id": "z3-n1-001",
  "zone": 3,
  "node": 3.1,
  "difficulty": "easy",
  "type": "mob",
  "question": "A technician wants to update the firmware on a core switch. Which process must be followed to ensure the change is recorded and risks are mitigated?",
  "options": ["Change Management", "Disaster Recovery", "Incident Management", "Asset Management"],
  "correct_index": 0,
  "explanation": "Change Management is the formal process used to ensure that changes to the IT environment are documented, evaluated, and approved to minimize service disruption.",
  "xp_reward": 20,
  "bits_reward": 10,
  "tags": ["documentation", "change-management"]
}
```

**Node 3.2 - Monitoring:**
```json
{
  "id": "z3-n2-003",
  "zone": 3,
  "node": 3.2,
  "difficulty": "medium",
  "type": "mob",
  "question": "Which version of SNMP provides the highest level of security through encryption and authentication?",
  "options": ["SNMPv3", "SNMPv2c", "SNMPv1", "SNMP-Secure"],
  "correct_index": 0,
  "explanation": "SNMPv3 introduced user-based security models that provide authentication and encryption, whereas v1 and v2c rely on plain-text community strings.",
  "xp_reward": 30,
  "bits_reward": 15,
  "tags": ["monitoring", "snmp"]
}
```

**Node 3.4 - IPv4 Services:**
```json
{
  "id": "z3-n4-007",
  "zone": 3,
  "node": 3.4,
  "difficulty": "hard",
  "type": "mob",
  "question": "A client computer is unable to connect to the internet and has an IP address of 169.254.10.5. What is the most likely cause?",
  "options": ["The client failed to reach a DHCP server", "The DNS server is down", "The NAT gateway is misconfigured", "The client has a duplicate IP address"],
  "correct_index": 0,
  "explanation": "The 169.254.x.x range is APIPA (Automatic Private IP Addressing). This occurs when a client is configured for DHCP but cannot communicate with a DHCP server to receive an address.",
  "xp_reward": 50,
  "bits_reward": 25,
  "tags": ["DHCP", "Troubleshooting"]
}
```

**Node 3.5 - IPv6 Services:**
```json
{
  "id": "z3-n5-004",
  "zone": 3,
  "node": 3.5,
  "difficulty": "medium",
  "type": "mob",
  "question": "Which protocol in IPv6 replaces the function of ARP used in IPv4?",
  "options": ["Neighbor Discovery Protocol (NDP)", "ICMPv6", "DHCPv6", "SLAAC"],
  "correct_index": 0,
  "explanation": "Neighbor Discovery Protocol (NDP) uses ICMPv6 messages to perform functions like address resolution (replacing ARP), router discovery, and duplicate address detection.",
  "xp_reward": 30,
  "bits_reward": 15,
  "tags": ["IPv6", "NDP"]
}
```

**Node 3.7 - Remote Access:**
```json
{
  "id": "z3-n7-008",
  "zone": 3,
  "node": 3.7,
  "difficulty": "hard",
  "type": "mob",
  "question": "A company implements split tunneling to improve performance for remote users. Which of the following is a primary security concern resulting from this decision?",
  "options": ["The VPN tunnel becomes too slow for VoIP traffic.", "The user's local traffic is unencrypted by the VPN.", "Malware on the user's device could bypass corporate firewalls via the local internet connection and reach the VPN.", "The VPN gateway cannot handle multiple simultaneous connections."],
  "correct_index": 2,
  "explanation": "In split tunneling, because the user's internet traffic bypasses the corporate security stack (firewalls, IDS/IPS), a device could be compromised via the public web and then use the active VPN tunnel to spread malware into the corporate network.",
  "xp_reward": 50,
  "bits_reward": 25,
  "tags": ["vpn", "split-tunneling", "security-risk"]
}
```

**Full Zone 3 JSON file needs to be created with all 64 questions.**

---

## 5. IMPLEMENTATION REQUIREMENTS

### New Encounter Types Needed:

1. **`cli_encounter`** in `game/encounter.py`
   - Accept text input from user
   - Support partial matching (abbreviated commands)
   - Show hint after first wrong attempt
   - Validate against multiple correct answer variations

2. **`topology_encounter`** in `game/encounter.py`
   - Display ASCII diagram in Rich panel
   - Standard multiple choice question
   - Diagram shown above question

### Files to Modify:

- `game/encounter.py` - Add new encounter types
- `game/combat.py` - Handle CLI and topology encounters
- `ui/screens.py` - Display ASCII diagrams, handle text input
- `game/zone_manager.py` - Load new encounter types
- `main.py` - Wire up new encounter handling

### New Files to Create:

- `content/zone-3.json` - 64 questions for Network Operations domain
- `content/cli-encounters.json` - 5 CLI command scenarios
- `content/topology-encounters.json` - 5 ASCII diagram scenarios
- `content/flavor-texts.json` - Zone entries, transitions, intros

### Acceptance Criteria:

- [ ] CLI encounters accept text input and validate correctly
- [ ] Partial command matching works ("sh ip int br" = "show ip interface brief")
- [ ] ASCII diagrams display cleanly in Rich panels
- [ ] Zone 3 loads and all 64 questions are playable
- [ ] Flavor texts appear at appropriate times
- [ ] Save/load works with new encounter types
- [ ] No regressions in existing Zones 1-2

---

## 6. EXISTING CODE PATTERNS TO FOLLOW

### Combat System (`game/combat.py`):
```python
class Combat:
    def __init__(self, player: Player, encounter: Encounter)
    def process_answer(self, selected_index: int) -> CombatResult
```

### Encounter Dataclass (`game/encounter.py`):
```python
@dataclass
class Encounter:
    id: str
    zone: int
    node: float
    difficulty: str
    type: str  # "mob", "mini-boss", "guardian"
    question: str
    options: List[str]
    correct_index: int
    explanation: str
    xp_reward: int
    bits_reward: int
    tags: List[str]
```

### UI Pattern (`ui/screens.py`):
- Use `rich` for panels, tables, colors
- Use `questionary` for interactive menus
- `Console()` for output

### Zone Loading (`game/zone_manager.py`):
- JSON files in `content/zone-X.json`
- `load_zone()` method
- Zone/Node dataclasses

---

**Total Content Generated:**
- 5 CLI encounters
- 5 ASCII topology diagrams
- 64 Zone 3 questions
- 15 flavor texts (5 zones + 5 transitions + 5 intros)

**Cost:** $0.00 (all generated locally via Ollama/Gemma4 26B)
