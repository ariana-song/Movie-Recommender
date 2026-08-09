"""
api/index.py

Chatbot UI and thumbs feedback were generated using AI.

Flask entry point: chatbot UI + thumbs feedback + TMDB search.

Flow:
  chat     -> Claude plans filters from the message + feedback memory
  like     -> save thumbs up, ask for more similar movies
  dislike  -> save thumbs down, ask for different movies
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from flask import Flask, request

from chatbot import plan_search, split_titles
from page_builder import build_page
from recommender import get_recommendations

load_dotenv()

app = Flask(__name__)


def blank_state():
    return {
        "liked": [],
        "disliked": [],
        "shown": [],
        "last_message": "",
    }


def read_state(form):
    """Read thumbs memory + last chat message from the submitted form."""
    state = blank_state()
    state["liked"] = split_titles(form.get("liked", ""))
    state["disliked"] = split_titles(form.get("disliked", ""))
    state["shown"] = split_titles(form.get("shown", ""))
    state["last_message"] = str(form.get("last_message", "")).strip()
    return state


def remember_shown(state, movies):
    """Add newly recommended titles to the 'already shown' list."""
    for movie in movies:
        title = movie["title"]
        if title not in state["shown"]:
            state["shown"].append(title)


def run_chat(user_message, state):
    """Ask Claude for a plan, then fetch movies from TMDB."""
    tmdb_key = os.getenv("TMDB_API_KEY", "").strip()
    if tmdb_key == "":
        return state, None, None, "Missing TMDB_API_KEY."

    if user_message.strip() == "":
        return state, None, None, "Type a message first — tell me what you want to watch."

    state["last_message"] = user_message.strip()

    plan = plan_search(
        state["last_message"],
        state["liked"],
        state["disliked"],
        state["shown"],
    )

    try:
        movies = get_recommendations(
            tmdb_key,
            plan["genre"],
            plan["min_runtime"],
            plan["max_runtime"],
            language=plan["language"],
            max_results=5,
        )
    except Exception as err:
        return state, None, plan["reply"], str(err)

    # Drop anything the user already disliked, just in case
    filtered = []
    for movie in movies:
        if movie["title"] not in state["disliked"]:
            filtered.append(movie)

    remember_shown(state, filtered)
    return state, filtered, plan["reply"], None


def render_home():
    if request.method == "GET":
        return build_page(blank_state())

    action = request.form.get("action", "chat")
    state = read_state(request.form)

    if action == "like":
        title = str(request.form.get("movie_title", "")).strip()
        if title != "" and title not in state["liked"]:
            state["liked"].append(title)
        # If it was disliked before, forgive it
        state["disliked"] = [t for t in state["disliked"] if t != title]
        # Ask for more like the liked list
        message = state["last_message"] or "Find me more movies like the ones I liked."
        message = message + " (Please recommend more like my thumbs-up movies.)"
        state, movies, reply, error = run_chat(message, state)
        return build_page(state, movies=movies, reply=reply, error=error)

    if action == "dislike":
        title = str(request.form.get("movie_title", "")).strip()
        if title != "" and title not in state["disliked"]:
            state["disliked"].append(title)
        state["liked"] = [t for t in state["liked"] if t != title]
        message = state["last_message"] or "Find me something else to watch."
        message = message + " (Avoid my thumbs-down movies and try something different.)"
        state, movies, reply, error = run_chat(message, state)
        return build_page(state, movies=movies, reply=reply, error=error)

    # Default: new chat message
    user_message = str(request.form.get("message", "")).strip()
    state, movies, reply, error = run_chat(user_message, state)
    return build_page(state, movies=movies, reply=reply, error=error)


@app.route("/", defaults={"path": ""}, methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def home(path):
    return render_home()


if __name__ == "__main__":
    app.run(debug=True)
