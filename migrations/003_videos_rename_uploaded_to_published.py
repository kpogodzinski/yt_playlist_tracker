import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(__file__), "../databases")

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())

def run():
    for file in os.listdir(DB_DIR):
        if file.endswith(".db") and file != "users.db":
            conn = sqlite3.connect(os.path.join(DB_DIR, file))
            cursor = conn.cursor()

            if column_exists(cursor, "videos", "uploaded"):
                cursor.execute("ALTER TABLE videos RENAME COLUMN uploaded TO published")
                print(f"Renamed 'uploaded' column to 'published' in {file}")

            conn.commit()
            conn.close()

if __name__ == "__main__":
    run()