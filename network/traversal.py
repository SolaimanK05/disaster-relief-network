"""BFS and DFS for connectivity verification and failure detection.

After the backbone is built (or after a simulated relay/link failure), we
need to answer: "is every camp still reachable from every other camp, and
if not, which camps got cut off?" Both traversals answer this in O(V + E).
"""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Set

from .graph import Graph


def bfs(graph: Graph, start: str) -> List[str]:
    """Breadth-first traversal order starting at ``start``."""
    if start not in graph.nodes:
        return []
    visited: Set[str] = {start}
    order: List[str] = []
    queue = deque([start])
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbour in sorted(graph.neighbours(node)):
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append(neighbour)
    return order


def dfs(graph: Graph, start: str) -> List[str]:
    """Depth-first traversal order starting at ``start`` (iterative, to
    avoid Python recursion-depth limits on larger networks)."""
    if start not in graph.nodes:
        return []
    visited: Set[str] = set()
    order: List[str] = []
    stack = [start]
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        for neighbour in sorted(graph.neighbours(node), reverse=True):
            if neighbour not in visited:
                stack.append(neighbour)
    return order


def connected_components(graph: Graph) -> List[Set[str]]:
    seen: Set[str] = set()
    components: List[Set[str]] = []
    for node in graph.nodes:
        if node in seen:
            continue
        reached = set(bfs(graph, node))
        seen |= reached
        components.append(reached)
    return components


def reachable_from(graph: Graph, start: str) -> Set[str]:
    return set(bfs(graph, start))


def isolated_camps(graph: Graph, all_camps: List[str], reference: str) -> List[str]:
    """Camps that exist in ``all_camps`` but are no longer reachable from
    ``reference`` (e.g. the control centre) -- the direct output of a
    post-failure BFS/DFS check."""
    reachable = reachable_from(graph, reference)
    return sorted(c for c in all_camps if c not in reachable)
