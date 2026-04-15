import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(__file__), "../databases")

def run():
    for file in os.listdir(DB_DIR):
        if file.endswith(".db") and file != "users.db":
            conn = sqlite3.connect(os.path.join(DB_DIR, file))
            cursor = conn.cursor()

            cursor.execute("PRAGMA foreign_keys = OFF")

            ### Drop the triggers temporarily
            trigger_sqls = []

            cursor.execute("""
                SELECT sql
                FROM sqlite_master
                WHERE type='trigger'
            """)

            for (sql,) in cursor.fetchall():
                if sql:
                    trigger_sqls.append(sql)

            cursor.execute("""
            SELECT name, sql
            FROM sqlite_master
            WHERE type='trigger' AND sql LIKE '%playlists%'
            """)

            triggers = cursor.fetchall()

            for name, _ in triggers:
                cursor.execute(f"DROP TRIGGER IF EXISTS {name}")

            ### Recreate the playlists table
            cursor.execute("""
                CREATE TABLE new_playlists (
                    id TEXT PRIMARY KEY,
                    channel_id TEXT,
                    title TEXT,
                    thumbnail TEXT,
                    date_saved TEXT DEFAULT current_timestamp,
                    last_watched TEXT DEFAULT "1970-01-01",
                    progress INTEGER DEFAULT 0,
                    FOREIGN KEY(channel_id) REFERENCES channels(id) ON DELETE RESTRICT
                )
            """)

            cursor.execute("""
                INSERT INTO new_playlists (id, channel_id, title, thumbnail, date_saved, last_watched, progress)
                SELECT id, channel_id, title, thumbnail, date_saved, last_watched, progress FROM playlists
            """)

            cursor.execute("""
                DROP TABLE playlists
            """)

            cursor.execute("""
                ALTER TABLE new_playlists RENAME TO playlists
            """)

            ### Recreate the triggers
            for sql in trigger_sqls:
                cursor.execute(sql)

            cursor.execute("PRAGMA foreign_keys = ON")

            conn.commit()
            conn.close()

if __name__ == "__main__":
    run()