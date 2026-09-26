"""Sample relief-camp dataset.

Scenario: a cluster of temporary relief camps set up after severe monsoon
flooding in the Sylhet-Sunamganj haor region of Bangladesh (the same
disaster context referenced in the group's Assignment-3 reports). Camp
positions are relative (x, y) coordinates in kilometres, used only to make
the demo visualisation intuitive -- the algorithms themselves only see the
graph of candidate links.

Candidate-link installation cost is modelled as:

    cost = distance_km * terrain_difficulty_factor

and transmission delay (ms) as:

    delay = distance_km * link_quality_factor

Both numbers are illustrative, not measured field data -- exactly the kind
of synthetic-but-structurally-realistic dataset expected for a course
assignment demo.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

from network.graph import Graph

# camp_id -> (x_km, y_km, display_name)
CAMPS: Dict[str, Tuple[float, float, str]] = {
    "C0": (0.0, 0.0, "Control Centre (Sunamganj Town)"),
    "C1": (3.0, 1.5, "Tahirpur Camp"),
    "C2": (5.5, 4.0, "Dowarabazar Camp"),
    "C3": (-2.5, 3.0, "Jamalganj Camp"),
    "C4": (-4.0, 6.5, "Bishwamvarpur Camp"),
    "C5": (2.0, 6.0, "Dharmapasha Camp"),
    "C6": (6.5, 7.5, "Derai Camp"),
    "C7": (-1.0, -3.0, "Chhatak Camp"),
    "C8": (4.0, -2.0, "Sullah Camp"),
    "C9": (-5.5, -1.0, "Doarabazar Char Camp"),
    "C10": (8.0, 2.0, "Bishwanath Camp"),
    "C11": (-3.0, -5.0, "South Sunamganj Camp"),
}

CONTROL_CENTRE = "C0"

# Terrain difficulty multiplier per link: haor (wetland) crossings and
# char (river-island) links are more expensive to install than links that
# stay on higher, more accessible ground.
_HARD_TERRAIN_EDGES = {
    ("C3", "C4"), ("C4", "C5"), ("C9", "C11"), ("C7", "C11"), ("C1", "C2"),
}


def _distance(a: str, b: str) -> float:
    ax, ay, _ = CAMPS[a]
    bx, by, _ = CAMPS[b]
    return math.hypot(ax - bx, ay - by)


def build_candidate_graph(max_link_range_km: float = 7.5) -> Graph:
    """Every pair of camps within ``max_link_range_km`` of each other is a
    candidate link (a relay can't usefully bridge an arbitrarily long
    distance). Returns the *full* candidate graph -- Kruskal's algorithm
    then picks the cheapest subset that spans it.
    """
    graph = Graph()
    ids = list(CAMPS.keys())
    for cid in ids:
        graph.add_node(cid)

    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            dist = _distance(a, b)
            if dist > max_link_range_km:
                continue
            key = (a, b) if (a, b) in _HARD_TERRAIN_EDGES else (b, a)
            terrain_factor = 2.2 if key in _HARD_TERRAIN_EDGES or (b, a) in _HARD_TERRAIN_EDGES else 1.0
            cost = round(dist * (1.4 + terrain_factor), 2)
            delay = round(dist * 3.0, 2)  # ms per km, illustrative
            graph.add_edge(a, b, cost=cost, delay=delay)

    return graph


def camp_label(cid: str) -> str:
    return CAMPS[cid][2]


def camp_position(cid: str) -> Tuple[float, float]:
    x, y, _ = CAMPS[cid]
    return x, y


def all_camp_ids() -> List[str]:
    return list(CAMPS.keys())
