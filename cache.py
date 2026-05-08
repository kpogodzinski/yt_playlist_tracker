from flask_caching import Cache

cache = Cache(config={
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 3600
})

def get_token(query, page):
    tokens = cache.get(f"tokens:{query}") or {}
    return tokens.get(str(page))

def cache_token(query, page, next_token):
    key = f"tokens:{query.strip().lower()}"
    tokens = cache.get(key) or {}

    tokens[str(page + 1)] = next_token

    cache.set(key, tokens, timeout=600)

def get_playlists(channel_id):
    return cache.get(f"playlists:{channel_id}")

def cache_playlists(channel_id, playlists):
    cache.set(f"playlists:{channel_id}", playlists, timeout=1800)
