import requests
import re
from os import getenv
from itertools import islice
from datetime import datetime

YOUTUBE_API_KEY = getenv("YOUTUBE_API_KEY")

def get_channel_playlists(channel_id):
    playlists = []
    url = "https://www.googleapis.com/youtube/v3/playlists"
    page_token = None
    while True:
        params = {
            "part": "snippet",
            "channelId": channel_id,
            "maxResults": 50,
            "key": YOUTUBE_API_KEY
        }
        if page_token:
            params["pageToken"] = page_token

        response = requests.get(url, params=params)
        data = response.json()
        playlists.extend(data.get("items", []))

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    data = [{
        "id": playlist["id"],
        "title": playlist["snippet"]["title"],
        "thumbnail": playlist["snippet"]["thumbnails"]["high"]["url"],
        "channel_id": playlist["snippet"]["channelId"],
        "channel_name": playlist["snippet"]["channelTitle"],
        "date_created": playlist["snippet"]["publishedAt"]
    } for playlist in playlists]
    return data

def get_playlist_data(playlist_id):
    url = "https://www.googleapis.com/youtube/v3/playlists"
    params = {
        "part": "snippet",
        "id": playlist_id,
        "key": YOUTUBE_API_KEY
    }

    response = requests.get(url, params=params)
    snippet = response.json()["items"][0]["snippet"]
    data = {
        "playlist_id": playlist_id,
        "channel_id": snippet.get("channelId"),
        "title": snippet.get("title"),
        "thumbnail": snippet.get("thumbnails").get("high").get("url")
    }
    return data

def get_channel_data(channel_id):
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "snippet",
        "id": channel_id,
        "key": YOUTUBE_API_KEY
    }

    response = requests.get(url, params=params)
    snippet = response.json()["items"][0]["snippet"]
    data = {
        "channel_id": channel_id,
        "name": snippet.get("title"),
        "thumbnail": snippet.get("thumbnails").get("high").get("url")
    }
    return data

def __get_videos_durations_and_dates__(ids):
    url = "https://www.googleapis.com/youtube/v3/videos/"
    params = {
        "part": "snippet,contentDetails",
        "id": ids,
        "key": YOUTUBE_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()

    video_durations = {}
    video_dates = {}
    for item in data["items"]:
        video_durations[item["id"]] = item["contentDetails"]["duration"]
        video_dates[item["id"]] = item["snippet"]["publishedAt"]

    return video_durations, video_dates

def __parse_duration__(duration):
    pattern = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")
    match = pattern.match(duration)
    if not match:
        return 0, 0, 0

    h, m, s = match.groups()
    h = int(h or 0)
    m = int(m or 0)
    s = int(s or 0)

    if h > 0:
        return f"{h}:{m:02}:{s:02}"
    else:
        return f"{m:02}:{s:02}"

def __batch__(iterable, n=50):
    it = iter(iterable)
    while __batch__ := list(islice(it, n)):
        yield __batch__

def get_videos(playlist_id):
    videos = []
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    page_token = None
    while True:
        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": 50,
            "key": YOUTUBE_API_KEY
        }
        if page_token:
            params["pageToken"] = page_token

        response = requests.get(url, params=params)
        data = response.json()
        videos.extend(data.get("items", []))

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    video_ids = [v["snippet"]["resourceId"]["videoId"] for v in videos]
    video_durations = {}
    video_dates = {}
    for batch_ids in __batch__(video_ids, 50):
        ids = ",".join(batch_ids)
        dur, dat = __get_videos_durations_and_dates__(ids)
        video_durations.update(dur)
        video_dates.update(dat)

    data = []
    for video in videos:
        try:
            vid = video["snippet"]["resourceId"]["videoId"]
            data.append({
                "id": video["id"],
                "playlist_id": playlist_id,
                "position": video["snippet"]["position"],
                "title": video["snippet"]["title"],
                "thumbnail": video["snippet"]["thumbnails"]["high"]["url"],
                "duration": __parse_duration__(video_durations[vid]),
                "published": (datetime.fromisoformat(video_dates[vid].replace("Z", "+00:00"))).strftime("%d %B %Y")
            })
        except KeyError:
            print(f"Video {video['id']} is private.")
    return data

def search_channels(query, limit, page_token=None):
    channels = []
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "channel",
        "maxResults": limit,
        "pageToken": page_token,
        "key": YOUTUBE_API_KEY,
    }

    response = requests.get(url, params=params)
    data = response.json()
    channels.extend(data.get("items", []))
    tokens = [data.get("prevPageToken"), data.get("nextPageToken")]

    data = []
    for channel in channels:
        try:
            data.append({
                "id": channel["id"]["channelId"],
                "title": channel["snippet"]["title"],
                "thumbnail": channel["snippet"]["thumbnails"]["high"]["url"]
            })
        except KeyError:
            print(f"Channel {channel['id']} could not be loaded.")

    return data, tokens