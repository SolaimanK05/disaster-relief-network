"""Unit tests validating each algorithm against known-correct results.

Run with:
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest

from network.graph import Graph
from network.sorting import merge_sort
from network.union_find import UnionFind
from network.mst import kruskal_mst
from network.traversal import bfs, dfs, connected_components, isolated_camps
from network.dijkstra import dijkstra, shortest_path
from network.redundancy import augment_for_fault_tolerance
from network.simulation import simulate_link_failure, simulate_tower_failure


class TestMergeSort(unittest.TestCase):
    def test_sorts_ascending(self):
        data = [5, 3, 8, 1, 9, 2]
        self.assertEqual(merge_sort(data, key=lambda x: x), [1, 2, 3, 5, 8, 9])

    def test_empty_and_single(self):
        self.assertEqual(merge_sort([], key=lambda x: x), [])
        self.assertEqual(merge_sort([7], key=lambda x: x), [7])

    def test_stable_and_matches_builtin(self):
        import random

        data = [random.randint(0, 50) for _ in range(200)]
        self.assertEqual(merge_sort(data, key=lambda x: x), sorted(data))


class TestUnionFind(unittest.TestCase):
    def test_union_and_find(self):
        uf = UnionFind(["a", "b", "c", "d"])
        self.assertTrue(uf.union("a", "b"))
        self.assertTrue(uf.connected("a", "b"))
        self.assertFalse(uf.connected("a", "c"))
        self.assertFalse(uf.union("a", "b"))  # already connected -> cycle
        uf.union("c", "d")
        uf.union("b", "c")
        self.assertTrue(uf.connected("a", "d"))


class TestKruskalMST(unittest.TestCase):
    def _small_graph(self) -> Graph:
        # classic textbook example with a known-optimal MST cost
        g = Graph()
        edges = [
            ("A", "B", 4), ("A", "C", 1), ("B", "C", 2),
            ("B", "D", 5), ("C", "D", 8), ("C", "E", 10),
            ("D", "E", 2), ("D", "F", 6), ("E", "F", 3),
        ]
        for u, v, w in edges:
            g.add_edge(u, v, cost=w, delay=w)
        return g

    def test_mst_is_spanning_and_minimum(self):
        g = self._small_graph()
        result = kruskal_mst(g)
        self.assertTrue(result.is_spanning)
        self.assertEqual(len(result.edges), len(g.nodes) - 1)
        # Known optimum for this graph: A-C(1), B-C(2), D-E(2), E-F(3), B-D(5)
        # -- verified by brute-force enumeration of all spanning trees.
        self.assertAlmostEqual(result.total_cost, 1 + 2 + 2 + 3 + 5)

    def test_disconnected_graph_reports_not_spanning(self):
        g = Graph()
        g.add_edge("A", "B", cost=1, delay=1)
        g.add_node("Z")  # isolated
        result = kruskal_mst(g)
        self.assertFalse(result.is_spanning)


class TestTraversal(unittest.TestCase):
    def _chain_graph(self) -> Graph:
        g = Graph()
        for a, b in [("A", "B"), ("B", "C"), ("C", "D")]:
            g.add_edge(a, b, cost=1, delay=1)
        return g

    def test_bfs_dfs_visit_all_nodes(self):
        g = self._chain_graph()
        self.assertEqual(set(bfs(g, "A")), {"A", "B", "C", "D"})
        self.assertEqual(set(dfs(g, "A")), {"A", "B", "C", "D"})

    def test_connected_components(self):
        g = self._chain_graph()
        g.add_edge("X", "Y", cost=1, delay=1)  # separate component
        comps = connected_components(g)
        self.assertEqual(len(comps), 2)

    def test_isolated_camps_after_cut(self):
        g = self._chain_graph()
        g.remove_edge("B", "C")
        cut_off = isolated_camps(g, g.nodes, "A")
        self.assertEqual(cut_off, ["C", "D"])


class TestDijkstra(unittest.TestCase):
    def test_shortest_path_matches_manual_calc(self):
        g = Graph()
        g.add_edge("A", "B", cost=1, delay=1)
        g.add_edge("B", "C", cost=1, delay=2)
        g.add_edge("A", "C", cost=1, delay=10)  # longer direct route
        path, total = shortest_path(g, "A", "C")
        self.assertEqual(path, ["A", "B", "C"])
        self.assertAlmostEqual(total, 3)

    def test_unreachable_target(self):
        g = Graph()
        g.add_edge("A", "B", cost=1, delay=1)
        g.add_node("Z")
        path, total = shortest_path(g, "A", "Z")
        self.assertIsNone(path)
        self.assertEqual(total, float("inf"))


class TestRedundancyAndSimulation(unittest.TestCase):
    def test_augmentation_raises_min_degree(self):
        candidates = Graph()
        # square with both diagonals as extra candidates
        for u, v in [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"), ("A", "C"), ("B", "D")]:
            candidates.add_edge(u, v, cost=1, delay=1)

        mst = kruskal_mst(candidates)
        backbone = Graph()
        for n in candidates.nodes:
            backbone.add_node(n)
        for e in mst.edges:
            backbone.add_edge(e.u, e.v, e.cost, e.delay)

        result = augment_for_fault_tolerance(backbone, candidates)
        self.assertGreaterEqual(result.min_degree_after, 2)

    def test_link_failure_isolates_leaf_in_tree(self):
        g = Graph()
        g.add_edge("root", "mid", cost=1, delay=1)
        g.add_edge("mid", "leaf", cost=1, delay=1)
        report = simulate_link_failure(g, "mid", "leaf", "root")
        self.assertFalse(report.still_fully_connected)
        self.assertEqual(report.isolated, ["leaf"])

    def test_tower_failure_isolates_its_subtree(self):
        g = Graph()
        g.add_edge("root", "mid", cost=1, delay=1)
        g.add_edge("mid", "leaf", cost=1, delay=1)
        report = simulate_tower_failure(g, "mid", "root")
        self.assertFalse(report.still_fully_connected)
        self.assertEqual(report.isolated, ["leaf"])


if __name__ == "__main__":
    unittest.main()
