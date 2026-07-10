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

            ### Add column 'description' to the playlists table
            if not column_exists(cursor, "playlists", "description"):
                cursor.execute("ALTER TABLE playlists ADD COLUMN description TEXT")

            ### Add column 'created' to the playlists table
            if not column_exists(cursor, "playlists", "created"):
                cursor.execute("ALTER TABLE playlists ADD COLUMN created TEXT DEFAULT '1970-01-01'")

            ### Add column 'description' to the videos table
            if not column_exists(cursor, "videos", "description"):
                cursor.execute("ALTER TABLE videos ADD COLUMN description TEXT")

            conn.commit()
            conn.close()

    print("PLEASE USE THE 'REFRESH ALL' BUTTON FOR EACH USER!")

if __name__ == "__main__":
    run()