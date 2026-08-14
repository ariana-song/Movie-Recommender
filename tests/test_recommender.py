"""
tests/test_recommender.py

Bare-bones pytest suite for TMDB helpers. API calls are mocked so tests run offline.
"""

from unittest.mock import MagicMock, patch

import pytest

from recommender import (
    GENRE_IDS,
    clean_results,
    discover_movies,
    get_recommendations,
    resolve_language_code,
)


FAKE_RESULTS = [
    {
        "title": "Fight Club",
        "release_date": "1999-10-15",
        "vote_average": 8.4,
        "overview": "An office worker and a soap maker form a fight club.",
    },
    {
        "title": "Mystery Film",
        # missing release_date / overview on purpose
        "vote_average": 7.0,
    },
]


def make_fake_response(payload, status_code=200):
    fake = MagicMock()
    fake.status_code = status_code
    fake.json.return_value = payload
    fake.raise_for_status.return_value = None
    if status_code >= 400:
        fake.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return fake


def test_genre_ids_basic():
    assert GENRE_IDS["Comedy"] == 35
    assert GENRE_IDS["Drama"] == 18
    assert GENRE_IDS["Horror"] == 27


def test_resolve_language_code():
    assert resolve_language_code("English") == "en"
    assert resolve_language_code("Korean") == "ko"
    assert resolve_language_code("xx") == "xx"  # pass-through


def test_clean_results():
    cleaned = clean_results(FAKE_RESULTS)
    assert cleaned[0]["title"] == "Fight Club"
    assert cleaned[0]["year"] == "1999"
    assert cleaned[0]["rating"] == 8.4
    assert cleaned[1]["year"] == "Unknown"
    assert cleaned[1]["overview"] == "No description available."


@patch("recommender.requests.get")
def test_discover_movies_mocked(mock_get):
    mock_get.return_value = make_fake_response({"results": FAKE_RESULTS})

    results = discover_movies(
        "fake-key", GENRE_IDS, "Comedy", 90, 150, language="English", max_results=2
    )

    assert len(results) == 2
    assert results[0]["title"] == "Fight Club"
    assert mock_get.call_count == 1
    # genre id for Comedy should be in the request params
    params = mock_get.call_args.kwargs["params"]
    assert params["with_genres"] == 35


def test_discover_movies_unknown_genre():
    with pytest.raises(ValueError):
        discover_movies("fake-key", GENRE_IDS, "Pizza", 90, 150)


def test_discover_movies_bad_runtime():
    with pytest.raises(ValueError):
        discover_movies("fake-key", GENRE_IDS, "Comedy", 200, 90)


@patch("recommender.requests.get")
def test_discover_movies_without_genres(mock_get):
    mock_get.return_value = make_fake_response({"results": FAKE_RESULTS})

    discover_movies(
        "fake-key", GENRE_IDS, "Comedy", 90, 150,
        language="English", max_results=2, without_genres=["Animation", "Comedy"],
    )

    params = mock_get.call_args.kwargs["params"]
    # Comedy is the requested genre, so it should not also be excluded.
    assert params["without_genres"] == "16"


@patch("recommender.requests.get")
def test_get_recommendations_mocked(mock_get):
    mock_get.return_value = make_fake_response({"results": FAKE_RESULTS})

    movies = get_recommendations("fake-key", "Drama", 90, 150, max_results=1)

    assert len(movies) == 1
    assert movies[0]["title"] == "Fight Club"
    assert movies[0]["year"] == "1999"
    # uses GENRE_IDS directly — only the discover call, not genre/list
    assert mock_get.call_count == 1
    params = mock_get.call_args.kwargs["params"]
    assert params["with_genres"] == 18  # Drama
