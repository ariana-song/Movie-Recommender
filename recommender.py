"""
recommender.py

Core logic for the movie recommender. Given a genre, a runtime range, and a
language, queries The Movie Database (TMDB) API and returns a list of
matching movies.
"""

import requests

BASE_URL = "https://api.themoviedb.org/3"

# TMDB's language filter expects ISO 639-1 codes, not full names.
# This maps common language names to their codes.
LANGUAGE_MAP = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Japanese": "ja",
    "Korean": "ko",
    "Mandarin": "zh",
    "Hindi": "hi",
    "Italian": "it",
    "Portuguese": "pt",
}


def get_genre_map(api_key):
    """
    Fetch TMDB's movie genre list and return a {name: id} dict.

    Args:
        api_key (str): TMDB API key.

    Returns:
        dict: e.g. {"Action": 28, "Comedy": 35, ...}
    """
    resp = requests.get(f"{BASE_URL}/genre/movie/list", params={"api_key": api_key})
    resp.raise_for_status()
    genres = resp.json()["genres"]
    return {g["name"]: g["id"] for g in genres}


def resolve_language_code(language_name):
    """
    Map a friendly language name (e.g. "English") to its ISO 639-1 code
    (e.g. "en"). If the input isn't in the map, assume it's already a
    valid code and pass it through unchanged.
    """
    return LANGUAGE_MAP.get(language_name, language_name)


def discover_movies(api_key, genre_map, genre_name, min_runtime, max_runtime,
                     language="English", max_results=10):
    """
    Query TMDB's discover endpoint using genre/runtime/language filters.

    Args:
        api_key (str): TMDB API key.
        genre_map (dict): {name: id} mapping, from get_genre_map().
        genre_name (str): e.g. "Comedy". Must exist in genre_map.
        min_runtime (int): minimum runtime in minutes.
        max_runtime (int): maximum runtime in minutes.
        language (str): friendly language name or ISO code.
        max_results (int): max number of results to return.

    Returns:
        list[dict]: raw TMDB movie result dicts.
    """
    genre_id = genre_map.get(genre_name)
    if genre_id is None:
        raise ValueError(f"Unknown genre: {genre_name!r}")

    if min_runtime > max_runtime:
        raise ValueError(f"min_runtime ({min_runtime}) cannot exceed max_runtime ({max_runtime})")

    params = {
        "api_key": api_key,
        "with_genres": genre_id,
        "with_runtime.gte": min_runtime,
        "with_runtime.lte": max_runtime,
        "with_original_language": resolve_language_code(language),
        "sort_by": "popularity.desc",
    }
    resp = requests.get(f"{BASE_URL}/discover/movie", params=params)
    resp.raise_for_status()
    return resp.json()["results"][:max_results]


def clean_results(results):
    """
    Shape raw TMDB results into a simplified, UI-friendly list of dicts.
    Handles movies with missing release_date or runtime data gracefully.

    Args:
        results (list[dict]): raw TMDB movie result dicts.

    Returns:
        list[dict]: each with keys "title", "year", "rating", "overview".
    """
    cleaned = []
    for r in results:
        cleaned.append({
            "title": r.get("title", "Untitled"),
            "year": r["release_date"][:4] if r.get("release_date") else "Unknown",
            "rating": r.get("vote_average", "N/A"),
            "overview": r.get("overview") or "No description available.",
        })
    return cleaned


def get_recommendations(api_key, genre_name, min_runtime, max_runtime,
                         language="English", max_results=10):
    """
    Convenience wrapper: fetches the genre map, queries discover_movies,
    and returns cleaned results in one call. This is the function the UI
    layer will call directly.

    Args:
        api_key (str): TMDB API key.
        genre_name (str): e.g. "Comedy".
        min_runtime (int): minimum runtime in minutes.
        max_runtime (int): maximum runtime in minutes.
        language (str): friendly language name or ISO code.
        max_results (int): max number of results to return.

    Returns:
        list[dict]: cleaned movie results, or an empty list if none match.
    """
    genre_map = get_genre_map(api_key)
    raw_results = discover_movies(
        api_key, genre_map, genre_name, min_runtime, max_runtime,
        language=language, max_results=max_results,
    )
    return clean_results(raw_results)
