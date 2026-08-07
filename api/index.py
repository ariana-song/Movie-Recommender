"""
api/index.py

Bare-bones Flask entry point for local use and Vercel deploy.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from flask import Flask, request

from page_builder import build_page
from recommender import GENRE_IDS, LANGUAGE_MAP, get_recommendations

load_dotenv()

app = Flask(__name__)


def blank_answers():
    return {
        "genre": "Comedy",
        "language": "English",
        "min_runtime": "0",
        "max_runtime": "150",
        "max_results": "5",
    }


def read_submitted_answers(form):
    answers = blank_answers()
    for field_name in answers:
        submitted_value = form.get(field_name, answers[field_name])
        if str(submitted_value).strip() != "":
            answers[field_name] = str(submitted_value).strip()
    return answers


def to_int(value, default_value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default_value


def render_home():
    """Shared handler for the one page of the app."""
    genres = sorted(GENRE_IDS.keys())
    languages = sorted(LANGUAGE_MAP.keys())

    if request.method == "GET":
        return build_page(blank_answers(), genres, languages)

    answers = read_submitted_answers(request.form)
    api_key = os.getenv("TMDB_API_KEY", "").strip()

    if api_key == "":
        return build_page(
            answers, genres, languages,
            error="Missing TMDB_API_KEY. Set it in Vercel Environment Variables "
                  "(or in .env locally).",
        )

    try:
        movies = get_recommendations(
            api_key,
            answers["genre"],
            to_int(answers["min_runtime"], 0),
            to_int(answers["max_runtime"], 150),
            language=answers["language"],
            max_results=to_int(answers["max_results"], 5),
        )
    except Exception as err:
        return build_page(answers, genres, languages, error=str(err))

    if len(movies) == 0:
        return build_page(
            answers, genres, languages,
            error="No movies matched. Try different filters.",
        )

    return build_page(answers, genres, languages, movies=movies)


# Vercel rewrites "/" to "/api/index", so Flask may see that path instead of "/".
# Catch every path so the same page always loads.
@app.route("/", defaults={"path": ""}, methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def home(path):
    return render_home()


if __name__ == "__main__":
    app.run(debug=True)
