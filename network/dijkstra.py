"""Dijkstra's algorithm: fastest (lowest-delay) route for an emergency
message or supply-convoy instruction between any two camps.

Implemented with a binary heap (``heapq``) as the priority queue, giving
O((V + E) log V) time -- the standard, industry-practice implementation for
non-negative edge weights. Edge weight here is transmission *delay*, not
installation cost, since routing cares about speed, not the one-off price
of the link.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .graph import Graph


@dataclass
class ShortestPathResult:
    distances: Dict[str, float]
    previous: Dict[str, Optional[str]]
    source: str

    def path_to(self, target: str) -> Optional[List[str]]:
        if target not in self.distances or self.distances[target] == float("inf"):
            return None
        path = [target]
        while path[-1] != self.source:
            prev = self.previous[path[-1]]
            if prev is None:
                return None
            path.append(prev)
        path.reverse()
        return path


def dijkstra(graph: Graph, source: str) -> ShortestPathResult:
    distances: Dict[str, float] = {node: float("inf") for node in graph.nodes}
    previous: Dict[str, Optional[str]] = {node: None for node in graph.nodes}
    distances[source] = 0.0

    visited = set()
    heap: List[tuple] = [(0.0, source)]

    while heap:
        dist_u, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)

        for v in graph.neighbours(u):
            if v in visited:
                continue
            edge = graph.edge(u, v)
            candidate = dist_u + edge.delay
            if candidate < distances[v]:
                distances[v] = candidate
                previous[v] = u
                heapq.heappush(heap, (candidate, v))

    return ShortestPathResult(distances=distances, previous=previous, source=source)


def shortest_path(graph: Graph, source: str, target: str):
    """Convenience wrapper: returns (path, total_delay) or (None, inf)."""
    result = dijkstra(graph, source)
    path = result.path_to(target)
    total = result.distances.get(target, float("inf"))
    return path, total
