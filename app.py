from flask import *
import sqlite3
from dotenv import load_dotenv
from os import getenv

load_dotenv()

import database_manager as db
import youtube_api as yt

app = Flask(__name__)
app.secret_key = getenv('SECRET_KEY')

@app.context_processor
def inject_current_path():
    return dict(path=request.path)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        password_repeated = request.form["password_repeated"]

        if password != password_repeated:
            return "Passwords don't match", 403
        try:
            db.register_user(username, password)
        except sqlite3.IntegrityError:
            return "Username already exists.", 403

        return redirect(url_for("login"))

    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = db.login_user(username, password)
        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect(url_for("home"))
        else:
            return "Invalid login or password."

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    channels = db.get_saved_channels(session["username"])

    return render_template("index.html", channels=channels)

@app.route("/<channel_id>")
def channel(channel_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    sort_by = request.args.get("sort_by", "date_saved")

    playlists = db.get_saved_playlists(session["username"], channel_id)
    channel_name = db.get_channel_data(session["username"], playlists[0]["channel_id"])["name"] if playlists else None

    if sort_by == "date_saved":
        playlists.sort(key=lambda p: p["date_saved"], reverse=True)
    elif sort_by == "date_watched":
        playlists.sort(key=lambda p: p["last_watched"], reverse=True)
    elif sort_by == "title":
        playlists.sort(key=lambda p: p["title"].lower())
    elif sort_by == "progress":
        playlists.sort(key=lambda p: p["progress"], reverse=True)

    return render_template("index.html", playlists=playlists, channel_name=channel_name, sort_by=sort_by)

@app.route("/search", methods=["GET", "POST"])
def search():
    if "user_id" not in session:
        return redirect(url_for("login"))

    channels = []

    if request.method == "POST":
        query = request.form.get("query")
        channels = yt.search_channels(query)

    return render_template("search.html", channels=channels)

@app.route("/search/<channel_id>")
def search_channel(channel_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    sort_by = request.args.get("sort_by", "date_created")

    playlists = yt.get_channel_playlists(channel_id)
    saved_playlists = db.get_saved_playlist_ids(session["username"])
    channel_name = playlists[0]["channel_name"] if playlists else None

    if sort_by == "title":
        playlists.sort(key=lambda p: p["title"].lower())
    elif sort_by == "date_created":
        playlists.sort(key=lambda p: p["date_created"], reverse=True)

    if not playlists:
        playlists = "empty"

    return render_template("search.html",
                           channel_name=channel_name,
                           playlists=playlists,
                           saved_playlists=saved_playlists,
                           sort_by=sort_by)

@app.route("/save_playlist/<playlist_id>", methods=["POST"])
def save_playlist(playlist_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    data = yt.get_playlist_data(playlist_id)
    channel = yt.get_channel_data(data["channel_id"])

    try:
        db.save_channel(session["username"], channel["channel_id"], channel["name"], channel["thumbnail"])
    except sqlite3.IntegrityError:
        print(f"Channel {channel['channel_id']} already exists.")

    status = "success"
    try:
        db.save_playlist(session["username"], playlist_id, data["channel_id"], data["title"], data["thumbnail"])
    except sqlite3.IntegrityError:
        status = "exists"

    return jsonify({"status": status})

@app.route("/remove_playlist/<playlist_id>", methods=["POST"])
def remove_playlist(playlist_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    status = "success"
    try:
        db.remove_playlist(session["username"], playlist_id)
    except sqlite3.IntegrityError:
        status = "error"

    return jsonify({"status": status})

@app.route("/playlist/<playlist_id>")
def playlist_details(playlist_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    saved_playlists = db.get_saved_playlist_ids(session["username"])
    if playlist_id in saved_playlists:
        playlist_data = db.get_playlist_data(session["username"], playlist_id)
        videos = db.get_playlist_videos(session["username"], playlist_id)
    else:
        data = yt.get_playlist_data(playlist_id)
        playlist_data = {
            "id": playlist_id,
            "title": data["title"],
            "thumbnail": data["thumbnail"],
            "progress": 0
        }
        data = yt.get_videos(playlist_id)
        videos = [{
            "id": video["id"],
            "playlist_id": playlist_id,
            "position": video["position"],
            "title": video["title"],
            "thumbnail": video["thumbnail"],
            "is_watched": 0
        } for video in data]

    return render_template("playlist.html",
                           playlist=playlist_data,
                           saved_playlists=saved_playlists,
                           videos=videos)

@app.route("/watch_video/<video_id>", methods=["POST"])
def watch_video(video_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        is_watched = db.is_video_watched(session["username"], video_id)
        if is_watched is not None:
            db.watch_video(session["username"], video_id, unwatch=is_watched)
            status = "unwatched" if is_watched else "watched"
        else:
            status = "not saved"
    except sqlite3.IntegrityError:
        status = "error"

    return jsonify({"status": status})

@app.route("/playlist/<playlist_id>/watch_all", methods=["POST"])
def watch_all(playlist_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    playlist = db.get_playlist_data(session["username"], playlist_id)
    videos = db.get_playlist_videos(session["username"], playlist_id)

    if playlist_id not in db.get_saved_playlist_ids(session["username"]):
        status = "not saved"
    else:
        for video in videos:
            db.watch_video(session["username"], video["id"], unwatch = playlist["progress"] == 100)
        status = "unwatched" if playlist["progress"] == 100 else "watched"

    return jsonify({"status": status})

@app.route("/fetch_playlist/<playlist_id>", methods=["POST"])
def fetch_playlist(playlist_id):
    videos = yt.get_videos(playlist_id)
    for video in videos:
        try:
            db.insert_video(session["username"],
                            video["id"],
                            video["playlist_id"],
                            video["position"],
                            video["title"],
                            video["thumbnail"])
        except sqlite3.IntegrityError:
            print(f"Video {video['id']} already exists.")

    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)