"""Disjoint-Set Union (Union-Find) with path compression and union by rank.

Kruskal's algorithm needs a near-constant-time way to ask "are these two
camps already in the same partially-built network?" -- that's exactly what
this structure provides, in O(alpha(n)) amortised time per operation.
"""

from __future__ import annotations

from typing import Dict, Iterable


class UnionFind:
    def __init__(self, items: Iterable[str]) -> None:
        self._parent: Dict[str, str] = {x: x for x in items}
        self._rank: Dict[str, int] = {x: 0 for x in items}

    def find(self, x: str) -> str:
        # Path compression: point every visited node directly at the root.
        root = x
        while self._parent[root] != root:
            root = self._parent[root]
        while self._parent[x] != root:
            self._parent[x], x = root, self._parent[x]
        return root

    def union(self, a: str, b: str) -> bool:
        """Merge the sets containing a and b. Returns False if they were
        already in the same set (i.e. adding edge (a, b) would form a
        cycle)."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        # Union by rank keeps the resulting trees shallow.
        if self._rank[ra] < self._rank[rb]:
            ra, rb = rb, ra
        self._parent[rb] = ra
        if self._rank[ra] == self._rank[rb]:
            self._rank[ra] += 1
        return True

    def connected(self, a: str, b: str) -> bool:
        return self.find(a) == self.find(b)
