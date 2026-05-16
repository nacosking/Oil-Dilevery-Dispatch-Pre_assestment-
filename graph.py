"""
Task 2: Build the Graph
Task 3: Shortest Path — both Dijkstra and A*
"""

import heapq
import math
from typing import Optional
from db import get_roads, get_all_locations


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


def build_coord_map() -> dict[int, tuple[float, float]]:
    """
    Return a map of { location_id: (lat, lng) } for all locations.
    Used by A* as the heuristic source.
    """
    locations = get_all_locations()
    return {
        loc["id"]: (loc["lat"], loc["lng"])
        for loc in locations
        if loc["lat"] is not None and loc["lng"] is not None
    }


# ── Task 3a: Dijkstra ─────────────────────────────────────────────────────────

def dijkstra(
    graph: dict[int, list[tuple[int, float]]],
    source: int,
    target: int,
) -> tuple[Optional[list[int]], Optional[float]]:
    """
    Dijkstra's algorithm — explores all directions equally by lowest cost.
    Guaranteed to find the shortest path on any non-negative weighted graph.

    Best when: no coordinates available, or all edge weights are similar.

    Returns (path, total_distance) or (None, None) if unreachable.
    """
    # Min-heap: (cumulative_distance, current_node)
    heap = [(0.0, source)]

    # Best known distance to each node
    dist  = {source: 0.0}

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


# ── Task 3b: A* ───────────────────────────────────────────────────────────────

def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Straight-line distance between two GPS coordinates in kilometres.
    Used as the A* heuristic — it never overestimates real road distance,
    so A* is guaranteed to find the optimal path (admissible heuristic).
    """
    R = 6371  # Earth radius in km
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(d_lng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def astar(
    graph: dict[int, list[tuple[int, float]]],
    coord_map: dict[int, tuple[float, float]],
    source: int,
    target: int,
) -> tuple[Optional[list[int]], Optional[float]]:
    """
    A* algorithm — uses straight-line (haversine) distance as a heuristic
    to guide the search toward the target, skipping unlikely directions.

    Faster than Dijkstra in practice because it expands fewer nodes.
    Falls back to Dijkstra behaviour (h=0) if coordinates are missing.

    Returns (path, total_distance) or (None, None) if unreachable.
    """
    def h(node: int) -> float:
        """Heuristic: straight-line km from node to target."""
        if node not in coord_map or target not in coord_map:
            return 0.0  # fallback: behaves like Dijkstra
        lat1, lng1 = coord_map[node]
        lat2, lng2 = coord_map[target]
        return _haversine(lat1, lng1, lat2, lng2)

    # Min-heap: (f_score, g_score, node)
    # f = g + h  where g = actual cost so far, h = estimated cost to target
    start_h = h(source)
    heap = [(start_h, 0.0, source)]

    # Best actual cost (g) to reach each node
    g_score: dict[int, float] = {source: 0.0}

    # Track previous node for path reconstruction
    prev: dict[int, Optional[int]] = {source: None}

    visited: set[int] = set()

    while heap:
        f, g, node = heapq.heappop(heap)

        if node in visited:
            continue
        visited.add(node)

        if node == target:
            return _reconstruct_path(prev, target), round(g, 4)

        for neighbour, edge_dist in graph.get(node, []):
            if neighbour in visited:
                continue
            new_g = g + edge_dist
            if new_g < g_score.get(neighbour, float("inf")):
                g_score[neighbour] = new_g
                prev[neighbour] = node
                f_score = new_g + h(neighbour)
                heapq.heappush(heap, (f_score, new_g, neighbour))

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
    coord_map: dict[int, tuple[float, float]],
    depot_id: int,
    customer_ids: list[int],
) -> list[int]:
    """
    Return customer IDs that have no path from the depot.
    Uses A* — correct even for isolated clusters with roads between them.
    """
    unreachable = []
    for cid in customer_ids:
        path, _ = astar(graph, coord_map, depot_id, cid)
        if path is None:
            unreachable.append(cid)
    return unreachable