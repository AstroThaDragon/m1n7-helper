import sqlite3

def init_db():
    conn = sqlite3.connect("levels.db")
    cursor = conn.cursor()

    # 1. Create tables if they don't exist at all
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            stardust INTEGER DEFAULT 0,
            bio TEXT DEFAULT 'Exploring the outer rims of Enceladus Station. 🚀',
            active_background TEXT DEFAULT 'default_nebula',
            time_crystals INTEGER DEFAULT 0,
            mining_charges INTEGER DEFAULT 5,
            last_mined REAL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            user_id INTEGER,
            item_id TEXT,
            item_type TEXT,
            PRIMARY KEY (user_id, item_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            user_id INTEGER PRIMARY KEY,
            pet_name TEXT DEFAULT 'Cosmic Egg',
            pet_stage TEXT DEFAULT 'egg',
            fed_count INTEGER DEFAULT 0
        )
    """)

    # 2. Safety check: If the users table already existed from before, 
    # ensure any new columns we added are present so it doesn't crash.
    new_columns = [
        ("stardust", "INTEGER DEFAULT 0"),
        ("bio", "TEXT DEFAULT 'Exploring the outer rims of Enceladus Station. 🚀'"),
        ("active_background", "TEXT DEFAULT 'default_nebula'"),
        ("time_crystals", "INTEGER DEFAULT 0"),
        ("mining_charges", "INTEGER DEFAULT 5"),
        ("last_mined", "REAL DEFAULT 0")
    ]

    for col_name, col_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            # Column already exists, safe to ignore
            pass

    conn.commit()
    conn.close()