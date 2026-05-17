"""
test_all.py - Full Test Suite
Covers Task 1 (db.py), Task 2+3 (graph.py), and all PDF test cases.

Usage:
    Option A - Test db.py and graph.py only (no server needed):
        python test_all.py

    Option B - Run all tests including API (server must be running):
        1. python app.py          (Terminal 1)
        2. python test_all.py     (Terminal 2)
"""

import json
import sys
import urllib.request
import urllib.error
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

BASE   = "http://localhost:5000"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

passed = 0
failed = 0


# Helpers

def check(label, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"    {GREEN}PASS{RESET} - {label}")
    else:
        failed += 1
        print(f"    {RED}FAIL{RESET} - {label}")


def section(title):
    print(f"\n{BOLD}{CYAN}{'=' * 55}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 55}{RESET}\n")


def make_request(method, path, body=None):
    """HTTP client for live API calls."""
    url     = BASE + path
    data    = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    req     = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def call(method, path, body=None):
    print(f"  {YELLOW}> {method} {path}{RESET}")
    if body:
        print(f"    Body: {json.dumps(body)}")
    status, data = make_request(method, path, body)
    print(f"    Status  : {BOLD}{status}{RESET}")
    print(f"    Response: {json.dumps(data, indent=4)[:500]}")
    print()
    return status, data


# ─────────────────────────────────────────────────────────────────────────────
section("Task 1 - Database Layer (db.py)")
# ─────────────────────────────────────────────────────────────────────────────

print(f"  {YELLOW}get_depot(){RESET}")
depot = get_depot()
check("returns a result",              depot is not None)
check("type is depot",                 depot["type"] == "depot")

print(f"\n  {YELLOW}get_location_by_id(){RESET}")
loc = get_location_by_id(7)
check("finds location id=7",           loc is not None)
check("name is Petronas Cyberjaya",    loc["name"] == "Petronas Cyberjaya")
check("type is customer",              loc["type"] == "customer")
missing = get_location_by_id(999)
check("returns None for id=999",       missing is None)

print(f"\n  {YELLOW}get_all_locations(){RESET}")
locations = get_all_locations()
check("returns 12 locations",          len(locations) == 12)
check("each row has road_count",       all("road_count" in l for l in locations))
isolated = next((l for l in locations if l["id"] == 11), None)
check("id=11 has road_count = 1",      isolated is not None and isolated["road_count"] == 1)

print(f"\n  {YELLOW}get_roads(){RESET}")
roads = get_roads()
check("returns roads",                 len(roads) > 0)
check("each road has distance_km",     all("distance_km" in r for r in roads))
check("each road has from_id/to_id",   all("from_id" in r and "to_id" in r for r in roads))

print(f"\n  {YELLOW}create_delivery() + get_delivery_by_id(){RESET}")
new_delivery = create_delivery(7, "WB0001T")
check("delivery created",              new_delivery is not None)
check("status is departed",            new_delivery["status"] == "departed")
check("customer_id is 7",             new_delivery["customer_id"] == 7)
check("truck_plate matches",           new_delivery["truck_plate"] == "WB0001T")
check("departed_at is set",            new_delivery["departed_at"] is not None)
check("arrived_at is None",            new_delivery["arrived_at"] is None)
fetched = get_delivery_by_id(new_delivery["id"])
check("can fetch by id",               fetched is not None)
check("fetched id matches",            fetched["id"] == new_delivery["id"])

print(f"\n  {YELLOW}mark_delivery_arrived(){RESET}")
arrived, error = mark_delivery_arrived(new_delivery["id"])
check("no error on valid transition",  error is None)
check("status updated to arrived",     arrived["status"] == "arrived")
check("arrived_at is now set",         arrived["arrived_at"] is not None)
_, error2 = mark_delivery_arrived(new_delivery["id"])
check("blocks arrived -> arrived",     error2 is not None)
_, error3 = mark_delivery_arrived(99999)
check("returns not_found for id=99999", error3 == "not_found")


# ─────────────────────────────────────────────────────────────────────────────
section("Task 2 - Graph Builder (graph.py)")
# ─────────────────────────────────────────────────────────────────────────────

graph = build_graph()

print(f"  {YELLOW}build_graph(){RESET}")
check("graph is not empty",            len(graph) > 0)
check("depot (id=1) is in graph",      1 in graph)
check("depot has 3 neighbours",        len(graph[1]) == 3)
neighbours_of_1 = [n for n, _ in graph[1]]
check("road 1->2 exists",              2 in neighbours_of_1)
neighbours_of_2 = [n for n, _ in graph[2]]
check("road 2->1 exists (bidirect)",   1 in neighbours_of_2)


# ─────────────────────────────────────────────────────────────────────────────
section("Task 3 - Dijkstra (graph.py)")
# ─────────────────────────────────────────────────────────────────────────────

print(f"  {YELLOW}dijkstra(){RESET}")
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

print(f"\n  {YELLOW}find_unreachable_customers(){RESET}")
all_locs    = get_all_locations()
cust_ids    = [l["id"] for l in all_locs if l["type"] == "customer"]
unreachable = find_unreachable_customers(graph, depot["id"], cust_ids)
check("finds 2 unreachable customers",     len(unreachable) == 2)
check("id=11 is unreachable",              11 in unreachable)
check("id=12 is unreachable",              12 in unreachable)
check("id=7 is NOT unreachable",           7 not in unreachable)


# ─────────────────────────────────────────────────────────────────────────────
# Check if server is running before API tests
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{BOLD}Checking server at {BASE}...{RESET}")
server_running = False
try:
    urllib.request.urlopen(BASE + "/locations")
    print(f"{GREEN}Server is running - running API tests{RESET}")
    server_running = True
except Exception:
    print(f"{YELLOW}Server is not running - skipping API tests{RESET}")
    print(f"  To run API tests: start the server with {BOLD}python app.py{RESET} first")


if server_running:

    # ─────────────────────────────────────────────────────────────────────────
    section("1A - Shortest Path: Happy Path")
    # ─────────────────────────────────────────────────────────────────────────

    status, data = call("GET", "/route?from=1&to=7")
    check("HTTP 200",                          status == 200)
    check("reachable is true",                 data.get("reachable") == True)
    check("path goes via Subang Jaya (3)",     any(n["id"] == 3 for n in data.get("path", [])))
    check("path ends at Cyberjaya (7)",        data.get("path", [{}])[-1].get("id") == 7)
    check("total distance is 40.5 km",        data.get("total_distance_km") == 40.5)

    print()

    status, data = call("GET", "/route?from=1&to=9")
    check("HTTP 200",                   status == 200)
    check("reachable is true",          data.get("reachable") == True)
    check("path ends at Gombak (9)",    data.get("path", [{}])[-1].get("id") == 9)
    check("total distance is 15.8 km", data.get("total_distance_km") == 15.8)


    # ─────────────────────────────────────────────────────────────────────────
    section("1B - Unreachable Location: No Crash")
    # ─────────────────────────────────────────────────────────────────────────

    status, data = call("GET", "/route?from=1&to=11")
    check("HTTP 200 - did not crash",      status == 200)
    check("reachable is false",            data.get("reachable") == False)
    check("path is empty list",            data.get("path") == [])
    check("total_distance_km is null",     data.get("total_distance_km") is None)


    # ─────────────────────────────────────────────────────────────────────────
    section("1C - Delivery Creation: Validation")
    # ─────────────────────────────────────────────────────────────────────────

    print(f"  {YELLOW}Run A - valid reachable customer (id=7){RESET}\n")
    status, data = call("POST", "/deliveries", {"customer_id": 7, "truck_plate": "WB5678C"})
    check("HTTP 201 created",              status == 201)
    check("status is departed",            data.get("status") == "departed")
    check("customer_id is 7",             data.get("customer_id") == 7)
    check("truck_plate is WB5678C",       data.get("truck_plate") == "WB5678C")
    check("departed_at is set",            data.get("departed_at") is not None)
    check("arrived_at is null",            data.get("arrived_at") is None)

    print()
    print(f"  {YELLOW}Run B - unreachable customer (id=11){RESET}\n")
    status, data = call("POST", "/deliveries", {"customer_id": 11, "truck_plate": "WB5678C"})
    check("HTTP 400 rejected",             status == 400)
    check("error message returned",        "error" in data)

    print()
    print(f"  {YELLOW}Run C - depot passed as customer (id=1){RESET}\n")
    status, data = call("POST", "/deliveries", {"customer_id": 1, "truck_plate": "WB5678C"})
    check("HTTP 400 rejected",             status == 400)
    check("error message returned",        "error" in data)


    # ─────────────────────────────────────────────────────────────────────────
    section("1D - Status Transition: State Machine")
    # ─────────────────────────────────────────────────────────────────────────

    _, fresh    = make_request("POST", "/deliveries", {"customer_id": 7, "truck_plate": "TESTPLATE"})
    delivery_id = fresh.get("id")
    print(f"  Created fresh delivery id={delivery_id} (status=departed)\n")

    print(f"  {YELLOW}Run A - departed -> arrived (valid transition){RESET}\n")
    status, data = call("PATCH", f"/deliveries/{delivery_id}/status", {"status": "arrived"})
    check("HTTP 200",                      status == 200)
    check("status is now arrived",         data.get("status") == "arrived")
    check("arrived_at is set",             data.get("arrived_at") is not None)

    print()
    print(f"  {YELLOW}Run B - arrived -> departed (invalid - already arrived){RESET}\n")
    status, data = call("PATCH", f"/deliveries/{delivery_id}/status", {"status": "departed"})
    check("HTTP 422 rejected",             status == 422)
    check("error message returned",        "error" in data)



# Final summary
total = passed + failed
print(f"\n{BOLD}{'=' * 55}{RESET}")
print(f"{BOLD}  RESULTS: {GREEN}{passed} passed{RESET}{BOLD} / {RED}{failed} failed{RESET}{BOLD} / {total} total{RESET}")
if not server_running:
    print(f"  {YELLOW}Note: API tests were skipped (server not running){RESET}")
if failed == 0:
    print(f"  {GREEN}{BOLD}All tests passed! 🎉{RESET}")
else:
    print(f"  {RED}{BOLD}{failed} test(s) need attention.{RESET}")
print(f"{BOLD}{'=' * 55}{RESET}\n")