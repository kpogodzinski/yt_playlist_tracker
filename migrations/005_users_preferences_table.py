import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(__file__), "../databases")

def run():
    conn = sqlite3.connect(os.path.join(DB_DIR, "users.db"))
    cursor = conn.cursor()

    ### Create the preferences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            user_id INTEGER PRIMARY KEY,
            playlists_sort_by TEXT NOT NULL DEFAULT 'date_saved',
            playlists_hide_completed INTEGER NOT NULL DEFAULT 0,
            videos_hide_watched INTEGER NOT NULL DEFAULT 0,
            search_results_per_page INTEGER NOT NULL DEFAULT 10,
            search_playlists_sort_by TEXT NOT NULL DEFAULT 'date_created',
            search_playlists_hide_saved INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id),
            
            CHECK(playlists_sort_by IN ('date_saved', 'last_watched', 'title', 'progress')),
            CHECK(playlists_hide_completed IN (0,1)),
            CHECK(videos_hide_watched IN (0,1)),
            CHECK(search_results_per_page IN (10, 20, 30, 40, 50)),
            CHECK(search_playlists_sort_by IN ('date_created', 'title')),
            CHECK(search_playlists_hide_saved IN (0,1))
        );
    """)

    ### Add all existing users to the preferences table
    cursor.execute("""
        INSERT OR IGNORE INTO preferences (user_id)
        SELECT id FROM users
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    run()