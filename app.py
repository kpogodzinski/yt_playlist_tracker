import os

from dotenv import load_dotenv
load_dotenv()

from flask import *
import sqlite3
from os import getenv
from datetime import timedelta
from math import ceil

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")
app.jinja_env.globals.update(ceil=ceil)

import database_manager as db
import youtube_api as yt
import cache as cache

cache.cache.init_app(app)

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
            session["display_name"] = user[2] or ""
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

    channels = db.get_channels(session["username"])
    display_name = session["display_name"] or session["username"]

    return render_template("index.html", channels=channels, display_name=display_name)

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    display_name = session["display_name"]

    if request.method == "POST":
        ### PROFILE SECTION ###
        if request.form["form_id"] == "profileForm":
            new_display_name = request.form["display_name"]

            status = db.change_display_name(username, new_display_name)
            if status == "error":
                flash("Something went wrong.", "error profile")
            elif status == "success":
                flash("Display name changed successfully.", "success profile")
                session["display_name"] = new_display_name
                return redirect(url_for("profile"))

        ### PASSWORD SECTION ###
        elif request.form["form_id"] == "changePasswordForm":
            current_password = request.form["current_password"]
            new_password = request.form["new_password"]
            repeat_new_password = request.form["repeat_new_password"]

            if new_password != repeat_new_password:
                flash("Passwords don't match!", "error password")
                return redirect(url_for("profile"))

            status = db.change_password(username, current_password, new_password)
            if status == "invalid":
                flash("Invalid current password!", "error password")
            elif status == "error":
                flash("Something went wrong.", "error password")
            else:
                flash("Password changed successfully.", "success password")
            return redirect(url_for("profile"))

    ### DELETE ACCOUNT SECTION ###
    flash("For security reasons, please confirm your password one last time.", "warning delete")
    flash("All your data will be permanently deleted.", "warning delete")
    return render_template("profile.html", username=username, display_name=display_name)

@app.route("/<channel_id>")
def channel(channel_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    current_page = int(request.args.get("page", 1))
    if current_page < 1:
        current_page = 1

    preferences = db.get_preferences(session["user_id"])
    playlists_sort_by = preferences["playlists_sort_by"]
    playlists_per_page = preferences["playlists_per_page"]
    playlists_hide_completed = preferences["playlists_hide_completed"]

    playlists = db.get_playlists_by_channel(session["username"], channel_id)
    all_playlist_ids = [p["id"] for p in playlists]
    channel_name = db.get_channel(session["username"], playlists[0]["channel_id"])["name"] if playlists else None

    total_playlists = len(playlists)
    if playlists_hide_completed:
        playlists = [p for p in playlists if p["progress"] < 100]
    visible_playlists = len(playlists)

    if playlists_sort_by == "date_saved":
        playlists.sort(key=lambda p: p["date_saved"], reverse=True)
    elif playlists_sort_by == "last_watched":
        playlists.sort(key=lambda p: p["last_watched"], reverse=True)
    elif playlists_sort_by == "title":
        playlists.sort(key=lambda p: p["title"].lower())
    elif playlists_sort_by == "progress":
        playlists.sort(key=lambda p: p["progress"], reverse=True)

    start = (current_page - 1) * playlists_per_page
    end = start + playlists_per_page
    playlists = playlists[start:end]

    return render_template("index.html",
                           playlists=playlists,
                           all_playlist_ids=all_playlist_ids,
                           channel_id=channel_id,
                           channel_name=channel_name,
                           playlists_sort_by=playlists_sort_by,
                           playlists_per_page=playlists_per_page,
                           playlists_hide_completed=playlists_hide_completed,
                           total_playlists=total_playlists,
                           visible_playlists=visible_playlists,
                           current_page=current_page)

@app.route("/search")
def search():
    if "user_id" not in session:
        return redirect(url_for("login"))

    query = request.args.get("q", "")
    current_page = int(request.args.get("page", 1))
    if current_page < 1:
        current_page = 1

    search_results_per_page = db.get_preferences(session["user_id"])["search_results_per_page"]

    channels = []
    total_results = 0

    if query:
        if cache.get_channels(query, "first") is None:
            data = yt.search_channels(query)
            cache.cache_channels(query, "first", data)

        data = cache.get_channels(query, "first")
        next_token = data["next_token"]
        total_results = data["total_results"]
        channels = data["channels"]

        required_items = current_page * search_results_per_page
        while len(channels) < required_items and next_token:
            if cache.get_channels(query, next_token) is None:
                data = yt.search_channels(query, next_token)
                cache.cache_channels(query, next_token, data)

            data = cache.get_channels(query, next_token)
            channels.extend(data["channels"])
            next_token = data["next_token"]

        start = (current_page - 1) * search_results_per_page
        end = start + search_results_per_page
        channels = channels[start:end]

    return render_template("search.html",
                           channels=channels,
                           query=query,
                           search_results_per_page=search_results_per_page,
                           total_results=total_results,
                           current_page=current_page)

@app.route("/search/<channel_id>")
def search_channel(channel_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    current_page = int(request.args.get("page", 1))
    if current_page < 1:
        current_page = 1

    search_playlists_sort_by = db.get_preferences(session["user_id"])["search_playlists_sort_by"]
    search_playlists_per_page = db.get_preferences(session["user_id"])["search_playlists_per_page"]
    search_playlists_hide_saved = db.get_preferences(session["user_id"])["search_playlists_hide_saved"]

    if cache.get_playlists(channel_id) is None:
        playlists = yt.get_playlists_by_channel(channel_id)
        cache.cache_playlists(channel_id, playlists)

    playlists = cache.get_playlists(channel_id)
    total_playlists = playlists["total_playlists"]
    playlists = playlists["playlists"]
    channel_name = playlists[0]["channel_name"] if playlists else None

    saved_playlists = db.get_playlist_ids(session["username"])
    if search_playlists_hide_saved:
        playlists = [p for p in playlists if p["id"] not in saved_playlists]
    visible_playlists = len(playlists)

    if search_playlists_sort_by == "title":
        playlists.sort(key=lambda p: p["title"].lower())
    elif search_playlists_sort_by == "date_created":
        playlists.sort(key=lambda p: p["date_created"], reverse=True)

    start = (current_page - 1) * search_playlists_per_page
    end = start + search_playlists_per_page
    playlists = playlists[start:end]

    if not playlists:
        playlists = "empty"

    return render_template("search.html",
                           channel_id=channel_id,
                           channel_name=channel_name,
                           playlists=playlists,
                           saved_playlists=saved_playlists,
                           search_playlists_sort_by=search_playlists_sort_by,
                           search_playlists_per_page=search_playlists_per_page,
                           search_playlists_hide_saved=search_playlists_hide_saved,
                           total_playlists=total_playlists,
                           visible_playlists=visible_playlists,
                           current_page=current_page)

@app.route("/playlist/<playlist_id>")
def playlist_details(playlist_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    videos_hide_watched = db.get_preferences(session["user_id"])["videos_hide_watched"]
    saved_playlists = db.get_playlist_ids(session["username"])

    if playlist_id in saved_playlists:
        playlist_data = db.get_playlist(session["username"], playlist_id)
        videos = db.get_videos_by_playlist(session["username"], playlist_id)
        channel_id = playlist_data["channel_id"]
        channel_name = db.get_channel(session["username"], playlist_data["channel_id"])["name"] if playlist_data else None
    else:
        data = yt.get_playlist(playlist_id)
        channel_id = data["channel_id"]
        channel_name = data["channel_name"]
        playlist_data = {
            "id": playlist_id,
            "title": data["title"],
            "description": data["description"],
            "thumbnail": data["thumbnail"],
            "created": data["created"],
            "count": data["count"],
            "progress": 0
        }
        data = yt.get_videos_by_playlist(playlist_id)
        videos = [{
            "id": video["id"],
            "playlist_id": playlist_id,
            "position": video["position"],
            "title": video["title"],
            "description": video["description"],
            "thumbnail": video["thumbnail"],
            "duration": video["duration"],
            "published": video["published"],
            "is_watched": 0
        } for video in data]

    total_videos = len(videos)
    watched_videos = len([v for v in videos if v["is_watched"]])
    if videos_hide_watched:
        videos = [v for v in videos if not v["is_watched"]]

    return render_template("playlist.html",
                           playlist=playlist_data,
                           saved_playlists=saved_playlists,
                           channel_id=channel_id,
                           channel_name=channel_name,
                           videos=videos,
                           watched_videos=watched_videos,
                           total_videos=total_videos,
                           videos_hide_watched=videos_hide_watched)

@app.route("/set_preference", methods=["POST"])
def set_preference():
    if "user_id" not in session:
        return redirect(url_for("login"))

    PREFERENCES = [
        "playlists_sort_by",
        "playlists_per_page",
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

@app.route("/delete_account", methods=["DELETE"])
def delete_account():
    if "user_id" not in session:
        return redirect(url_for("login"))

    password = request.get_json()["password"]
    if db.check_password(session["username"], password):
        db.delete_user(session["user_id"])
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "databases", f"{session['username']}.db")
        os.remove(db_path)
        session.clear()
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "wrong_password"})


########## BEGIN API ##########

""" USERS """

""" CHANNELS """
@app.route("/api/channels/<channel_id>", methods=["GET"])
def get_channel(channel_id):
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    channel = db.get_channel(session["username"], channel_id)

    if not channel:
        return jsonify({"status": "error", "message": "Channel not found"}), 404

    channel = dict(channel)
    return jsonify({"status": "success", "data": channel}), 200

@app.route("/api/channels", methods=["POST"])
def save_channel():
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    channel_id = request.get_json().get("channel_id")
    channel = yt.get_channel(channel_id)

    status = db.save_channel(session["username"], channel_id, channel["name"], channel["thumbnail"])

    if status == "SUCCESS":
        return jsonify({"status": "success", "message": "Channel saved"}), 201
    elif status == "EXISTS":
        return jsonify({"status": "error", "message": "Channel already exists"}), 409
    elif status == "ERROR":
        return jsonify({"status": "error", "message": "Internal database error"}), 500

""" PLAYLISTS """
@app.route("/api/playlists/<playlist_id>", methods=["GET"])
def get_playlist(playlist_id):
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    playlist = db.get_playlist(session["username"], playlist_id)

    if not playlist:
        return jsonify({"status": "error", "message": "Playlist not found"}), 404

    playlist = dict(playlist)
    return jsonify({"status": "success", "data": playlist}), 200

@app.route("/api/playlists", methods=["POST"])
def save_playlist():
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    playlist_id = request.get_json().get("playlist_id")
    playlist = yt.get_playlist(playlist_id)

    status = db.save_playlist(
        session["username"],
        playlist_id,
        playlist["channel_id"],
        playlist["title"],
        playlist["description"],
        playlist["thumbnail"],
        playlist["created"]
    )

    if status == "SUCCESS":
        return jsonify({"status": "success", "message": "Playlist saved"}), 201
    elif status == "EXISTS":
        return jsonify({"status": "error", "message": "Playlist already exists"}), 409
    elif status == "ERROR":
        return jsonify({"status": "error", "message": "Internal database error"}), 500

@app.route("/api/playlists/<playlist_id>", methods=["PUT"])
def update_playlist(playlist_id):
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    playlist = yt.get_playlist(playlist_id)

    status = db.update_playlist(
        session["username"],
        playlist_id,
        playlist["title"],
        playlist["description"],
        playlist["thumbnail"],
        playlist["created"]
    )

    if status == "SUCCESS":
        return jsonify({"status": "success", "message": "Playlist updated"}), 200
    elif status == "NOT_FOUND":
        return jsonify({"status": "error", "message": "Playlist does not exist"}), 404
    elif status == "ERROR":
        return jsonify({"status": "error", "message": "Internal database error"}), 500

@app.route("/api/playlists", methods=["PUT"])
def update_playlists():
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    playlist_ids = db.get_playlist_ids(session["username"])
    playlists = yt.get_playlists(playlist_ids)

    status = db.update_playlists(session["username"], playlists)

    if status == "SUCCESS":
        return jsonify({"status": "success", "message": "Playlists updated"}), 200
    elif status == "PARTIAL":
        return jsonify({"status": "success", "message": "Some playlists not updated"}), 200
    elif status == "ERROR":
        return jsonify({"status": "error", "message": "Internal database error"}), 500

@app.route("/api/playlists/<playlist_id>", methods=["DELETE"])
def delete_playlist(playlist_id):
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    status = db.delete_playlist(session["username"], playlist_id)

    if status == "SUCCESS":
        return jsonify({"status": "success", "message": "Playlist deleted"}), 200
    elif status == "NOT_FOUND":
        return jsonify({"status": "error", "message": "Playlist not found"}), 404
    elif status == "ERROR":
        return jsonify({"status": "error", "message": "Internal database error"}), 500

""" VIDEOS """
@app.route("/api/videos/<video_id>", methods=["GET"])
def get_video(video_id):
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    video = db.get_video(session["username"], video_id)

    if not video:
        return jsonify({"status": "error", "message": "Video not found"}), 404

    video = dict(video)
    return jsonify({"status": "success", "data": video}), 200

@app.route("/api/videos", methods=["GET"])
def get_videos():
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    playlist_id = request.args.get("playlist_id")

    if playlist_id:
        playlist = db.get_playlist(session["username"], playlist_id)

        if playlist is None:
            return jsonify({"status": "error", "message": "Playlist not found"}), 404

        videos = db.get_videos_by_playlist(session["username"], playlist_id)

    else:
        videos = db.get_videos(session["username"])

    videos = [dict(video) for video in videos]
    return jsonify({"status": "success", "data": videos}), 200

@app.route("/api/videos", methods=["POST"])
def save_videos_by_playlist():
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.get_json()
    playlist_id = data["playlist_id"]
    videos = yt.get_videos_by_playlist(playlist_id)

    status = db.save_videos(session["username"], videos)

    if status == "SUCCESS":
        return jsonify({"status": "success", "message": "Videos saved"}), 201
    elif status == "PARTIAL":
        return jsonify({"status": "success", "message": "Some videos already exist"}), 200
    elif status == "ERROR":
        return jsonify({"status": "error", "message": "Internal database error"}), 500

@app.route("/api/videos", methods=["PUT"])
def sync_videos_by_playlist():
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.get_json()
    playlist_id = data["playlist_id"]

    videos = yt.get_videos_by_playlist(playlist_id)
    existing_ids = db.get_videos_ids_by_playlist(session["username"], playlist_id)
    existing_videos = [v for v in videos if v["id"] in existing_ids]
    new_videos = [v for v in videos if v["id"] not in existing_ids]

    status = db.save_videos(session["username"], new_videos)

    if status == "ERROR":
        return jsonify({"status": "error", "message": "Internal database error"}), 500

    status = db.update_videos(session["username"], existing_videos)

    if status == "SUCCESS":
        return jsonify({"status": "success", "message": "Videos updated"}), 200
    elif status == "PARTIAL":
        return jsonify({"status": "success", "message": "Some videos not updated"}), 200
    elif status == "ERROR":
        return jsonify({"status": "error", "message": "Internal database error"}), 500

@app.route("/api/videos/<video_id>", methods=["PATCH"])
def set_video_watched(video_id):
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    watched = request.get_json()["watched"]

    status = db.set_video_watched(session["username"], video_id, watched)

    if status == "SUCCESS":
        return jsonify({"status": "success", "message": "Video updated", "watched": watched}), 200
    elif status == "NOT_FOUND":
        return jsonify({"status": "error", "message": "Video not found"}), 404
    elif status == "ERROR":
        return jsonify({"status": "error", "message": "Internal database error"}), 500

@app.route("/api/videos", methods=["PATCH"])
def set_videos_watched_by_playlist():
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.get_json()
    playlist_id = data["playlist_id"]
    watched = data["watched"]

    status = db.set_videos_watched_by_playlist(session["username"], playlist_id, watched)

    if status == "SUCCESS":
        return jsonify({"status": "success", "message": "Playlist videos updated", "watched": watched}), 200
    elif status == "NOT_FOUND":
        return jsonify({"status": "error", "message": "Playlist not found"}), 404
    elif status == "ERROR":
        return jsonify({"status": "error", "message": "Internal database error"}), 500

########## END API ##########

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)