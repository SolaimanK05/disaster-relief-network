"""Graph representation for the relief-camp communication network.

The graph is undirected and weighted: nodes are relief camps, edges are
candidate wireless-relay / cable links, and each edge carries two
independent weights:

* ``cost``  -- one-off installation cost (used by Kruskal's MST when
  building the cheapest backbone).
* ``delay`` -- current transmission delay in this link (used by Dijkstra
  when routing emergency messages). Delay can change over time as roads
  and relays are damaged or repaired.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple


@dataclass(frozen=True)
class Edge:
    """A candidate link between two camps."""

    u: str
    v: str
    cost: float
    delay: float

    def other(self, node: str) -> str:
        if node == self.u:
            return self.v
        if node == self.v:
            return self.u
        raise ValueError(f"{node!r} is not an endpoint of edge {self!r}")

    def key(self) -> Tuple[str, str]:
        """Undirected, order-independent identity for this edge."""
        return (self.u, self.v) if self.u <= self.v else (self.v, self.u)


class Graph:
    """A simple undirected weighted graph backed by an adjacency list.

    Using an adjacency list (dict of dicts) rather than an adjacency
    matrix keeps memory and traversal cost at O(V + E), which matters
    once the candidate-link set grows beyond a handful of camps.
    """

    def __init__(self) -> None:
        self._nodes: Set[str] = set()
        # adjacency[u][v] -> Edge
        self._adjacency: Dict[str, Dict[str, Edge]] = {}

    # -- construction -----------------------------------------------
    def add_node(self, node: str) -> None:
        if node not in self._nodes:
            self._nodes.add(node)
            self._adjacency[node] = {}

    def add_edge(self, u: str, v: str, cost: float, delay: float) -> None:
        self.add_node(u)
        self.add_node(v)
        edge = Edge(u, v, cost, delay)
        self._adjacency[u][v] = edge
        self._adjacency[v][u] = edge

    def remove_edge(self, u: str, v: str) -> None:
        self._adjacency.get(u, {}).pop(v, None)
        self._adjacency.get(v, {}).pop(u, None)

    def remove_node(self, node: str) -> None:
        """Simulate a relay tower failing: drop the node and every link to it."""
        for neighbour in list(self._adjacency.get(node, {})):
            self.remove_edge(node, neighbour)
        self._adjacency.pop(node, None)
        self._nodes.discard(node)

    def update_delay(self, u: str, v: str, new_delay: float) -> None:
        """Change the transmission delay of an existing link (road/relay repaired
        or degraded)."""
        edge = self._adjacency[u][v]
        replacement = Edge(edge.u, edge.v, edge.cost, new_delay)
        self._adjacency[u][v] = replacement
        self._adjacency[v][u] = replacement

    # -- queries ------------------------------------------------------
    @property
    def nodes(self) -> List[str]:
        return sorted(self._nodes)

    def neighbours(self, node: str) -> Iterable[str]:
        return self._adjacency.get(node, {}).keys()

    def edge(self, u: str, v: str) -> Optional[Edge]:
        return self._adjacency.get(u, {}).get(v)

    def has_edge(self, u: str, v: str) -> bool:
        return v in self._adjacency.get(u, {})

    def edges(self) -> List[Edge]:
        """All edges, each returned exactly once."""
        seen: Set[Tuple[str, str]] = set()
        result: List[Edge] = []
        for u, nbrs in self._adjacency.items():
            for v, edge in nbrs.items():
                k = edge.key()
                if k not in seen:
                    seen.add(k)
                    result.append(edge)
        return result

    def copy(self) -> "Graph":
        g = Graph()
        for node in self._nodes:
            g.add_node(node)
        for edge in self.edges():
            g.add_edge(edge.u, edge.v, edge.cost, edge.delay)
        return g

    def __len__(self) -> int:
        return len(self._nodes)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Graph(nodes={len(self._nodes)}, edges={len(self.edges())})"
