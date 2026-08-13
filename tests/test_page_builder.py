"""
tests/test_page_builder.py

Tests for HTML page generation (no network required).
"""

from page_builder import build_page, join_entries

BLANK_STATE = {
    "genre": "Comedy",
    "language": "English",
    "min_runtime": "90",
    "max_runtime": "150",
    "liked": [],
    "disliked": [],
    "shown": [],
    "last_message": "",
}

SAMPLE_MOVIE = {
    "title": "Superbad",
    "year": "2007",
    "rating": 7.2,
    "overview": "Two friends try to buy alcohol for a party.",
}


def test_build_page_includes_form_and_filters():
    html = build_page(BLANK_STATE)
    assert "Movie Chatbot" in html
    assert 'name="genre"' in html
    assert 'name="language"' in html
    assert 'id="min_runtime"' in html
    assert 'id="max_runtime"' in html
    assert 'name="message"' in html
    assert "Find movies" in html


def test_build_page_shows_memory():
    state = {
        **BLANK_STATE,
        "liked": ["Superbad :: 2007, Comedy, rating 7.2 - plot"],
        "disliked": ["Cars :: 2006, Animation, rating 7.1 - talking cars"],
    }
    html = build_page(state)
    assert "Liked: Superbad" in html
    assert "Disliked: Cars" in html
    assert "none yet" not in html


def test_build_page_shows_results_and_reply():
    html = build_page(
        BLANK_STATE,
        movies=[SAMPLE_MOVIE],
        reply="These match your taste.",
    )
    assert "Superbad" in html
    assert "These match your taste." in html
    assert "More like this" in html
    assert "Not for me" in html
    assert "1 recommendation(s)" in html


def test_build_page_shows_error():
    html = build_page(BLANK_STATE, error="Missing TMDB_API_KEY.")
    assert "Error: Missing TMDB_API_KEY." in html


def test_build_page_escapes_user_input():
    state = {**BLANK_STATE, "last_message": '<script>alert("xss")</script>'}
    html = build_page(state)
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_hidden_fields_carry_memory():
    state = {
        **BLANK_STATE,
        "liked": ["Superbad :: 2007, Comedy, rating 7.2 - plot"],
        "shown": ["Superbad"],
    }
    html = build_page(state, movies=[SAMPLE_MOVIE])
    assert f'value="{join_entries(state["liked"])}"' in html
    assert 'name="shown"' in html
