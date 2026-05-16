"""
Task 2: Build the graph
Task 3: Shortest path algorithm - both Dijkstra and A*
"""
import heapq
import math
from typing import Optional
from db import get_roads

def build_graph() -> dict[int, list[tuple[int, float]]]:
   roads = get_roads()
   graph: dict[int, list[tuple[int, float]]] = {}

   for road in roads:
       from_id = road['from_id']
       to_id = road['to_id']
       distance = road['distance']

       if from_id not in graph:
           graph[from_id] = []
       if to_id not in graph:
           graph[to_id] = []

       graph[from_id].append((to_id, distance))
       graph[to_id].append((from_id, distance))  # Undirected graph

   return graph


   def build_coord_map() -> dict[int, tuple[float, float]]:
        
        locations = get_all_locations()
        return {
            loc['id']: (loc['latitude'], loc['longitude'])
            for loc in locations
            if loc['latitude'] is not None and loc['longitude'] is not None
        }

# Task 3a - Dijkstra's algorithm
def dijsktra(
    graph: dict[int, list[tuple[int, float]]],
    source: int,
    target: int
) -> tuple[Optional[list[int]], Optional[float]]:

    heap = [(0.0, source, [])]  # (cost, node, path)
    distances = {source: 0.0}
    prev: dict[int, Optional[int]] = {source: None}

    visted = set()

    while heap:
        current_distance, current_node = heapq.heappop(heap)

        if current_node in visted:
            continue
        visted.add(current_node)

        if current_node == target:
            return _reconstruct_path(prev, target), round(current_distance, 4)

            for neighbor, edge_distance in graph.get(current_node, []):
                if neighbor in visted:
                    continue
                new_distance = current_distance + edge_distance
                if new_distance < distances.get(neighbor, math.inf):
                    distances[neighbor] = new_distance
                    prev[neighbor] = current_node
                    heapq.heappush(heap, (new_distance, neighbor))
    return None, None  # No path found
    
    