"""
api/index.py was largely generated using AI to create the chatbot UI and thumbs feedback.

Flask app. Filters -> Claude -> TMDB -> Claude -> movies with thumbs up/down.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from flask import Flask, request

from chatbot import pick_movies, plan_search, split_entries, title_of, titles_of
from page_builder import build_page
from recommender import GENRE_IDS, LANGUAGE_MAP, get_recommendations

load_dotenv()

app = Flask(__name__)

MOVIE_COUNT = 5

FEEDBACK_HINT = {
    "like": " Recommend NEW movies like my thumbs-up list.",
    "dislike": " Avoid my thumbs-down movies and suggest different ones.",
}


def blank_state():
    """Default filters and empty thumbs memory for a new visitor."""
    return {
        "genre": "Comedy",
        "language": "English",
        "min_runtime": "0",
        "max_runtime": "150",
        "liked": [],
        "disliked": [],
        "shown": [],
        "last_message": "",
    }


def to_int(value, fallback):
    """Parse an integer from form input, or return fallback if it is not a number."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def read_state(form):
    """Rebuild the state from the submitted form: filters + thumbs memory."""
    state = blank_state()

    if form.get("genre") in GENRE_IDS:
        state["genre"] = form["genre"]
    if form.get("language") in LANGUAGE_MAP:
        state["language"] = form["language"]

    state["min_runtime"] = str(to_int(form.get("min_runtime"), 0))
    state["max_runtime"] = str(to_int(form.get("max_runtime"), 150))

    state["liked"] = split_entries(form.get("liked"))
    state["disliked"] = split_entries(form.get("disliked"))
    state["shown"] = split_entries(form.get("shown"))
    state["last_message"] = str(form.get("last_message", "")).strip()
    return state


def save_feedback(state, action):
    """Save the thumbed movie's details so Claude can learn the user's taste."""
    form = request.form
    title = str(form.get("movie_title", "")).strip()
    if title == "":
        return

    entry = (
        f"{title} :: {form.get('movie_year', '')}, {state['genre']}, "
        f"rating {form.get('movie_rating', '')} - {form.get('movie_overview', '')}"
    )
    add_to = "liked" if action == "like" else "disliked"
    remove_from = "disliked" if action == "like" else "liked"

    if title not in titles_of(state[add_to]):
        state[add_to].append(entry)
    state[remove_from] = [
        other for other in state[remove_from] if title_of(other) != title
    ]


def fetch_pool(tmdb_key, state, without_genres, want=20):
    """Collect TMDB movies the user has not seen yet, across a few pages."""
    seen = set(
        state["shown"] + titles_of(state["liked"]) + titles_of(state["disliked"])
    )
    pool = []
    for page in [1, 2, 3]:
        movies = get_recommendations(
            tmdb_key,
            state["genre"],
            to_int(state["min_runtime"], 0),
            to_int(state["max_runtime"], 150),
            language=state["language"],
            max_results=20,
            page=page,
            without_genres=without_genres,
        )
        for movie in movies:
            if movie["title"] not in seen:
                seen.add(movie["title"])
                pool.append(movie)
        if len(pool) >= want:
            break
    return pool[:want]


def run_chat(state, message):
    """Returns (movies, reply, error) and records what was shown."""
    tmdb_key = (os.getenv("TMDB_API_KEY") or "").strip()
    if tmdb_key == "":
        return None, None, "Missing TMDB_API_KEY."

    plan = plan_search(message, state["genre"], state["liked"], state["disliked"])

    try:
        pool = fetch_pool(tmdb_key, state, plan["without_genres"])
    except Exception as err:
        return None, None, str(err)

    if len(pool) == 0:
        return [], "No new movies for those filters. Try widening them.", None

    movies, reply = pick_movies(
        message,
        pool,
        state["liked"],
        state["disliked"],
        notes=plan["notes"],
        limit=MOVIE_COUNT,
    )
    for movie in movies:
        if movie["title"] not in state["shown"]:
            state["shown"].append(movie["title"])
    return movies, reply, None


@app.route("/", defaults={"path": ""}, methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def home(path):
    """
    Handle every URL. Vercel rewrites all traffic to this file, so unknown
    paths still need to land on the same page instead of a Flask 404.
    """
    if request.method == "GET":
        return build_page(blank_state())

    state = read_state(request.form)
    action = request.form.get("action", "chat")

    if action in FEEDBACK_HINT:
        save_feedback(state, action)
        base = state["last_message"] or f"{state['genre']} movies"
        message = base + FEEDBACK_HINT[action]
    else:
        state["last_message"] = str(request.form.get("message", "")).strip()
        message = state["last_message"] or (
            f"{state['genre']} movies in {state['language']}"
        )

    movies, reply, error = run_chat(state, message)
    return build_page(state, movies=movies, reply=reply, error=error)


if __name__ == "__main__":
    app.run(debug=True)
