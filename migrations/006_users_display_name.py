import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(__file__), "../databases")

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())

def run():
    conn = sqlite3.connect(os.path.join(DB_DIR, "users.db"))
    cursor = conn.cursor()

    ### Add column 'display_name' to the users table
    if not column_exists(cursor, "users", "display_name"):
        cursor.execute("ALTER TABLE users ADD COLUMN display_name TEXT")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    run()