"""
test.py — Manual tests for Task 1 (db.py) and Task 2+3 (graph.py)
Run with: python3 test.py
"""

from db import (
    get_all_locations,
    get_location_by_id,
    get_depot,
    get_roads,
    create_delivery,
    get_delivery_by_id,
    mark_delivery_arrived,
)
from graph import (
    build_graph,
    dijkstra,
    find_unreachable_customers,
)

PASS = "✅ PASS"
FAIL = "❌ FAIL"

def check(label: str, condition: bool):
    print(f"  {PASS if condition else FAIL} — {label}")


# ─────────────────────────────────────────────────────────────────────────────
print("\n══ Task 1: Database Layer (db.py) ══\n")
# ─────────────────────────────────────────────────────────────────────────────

print("▸ get_depot()")
depot = get_depot()
check("returns a result",            depot is not None)
check("type is 'depot'",             depot["type"] == "depot")

print("\n▸ get_location_by_id()")
loc = get_location_by_id(7)
check("finds location id=7",         loc is not None)
check("name is Petronas Cyberjaya",  loc["name"] == "Petronas Cyberjaya")
check("type is 'customer'",          loc["type"] == "customer")
missing = get_location_by_id(999)
check("returns None for id=999",     missing is None)

print("\n▸ get_all_locations()")
locations = get_all_locations()
check("returns 12 locations",        len(locations) == 12)
check("each row has road_count",     all("road_count" in l for l in locations))
isolated = next((l for l in locations if l["id"] == 11), None)
check("id=11 has road_count = 1",    isolated is not None and isolated["road_count"] == 1)

print("\n▸ get_roads()")
roads = get_roads()
check("returns roads",               len(roads) > 0)
check("each road has distance_km",   all("distance_km" in r for r in roads))
check("each road has from_id/to_id", all("from_id" in r and "to_id" in r for r in roads))

print("\n▸ create_delivery() + get_delivery_by_id()")
new_delivery = create_delivery(7, "WB0001T")
check("delivery created",            new_delivery is not None)
check("status is 'departed'",        new_delivery["status"] == "departed")
check("customer_id is 7",            new_delivery["customer_id"] == 7)
check("truck_plate matches",         new_delivery["truck_plate"] == "WB0001T")
check("departed_at is set",          new_delivery["departed_at"] is not None)
check("arrived_at is None",          new_delivery["arrived_at"] is None)
fetched = get_delivery_by_id(new_delivery["id"])
check("can fetch by id",             fetched is not None)
check("fetched id matches",          fetched["id"] == new_delivery["id"])

print("\n▸ mark_delivery_arrived()")
arrived, error = mark_delivery_arrived(new_delivery["id"])
check("no error on valid transition", error is None)
check("status updated to arrived",    arrived["status"] == "arrived")
check("arrived_at is now set",        arrived["arrived_at"] is not None)
_, error2 = mark_delivery_arrived(new_delivery["id"])
check("blocks arrived -> arrived",    error2 is not None)
_, error3 = mark_delivery_arrived(99999)
check("returns not_found for id=99999", error3 == "not_found")


# ─────────────────────────────────────────────────────────────────────────────
print("\n══ Task 2: Graph Builder (graph.py) ══\n")
# ─────────────────────────────────────────────────────────────────────────────

graph = build_graph()

print("▸ build_graph()")
check("graph is not empty",          len(graph) > 0)
check("depot (id=1) is in graph",    1 in graph)
check("depot has 3 neighbours",      len(graph[1]) == 3)
neighbours_of_1 = [n for n, _ in graph[1]]
check("road 1->2 exists",            2 in neighbours_of_1)
neighbours_of_2 = [n for n, _ in graph[2]]
check("road 2->1 exists (bidirect)", 1 in neighbours_of_2)


# ─────────────────────────────────────────────────────────────────────────────
print("\n══ Task 3: Dijkstra (graph.py) ══\n")
# ─────────────────────────────────────────────────────────────────────────────

print("▸ dijkstra()")
path, dist = dijkstra(graph, 1, 7)
check("finds path depot -> id=7",          path is not None)
check("path starts at depot (1)",          path[0] == 1)
check("path ends at target (7)",           path[-1] == 7)
check("distance is 40.5 km",              dist == 40.5)

path2, dist2 = dijkstra(graph, 1, 11)
check("returns None path for unreachable", path2 is None)
check("returns None dist for unreachable", dist2 is None)

path3, dist3 = dijkstra(graph, 1, 1)
check("same source and target",            path3 == [1] and dist3 == 0.0)

print("\n▸ find_unreachable_customers()")
all_locs    = get_all_locations()
cust_ids    = [l["id"] for l in all_locs if l["type"] == "customer"]
unreachable = find_unreachable_customers(graph, depot["id"], cust_ids)
check("finds 2 unreachable customers", len(unreachable) == 2)
check("id=11 is unreachable",          11 in unreachable)
check("id=12 is unreachable",          12 in unreachable)
check("id=7 is NOT unreachable",       7 not in unreachable)

print("\n" + "═" * 45)
print("All tests complete!")
print("═" * 45 + "\n")