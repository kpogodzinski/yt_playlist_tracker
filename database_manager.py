import sqlite3
import youtube_api as yt
import os
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
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            __create_users_db__()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                           (username, password_hash))
        else:
            raise

    conn.commit()
    conn.close()

    __create_user_tables__(username)

def login_user(username, password):
    if not os.path.exists("databases"):
        os.mkdir("databases")

    conn, cursor = db_connect("users")

    try:
        cursor.execute("SELECT * FROM users WHERE username = (?)", (username,))
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            __create_users_db__()
            cursor.execute("SELECT * FROM users WHERE username = (?)", (username,))
        else:
            raise

    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[2], password):
        return user[0:2]
    else:
        return None

def __create_users_db__():
    conn, cursor = db_connect("users")
    cursor.execute("""
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL
                    );
                """)
    conn.commit()
    conn.close()

def __create_user_tables__(username):
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
                    thumbnail TEXT,
                    date_saved TEXT DEFAULT current_timestamp,
                    last_watched TEXT DEFAULT current_timestamp,
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
                    thumbnail TEXT,
                    duration TEXT,
                    uploaded TEXT,
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
                        WHEN NEW.is_watched = 1
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
    conn.close()

""" CHANNELS """

def save_channel(username, channel_id, name, thumbnail):
    conn, cursor = db_connect(username)
    cursor.execute("INSERT INTO channels VALUES (?, ?, ?)", (channel_id, name, thumbnail))
    conn.commit()
    conn.close()

def get_channel_data(username, channel_id):
    conn, cursor = db_connect(username)
    row = cursor.execute("SELECT * FROM channels WHERE id = (?)", (channel_id,)).fetchone()
    conn.close()
    return row

def get_saved_channels(username):
    conn, cursor = db_connect(username)
    rows = cursor.execute("SELECT * FROM channels").fetchall()
    conn.close()
    return rows

""" PLAYLISTS """

def save_playlist(username, playlist_id, channel_id, title, thumbnail):
    conn, cursor = db_connect(username)
    cursor.execute("INSERT INTO playlists (id, channel_id, title, thumbnail) VALUES (?, ?, ?, ?)",
                   (playlist_id, channel_id, title, thumbnail))

    videos = yt.get_videos(playlist_id)
    for video in videos:
        cursor.execute("INSERT INTO videos (id, playlist_id, position, title, thumbnail, duration, uploaded) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (video.get("id"),
                    playlist_id,
                    video.get("position"),
                    video.get("title"),
                    video.get("thumbnail"),
                    video.get("duration"),
                    video.get("uploaded")))
    conn.commit()
    conn.close()

def get_playlist_data(username, playlist_id):
    conn, cursor = db_connect(username)
    row = cursor.execute("SELECT * FROM playlists WHERE id = (?)", (playlist_id,)).fetchone()
    conn.close()
    return row

def get_saved_playlists(username, channel_id):
    conn, cursor = db_connect(username)
    rows = cursor.execute("SELECT * FROM playlists WHERE channel_id = (?)", (channel_id,)).fetchall()
    conn.close()
    return rows

def get_saved_playlist_ids(username):
    conn, cursor = db_connect(username)
    rows = cursor.execute("SELECT id FROM playlists").fetchall()
    conn.close()
    return {row["id"] for row in rows}

def remove_playlist(username, playlist_id):
    conn, cursor = db_connect(username)
    cursor.execute("DELETE FROM playlists WHERE id = (?)",
                   (playlist_id,))
    conn.commit()
    conn.close()

""" VIDEOS """

def get_playlist_videos(username, playlist_id):
    conn, cursor = db_connect(username)
    rows = cursor.execute("SELECT * FROM videos WHERE playlist_id = (?)", (playlist_id,)).fetchall()
    conn.close()
    return rows

def insert_or_update_video(username, id, playlist_id, position, title, thumbnail, duration, uploaded):
    conn, cursor = db_connect(username)

    try:
        cursor.execute(
            "INSERT INTO videos (id, playlist_id, position, title, thumbnail, duration, uploaded) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (id, playlist_id, position, title, thumbnail, duration, uploaded))
    except sqlite3.IntegrityError:
        cursor.execute(
            """
            UPDATE videos 
            SET playlist_id = ?, 
                position = ?, 
                title = ?, 
                thumbnail = ?, 
                duration = ?, 
                uploaded = ?
            WHERE id = ?
            """,
            (playlist_id, position, title, thumbnail, duration, uploaded, id)
        )
    conn.commit()
    conn.close()

def watch_video(username, video_id, unwatch=False):
    conn, cursor = db_connect(username)
    cursor.execute("UPDATE videos SET is_watched = (?) WHERE id = (?)", (not unwatch, video_id))
    conn.commit()
    conn.close()

def is_video_watched(username, video_id):
    conn, cursor = db_connect(username)
    row = cursor.execute("SELECT is_watched FROM videos WHERE id = (?)", (video_id,)).fetchone()
    conn.close()
    return row["is_watched"] if row else None
