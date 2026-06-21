"""Command Lab — a simulated terminal for hands-on troubleshooting.

This is the closest thing in the game to a performance-based exam question
(PBQ). Each scenario drops you into a broken network with a symptom. You type
real diagnostic commands (ping, ipconfig, nslookup, tracert, ...) against
scripted output, read the clues, and then commit to a diagnosis. The point is
to practice the *method* — isolating a fault by what each command reveals —
not to recognize a memorized answer.

Scenarios are pure data; the runner lives in main.py / ui.screens.
"""

from dataclasses import dataclass, field
from typing import Dict, List


def _norm(cmd: str) -> str:
    """Lowercase + collapse whitespace so 'ping   8.8.8.8' == 'ping 8.8.8.8'."""
    return " ".join(cmd.lower().split())


@dataclass
class Scenario:
    id: str
    title: str
    brief: str
    commands: Dict[str, str]      # normalized command -> output text
    available: List[str]          # commands to advertise to the learner
    question: str
    options: List[str]
    answer_index: int
    explanation: str
    aliases: Dict[str, str] = field(default_factory=dict)  # alias -> canonical command

    def run_command(self, raw: str) -> str:
        cmd = _norm(raw)
        cmd = self.aliases.get(cmd, cmd)
        if cmd in self.commands:
            return self.commands[cmd]
        return ("Command not recognized or not useful here. Type 'help' for "
                "available commands, or 'solve' when you're ready to diagnose.")


SCENARIOS: List[Scenario] = [
    Scenario(
        id="dns",
        title="Can't reach websites",
        brief=("A user reports: \"The internet is down — no websites load.\" "
               "Other users on the same LAN are fine. Diagnose it."),
        available=["ping 8.8.8.8", "ping google.com", "nslookup google.com", "ipconfig"],
        commands={
            "ping 8.8.8.8":
                "Reply from 8.8.8.8: bytes=32 time=14ms TTL=118\n"
                "Reply from 8.8.8.8: bytes=32 time=13ms TTL=118\n"
                "    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)",
            "ping google.com":
                "Ping request could not find host google.com. Please check the "
                "name and try again.",
            "nslookup google.com":
                "Server:  UnKnown\nAddress:  192.168.1.1\n\n"
                "*** UnKnown can't find google.com: No response from server",
            "ipconfig":
                "IPv4 Address. . . . . . . . . . . : 192.168.1.50\n"
                "Subnet Mask . . . . . . . . . . . : 255.255.255.0\n"
                "Default Gateway . . . . . . . . . : 192.168.1.1\n"
                "DNS Servers . . . . . . . . . . . : 192.168.1.1",
        },
        aliases={"ping 8.8.8.8 -n 4": "ping 8.8.8.8", "nslookup": "nslookup google.com"},
        question="What is the most likely cause?",
        options=[
            "The DNS server is failing to resolve names",
            "The default gateway is down",
            "The host has no IP address (DHCP failure)",
            "The physical cable is disconnected",
        ],
        answer_index=0,
        explanation=(
            "Ping to 8.8.8.8 (an IP) succeeds, so connectivity and routing to the "
            "internet are fine. Ping by NAME fails and nslookup gets 'no response "
            "from server' — name resolution is broken. The host has a valid IP, "
            "mask, and gateway. Classic 'connected but can't browse' = DNS problem."),
    ),
    Scenario(
        id="dhcp",
        title="No network access after reboot",
        brief=("A workstation can't reach anything after a reboot. Find out why."),
        available=["ipconfig", "ping 192.168.1.1", "ipconfig /release", "ipconfig /renew"],
        commands={
            "ipconfig":
                "IPv4 Address. . . . . . . . . . . : 169.254.23.114\n"
                "Subnet Mask . . . . . . . . . . . : 255.255.0.0\n"
                "Default Gateway . . . . . . . . . :",
            "ping 192.168.1.1":
                "Destination host unreachable.\n"
                "    Packets: Sent = 4, Received = 0, Lost = 4 (100% loss)",
            "ipconfig /release":
                "No operation can be performed while media is disconnected, or no "
                "lease is held.",
            "ipconfig /renew":
                "An error occurred while renewing interface Ethernet: unable to "
                "contact your DHCP server. Request has timed out.",
        },
        aliases={"ping gateway": "ping 192.168.1.1"},
        question="What is happening?",
        options=[
            "The DHCP server is unreachable, so the host self-assigned an APIPA address",
            "DNS is misconfigured",
            "The default gateway is blocking ICMP",
            "The subnet mask is wrong",
        ],
        answer_index=0,
        explanation=(
            "The 169.254.x.x address is APIPA — the host self-assigned it because it "
            "got no DHCP lease. There's no default gateway and renew can't contact the "
            "DHCP server. Fix the DHCP server/scope or the path to it (cabling, relay, "
            "switch port)."),
    ),
    Scenario(
        id="gateway",
        title="Can reach the LAN but not the internet",
        brief=("A user can open the local file server but no external sites. "
               "Local DNS resolves fine. Diagnose the break."),
        available=["ping 192.168.1.1", "ping 8.8.8.8", "tracert 8.8.8.8", "ipconfig"],
        commands={
            "ping 192.168.1.1":
                "Reply from 192.168.1.1: bytes=32 time=1ms TTL=64\n"
                "    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)",
            "ping 8.8.8.8":
                "Request timed out.\nRequest timed out.\n"
                "    Packets: Sent = 4, Received = 0, Lost = 4 (100% loss)",
            "tracert 8.8.8.8":
                "  1    1 ms    1 ms    1 ms  192.168.1.1\n"
                "  2     *        *        *     Request timed out.\n"
                "  3     *        *        *     Request timed out.\n"
                "  (continues timing out)",
            "ipconfig":
                "IPv4 Address. . . . . . . . . . . : 192.168.1.50\n"
                "Subnet Mask . . . . . . . . . . . : 255.255.255.0\n"
                "Default Gateway . . . . . . . . . : 192.168.1.1",
        },
        aliases={},
        question="Where is the fault?",
        options=[
            "Beyond the local gateway — upstream routing or the ISP link is down",
            "The host's NIC has failed",
            "DNS resolution is broken",
            "The host is on the wrong VLAN",
        ],
        answer_index=0,
        explanation=(
            "The host reaches its gateway (hop 1 in tracert, ping 192.168.1.1 OK) but "
            "everything past it times out. Local connectivity and the default gateway "
            "are fine; the break is upstream — the router's WAN/uplink or the ISP. "
            "tracert pinpoints exactly where the path dies."),
    ),
    Scenario(
        id="duplex",
        title="Slow, flaky link to one server",
        brief=("Transfers to one server are painfully slow and the connection drops "
               "intermittently. The link shows 'up'. Investigate the switch port."),
        available=["show interface gig0/1", "show interface gig0/1 counters", "ping 10.0.0.5"],
        commands={
            "show interface gig0/1":
                "GigabitEthernet0/1 is up, line protocol is up\n"
                "  Full-duplex is DISABLED, Half-duplex, 100Mb/s\n"
                "  input errors 0, CRC 0\n"
                "  late collisions 1422, output errors 1422",
            "show interface gig0/1 counters":
                "  Align-Err  FCS-Err  Runts  Late-Coll  Excess-Coll\n"
                "  0          2841     193    1422       318",
            "ping 10.0.0.5":
                "Reply from 10.0.0.5: time=2ms\nRequest timed out.\n"
                "Reply from 10.0.0.5: time=47ms\nRequest timed out.\n"
                "    Packets: Sent = 4, Received = 2, Lost = 2 (50% loss)",
        },
        aliases={"show int gig0/1": "show interface gig0/1"},
        question="What is the root cause?",
        options=[
            "A duplex mismatch (one side full, the other half-duplex)",
            "The cable is completely severed",
            "An IP address conflict",
            "The switch port is administratively shut down",
        ],
        answer_index=0,
        explanation=(
            "Late collisions plus FCS/CRC errors plus half-duplex on one end while the "
            "other expects full-duplex is the textbook signature of a DUPLEX MISMATCH. "
            "It causes slowness and intermittent loss, not a hard down. Fix: set both "
            "ends to the same duplex (or both to autonegotiate)."),
    ),
]


def get_scenario(scenario_id: str):
    return next((s for s in SCENARIOS if s.id == scenario_id), None)
