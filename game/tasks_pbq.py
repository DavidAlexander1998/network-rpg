"""Performance-based-style tasks: ordering and matching.

The real N10-009 includes drag-and-drop PBQs — put steps in order, match items
to categories. These force you to *produce* a structure instead of recognizing
one option, which is a deeper test of understanding. Tasks are pure data; the
runner (sequential selects) lives in main.py / ui.screens.
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class OrderingTask:
    id: str
    prompt: str
    ordered: List[str]   # the CORRECT order
    explanation: str


@dataclass
class MatchingTask:
    id: str
    prompt: str
    pairs: List[Tuple[str, str]]  # (left, correct right)
    explanation: str


ORDERING_TASKS: List[OrderingTask] = [
    OrderingTask(
        id="troubleshoot-steps",
        prompt="Put CompTIA's 7 troubleshooting steps in the correct order:",
        ordered=[
            "Identify the problem",
            "Establish a theory of probable cause",
            "Test the theory to determine cause",
            "Establish a plan of action",
            "Implement the solution or escalate",
            "Verify full system functionality",
            "Document findings, actions, and outcomes",
        ],
        explanation=("Identify -> Theory -> Test -> Plan -> Implement -> Verify -> "
                     "Document. Mnemonic: 'I Eat Tacos Everyday In Various Diners.'"),
    ),
    OrderingTask(
        id="osi-bottom-up",
        prompt="Order the OSI layers from Layer 1 (bottom) to Layer 7 (top):",
        ordered=["Physical", "Data Link", "Network", "Transport",
                 "Session", "Presentation", "Application"],
        explanation=("L1 Physical -> L2 Data Link -> L3 Network -> L4 Transport -> "
                     "L5 Session -> L6 Presentation -> L7 Application. "
                     "'Please Do Not Throw Sausage Pizza Away.'"),
    ),
    OrderingTask(
        id="tcp-handshake",
        prompt="Order the steps of the TCP three-way handshake:",
        ordered=["Client sends SYN", "Server replies SYN-ACK", "Client sends ACK"],
        explanation="TCP opens a connection with SYN -> SYN-ACK -> ACK before any data.",
    ),
    OrderingTask(
        id="encapsulation",
        prompt="Order the data encapsulation units as data moves DOWN the stack (sending):",
        ordered=["Data (Application)", "Segment (Transport)", "Packet (Network)",
                 "Frame (Data Link)", "Bits (Physical)"],
        explanation=("Going down the stack: Data -> Segment -> Packet -> Frame -> Bits. "
                     "Each layer wraps the one above it."),
    ),
]


MATCHING_TASKS: List[MatchingTask] = [
    MatchingTask(
        id="ports",
        prompt="Match each protocol to its default port:",
        pairs=[("SSH", "22"), ("DNS", "53"), ("HTTPS", "443"),
               ("RDP", "3389"), ("SMTP", "25"), ("SNMP", "161")],
        explanation=("SSH 22, DNS 53, HTTPS 443, RDP 3389, SMTP 25, SNMP 161. "
                     "These are guaranteed exam points."),
    ),
    MatchingTask(
        id="cloud-models",
        prompt="Match each cloud service model to what the customer manages:",
        pairs=[
            ("IaaS", "Customer manages OS, runtime, and apps (provider: hardware/virtualization)"),
            ("PaaS", "Customer manages only their app and data (provider: OS + runtime)"),
            ("SaaS", "Customer manages nothing — just uses the application"),
        ],
        explanation=("IaaS = most customer control (e.g., EC2). PaaS = managed platform "
                     "(e.g., App Engine). SaaS = ready-to-use app (e.g., Microsoft 365)."),
    ),
    MatchingTask(
        id="connectors",
        prompt="Match each connector to its media type:",
        pairs=[("RJ45", "Twisted-pair copper Ethernet"),
               ("LC / SC", "Fiber optic"),
               ("BNC", "Coaxial"),
               ("F-type", "Coaxial (cable modem/TV)")],
        explanation=("RJ45 = copper Ethernet; LC/SC = fiber; BNC and F-type = coax. "
                     "Know connectors by sight and media for the exam."),
    ),
    MatchingTask(
        id="attacks",
        prompt="Match each attack to its description:",
        pairs=[
            ("ARP spoofing", "Maps attacker's MAC to the gateway IP for on-path interception"),
            ("Evil twin", "Rogue AP imitating a legitimate SSID to harvest credentials"),
            ("SYN flood", "Sends many half-open TCP connections to exhaust a server"),
            ("DNS poisoning", "Corrupts DNS records to redirect users to malicious sites"),
        ],
        explanation=("These are the most-tested attack types — recognize each by its "
                     "mechanism, not just its name."),
    ),
]


def get_ordering(task_id: str):
    return next((t for t in ORDERING_TASKS if t.id == task_id), None)


def get_matching(task_id: str):
    return next((t for t in MATCHING_TASKS if t.id == task_id), None)
