#!/usr/bin/env python3
"""
Interactive Tkinter visualizer for the Disaster-Relief Communication
Network solution.

Uses only the Python standard library (Tkinter ships with every standard
Python install on Windows/macOS/Linux), so it runs with zero extra
dependencies -- ideal for recording the assignment's demo video.

Run:
    python gui_app.py

The window opens maximized. Press F11 to toggle true fullscreen (borderless),
and Escape to exit fullscreen. The map canvas resizes with the window.

Suggested video walkthrough:
    1. Launch -> candidate network is drawn (grey links).
    2. Click "1. Build MST (Kruskal)" -> cheapest backbone drawn in green,
       cost shown.
    3. Click "2. Verify Connectivity (BFS/DFS)" -> status panel confirms
       every camp is reachable.
    4. Click "3. Simulate Link Failure" then click any GREEN link on the
       canvas -> it turns red, and any camp cut off turns red too.
    5. Click "Reset" then "4. Add Redundancy" -> extra blue dashed links
       appear; repeat the same failure -> network stays connected.
    6. Pick a source/target camp in the dropdowns and click
       "5. Find Fastest Route (Dijkstra)" -> path highlighted in orange
       with total delay shown.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Tuple

from data.camps import build_candidate_graph, camp_label, camp_position, all_camp_ids, CONTROL_CENTRE
from network.graph import Graph, Edge
from network.mst import kruskal_mst
from network.traversal import connected_components, isolated_camps
from network.redundancy import augment_for_fault_tolerance
from network.simulation import apply_link_failure
from network.dijkstra import shortest_path

INITIAL_CANVAS_W, INITIAL_CANVAS_H = 1100, 760
MARGIN = 80

# Fonts -- bumped up for readability on a maximized / fullscreen window,
# especially useful when screen-recording for the demo video.
FONT_TITLE = ("Segoe UI", 15, "bold")
FONT_SUBTITLE = ("Segoe UI", 11)
FONT_LABEL = ("Segoe UI", 11)
FONT_BUTTON = ("Segoe UI", 11)
FONT_STATUS = ("Consolas", 11)
FONT_NODE_ID = ("Segoe UI", 11, "bold")
FONT_NODE_NAME = ("Segoe UI", 9)


class NetworkApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Disaster-Relief Communication Network - CSE 4403 Assignment 2")
        self.root.minsize(900, 600)

        self.is_fullscreen = False
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<Escape>", self._exit_fullscreen)

        self.candidates: Graph = build_candidate_graph()
        self.active: Optional[Graph] = None
        self.backbone_edges: List[Edge] = []
        self.redundant_edges: List[Edge] = []
        self.failed_edges: List[Tuple[str, str]] = []
        self.highlight_path: List[str] = []
        self.failure_mode = False
        self.screen_pos: Dict[str, Tuple[float, float]] = {}

        self._build_style()
        self._build_layout()
        self._compute_layout(INITIAL_CANVAS_W, INITIAL_CANVAS_H)
        self._draw()

        # Start maximized; fall back gracefully on platforms/window managers
        # that don't support the 'zoomed' state.
        self.root.update_idletasks()
        try:
            self.root.state("zoomed")
        except tk.TclError:
            try:
                self.root.attributes("-zoomed", True)
            except tk.TclError:
                w = self.root.winfo_screenwidth()
                h = self.root.winfo_screenheight()
                self.root.geometry(f"{w}x{h}+0+0")

    # ---------------------------------------------------------------
    def _build_style(self) -> None:
        style = ttk.Style()
        style.configure("TLabel", font=FONT_LABEL)
        style.configure("TButton", font=FONT_BUTTON, padding=6)
        style.configure("TCombobox", font=FONT_LABEL)
        self.root.option_add("*TCombobox*Listbox.font", FONT_LABEL)

    def _toggle_fullscreen(self, event=None) -> None:
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)

    def _exit_fullscreen(self, event=None) -> None:
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.root.attributes("-fullscreen", False)

    # ---------------------------------------------------------------
    def _compute_layout(self, width: int, height: int) -> None:
        xs = [camp_position(c)[0] for c in all_camp_ids()]
        ys = [camp_position(c)[1] for c in all_camp_ids()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        def scale(v, lo, hi, out_lo, out_hi):
            if hi == lo:
                return (out_lo + out_hi) / 2
            return out_lo + (v - lo) / (hi - lo) * (out_hi - out_lo)

        for c in all_camp_ids():
            x, y = camp_position(c)
            sx = scale(x, min_x, max_x, MARGIN, max(width - MARGIN, MARGIN + 1))
            # invert y so "north" is up on screen
            sy = scale(y, min_y, max_y, max(height - MARGIN, MARGIN + 1), MARGIN)
            self.screen_pos[c] = (sx, sy)

    def _on_canvas_resize(self, event) -> None:
        if event.width < 10 or event.height < 10:
            return
        self._compute_layout(event.width, event.height)
        self._draw()

    # ---------------------------------------------------------------
    def _build_layout(self) -> None:
        outer = ttk.Frame(self.root, padding=8)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(outer, width=INITIAL_CANVAS_W, height=INITIAL_CANVAS_H, bg="white",
                                 highlightthickness=1, highlightbackground="#999")
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        side = ttk.Frame(outer, width=360)
        side.grid(row=0, column=1, sticky="ns")
        side.grid_propagate(False)

        ttk.Label(side, text="Disaster-Relief Comm. Network", font=FONT_TITLE).grid(
            row=0, column=0, columnspan=2, pady=(0, 4), sticky="w")
        ttk.Label(side, text="CSE 4403 - Assignment 2", font=FONT_SUBTITLE).grid(
            row=1, column=0, columnspan=2, pady=(0, 12), sticky="w")

        ttk.Button(side, text="1. Build MST (Kruskal's)", command=self.build_mst).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=3)
        ttk.Button(side, text="2. Verify Connectivity (BFS/DFS)", command=self.verify_connectivity).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=3)
        ttk.Button(side, text="3. Add Redundancy (Greedy)", command=self.add_redundancy).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=3)
        self.fail_btn = ttk.Button(side, text="4. Simulate Link Failure (click a link)",
                                    command=self.toggle_failure_mode)
        self.fail_btn.grid(row=5, column=0, columnspan=2, sticky="ew", pady=3)
        ttk.Button(side, text="Reset Network", command=self.reset).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(3, 14))

        ttk.Separator(side, orient="horizontal").grid(row=7, column=0, columnspan=2, sticky="ew", pady=6)

        ttk.Label(side, text="Route an emergency message:", font=FONT_LABEL).grid(
            row=8, column=0, columnspan=2, sticky="w", pady=(8, 4))
        labels = [f"{c} - {camp_label(c)}" for c in all_camp_ids()]
        self.src_var = tk.StringVar(value=labels[0])
        self.dst_var = tk.StringVar(value=labels[-1])
        ttk.Label(side, text="From:", font=FONT_LABEL).grid(row=9, column=0, sticky="w", pady=2)
        ttk.Combobox(side, textvariable=self.src_var, values=labels, width=26,
                     state="readonly", font=FONT_LABEL).grid(row=9, column=1, sticky="ew", pady=2)
        ttk.Label(side, text="To:", font=FONT_LABEL).grid(row=10, column=0, sticky="w", pady=2)
        ttk.Combobox(side, textvariable=self.dst_var, values=labels, width=26,
                     state="readonly", font=FONT_LABEL).grid(row=10, column=1, sticky="ew", pady=2)
        ttk.Button(side, text="5. Find Fastest Route (Dijkstra)", command=self.find_route).grid(
            row=11, column=0, columnspan=2, sticky="ew", pady=(10, 14))

        ttk.Separator(side, orient="horizontal").grid(row=12, column=0, columnspan=2, sticky="ew", pady=6)
        ttk.Label(side, text="Status:", font=FONT_LABEL).grid(row=13, column=0, sticky="w", pady=(8, 4))

        status_frame = ttk.Frame(side)
        status_frame.grid(row=14, column=0, columnspan=2, sticky="nsew")
        side.rowconfigure(14, weight=1)
        side.columnconfigure(1, weight=1)

        scrollbar = ttk.Scrollbar(status_frame)
        scrollbar.pack(side="right", fill="y")
        self.status = tk.Text(status_frame, width=38, height=18, wrap="word", font=FONT_STATUS,
                               yscrollcommand=scrollbar.set)
        self.status.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.status.yview)

        hint = ("Tip: F11 = fullscreen, Esc = exit fullscreen")
        ttk.Label(side, text=hint, font=("Segoe UI", 9), foreground="#666").grid(
            row=15, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self._log("Candidate network loaded.\n"
                   f"{len(self.candidates.nodes)} camps, "
                   f"{len(self.candidates.edges())} candidate links.\n"
                   "Click '1. Build MST' to begin.")

    def _log(self, msg: str) -> None:
        self.status.insert("end", msg + "\n\n")
        self.status.see("end")

    # ---------------------------------------------------------------
    def build_mst(self) -> None:
        result = kruskal_mst(self.candidates)
        self.active = Graph()
        for c in self.candidates.nodes:
            self.active.add_node(c)
        for e in result.edges:
            self.active.add_edge(e.u, e.v, e.cost, e.delay)
        self.backbone_edges = result.edges
        self.redundant_edges = []
        self.failed_edges = []
        self.highlight_path = []
        self._log(f"MST built via Kruskal's algorithm.\n"
                   f"Links: {len(result.edges)}  Total cost: {result.total_cost:.2f}\n"
                   f"Spans all camps: {result.is_spanning}")
        self._draw()

    def verify_connectivity(self) -> None:
        if self.active is None:
            messagebox.showinfo("Info", "Build the MST first.")
            return
        comps = connected_components(self.active)
        cut_off = isolated_camps(self.active, self.active.nodes, CONTROL_CENTRE)
        self._log(f"BFS/DFS connectivity check:\n"
                   f"Connected components: {len(comps)}\n"
                   f"Camps unreachable from control centre: {cut_off or 'none'}")
        self._draw()

    def add_redundancy(self) -> None:
        if self.active is None:
            messagebox.showinfo("Info", "Build the MST first.")
            return
        result = augment_for_fault_tolerance(self.active, self.candidates)
        self.redundant_edges = result.added_edges
        self._log(f"Greedy redundancy augmentation:\n"
                   f"Min camp degree {result.min_degree_before} -> {result.min_degree_after}\n"
                   f"Extra links added: {len(result.added_edges)}  "
                   f"extra cost: {result.added_cost:.2f}")
        self._draw()

    def toggle_failure_mode(self) -> None:
        if self.active is None:
            messagebox.showinfo("Info", "Build the MST first.")
            return
        self.failure_mode = not self.failure_mode
        self.fail_btn.state(["pressed"] if self.failure_mode else ["!pressed"])
        self._log("Click a link on the canvas to simulate its failure."
                   if self.failure_mode else "Failure-selection mode off.")

    def reset(self) -> None:
        self.active = None
        self.backbone_edges = []
        self.redundant_edges = []
        self.failed_edges = []
        self.highlight_path = []
        self.failure_mode = False
        self._log("Network reset.")
        self._draw()

    def find_route(self) -> None:
        if self.active is None:
            messagebox.showinfo("Info", "Build the MST first.")
            return
        src = self.src_var.get().split(" - ")[0]
        dst = self.dst_var.get().split(" - ")[0]
        path, total_delay = shortest_path(self.active, src, dst)
        if not path:
            self._log(f"No route currently exists from {src} to {dst}.")
            self.highlight_path = []
        else:
            self.highlight_path = path
            self._log(f"Dijkstra's shortest (fastest) route:\n"
                       f"{' -> '.join(path)}\n"
                       f"Total transmission delay: {total_delay:.2f} ms")
        self._draw()

    # ---------------------------------------------------------------
    def _on_canvas_click(self, event) -> None:
        if not self.failure_mode or self.active is None:
            return
        click = (event.x, event.y)
        best_edge = None
        best_dist = 12  # px tolerance
        for e in self.active.edges():
            x1, y1 = self.screen_pos[e.u]
            x2, y2 = self.screen_pos[e.v]
            d = self._point_to_segment_dist(click, (x1, y1), (x2, y2))
            if d < best_dist:
                best_dist = d
                best_edge = e
        if best_edge is None:
            return
        apply_link_failure(self.active, best_edge.u, best_edge.v)
        self.failed_edges.append((best_edge.u, best_edge.v))
        cut_off = isolated_camps(self.active, self.active.nodes, CONTROL_CENTRE)
        self._log(f"Simulated failure: link {best_edge.u}-{best_edge.v} down.\n"
                   f"Camps isolated from control centre: {cut_off or 'none'}")
        self._draw()

    @staticmethod
    def _point_to_segment_dist(p, a, b) -> float:
        import math
        px, py = p
        ax, ay = a
        bx, by = b
        dx, dy = bx - ax, by - ay
        if dx == dy == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        proj_x, proj_y = ax + t * dx, ay + t * dy
        return math.hypot(px - proj_x, py - proj_y)

    # ---------------------------------------------------------------
    def _draw(self) -> None:
        self.canvas.delete("all")

        # candidate links (faint grey), only shown before MST is built
        if self.active is None:
            for e in self.candidates.edges():
                self._draw_edge(e.u, e.v, fill="#ddd", width=1)

        # redundant links (blue dashed)
        for e in self.redundant_edges:
            if (e.u, e.v) in self.failed_edges or (e.v, e.u) in self.failed_edges:
                continue
            self._draw_edge(e.u, e.v, fill="#2b6cb0", width=3, dash=(5, 3))

        # backbone links (green), or red if failed
        for e in self.backbone_edges:
            failed = (e.u, e.v) in self.failed_edges or (e.v, e.u) in self.failed_edges
            self._draw_edge(e.u, e.v, fill="#c0392b" if failed else "#27ae60", width=4)

        # highlighted route (orange, on top)
        for a, b in zip(self.highlight_path, self.highlight_path[1:]):
            self._draw_edge(a, b, fill="#e67e22", width=6)

        isolated = set()
        if self.active is not None:
            isolated = set(isolated_camps(self.active, self.active.nodes, CONTROL_CENTRE))

        for c in all_camp_ids():
            x, y = self.screen_pos[c]
            is_control = c == CONTROL_CENTRE
            color = "#8e44ad" if is_control else ("#c0392b" if c in isolated else "#2c3e50")
            r = 20 if is_control else 16
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="white", width=2)
            self.canvas.create_text(x, y, text=c, fill="white", font=FONT_NODE_ID)
            self.canvas.create_text(x, y + r + 14, text=camp_label(c), fill="#333", font=FONT_NODE_NAME)

    def _draw_edge(self, u: str, v: str, **kwargs) -> None:
        x1, y1 = self.screen_pos[u]
        x2, y2 = self.screen_pos[v]
        self.canvas.create_line(x1, y1, x2, y2, **kwargs)


def main() -> None:
    root = tk.Tk()
    NetworkApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
