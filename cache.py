from flask_caching import Cache

cache = Cache(config={
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 3600
})

def get_playlists(channel_id):
    return cache.get(f"playlists:{channel_id}")

def cache_playlists(channel_id, playlists):
    cache.set(f"playlists:{channel_id}", playlists)

def get_channels(query, page_token):
    return cache.get(f"channels:{query.strip().lower()}:{page_token}")

def cache_channels(query, page_token, channels):
    cache.set(f"channels:{query.strip().lower()}:{page_token}", channels)