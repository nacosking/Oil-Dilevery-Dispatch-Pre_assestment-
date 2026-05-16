"""
Task 2: Build the Graph
Task 3: Shortest Path — Dijkstra's Algorithm
"""

import heapq
from typing import Optional
from db import get_roads


# ── Task 2: Build the graph ───────────────────────────────────────────────────

def build_graph() -> dict[int, list[tuple[int, float]]]:
    """
    Load every road from the database and return a bidirectional adjacency list.

    Structure:
        { location_id: [(neighbour_id, distance_km), ...], ... }

    A road A -> B is stored in both directions:
        A -> [(B, dist), ...]
        B -> [(A, dist), ...]
    """
    roads = get_roads()
    graph: dict[int, list[tuple[int, float]]] = {}

    for road in roads:
        a    = road["from_id"]
        b    = road["to_id"]
        dist = road["distance_km"]

        # A -> B
        if a not in graph:
            graph[a] = []
        graph[a].append((b, dist))

        # B -> A (bidirectional)
        if b not in graph:
            graph[b] = []
        graph[b].append((a, dist))

    return graph


# ── Task 3: Dijkstra ──────────────────────────────────────────────────────────

def dijkstra(
    graph: dict[int, list[tuple[int, float]]],
    source: int,
    target: int,
) -> tuple[Optional[list[int]], Optional[float]]:
    """
    Dijkstra's algorithm — finds the shortest path by total distance.

    How it works:
    1. Start at source with cost 0, everything else is infinity
    2. Always expand the cheapest unvisited node first (min-heap)
    3. When we reach the target, walk back through prev to get the path
    4. If target is never reached, return None (unreachable)

    Returns (path, total_distance) or (None, None) if unreachable.
    """
    # Min-heap: (cumulative_distance, current_node)
    heap = [(0.0, source)]

    # Best known distance to each node
    dist: dict[int, float] = {source: 0.0}

    # Track previous node for path reconstruction
    prev: dict[int, Optional[int]] = {source: None}

    visited: set[int] = set()

    while heap:
        current_dist, node = heapq.heappop(heap)

        if node in visited:
            continue
        visited.add(node)

        if node == target:
            return _reconstruct_path(prev, target), round(current_dist, 4)

        for neighbour, edge_dist in graph.get(node, []):
            if neighbour in visited:
                continue
            new_dist = current_dist + edge_dist
            if new_dist < dist.get(neighbour, float("inf")):
                dist[neighbour] = new_dist
                prev[neighbour] = node
                heapq.heappush(heap, (new_dist, neighbour))

    return None, None  # unreachable


# ── Shared helpers ────────────────────────────────────────────────────────────

def _reconstruct_path(
    prev: dict[int, Optional[int]], target: int
) -> list[int]:
    """Walk the prev map backwards from target to source, then reverse."""
    path = []
    cursor: Optional[int] = target
    while cursor is not None:
        path.append(cursor)
        cursor = prev[cursor]
    path.reverse()
    return path


def find_unreachable_customers(
    graph: dict[int, list[tuple[int, float]]],
    depot_id: int,
    customer_ids: list[int],
) -> list[int]:
    """
    Return customer IDs that have no path from the depot.
    Uses Dijkstra — correct even for isolated clusters with roads between them.
    """
    unreachable = []
    for cid in customer_ids:
        path, _ = dijkstra(graph, depot_id, cid)
        if path is None:
            unreachable.append(cid)
    return unreachable