"""
tests/test_chatbot.py

Tests for thumbs-memory helpers and Claude integration (mocked offline).
"""

from unittest.mock import patch

from chatbot import (
    join_entries,
    pick_movies,
    plan_search,
    split_entries,
    title_of,
    titles_of,
)

SAMPLE_MOVIES = [
    {
        "title": "Superbad",
        "year": "2007",
        "rating": 7.2,
        "overview": "Two friends try to buy alcohol for a party.",
    },
    {
        "title": "The Hangover",
        "year": "2009",
        "rating": 7.7,
        "overview": "A bachelor party in Vegas goes wrong.",
    },
]

LIKED_ENTRY = (
    "Superbad :: 2007, Comedy, rating 7.2 - Two friends try to buy alcohol..."
)


def test_split_and_join_entries():
    entries = ["one", "two"]
    joined = join_entries(entries)
    assert joined == "one||two"
    assert split_entries(joined) == entries
    assert split_entries("") == []
    assert split_entries(None) == []


def test_title_helpers():
    assert title_of(LIKED_ENTRY) == "Superbad"
    assert titles_of([LIKED_ENTRY, "Other :: 2010, Drama, rating 8 - plot"]) == [
        "Superbad",
        "Other",
    ]


@patch("chatbot.claude_key", return_value="")
def test_plan_search_without_claude_key(_mock_key):
    result = plan_search("funny movies", "Comedy", [LIKED_ENTRY], [])
    assert result == {"without_genres": [], "notes": ""}


@patch("chatbot.ask_claude")
@patch("chatbot.claude_key", return_value="fake-key")
def test_plan_search_with_claude(_mock_key, mock_ask):
    mock_ask.return_value = {
        "without_genres": ["Animation", "Comedy"],
        "notes": "live-action, raunchy humor",
    }
    result = plan_search("no cartoons", "Comedy", [], [])
    assert result["without_genres"] == ["Animation"]
    assert result["notes"] == "live-action, raunchy humor"


@patch("chatbot.ask_claude", side_effect=ValueError("API down"))
@patch("chatbot.claude_key", return_value="fake-key")
def test_plan_search_claude_failure(_mock_key, mock_ask):
    result = plan_search("funny movies", "Comedy", [], [])
    assert result == {"without_genres": [], "notes": ""}
    mock_ask.assert_called_once()


@patch("chatbot.claude_key", return_value="")
def test_pick_movies_without_claude_key(_mock_key):
    movies, reply = pick_movies("funny", SAMPLE_MOVIES, [], [], limit=1)
    assert movies == [SAMPLE_MOVIES[0]]
    assert "offline" in reply.lower()


@patch("chatbot.ask_claude")
@patch("chatbot.claude_key", return_value="fake-key")
def test_pick_movies_with_claude(_mock_key, mock_ask):
    mock_ask.return_value = {
        "chosen_titles": ["The Hangover"],
        "reply": "Similar vibe to your thumbs-up picks.",
    }
    movies, reply = pick_movies("funny", SAMPLE_MOVIES, [LIKED_ENTRY], [], limit=5)
    assert movies == [SAMPLE_MOVIES[1]]
    assert reply == "Similar vibe to your thumbs-up picks."


@patch("chatbot.ask_claude")
@patch("chatbot.claude_key", return_value="fake-key")
def test_pick_movies_unknown_title_falls_back(_mock_key, mock_ask):
    mock_ask.return_value = {
        "chosen_titles": ["Nonexistent Film"],
        "reply": "",
    }
    movies, reply = pick_movies("funny", SAMPLE_MOVIES, [], [], limit=5)
    assert movies == SAMPLE_MOVIES
    assert reply == "Here are your matches."
