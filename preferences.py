from enum import StrEnum

class Preference(StrEnum):
    PLAYLISTS_SORT_BY = "playlists_sort_by"
    PLAYLISTS_PER_PAGE = "playlists_per_page"
    PLAYLISTS_HIDE_COMPLETED = "playlists_hide_completed"
    VIDEOS_HIDE_WATCHED = "videos_hide_watched"
    SEARCH_RESULTS_PER_PAGE = "search_results_per_page"
    SEARCH_PLAYLISTS_PER_PAGE = "search_playlists_per_page"
    SEARCH_PLAYLISTS_SORT_BY = "search_playlists_sort_by"
    SEARCH_PLAYLISTS_HIDE_SAVED = "search_playlists_hide_saved"

PREFERENCE_VALIDATORS = {
    Preference.PLAYLISTS_SORT_BY:
        lambda value: isinstance(value, str) and value in {"date_saved", "last_watched", "title", "progress"},

    Preference.PLAYLISTS_PER_PAGE:
        lambda value: isinstance(value, str) and value in {"10", "20", "30", "40", "50"},

    Preference.PLAYLISTS_HIDE_COMPLETED:
        lambda value: isinstance(value, bool),

    Preference.VIDEOS_HIDE_WATCHED:
        lambda value: isinstance(value, bool),

    Preference.SEARCH_RESULTS_PER_PAGE:
        lambda value: isinstance(value, str) and value in {"10", "20", "30", "40", "50"},

    Preference.SEARCH_PLAYLISTS_PER_PAGE:
        lambda value: isinstance(value, str) and value in {"10", "20", "30", "40", "50"},

    Preference.SEARCH_PLAYLISTS_SORT_BY:
        lambda value: isinstance(value, str) and value in {"date_created", "title"},

    Preference.SEARCH_PLAYLISTS_HIDE_SAVED:
        lambda value: isinstance(value, bool)
}