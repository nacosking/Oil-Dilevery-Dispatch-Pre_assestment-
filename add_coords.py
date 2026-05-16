"""
add_coords.py — Run this ONCE to add lat/lng to your local delivery.db
Usage: python3 add_coords.py
"""

import sqlite3

conn = sqlite3.connect("delivery.db")

# Add columns (safe to run — skips if already exists)
try:
    conn.execute("ALTER TABLE locations ADD COLUMN lat REAL")
    conn.execute("ALTER TABLE locations ADD COLUMN lng REAL")
    print("✅ Columns lat/lng added.")
except Exception:
    print("ℹ️  Columns already exist, skipping ALTER TABLE.")

# Real Malaysian coordinates for each location
coords = {
    1:  (3.1390, 101.6869),  # Central Depot (KL)
    2:  (3.1478, 101.5744),  # Petronas Ara Damansara
    3:  (3.0738, 101.5836),  # Shell Subang Jaya
    4:  (3.0456, 101.6183),  # BHP Puchong
    5:  (3.0449, 101.4454),  # Caltex Klang
    6:  (3.0733, 101.5328),  # Shell Shah Alam
    7:  (2.9270, 101.6530),  # Petronas Cyberjaya
    8:  (2.9264, 101.6964),  # BHP Putrajaya
    9:  (3.2167, 101.6894),  # Petronas Gombak
    10: (3.1598, 101.7654),  # BHP Ampang
    11: (4.5370, 103.4324),  # Kerteh Terminal (isolated)
    12: (3.8297, 103.3411),  # Gebeng Industrial Hub (isolated)
}

for loc_id, (lat, lng) in coords.items():
    conn.execute(
        "UPDATE locations SET lat = ?, lng = ? WHERE id = ?",
        (lat, lng, loc_id)
    )

conn.commit()
conn.close()
print("✅ Coordinates inserted. You can now run python3 test.py")