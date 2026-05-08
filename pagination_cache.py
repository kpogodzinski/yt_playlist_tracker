from flask import session

def get_token(query, page):
    return session.get("yt_cache", {}).get(query, {}).get(str(page))

def cache_token(query, page, next_token):
    session.setdefault("yt_cache", {})

    if "yt_cache" not in session:
        session["yt_cache"] = {}

    if query not in session["yt_cache"]:
        session["yt_cache"][query] = {}

    session["yt_cache"][query][str(page + 1)] = next_token

    session.modified = True