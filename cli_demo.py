#!/usr/bin/env python3
"""
Scripted, narrated command-line walkthrough of the full solution.

Run this for a quick, reproducible end-to-end demonstration (also useful
as the voice-over script / on-screen output for the assignment's demo
video, alongside or instead of the GUI):

    python cli_demo.py
"""

from __future__ import annotations

from data.camps import build_candidate_graph, camp_label, CONTROL_CENTRE
from network.mst import kruskal_mst
from network.traversal import connected_components, isolated_camps
from network.redundancy import augment_for_fault_tolerance
from network.simulation import simulate_link_failure, apply_link_failure
from network.dijkstra import shortest_path


def line(char: str = "-", n: int = 72) -> None:
    print(char * n)


def header(title: str) -> None:
    line("=")
    print(title)
    line("=")


def main() -> None:
    header("STEP 0 - Load candidate network")
    candidates = build_candidate_graph()
    print(f"Relief camps: {len(candidates)}")
    print(f"Candidate links (within relay range): {len(candidates.edges())}")

    header("STEP 1 - Sort candidate links by cost, build MST (Kruskal's Algorithm)")
    mst_result = kruskal_mst(candidates)
    print(f"Backbone links selected: {len(mst_result.edges)}")
    print(f"Total installation cost: {mst_result.total_cost:.2f}")
    print(f"Spans every camp: {mst_result.is_spanning}")
    print()
    for e in mst_result.edges:
        print(f"  {e.u:>4} -- {e.v:<4}  cost={e.cost:6.2f}  delay={e.delay:6.2f}ms")

    active = candidates.copy()
    # Reduce 'active' to just the MST edges to start with.
    from network.graph import Graph
    backbone = Graph()
    for cid in candidates.nodes:
        backbone.add_node(cid)
    for e in mst_result.edges:
        backbone.add_edge(e.u, e.v, e.cost, e.delay)

    header("STEP 2 - Verify connectivity (BFS/DFS)")
    comps = connected_components(backbone)
    print(f"Connected components in the MST backbone: {len(comps)} (expect 1)")
    cut_off = isolated_camps(backbone, backbone.nodes, CONTROL_CENTRE)
    print(f"Camps unreachable from control centre right now: {cut_off or 'none'}")

    header("STEP 3 - A bare MST is fault-fragile: simulate one link failure")
    sample_edge = mst_result.edges[len(mst_result.edges) // 2]
    report = simulate_link_failure(backbone, sample_edge.u, sample_edge.v, CONTROL_CENTRE)
    print(f"Simulated failure: {report.failure_description}")
    print(f"Fully connected afterwards? {report.still_fully_connected}")
    print(f"Camps isolated: {report.isolated or 'none'}")

    header("STEP 4 - Add fault-tolerant redundancy (greedy augmentation)")
    resilient = backbone.copy()
    redundancy = augment_for_fault_tolerance(resilient, candidates)
    print(f"Minimum camp degree before: {redundancy.min_degree_before}")
    print(f"Minimum camp degree after:  {redundancy.min_degree_after}")
    print(f"Extra links added: {len(redundancy.added_edges)}  "
          f"extra cost: {redundancy.added_cost:.2f}")
    total_cost = mst_result.total_cost + redundancy.added_cost
    print(f"Total backbone + redundancy cost: {total_cost:.2f}")

    header("STEP 5 - Re-simulate the same failure on the resilient network")
    report2 = simulate_link_failure(resilient, sample_edge.u, sample_edge.v, CONTROL_CENTRE)
    print(f"Simulated failure: {report2.failure_description}")
    print(f"Fully connected afterwards? {report2.still_fully_connected}")
    print(f"Camps isolated: {report2.isolated or 'none'}")

    header("STEP 6 - Route an emergency message (Dijkstra's Algorithm)")
    source, target = CONTROL_CENTRE, "C6"
    path, total_delay = shortest_path(resilient, source, target)
    print(f"Fastest route {camp_label(source)} -> {camp_label(target)}:")
    if path:
        print("  " + " -> ".join(f"{c}({camp_label(c)})" for c in path))
        print(f"  Total transmission delay: {total_delay:.2f} ms")
    else:
        print("  No route available.")

    header("STEP 7 - Damage a link on that route and re-route dynamically")
    if path and len(path) >= 2:
        u, v = path[0], path[1]
        apply_link_failure(resilient, u, v)
        print(f"Link {u}-{v} has just failed (aftershock).")
        new_path, new_delay = shortest_path(resilient, source, target)
        if new_path:
            print("  New fastest route: " + " -> ".join(new_path))
            print(f"  New total delay: {new_delay:.2f} ms")
        else:
            print("  Target is no longer reachable -- redundancy budget was insufficient.")

    header("Done")
    print("This mirrors the report's algorithmic pipeline:")
    print("  merge sort -> Kruskal's MST -> BFS/DFS verification ->")
    print("  greedy redundancy -> failure simulation -> Dijkstra re-routing.")


if __name__ == "__main__":
    main()
