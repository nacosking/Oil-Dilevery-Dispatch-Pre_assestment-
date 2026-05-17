"""Database access layer for the delivery demo app.

This module provides a minimal, well-documented set of helpers for
connecting to the SQLite database and running the queries used by
the application (locations, roads, deliveries).
"""

import sqlite3
from contextlib import contextmanager

# Path to the SQLite database file (relative to the project root).
DB_PATH = 'delivery.db'


@contextmanager
def get_db():
    """Context manager yielding a SQLite connection.

    - Enables `row_factory` so query results can be converted to dicts.
    - Turns on foreign key enforcement via PRAGMA.
    - Commits on successful exit, rolls back and re-raises on error.

    Usage:
        with get_db() as conn:
            conn.execute(...)
    """
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


# -----------------------------
# Location queries
# -----------------------------

def get_all_locations():
    """Return all locations with a count of connected roads.

    Each returned item is a plain dict with keys: ``id``, ``name``,
    ``type`` and ``road_count``.
    """
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
    """
    with get_db() as conn:
        cursor = conn.execute(sql)
        return [dict(row) for row in cursor.fetchall()]


def get_location_by_id(location_id: int):
    """Return a single location by its id, or ``None`` if not found."""
    sql = "SELECT id, name, type FROM locations WHERE id = ?"
    with get_db() as conn:
        cursor = conn.execute(sql, (location_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_depot():
    """Return the first location of type 'depot', or ``None`` if missing."""
    sql = "SELECT id, name, type FROM locations WHERE type = 'depot' LIMIT 1"
    with get_db() as conn:
        row = conn.execute(sql).fetchone()
        return dict(row) if row else None


# -----------------------------
# Road queries
# -----------------------------

def get_roads():
    """Return a list of roads as dicts.

    Each dict contains: ``id``, ``from_id``, ``to_id``, ``distance_km``,
    and ``travel_time_min``.
    """
    sql = "SELECT id, from_id, to_id, distance_km, travel_time_min FROM roads"
    with get_db() as conn:
        cursor = conn.execute(sql)
        return [dict(row) for row in cursor.fetchall()]


# -----------------------------
# Delivery queries
# -----------------------------

def create_delivery(customer_id: int, truck_plate: str):
    """Insert a new delivery and return the created record as a dict.

    The new delivery is created with status 'departed' and a current
    timestamp for ``departed_at``.
    """
    sql = """
        INSERT INTO deliveries (customer_id, truck_plate, status, departed_at)
        VALUES (?, ?, 'departed', datetime('now'))
    """
    with get_db() as conn:
        cursor = conn.execute(sql, (customer_id, truck_plate))
        return get_delivery_by_id(cursor.lastrowid, db=conn)


def get_delivery_by_id(delivery_id: int, *, db=None):
    """Return a delivery by id as a dict, or ``None`` if not found.

    If a database connection is provided via ``db`` it will be used
    (useful for transactional callers); otherwise a new connection
    is opened and closed for the query.
    """
    sql = """
        SELECT id, customer_id, truck_plate, status, departed_at, arrived_at
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
    """Mark a delivery as arrived.

    Returns a tuple ``(delivery_dict, None)`` on success, or
    ``(None, error_code)`` where ``error_code`` is one of:
      - ``'not_found'``: delivery id does not exist
      - ``'invalid_transition: ...'``: delivery in wrong state
    """
    with get_db() as conn:
        row = conn.execute(
            "SELECT status FROM deliveries WHERE id = ?", (delivery_id,)
        ).fetchone()

        if not row:
            return None, "not_found"

        if row['status'] != 'departed':
            return None, f"invalid_transition: cannot move '{row['status']}' to 'arrived'"

        conn.execute("""
            UPDATE deliveries SET status = 'arrived',
            arrived_at = datetime('now')
            WHERE id = ?
        """, (delivery_id,))
        return get_delivery_by_id(delivery_id, db=conn), None


def get_delivery_summary():
    """Return summary statistics for customer deliveries.

    Each returned dict contains: ``customer_id``, ``customer_name``,
    ``total_deliveries`` and ``last_delivery_at``.
    """
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
    with get_db() as conn:
        return [dict(row) for row in conn.execute(sql)]