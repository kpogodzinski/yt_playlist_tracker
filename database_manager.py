import os
import sqlite3

from werkzeug.security import generate_password_hash, check_password_hash

def db_connect(database=None):
    conn = sqlite3.connect("databases/test.db" if database is None else f"databases/{database}.db")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    return conn, cursor

""" USERS """

def register_user(username, password):
    if not os.path.exists("databases"):
        os.mkdir("databases")

    conn, cursor = db_connect("users")
    password_hash = generate_password_hash(password)

    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                       (username, password_hash))
        cursor.execute("INSERT INTO preferences (user_id) SELECT id FROM users WHERE username = ?",
                       (username,))
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            _create_users_db()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                           (username, password_hash))
            cursor.execute("INSERT INTO preferences (user_id) SELECT id FROM users WHERE username = ?",
                           (username,))
        else:
            raise

    conn.commit()
    conn.close()

    _create_user_tables(username)

def login_user(username, password):
    if not os.path.exists("databases"):
        os.mkdir("databases")

    conn, cursor = db_connect("users")

    try:
        cursor.execute("SELECT id, username, display_name, password FROM users WHERE username = ?",
                       (username,))
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            _create_users_db()
            cursor.execute("SELECT id, username, display_name, password FROM users WHERE username = ?",
                           (username,))
        else:
            raise

    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[-1], password):
        return user[0:-1]
    else:
        return None

def change_password(username, current_password, new_password):
    conn, cursor = db_connect("users")

    cursor.execute("SELECT password FROM users WHERE username=?", (username,))
    password = cursor.fetchone()[0]

    if not check_password_hash(password, current_password):
        conn.close()
        return "invalid"

    try:
        new_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password=? WHERE username=?", (new_hash, username))
        conn.commit()
        return "success"
    except sqlite3.Error:
        return "error"
    finally:
        conn.close()

def change_display_name(username, display_name):
    conn, cursor = db_connect("users")
    try:
        cursor.execute("UPDATE users SET display_name=? WHERE username=?", (display_name, username))
        conn.commit()
        return "success"
    except sqlite3.Error:
        return "error"
    finally:
        conn.close()

def check_password(username, password):
    conn, cursor = db_connect("users")
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    password_hash = cursor.fetchone()[0]
    conn.close()
    return check_password_hash(password_hash, password)

def get_preferences(user_id):
    conn, cursor = db_connect("users")
    row = cursor.execute("SELECT * FROM preferences WHERE user_id = (?)", (user_id,)).fetchone()
    conn.close()
    return row

def set_preference(user_id, preference, value):
    conn, cursor = db_connect("users")
    try:
        query = f"UPDATE preferences SET {preference} = ? WHERE user_id = ?"
        cursor.execute(query, (value, user_id))
    except:
        raise
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn, cursor = db_connect("users")
    try:
        cursor.execute("DELETE FROM preferences WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return "success"
    except sqlite3.Error:
        return "error"
    finally:
        conn.close()

def _create_users_db():
    conn, cursor = db_connect("users")
    cursor.execute("""
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        display_name TEXT,
                        password TEXT NOT NULL
                    );
                """)

    cursor.execute("""
                    CREATE TABLE preferences (
                        user_id INTEGER PRIMARY KEY,
                        playlists_sort_by TEXT NOT NULL DEFAULT 'date_saved',
                        playlists_per_page INTEGER NOT NULL DEFAULT 10,
                        playlists_hide_completed INTEGER NOT NULL DEFAULT 0,
                        videos_hide_watched INTEGER NOT NULL DEFAULT 0,
                        search_results_per_page INTEGER NOT NULL DEFAULT 10,
                        search_playlists_per_page INTEGER NOT NULL DEFAULT 10,
                        search_playlists_sort_by TEXT NOT NULL DEFAULT 'date_created',
                        search_playlists_hide_saved INTEGER NOT NULL DEFAULT 0,
                        FOREIGN KEY(user_id) REFERENCES users(id),
                        
                        CHECK(playlists_sort_by IN ('date_saved', 'last_watched', 'title', 'progress')),
                        CHECK(playlists_per_page IN (10, 20, 30, 40, 50)),
                        CHECK(playlists_hide_completed IN (0,1)),
                        CHECK(videos_hide_watched IN (0,1)),
                        CHECK(search_results_per_page IN (10, 20, 30, 40, 50)),
                        CHECK(search_playlists_per_page IN (10, 20, 30, 40, 50)),
                        CHECK(search_playlists_sort_by IN ('date_created', 'title')),
                        CHECK(search_playlists_hide_saved IN (0,1))
                    );
                """)
    conn.commit()
    conn.close()

def _create_user_tables(username):
    conn, cursor = db_connect(username)
    cursor.execute("""
                    CREATE TABLE channels (
                        id TEXT PRIMARY KEY,
                        name TEXT,
                        thumbnail TEXT
                    );
                """)
    conn.commit()

    cursor.execute("""
                CREATE TABLE playlists (
                    id TEXT PRIMARY KEY,
                    channel_id TEXT,
                    title TEXT,
                    description TEXT,
                    thumbnail TEXT,
                    created TEXT DEFAULT '1970-01-01',
                    date_saved TEXT DEFAULT current_timestamp,
                    last_watched TEXT DEFAULT '1970-01-01',
                    count INTEGER DEFAULT 0,
                    progress INTEGER DEFAULT 0,
                    FOREIGN KEY(channel_id) REFERENCES channels(id) ON DELETE RESTRICT
                );
            """)
    conn.commit()

    cursor.execute("""
                CREATE TABLE videos (
                    id TEXT PRIMARY KEY,
                    playlist_id TEXT,
                    position INTEGER,
                    title TEXT,
                    description TEXT,
                    thumbnail TEXT,
                    duration TEXT,
                    published TEXT,
                    is_watched BOOLEAN DEFAULT 0,
                    FOREIGN KEY(playlist_id) REFERENCES playlists(id) ON DELETE CASCADE
                );
            """)
    conn.commit()

    cursor.execute("""
                CREATE TRIGGER progress_tracker_update
                AFTER UPDATE ON videos
                BEGIN
                    UPDATE playlists
                    SET progress = (
                        SELECT COUNT(CASE WHEN is_watched = 1 THEN 1 END) * 100 / COUNT(*)
                        FROM videos
                        WHERE playlist_id = NEW.playlist_id
                    )
                    WHERE id = NEW.playlist_id;
                END
            """)
    conn.commit()

    cursor.execute("""
                    CREATE TRIGGER progress_tracker_insert
                    AFTER INSERT ON videos
                    BEGIN
                        UPDATE playlists
                        SET progress = (
                            SELECT COUNT(CASE WHEN is_watched = 1 THEN 1 END) * 100 / COUNT(*)
                            FROM videos
                            WHERE playlist_id = NEW.playlist_id
                        )
                        WHERE id = NEW.playlist_id;
                    END
                """)
    conn.commit()

    cursor.execute("""
                        CREATE TRIGGER last_watched_tracker
                        AFTER UPDATE ON videos
                        WHEN NEW.is_watched = 1 AND OLD.is_watched = 0
                        BEGIN
                            UPDATE playlists
                            SET last_watched = current_timestamp
                            WHERE id = NEW.playlist_id;
                        END
                    """)
    conn.commit()

    cursor.execute("""
                            CREATE TRIGGER channel_playlist_count_tracker
                            AFTER DELETE ON playlists
                            WHEN (SELECT COUNT(*) FROM playlists WHERE channel_id = OLD.channel_id) = 0
                            BEGIN
                                DELETE FROM channels WHERE id = OLD.channel_id;
                            END
                        """)
    conn.commit()

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

""" CHANNELS """

def get_channel(username, channel_id):
    conn, cursor = db_connect(username)
    row = cursor.execute("SELECT * FROM channels WHERE id = ?", (channel_id,)).fetchone()
    conn.close()
    return row

def get_channels(username):
    conn, cursor = db_connect(username)
    rows = cursor.execute("SELECT * FROM channels").fetchall()
    conn.close()
    return rows

def save_channel(username, channel_id, name, thumbnail):
    conn, cursor = db_connect(username)
    try:
        cursor.execute("INSERT OR IGNORE INTO channels VALUES (?, ?, ?)", (channel_id, name, thumbnail))
        conn.commit()

        rows_inserted = cursor.rowcount
        if rows_inserted > 0:
            return "SUCCESS"
        else:
            print(f"Channel {name} ({channel_id}) already exists.")
            return "EXISTS"

    except sqlite3.Error as e:
        print(f"Database error while saving the channel: {e}")
        return "ERROR"

    finally:
        conn.close()

""" PLAYLISTS """

def get_playlist(username, playlist_id):
    conn, cursor = db_connect(username)
    row = cursor.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,)).fetchone()
    conn.close()
    return row

def get_playlist_ids(username):
    conn, cursor = db_connect(username)
    rows = cursor.execute("SELECT id FROM playlists").fetchall()
    conn.close()
    return {row["id"] for row in rows}

def get_playlists_by_channel(username, channel_id):
    conn, cursor = db_connect(username)
    rows = cursor.execute("SELECT * FROM playlists WHERE channel_id = ?", (channel_id,)).fetchall()
    conn.close()
    return rows

def save_playlist(username, playlist_id, channel_id, title, description, thumbnail, created):
    conn, cursor = db_connect(username)

    try:
        cursor.execute("""
                INSERT OR IGNORE INTO playlists (id, channel_id, title, description, thumbnail, created) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (playlist_id, channel_id, title, description, thumbnail, created)
        )
        conn.commit()

        rows_inserted = cursor.rowcount
        if rows_inserted > 0:
            return "SUCCESS"
        else:
            print(f"Playlist {title} ({playlist_id}) already exists.")
            return "EXISTS"

    except sqlite3.Error as e:
        print(f"Database error while saving the playlist: {e}")
        return "ERROR"

    finally:
        conn.close()

def update_playlist(username, playlist_id, title, description, thumbnail, created):
    conn, cursor = db_connect(username)

    try:
        cursor.execute("""
                UPDATE playlists 
                SET (title, description, thumbnail, created) = (?, ?, ?, ?) 
                WHERE id = ?
            """, (title, description, thumbnail, created, playlist_id))
        conn.commit()

        rows_updated = cursor.rowcount
        if rows_updated > 0:
            return "SUCCESS"
        else:
            return "NOT_FOUND"

    except sqlite3.Error as e:
        print(f"Database error while updating the playlist: {e}")
        return "ERROR"

    finally:
        conn.close()

def update_playlists(username, playlists):
    conn, cursor = db_connect(username)
    rowcount = 0

    try:
        for playlist in playlists:
            cursor.execute("""
                    UPDATE playlists 
                    SET (title, description, thumbnail, created) = (?, ?, ?, ?) 
                    WHERE id = ?
                """, (
                    playlist["title"],
                    playlist["description"],
                    playlist["thumbnail"],
                    playlist["created"],
                    playlist["playlist_id"]
                )
            )
            rowcount += cursor.rowcount
        conn.commit()

        if rowcount == len(playlists):
            return "SUCCESS"
        else:
            return "PARTIAL"

    except sqlite3.Error as e:
        print(f"Database error while updating the playlist: {e}")
        return "ERROR"

    finally:
        conn.close()

def delete_playlist(username, playlist_id):
    conn, cursor = db_connect(username)

    try:
        cursor.execute("DELETE FROM playlists WHERE id = ?",(playlist_id,))
        conn.commit()

        rows_deleted = cursor.rowcount
        if rows_deleted > 0:
            return "SUCCESS"
        else:
            return "NOT_FOUND"

    except sqlite3.Error as e:
        print(f"Database error while deleting the playlist: {e}")
        return "ERROR"

    finally:
        conn.close()

""" VIDEOS """

def get_video(username, video_id):
    conn, cursor = db_connect(username)
    row = cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    conn.close()
    return row

def get_videos(username):
    conn, cursor = db_connect(username)
    rows = cursor.execute("SELECT * FROM videos").fetchall()
    conn.close()
    return rows

def get_videos_by_playlist(username, playlist_id):
    conn, cursor = db_connect(username)
    rows = cursor.execute("SELECT * FROM videos WHERE playlist_id = ?", (playlist_id,)).fetchall()
    conn.close()
    return rows

def get_videos_ids_by_playlist(username, playlist_id):
    conn, cursor = db_connect(username)
    rows = cursor.execute("SELECT id FROM videos WHERE playlist_id = ?", (playlist_id,)).fetchall()
    conn.close()
    return {row["id"] for row in rows}

def save_videos(username, videos):
    conn, cursor = db_connect(username)
    rowcount = 0

    try:
        for video in videos:
            cursor.execute("""
                    INSERT OR IGNORE INTO videos (id, playlist_id, position, title, description, thumbnail, duration, published)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                    video["id"],
                    video["playlist_id"],
                    video["position"],
                    video["title"],
                    video["description"],
                    video["thumbnail"],
                    video["duration"],
                    video["published"]
                )
            )
            rowcount += cursor.rowcount
        conn.commit()

        if rowcount == len(videos):
            return "SUCCESS"
        else:
            return "PARTIAL"

    except sqlite3.Error as e:
        print(f"Database error while saving the videos: {e}")
        return "ERROR"

    finally:
        conn.close()

def update_videos(username, videos):
    conn, cursor = db_connect(username)
    rowcount = 0

    try:
        for video in videos:
            cursor.execute("""
                UPDATE videos 
                SET 
                    title = ?,
                    description = ?,
                    thumbnail = ?,
                    duration = ?,
                    published = ?,
                    position = ?
                WHERE id = ?
            """, (
                video["title"],
                video["description"],
                video["thumbnail"],
                video["duration"],
                video["published"],
                video["position"],
                video["id"]
            ))
            rowcount += cursor.rowcount
        conn.commit()

        if rowcount == len(videos):
            return "SUCCESS"
        else:
            return "PARTIAL"

    except sqlite3.Error as e:
        print(f"Database error while updating the videos: {e}")
        return "ERROR"

    finally:
        conn.close()

def is_video_watched(username, video_id):
    conn, cursor = db_connect(username)
    row = cursor.execute("SELECT is_watched FROM videos WHERE id = ?", (video_id,)).fetchone()
    conn.close()
    return row["is_watched"] if row else None

def set_video_watched(username, video_id, watched):
    conn, cursor = db_connect(username)

    try:
        cursor.execute("UPDATE videos SET is_watched = ? WHERE id = ?", (watched, video_id))
        conn.commit()

        rows_updated = cursor.rowcount
        if rows_updated > 0:
            return "SUCCESS"
        else:
            return "NOT_FOUND"

    except sqlite3.Error as e:
        print(f"Database error while updating the video: {e}")
        return "ERROR"

    finally:
        conn.close()

def set_videos_watched_by_playlist(username, playlist_id, watched):
    conn, cursor = db_connect(username)

    try:
        cursor.execute("UPDATE videos SET is_watched = ? WHERE playlist_id = ?", (watched, playlist_id))
        conn.commit()

        rows_updated = cursor.rowcount
        if rows_updated > 0:
            return "SUCCESS"
        else:
            return "NOT_FOUND"

    except sqlite3.Error as e:
        print(f"Database error while updating the video: {e}")
        return "ERROR"

    finally:
        conn.close()
