"""Greedy fault-tolerance augmentation.

A pure MST connects every camp at minimum cost, but it is a tree: losing
*any single* relay link disconnects part of the network (Problem
Description, paragraph 2: "the network must survive partial failures ...
without cutting off entire camps"). This directly implements the P2
conflicting-requirements trade-off named in the report: minimising cost
(favours a bare MST) versus fault tolerance (favours extra redundant
links).

Strategy: a greedy benchmark/fallback augmentation. Starting from the MST,
repeatedly add the cheapest remaining candidate edge that raises the
minimum node degree of the network, until every node has degree >= 2 (so a
single link failure can no longer isolate a camp) or the redundancy budget
is exhausted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .graph import Edge, Graph
from .sorting import merge_sort


@dataclass
class RedundancyResult:
    added_edges: List[Edge]
    added_cost: float
    min_degree_before: int
    min_degree_after: int


def _degree(graph: Graph, node: str) -> int:
    return len(list(graph.neighbours(node)))


def _min_degree(graph: Graph) -> int:
    if not graph.nodes:
        return 0
    return min(_degree(graph, n) for n in graph.nodes)


def augment_for_fault_tolerance(
    active: Graph,
    all_candidates: Graph,
    max_extra_links: Optional[int] = None,
    max_extra_cost: Optional[float] = None,
) -> RedundancyResult:
    """Mutates ``active`` in place, adding cheap redundant links from
    ``all_candidates`` until every camp has at least 2 independent links
    (degree >= 2), or a budget limit is hit first.
    """
    min_degree_before = _min_degree(active)

    remaining = [
        e
        for e in all_candidates.edges()
        if not active.has_edge(e.u, e.v)
    ]
    remaining = merge_sort(remaining, key=lambda e: e.cost)

    added: List[Edge] = []
    added_cost = 0.0

    for edge in remaining:
        if max_extra_links is not None and len(added) >= max_extra_links:
            break
        if max_extra_cost is not None and added_cost + edge.cost > max_extra_cost:
            continue
        deg_u = _degree(active, edge.u)
        deg_v = _degree(active, edge.v)
        if deg_u < 2 or deg_v < 2:
            active.add_edge(edge.u, edge.v, edge.cost, edge.delay)
            added.append(edge)
            added_cost += edge.cost
        if _min_degree(active) >= 2:
            break

    return RedundancyResult(
        added_edges=added,
        added_cost=added_cost,
        min_degree_before=min_degree_before,
        min_degree_after=_min_degree(active),
    )
