"""
tests/test_api.py

Tests for the Flask app: form state, routing, and chat flow (mocked offline).
"""

from unittest.mock import patch

import pytest

from api.index import app, blank_state, read_state, save_feedback

FAKE_MOVIES = [
    {
        "title": "Superbad",
        "year": "2007",
        "rating": 7.2,
        "overview": "Two friends try to buy alcohol for a party.",
    },
]

LIKED_ENTRY = (
    "Superbad :: 2007, Comedy, rating 7.2 - Two friends try to buy alcohol..."
)


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_get_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Movie Chatbot" in response.data
    assert b"Find movies" in response.data


def test_blank_state_defaults():
    state = blank_state()
    assert state["genre"] == "Comedy"
    assert state["language"] == "English"
    assert state["liked"] == []


def test_read_state_from_form():
    state = read_state({
        "genre": "Horror",
        "language": "Japanese",
        "min_runtime": "80",
        "max_runtime": "120",
        "liked": LIKED_ENTRY,
        "disliked": "",
        "shown": "Superbad",
        "last_message": "scary but not gory",
    })
    assert state["genre"] == "Horror"
    assert state["language"] == "Japanese"
    assert state["min_runtime"] == "80"
    assert state["max_runtime"] == "120"
    assert state["liked"] == [LIKED_ENTRY]
    assert state["shown"] == ["Superbad"]
    assert state["last_message"] == "scary but not gory"


def test_read_state_ignores_invalid_genre():
    state = read_state({"genre": "Pizza"})
    assert state["genre"] == "Comedy"


def test_read_state_invalid_runtime_uses_defaults():
    state = read_state({
        "min_runtime": "abc",
        "max_runtime": "",
    })
    assert state["min_runtime"] == "0"
    assert state["max_runtime"] == "150"


@patch("api.index.run_chat")
def test_post_chat_action(mock_run_chat, client):
    mock_run_chat.return_value = (FAKE_MOVIES, "Here you go.", None)
    response = client.post("/", data={
        "action": "chat",
        "genre": "Comedy",
        "language": "English",
        "min_runtime": "90",
        "max_runtime": "150",
        "message": "funny movies",
        "liked": "",
        "disliked": "",
        "shown": "",
    })
    assert response.status_code == 200
    assert b"Superbad" in response.data
    assert b"Here you go." in response.data
    mock_run_chat.assert_called_once()
    _, message = mock_run_chat.call_args[0]
    assert message == "funny movies"


@patch("api.index.run_chat")
def test_post_like_action_saves_feedback_and_reruns(mock_run_chat, client):
    mock_run_chat.return_value = (FAKE_MOVIES, "Adjusted picks.", None)
    response = client.post("/", data={
        "action": "like",
        "genre": "Comedy",
        "language": "English",
        "min_runtime": "90",
        "max_runtime": "150",
        "last_message": "funny movies",
        "movie_title": "Superbad",
        "movie_year": "2007",
        "movie_rating": "7.2",
        "movie_overview": "Two friends try to buy alcohol for a party.",
        "liked": "",
        "disliked": "",
        "shown": "",
    })
    assert response.status_code == 200
    state, message = mock_run_chat.call_args[0]
    assert any("Superbad" in entry for entry in state["liked"])
    assert "thumbs-up" in message


def test_save_feedback_adds_liked_entry():
    state = blank_state()
    with app.test_request_context("/", method="POST", data={
        "movie_title": "Superbad",
        "movie_year": "2007",
        "movie_rating": "7.2",
        "movie_overview": "Two friends try to buy alcohol for a party.",
    }):
        save_feedback(state, "like")
    assert len(state["liked"]) == 1
    assert "Superbad" in state["liked"][0]


def test_save_feedback_dislike_moves_off_liked():
    state = blank_state()
    state["liked"] = [LIKED_ENTRY]
    with app.test_request_context("/", method="POST", data={
        "movie_title": "Superbad",
        "movie_year": "2007",
        "movie_rating": "7.2",
        "movie_overview": "Two friends try to buy alcohol for a party.",
    }):
        save_feedback(state, "dislike")
    assert state["liked"] == []
    assert len(state["disliked"]) == 1
    assert "Superbad" in state["disliked"][0]


@patch.dict("os.environ", {"TMDB_API_KEY": ""})
def test_run_chat_missing_tmdb_key(client):
    response = client.post("/", data={
        "action": "chat",
        "genre": "Comedy",
        "language": "English",
        "min_runtime": "90",
        "max_runtime": "150",
        "message": "funny movies",
        "liked": "",
        "disliked": "",
        "shown": "",
    })
    assert response.status_code == 200
    assert b"Missing TMDB_API_KEY" in response.data
