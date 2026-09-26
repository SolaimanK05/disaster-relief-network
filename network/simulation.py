"""Failure simulation: model a relay tower or a single link going down
(aftershock, bad weather) and check, via BFS/DFS, which camps -- if any --
get cut off from the control centre.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .graph import Graph
from .traversal import isolated_camps


@dataclass
class FailureReport:
    failure_description: str
    isolated: List[str]
    still_fully_connected: bool


def simulate_link_failure(
    graph: Graph, u: str, v: str, control_centre: str
) -> FailureReport:
    working = graph.copy()
    working.remove_edge(u, v)
    all_camps = graph.nodes
    cut_off = isolated_camps(working, all_camps, control_centre)
    return FailureReport(
        failure_description=f"link {u}-{v} down",
        isolated=cut_off,
        still_fully_connected=not cut_off,
    )


def simulate_tower_failure(
    graph: Graph, node: str, control_centre: str
) -> FailureReport:
    working = graph.copy()
    all_camps = [n for n in graph.nodes if n != node]
    working.remove_node(node)
    cut_off = isolated_camps(working, all_camps, control_centre)
    return FailureReport(
        failure_description=f"relay tower {node} down",
        isolated=cut_off,
        still_fully_connected=not cut_off,
    )


def apply_link_failure(graph: Graph, u: str, v: str) -> None:
    """Mutates ``graph`` in place -- used when the GUI/demo wants the
    failure to persist for subsequent routing queries."""
    graph.remove_edge(u, v)


def apply_tower_failure(graph: Graph, node: str) -> None:
    graph.remove_node(node)
