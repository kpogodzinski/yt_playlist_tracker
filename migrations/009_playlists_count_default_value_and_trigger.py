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

            ### Drop column 'count' if exists
            if column_exists(cursor, "playlists", "count"):
                cursor.execute("ALTER TABLE playlists DROP COLUMN count")
                conn.commit()

            ### Add column 'count' with new default value
            cursor.execute("ALTER TABLE playlists ADD COLUMN count INTEGER DEFAULT 0")
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

            ### Add 'update_playlist_count' trigger
            cursor.execute("""
                CREATE TRIGGER update_playlist_count
                AFTER INSERT ON videos
                BEGIN
                    UPDATE playlists 
                    SET count = count + 1
                    WHERE id = NEW.playlist_id;
                END
            """)

            conn.commit()
            conn.close()

if __name__ == "__main__":
    run()