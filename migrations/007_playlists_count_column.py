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

            ### Add column 'count' to the playlists table
            if not column_exists(cursor, "playlists", "count"):
                cursor.execute("ALTER TABLE playlists ADD COLUMN count INTEGER")
                conn.commit()

            ### Update the count on each playlist
            cursor.execute("""
                UPDATE playlists
                SET count = (
                    SELECT COUNT(*)
                    FROM videos
                    WHERE videos.playlist_id = playlists.id
                )
            """)

            conn.commit()
            conn.close()

if __name__ == "__main__":
    run()