# Oil-Dilevery-Dispatch-Pre_assestment-

# Oil Delivery Dispatch API

A REST API for an oil tanker dispatch system. Given a road network stored in SQLite, it finds the shortest driving route from the depot to any customer and manages delivery records.

---

## Language & Framework

| Concern | Choice | Reason |
|---|---|---|
| Language | **Python 3.11+** | Clean syntax, rich standard library (`heapq`, `sqlite3`), fast to iterate |
| Framework | **Flask 3** | Minimal and explicit — every route is easy to read and reason about |
| Database | **SQLite** via `sqlite3` | Pre-seeded `delivery.db` provided; no ORM as required by the spec |

---

## Project Structure

```
oil-dispatch/
├── app.py              # Flask routes — all 6 endpoints
├── db.py               # Data access layer — all SQL lives here
├── graph.py            # Graph builder + Dijkstra algorithm
├── test_all.py         # Full test suite (db, graph, and API tests)
├── delivery.db         # Pre-seeded SQLite database
├── requirements.txt    # Python dependencies
└── templates/
    └── index.html      # Browser dashboard UI
```

---

## Setup & Installation

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Add coordinates to the database (run once)

The database needs lat/lng coordinates for the locations. Run this script once:

```bash
python add_coords.py
```

### 3. Start the server

```bash
python app.py
```

The server will start at `http://localhost:5000`

### 4. Open the dashboard (optional)

Visit `http://localhost:5000` in your browser to use the interactive route finder UI.

---

## How the Algorithm Works

The road network is modelled as a **weighted undirected graph**:

- Each **location** (depot or customer) is a **node**
- Each **road** is an **edge** with a `distance_km` weight
- Because roads are bidirectional, every road `A → B` is also stored as `B → A` in the adjacency list

**Dijkstra's algorithm** finds the shortest path:

1. Start at the source node with cost `0`; every other node starts at infinity
2. Use a **min-heap** (priority queue) to always expand the cheapest unvisited node first
3. For each neighbour, if the path through the current node is cheaper than what is known, update it and record the previous node
4. When the target node is reached, walk the `prev` pointers backwards to reconstruct the full path
5. If the target is never reached, the customer is unreachable — return `None`

> **Note on isolated customers:** `Kerteh Terminal` (id=11) and `Gebeng Industrial Hub` (id=12) each have `road_count=1` — they connect to each other but not to the main network. A simple SQL check for zero roads would miss them. Dijkstra correctly reports both as unreachable.

---

## API Endpoints

### `GET /locations`

Return all locations with type and direct road connection count.

```bash
curl http://localhost:5000/locations
```

**Response:**
```json
[
  { "id": 1, "name": "Central Depot", "type": "depot", "road_count": 3 },
  { "id": 7, "name": "Petronas Cyberjaya", "type": "customer", "road_count": 3 },
  { "id": 11, "name": "Kerteh Terminal", "type": "customer", "road_count": 1 }
]
```

---

### `GET /route?from=<id>&to=<id>`

Find the shortest route between two locations.

```bash
# Reachable customer
curl "http://localhost:5000/route?from=1&to=7"

# Unreachable customer
curl "http://localhost:5000/route?from=1&to=11"
```

**Response — route found:**
```json
{
  "from": { "id": 1, "name": "Central Depot" },
  "to": { "id": 7, "name": "Petronas Cyberjaya" },
  "path": [
    { "id": 1, "name": "Central Depot" },
    { "id": 3, "name": "Shell Subang Jaya" },
    { "id": 7, "name": "Petronas Cyberjaya" }
  ],
  "total_distance_km": 40.5,
  "reachable": true
}
```

**Response — no path:**
```json
{
  "from": { "id": 1, "name": "Central Depot" },
  "to": { "id": 11, "name": "Kerteh Terminal" },
  "path": [],
  "total_distance_km": null,
  "reachable": false
}
```

| Code | Meaning |
|---|---|
| 200 | Success (check `reachable` field) |
| 400 | Missing or non-integer `from` / `to` |
| 404 | Location ID not found in database |

---

### `POST /deliveries`

Log a new delivery departure.

```bash
curl -X POST http://localhost:5000/deliveries \
  -H "Content-Type: application/json" \
  -d '{"customer_id": 7, "truck_plate": "WB5678C"}'
```

**Response 201:**
```json
{
  "id": 7,
  "customer_id": 7,
  "truck_plate": "WB5678C",
  "status": "departed",
  "departed_at": "2025-05-16 10:00:00",
  "arrived_at": null
}
```

| Code | Meaning |
|---|---|
| 201 | Delivery created |
| 400 | Validation failed — not a customer, unreachable, or missing fields |

---

### `PATCH /deliveries/<id>/status`

Mark a delivery as arrived. Only valid transition: `departed → arrived`.

```bash
curl -X PATCH http://localhost:5000/deliveries/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "arrived"}'
```

**Response 200:**
```json
{
  "id": 1,
  "customer_id": 4,
  "truck_plate": "WA1234B",
  "status": "arrived",
  "departed_at": "2025-05-04 07:45:00",
  "arrived_at": "2025-05-16 10:05:00"
}
```

| Code | Meaning |
|---|---|
| 200 | Status updated |
| 404 | Delivery not found |
| 422 | Invalid transition or bad status value |

---

### `GET /locations/unreachable` *(Task 5)*

Return all customer locations with no road path to the depot.
Uses the graph algorithm — not a SQL zero-road check.

```bash
curl http://localhost:5000/locations/unreachable
```

---

### `GET /deliveries/summary` *(Task 6)*

Per-customer delivery totals and most recent delivery date.
Backed by a single SQL aggregation query — no application-level loops.

```bash
curl http://localhost:5000/deliveries/summary
```

**Response:**
```json
[
  {
    "customer_id": 2,
    "customer_name": "Petronas Ara Damansara",
    "total_deliveries": 2,
    "last_delivery_at": "2025-05-02 10:00:00"
  },
  {
    "customer_id": 6,
    "customer_name": "Shell Shah Alam",
    "total_deliveries": 0,
    "last_delivery_at": null
  }
]
```

---

## Running Tests

### Full test suite (no server needed for Task 1–3)

```bash
python test_all.py
```

### Full test suite including API tests

```bash
# Terminal 1
python app.py

# Terminal 2
python test_all.py
```

---

## Assumptions

| # | Assumption |
|---|---|
| 1 | The spec says `from` is a valid location of any type. The API allows routing between any two locations (depot-to-depot, customer-to-customer), not just depot-to-customer. Validation only applies to `POST /deliveries`. |
| 2 | `PATCH /deliveries/<id>/status` only accepts `"arrived"` as the new status. Any other value returns HTTP 422, including `"departed"`. |
| 3 | `GET /locations/unreachable` returns only customers, not the depot, as the depot is the origin point and routing from the depot to itself is not meaningful. |
| 4 | The database `lat` and `lng` columns were added via `add_coords.py` using real Malaysian GPS coordinates to support future A\* pathfinding enhancements. |
