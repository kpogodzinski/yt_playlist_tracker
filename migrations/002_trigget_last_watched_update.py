import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(__file__), "../databases")

def run():
    for file in os.listdir(DB_DIR):
        if file.endswith(".db") and file != "users.db":
            conn = sqlite3.connect(os.path.join(DB_DIR, file))
            cursor = conn.cursor()

            cursor.execute("DROP TRIGGER IF EXISTS last_watched_tracker")
            print(f"Dropped old 'last_watched_tracker' trigger in {file}")

            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS last_watched_tracker
                AFTER UPDATE ON videos
                WHEN NEW.is_watched = 1 AND OLD.is_watched = 0
                BEGIN
                    UPDATE playlists
                    SET last_watched = current_timestamp
                    WHERE id = NEW.playlist_id;
                END
            """)
            print(f"Added new 'last_watched_tracker' trigger in {file}")

            conn.commit()
            conn.close()
if __name__ == "__main__":
    run()