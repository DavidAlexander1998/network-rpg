"""Subnetting problem generator — unlimited fresh practice.

Subnetting is a *skill*, not a fact: you get fluent by doing many varied reps,
not by reading one worked example. This module generates randomized
multiple-choice subnetting questions across the question styles the N10-009
exam actually uses, each with plausible (not random) distractors built from the
classic mistakes — off-by-one boundaries, wrong block size, forgetting the −2,
mixing up mask and wildcard.

Generated problems are returned as `Encounter` objects so they flow through the
same quiz UI as the rest of the game, but they carry the id ``"subnet-gen"`` and
are intentionally *not* recorded into mastery/SR (they're ephemeral by design).
"""

import ipaddress
import random
from typing import List, Tuple, Optional

from game.encounter import Encounter

GEN_ID = "subnet-gen"

# Prefixes that produce interesting host-level boundaries (the exam's bread & butter).
_HOST_PREFIXES = [24, 25, 26, 27, 28, 29, 30]
_MIXED_PREFIXES = [16, 17, 18, 20, 22, 23, 24, 25, 26, 27, 28, 29, 30]


def _rand_ip(rng: random.Random) -> str:
    first = rng.choice([10, 172, 192, rng.randint(1, 223)])
    if first == 172:
        second = rng.randint(16, 31)
    elif first == 192:
        second = 168
    else:
        second = rng.randint(0, 255)
    return f"{first}.{second}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"


def _addr(base: ipaddress.IPv4Address, offset: int) -> str:
    try:
        return str(ipaddress.IPv4Address(int(base) + offset))
    except ipaddress.AddressValueError:
        return str(base)


def _finalize(question: str, correct: str, distractors: List[str], explanation: str,
              tags: List[str]) -> Encounter:
    """Assemble a 4-option Encounter, dedupe distractors, shuffle positions."""
    options = [correct]
    for d in distractors:
        if d not in options:
            options.append(d)
        if len(options) == 4:
            break
    # Pad if a distractor collided with the correct answer.
    pad = 0
    while len(options) < 4:
        filler = f"{correct} (option {pad})"
        if filler not in options:
            options.append(filler)
        pad += 1

    enc = Encounter(
        id=GEN_ID,
        question=question,
        options=options,
        correct_index=0,
        explanation=explanation,
        xp_reward=25,
        bits_reward=10,
        difficulty="medium",
        encounter_type="subnet",
        zone=1,
        node=1.7,
        tags=tags,
    )
    enc.shuffle_options()
    return enc


def _gen_network_address(rng: random.Random) -> Encounter:
    prefix = rng.choice(_HOST_PREFIXES)
    ip = _rand_ip(rng)
    net = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
    block = net.num_addresses
    correct = str(net.network_address)
    distractors = [
        str(net.broadcast_address),                 # confused broadcast for network
        _addr(net.network_address, 1),              # off-by-one (first host)
        _addr(net.network_address, block),          # next subnet's network
    ]
    explanation = (
        f"{ip}/{prefix}: block size = {block} addresses. The network address is the "
        f"lowest address in the block that {ip.rsplit('.',1)[0]}.x falls into → "
        f"{correct}. Broadcast is {net.broadcast_address}."
    )
    return _finalize(
        f"Host {ip}/{prefix} belongs to which network (subnet) address?",
        correct, distractors, explanation, ["subnetting", "network-address"],
    )


def _gen_broadcast(rng: random.Random) -> Encounter:
    prefix = rng.choice(_HOST_PREFIXES)
    ip = _rand_ip(rng)
    net = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
    block = net.num_addresses
    correct = str(net.broadcast_address)
    distractors = [
        str(net.network_address),
        _addr(net.broadcast_address, -1),           # last usable host
        _addr(net.broadcast_address, 1),            # next subnet's network
    ]
    explanation = (
        f"{ip}/{prefix}: block size = {block}. Broadcast is the highest address in the "
        f"block → {correct}. The next subnet starts at {_addr(net.broadcast_address, 1)}."
    )
    return _finalize(
        f"What is the broadcast address for {ip}/{prefix}?",
        correct, distractors, explanation, ["subnetting", "broadcast"],
    )


def _gen_usable_hosts(rng: random.Random) -> Encounter:
    prefix = rng.choice(_HOST_PREFIXES)
    total = 2 ** (32 - prefix)
    usable = total - 2 if prefix <= 30 else total
    correct = str(usable)
    distractors = [str(total), str(total - 1), str(max(0, usable - 2))]
    explanation = (
        f"/{prefix} has {32 - prefix} host bits → 2^{32 - prefix} = {total} total addresses. "
        f"Subtract 2 (network + broadcast) → {usable} usable hosts."
    )
    return _finalize(
        f"How many usable host addresses does a /{prefix} subnet provide?",
        correct, distractors, explanation, ["subnetting", "host-count"],
    )


def _gen_cidr_to_mask(rng: random.Random) -> Encounter:
    prefix = rng.choice(_MIXED_PREFIXES)
    net = ipaddress.ip_network(f"0.0.0.0/{prefix}")
    correct = str(net.netmask)
    distractors = [
        str(ipaddress.ip_network(f"0.0.0.0/{min(32, prefix + 1)}").netmask),
        str(ipaddress.ip_network(f"0.0.0.0/{max(1, prefix - 1)}").netmask),
        str(net.hostmask),                          # wildcard mask (classic ACL confusion)
    ]
    explanation = (
        f"/{prefix} means the first {prefix} bits are network bits → subnet mask {correct}. "
        f"({net.hostmask} is the wildcard/inverse mask used in ACLs.)"
    )
    return _finalize(
        f"What subnet mask corresponds to /{prefix}?",
        correct, distractors, explanation, ["subnetting", "cidr", "mask"],
    )


def _gen_mask_to_cidr(rng: random.Random) -> Encounter:
    prefix = rng.choice(_MIXED_PREFIXES)
    net = ipaddress.ip_network(f"0.0.0.0/{prefix}")
    mask = str(net.netmask)
    correct = f"/{prefix}"
    distractors = [f"/{min(32, prefix + 1)}", f"/{max(1, prefix - 1)}", f"/{prefix + 2 if prefix + 2 <= 32 else prefix - 2}"]
    explanation = (
        f"Mask {mask} has {prefix} contiguous 1-bits → CIDR /{prefix}."
    )
    return _finalize(
        f"What CIDR prefix matches the subnet mask {mask}?",
        correct, distractors, explanation, ["subnetting", "cidr", "mask"],
    )


def _gen_prefix_for_hosts(rng: random.Random) -> Encounter:
    prefix = rng.choice([24, 25, 26, 27, 28, 29])
    capacity = 2 ** (32 - prefix) - 2
    # Ask for the smallest subnet that still fits a host count just under capacity.
    needed = rng.randint(max(2, capacity // 2 + 1), capacity)
    correct = f"/{prefix}"
    distractors = [f"/{prefix + 1}", f"/{prefix - 1}", f"/{prefix + 2}"]
    explanation = (
        f"/{prefix} provides {capacity} usable hosts (2^{32 - prefix} − 2). A /{prefix + 1} "
        f"only gives {2 ** (32 - (prefix + 1)) - 2}, too few for {needed}. So /{prefix} is the "
        f"smallest subnet that fits {needed} hosts."
    )
    return _finalize(
        f"You need at least {needed} usable hosts on a subnet. What is the SMALLEST "
        f"subnet (largest prefix) that fits them?",
        correct, distractors, explanation, ["subnetting", "host-count", "prefix"],
    )


def _gen_usable_range(rng: random.Random) -> Encounter:
    prefix = rng.choice([25, 26, 27, 28, 29])
    ip = _rand_ip(rng)
    net = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
    first = _addr(net.network_address, 1)
    last = _addr(net.broadcast_address, -1)
    correct = f"{first} – {last}"
    distractors = [
        f"{net.network_address} – {net.broadcast_address}",   # included net+broadcast
        f"{first} – {net.broadcast_address}",                  # included broadcast
        f"{net.network_address} – {last}",                     # included network
    ]
    explanation = (
        f"{ip}/{prefix}: network {net.network_address}, broadcast {net.broadcast_address}. "
        f"Usable hosts are everything between them → {correct}."
    )
    return _finalize(
        f"What is the usable host range for {ip}/{prefix}?",
        correct, distractors, explanation, ["subnetting", "host-range"],
    )


_GENERATORS = [
    _gen_network_address,
    _gen_broadcast,
    _gen_usable_hosts,
    _gen_cidr_to_mask,
    _gen_mask_to_cidr,
    _gen_prefix_for_hosts,
    _gen_usable_range,
]


def generate_problem(rng: Optional[random.Random] = None) -> Encounter:
    rng = rng or random
    return rng.choice(_GENERATORS)(rng)


def generate_set(n: int, rng: Optional[random.Random] = None) -> List[Encounter]:
    return [generate_problem(rng) for _ in range(n)]
