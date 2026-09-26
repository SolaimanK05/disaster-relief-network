"""Kruskal's algorithm: cheapest backbone network connecting every camp.

Complexity: O(E log E) for sorting the candidate links plus O(E * alpha(V))
for the union-find operations, i.e. O(E log E) overall.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .graph import Edge, Graph
from .sorting import merge_sort
from .union_find import UnionFind


@dataclass
class MSTResult:
    edges: List[Edge]
    total_cost: float
    is_spanning: bool  # False if the candidate graph was already disconnected


def kruskal_mst(graph: Graph) -> MSTResult:
    nodes = graph.nodes
    candidate_edges = merge_sort(graph.edges(), key=lambda e: e.cost)

    uf = UnionFind(nodes)
    chosen: List[Edge] = []
    total_cost = 0.0

    for edge in candidate_edges:
        if uf.union(edge.u, edge.v):
            chosen.append(edge)
            total_cost += edge.cost
            if len(chosen) == len(nodes) - 1:
                break

    is_spanning = len(chosen) == len(nodes) - 1
    return MSTResult(edges=chosen, total_cost=total_cost, is_spanning=is_spanning)
