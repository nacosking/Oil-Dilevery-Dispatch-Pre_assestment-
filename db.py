"""
Task 1: Database access and layering
"""
import sqlite3
from contextdb import contextmanager

DB_Path = 'database.db'

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# Location queries
def get_all_locations():
    sql = """
        SELECT
            l.id,
            l.name,
            l.type,
            COUNT(r.id) AS road_count
        FROM locations l
        LEFT JOIN roads r
            ON l.id = r.from_id OR l.id = r.to_id
        GROUP BY l.id
        ORDER BY l.id
    """'
    with get_db() as conn:
        cursor = conn.execute(sql)
        return [dict(row) for row in cursor.fetchall()]

def get_location_by_id(location_id: int):
    sql = "SELECT id, name, type FROM locations WHERE id = ?"
    with get_db() as conn:
        cursor = conn.execute(sql, (location_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_depot():
    sql = "SELECT id, name, type FROM locations WHERE type = 'depot' LIMIT 1"
    with get_db() as conn:
        row = conn.execute(sql).fetchone()
        return dict(row) if row else None

# Road queries
def get_roads():
    sql = "SELECT id, from_id, to_id, distance_km, travel_time_min FROM roads"
    with get_db() as conn:
        cursor = conn.execute(sql)
        return [dict(row) for row in cursor.fetchall()]

# Delivery queries
def create_delivery(customer_id:int , truck_plate:str):
    sql = """
        INSERT INTO deliveries (customer_id, truck_plate, status, departed_at)
        VALUES (?, ?, 'departed', datetime('now'))
    """
    with get_db() as conn:
        cursor = conn.execute(sql, (customer_id, truck_plate))
        return cursor.lastrowid

def get_delivery_by_id(delivery_id: int, *, db=None):
    sql = """
        SELECT id, customer_id, truck_plate, status, departed_at, arrived_at,
        FROM deliveries WHERE id = ?
    """
    if db:
        cursor = db.execute(sql, (delivery_id,))
    else:
        with get_db() as conn:
            cursor = conn.execute(sql, (delivery_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def mark_delivery_arrived(delivery_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT status FROM deliveries WHERE id = ?", (delivery_id,)).fetchone()

        if not row:
            return None, "not_found"
        
        if row['status'] == 'departed':
            return None, f"invalid_transition: cannot move '{row['status']}' to 'arrived'"
        
        conn.execute("""
            UPDATE deliveries SET status = 'arrived', 
            arrived_at = datetime('now') 
            WHERE id = ?
        """, (delivery_id,))
        return get_delivery_by_id(delivery_id, db=conn), None

def get_delivery_summary():
    sql = """
        SELECT
            l.id               AS customer_id,
            l.name             AS customer_name,
            COUNT(d.id)        AS total_deliveries,
            MAX(d.departed_at) AS last_delivery_at
        FROM locations l
        LEFT JOIN deliveries d ON l.id = d.customer_id
        WHERE l.type = 'customer'
        GROUP BY l.id
        ORDER BY l.id
    """
    with get_conn() as conn:
        return [dict(row) for row in conn.execute(sql)]