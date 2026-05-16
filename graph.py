"""
Task 2: Build the graph
"""
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

   return graph~