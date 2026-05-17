"""
Task 4: REST API
Built with Flask. Four required endpoints.
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from graph import build_graph, dijkstra, find_unreachable_customers
import db

app = Flask(__name__)
CORS(app)


# ── Root: serve the dashboard UI ──────────────────────────────────────────────

@app.get("/")
def index():
    return render_template("index.html")


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_graph():
    """Build a fresh graph from the DB for each request."""
    return build_graph()

def get_depot():
    depot = db.get_depot()
    if not depot:
        raise RuntimeError("No depot found in the database.")
    return depot


# ── Endpoint 1: GET /locations ────────────────────────────────────────────────

@app.get("/locations")
def list_locations():
    """
    Return all locations with their type and direct road connection count.

    Example response:
    [
        { "id": 1, "name": "Central Depot", "type": "depot", "road_count": 3 },
        { "id": 11, "name": "Kerteh Terminal", "type": "customer", "road_count": 1 }
    ]
    """
    locations = db.get_all_locations()
    return jsonify(locations), 200


# ── Endpoint 2: GET /route ────────────────────────────────────────────────────

@app.get("/route")
def get_route():
    """
    Find the shortest path between two locations using Dijkstra.

    Query params: from=<int>  to=<int>

    Returns 400 if params are missing or not integers.
    Returns 404 if either location ID does not exist.
    Returns 200 with reachable=false if no path exists.
    """
    # --- Validate query parameters exist ---
    raw_from = request.args.get("from")
    raw_to   = request.args.get("to")

    if raw_from is None or raw_to is None:
        return jsonify({"error": "Both 'from' and 'to' query parameters are required."}), 400

    # --- Validate they are integers ---
    try:
        from_id = int(raw_from)
        to_id   = int(raw_to)
    except ValueError:
        return jsonify({"error": "'from' and 'to' must be valid integers."}), 400

    # --- Validate both locations exist in DB ---
    from_loc = db.get_location_by_id(from_id)
    to_loc   = db.get_location_by_id(to_id)

    if not from_loc:
        return jsonify({"error": f"Location with id={from_id} not found."}), 404
    if not to_loc:
        return jsonify({"error": f"Location with id={to_id} not found."}), 404

    # --- Same location edge case ---
    if from_id == to_id:
        return jsonify({
            "from": {"id": from_loc["id"], "name": from_loc["name"]},
            "to":   {"id": to_loc["id"],   "name": to_loc["name"]},
            "path": [{"id": from_loc["id"], "name": from_loc["name"]}],
            "total_distance_km": 0.0,
            "reachable": True,
        }), 200

    # --- Run Dijkstra ---
    graph              = get_graph()
    path_ids, total_dist = dijkstra(graph, from_id, to_id)

    # --- Unreachable ---
    if path_ids is None:
        return jsonify({
            "from": {"id": from_loc["id"], "name": from_loc["name"]},
            "to":   {"id": to_loc["id"],   "name": to_loc["name"]},
            "path": [],
            "total_distance_km": None,
            "reachable": False,
        }), 200

    # --- Build path with names ---
    loc_map     = {loc["id"]: loc["name"] for loc in db.get_all_locations()}
    path_detail = [{"id": pid, "name": loc_map[pid]} for pid in path_ids]

    return jsonify({
        "from": {"id": from_loc["id"], "name": from_loc["name"]},
        "to":   {"id": to_loc["id"],   "name": to_loc["name"]},
        "path": path_detail,
        "total_distance_km": total_dist,
        "reachable": True,
    }), 200


# ── Endpoint 3: POST /deliveries ──────────────────────────────────────────────

@app.post("/deliveries")
def create_delivery():
    """
    Log a new delivery departure.

    Body: { "customer_id": int, "truck_plate": str }

    Validates:
    1. customer_id exists and is type 'customer' (not depot)
    2. customer_id is reachable from the depot
    3. truck_plate is a non-empty string
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    customer_id = body.get("customer_id")
    truck_plate = body.get("truck_plate", "")

    # --- Validate truck_plate ---
    if not isinstance(truck_plate, str) or not truck_plate.strip():
        return jsonify({"error": "'truck_plate' is required and must be a non-empty string."}), 400

    # --- Validate customer_id type ---
    if not isinstance(customer_id, int):
        return jsonify({"error": "'customer_id' is required and must be an integer."}), 400

    # --- Validate location exists and is a customer ---
    location = db.get_location_by_id(customer_id)
    if not location:
        return jsonify({"error": f"Location with id={customer_id} not found."}), 400
    if location["type"] != "customer":
        return jsonify({"error": f"id={customer_id} is not a customer (type='{location['type']}')."}), 400

    # --- Validate reachability from depot ---
    depot = get_depot()
    graph = get_graph()
    path, _ = dijkstra(graph, depot["id"], customer_id)
    if path is None:
        return jsonify({
            "error": f"'{location['name']}' (id={customer_id}) is unreachable from the depot."
        }), 400

    # --- Save and return ---
    delivery = db.create_delivery(customer_id, truck_plate.strip())
    return jsonify(delivery), 201


# ── Endpoint 4: PATCH /deliveries/<id>/status ─────────────────────────────────

@app.patch("/deliveries/<int:delivery_id>/status")
def update_delivery_status(delivery_id: int):
    """
    Mark a delivery as arrived. Only valid transition: departed -> arrived.

    Body: { "status": "arrived" }

    Returns 404 if delivery not found.
    Returns 422 if transition is invalid.
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    new_status = body.get("status")

    # --- Only 'arrived' is accepted ---
    if new_status != "arrived":
        return jsonify({
            "error": f"Invalid status '{new_status}'. Only 'arrived' is accepted."
        }), 422

    delivery, error = db.mark_delivery_arrived(delivery_id)

    if error == "not_found":
        return jsonify({"error": f"Delivery with id={delivery_id} not found."}), 404
    if error:
        return jsonify({"error": error}), 422

    return jsonify(delivery), 200




# ── Endpoint 5: GET /locations/unreachable ────────────────────────────────────

@app.get("/locations/unreachable")
def unreachable_locations():
    """
    Task 5: Return all customer locations with no road path to the depot.

    Uses the graph + Dijkstra algorithm — NOT a SQL zero-road check.
    This correctly handles cases where a location has roads but they only
    connect to other isolated nodes (e.g. id=11 connects to id=12 but
    neither can reach the depot).
    """
    depot    = get_depot()
    all_locs = db.get_all_locations()

    # Get all customer IDs
    customer_ids = [loc["id"] for loc in all_locs if loc["type"] == "customer"]

    # Run Dijkstra for each customer from the depot
    graph        = get_graph()
    unreachable_ids = set(find_unreachable_customers(graph, depot["id"], customer_ids))

    # Filter and return only the unreachable ones
    result = [loc for loc in all_locs if loc["id"] in unreachable_ids]
    return jsonify(result), 200

# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)