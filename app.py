from flask import *
import sqlite3
from dotenv import load_dotenv
from os import getenv
from datetime import timedelta
from math import ceil

load_dotenv()

import database_manager as db
import youtube_api as yt
from pagination_cache import *

app = Flask(__name__)
app.secret_key = getenv('SECRET_KEY')
app.jinja_env.globals.update(ceil=ceil)

@app.before_request
def permanent_session():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=60)

@app.context_processor
def inject_current_path():
    return dict(path=request.path)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        password_repeated = request.form["password_repeated"]

        if password != password_repeated:
            flash("Passwords don't match!", "error")
            return redirect(url_for("register"))
        try:
            db.register_user(username, password)
        except sqlite3.IntegrityError:
            flash("This username already exists!", "error")
            return redirect(url_for("register"))

        flash("Account created successfully!", "success")
        return redirect(url_for("login"))

    elif "user_id" in session:
        return redirect(url_for("home"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = db.login_user(username, password)
        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password!", "error")
            return redirect(url_for("login"))

    elif "user_id" in session:
        return redirect(url_for("home"))

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

    playlists_sort_by = db.get_preferences(session["user_id"])["playlists_sort_by"]
    playlists_hide_completed = db.get_preferences(session["user_id"])["playlists_hide_completed"]

    playlists = db.get_saved_playlists(session["username"], channel_id)
    channel_name = db.get_channel_data(session["username"], playlists[0]["channel_id"])["name"] if playlists else None

    if playlists_sort_by == "date_saved":
        playlists.sort(key=lambda p: p["date_saved"], reverse=True)
    elif playlists_sort_by == "last_watched":
        playlists.sort(key=lambda p: p["last_watched"], reverse=True)
    elif playlists_sort_by == "title":
        playlists.sort(key=lambda p: p["title"].lower())
    elif playlists_sort_by == "progress":
        playlists.sort(key=lambda p: p["progress"], reverse=True)

    return render_template("index.html",
                           playlists=playlists,
                           channel_name=channel_name,
                           playlists_sort_by=playlists_sort_by,
                           playlists_hide_completed=playlists_hide_completed)

@app.route("/search", methods=["GET"])
def search():
    if "user_id" not in session:
        return redirect(url_for("login"))

    search_results_per_page = db.get_preferences(session["user_id"])["search_results_per_page"]

    query = request.args.get("q", "")
    current_page = int(request.args.get("page", 1))

    channels = []
    tokens = [None, None]
    total_results = 0

    if query:
        token = get_token(query, current_page)
        data = yt.search_channels(query, search_results_per_page, token)

        channels = data["channels"]
        tokens = data["tokens"]
        total_results = data["total_results"]

        cache_token(query, current_page, tokens[1])

    return render_template("search.html",
                           channels=channels,
                           query=query,
                           search_results_per_page=search_results_per_page,
                           total_results=total_results,
                           current_page=current_page,
                           prevToken=tokens[0],
                           nextToken=tokens[1])

@app.route("/search/<channel_id>", methods=["GET", "POST"])
def search_channel(channel_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    search_playlists_sort_by = db.get_preferences(session["user_id"])["search_playlists_sort_by"]
    search_playlists_per_page = db.get_preferences(session["user_id"])["search_playlists_per_page"]
    search_playlists_hide_saved = db.get_preferences(session["user_id"])["search_playlists_hide_saved"]

    data = yt.get_channel_playlists(channel_id, search_playlists_per_page)
    playlists = data["playlists"]
    tokens = data["tokens"]
    total_playlists = data["total_playlists"]
    saved_playlists = db.get_saved_playlist_ids(session["username"])
    channel_name = playlists[0]["channel_name"] if playlists else None

    if search_playlists_sort_by == "title":
        playlists.sort(key=lambda p: p["title"].lower())
    elif search_playlists_sort_by == "date_created":
        playlists.sort(key=lambda p: p["date_created"], reverse=True)

    if not playlists:
        playlists = "empty"

    if request.method == "POST":
        token = request.form.get("token")
        data = yt.get_channel_playlists(channel_id, search_playlists_per_page, token)
        playlists = data["playlists"]
        tokens = data["tokens"]
        total_playlists = data["total_playlists"]

    return render_template("search.html",
                           channel_name=channel_name,
                           playlists=playlists,
                           saved_playlists=saved_playlists,
                           search_playlists_sort_by=search_playlists_sort_by,
                           search_playlists_per_page=search_playlists_per_page,
                           search_playlists_hide_saved=search_playlists_hide_saved,
                           total_playlists=total_playlists,
                           prevToken=tokens[0],
                           nextToken=tokens[1])

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

    videos_hide_watched = db.get_preferences(session["user_id"])["videos_hide_watched"]

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
            "duration": video["duration"],
            "published": video["published"],
            "is_watched": 0
        } for video in data]

    return render_template("playlist.html",
                           playlist=playlist_data,
                           saved_playlists=saved_playlists,
                           videos=videos,
                           videos_hide_watched=videos_hide_watched)

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
    db.insert_or_update_videos(session["username"], videos)

    return jsonify({"status": "success"})

@app.route("/set_preference", methods=["POST"])
def set_preference():
    PREFERENCES = [
        "playlists_sort_by",
        "playlists_hide_completed",
        "videos_hide_watched",
        "search_results_per_page",
        "search_playlists_per_page",
        "search_playlists_sort_by",
        "search_playlists_hide_saved"
    ]

    for preference in PREFERENCES:
        value = request.form.get(preference)
        if value:
            try:
                db.set_preference(session["user_id"], preference, value)
                return jsonify({"status": "success"})
            except Exception as e:
                print("Something went wrong. Message: ", e)
                return jsonify({"status": "error"}), 500

    return jsonify({"status": "error"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)