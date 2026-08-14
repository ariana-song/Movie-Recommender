"""
chatbot.py was generated using AI. We were interested in how Claude would recommend movies.

Claude layer on top of recommender.py. Two calls:
  1. plan_search -> which genres to exclude, and what this user likes
  2. pick_movies -> choose the best movies out of the TMDB results

A thumbs up/down entry looks like:
  "Superbad :: 2007, Comedy, rating 7.2 - Two friends try to buy alcohol..."
"""

import json
import os

import requests
from dotenv import load_dotenv

from recommender import GENRE_IDS

load_dotenv()

CLAUDE_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-5"


def claude_key():
    return (os.getenv("ANTHROPIC_API_KEY") or "").strip()


def ask_claude(system_prompt, user_prompt):
    """
    Ask Claude one question and return its answer as a dictionary.

    NOTE: the book uses requests.get. Claude needs requests.post because we
    send the question in the request body instead of in the URL.
    """
    headers = {
        "x-api-key": claude_key(),
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": CLAUDE_MODEL,
        "max_tokens": 1024,
        # Sonnet 5 thinks by default; thinking tokens count toward max_tokens
        # and were cutting off the JSON reply.
        "thinking": {"type": "disabled"},
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    response = requests.post(CLAUDE_URL, headers=headers, json=body, timeout=60)
    if response.status_code != 200:
        raise ValueError(f"Claude error {response.status_code}")

    text = ""
    for block in response.json()["content"]:
        if block["type"] == "text":
            text += block["text"]

    # Claude sometimes wraps JSON in ``` fences, so read first { to last }
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Claude did not return JSON.")
    return json.loads(text[start:end + 1])


def feedback_list(entries):
    """Format thumbs entries for the prompt."""
    if not entries:
        return "  (none yet)"
    return "\n".join(f"  - {entry}" for entry in entries)


def plan_search(message, genre, liked, disliked):
    """Ask Claude which genres to exclude and what this user's taste is."""
    if claude_key() == "":
        return {"without_genres": [], "notes": ""}

    system_prompt = f"""
The user already chose genre, language and runtime. Do not change those.
Reply with:
- without_genres: genres to EXCLUDE, from this list: {", ".join(sorted(GENRE_IDS))}
  (no cartoons -> ["Animation"]; not for kids -> ["Animation", "Family"])
- notes: what this user enjoys, based on their thumbs up and thumbs down

Return ONLY JSON:
{{"without_genres": ["Animation"], "notes": "live-action, dark tone"}}
""".strip()

    user_prompt = (
        f"Request: {message}\n\n"
        f"THUMBS UP:\n{feedback_list(liked)}\n\n"
        f"THUMBS DOWN:\n{feedback_list(disliked)}"
    )

    try:
        answer = ask_claude(system_prompt, user_prompt)
    except Exception:
        return {"without_genres": [], "notes": ""}

    # Never exclude the genre the user actually asked for.
    without = [
        name for name in answer.get("without_genres", [])
        if name in GENRE_IDS and name != genre
    ]
    return {"without_genres": without, "notes": str(answer.get("notes", ""))}


def pick_movies(message, candidates, liked, disliked, notes="", limit=5):
    """Let Claude choose the best movies out of the real TMDB results."""
    if claude_key() == "":
        return candidates[:limit], "Claude is offline, showing the top TMDB matches."

    catalog = "\n".join(
        f"- {movie['title']} ({movie['year']}) rating {movie['rating']} "
        f"- {movie['overview'][:150]}"
        for movie in candidates
    )

    system_prompt = f"""
Choose up to {limit} movies from the candidate list that best fit the user.
Work out what their thumbs up movies have in common and match it.
Steer away from what their thumbs down movies have in common.
Drop anything that clashes with the request (e.g. cartoons if they want live action).
Only use exact titles from the list. Do not add the year.

Return ONLY JSON:
{{"chosen_titles": ["Title One"], "reply": "why these fit, 1-2 sentences"}}
""".strip()

    user_prompt = (
        f"Request: {message}\n"
        f"Notes: {notes or 'none'}\n\n"
        f"THUMBS UP:\n{feedback_list(liked)}\n\n"
        f"THUMBS DOWN:\n{feedback_list(disliked)}\n\n"
        f"Candidates:\n{catalog}"
    )

    try:
        answer = ask_claude(system_prompt, user_prompt)
    except Exception:
        return candidates[:limit], "Claude could not rank these, showing top matches."

    by_title = {movie["title"].lower(): movie for movie in candidates}
    picked = []
    for title in answer.get("chosen_titles", []):
        name = str(title).strip().lower()
        movie = by_title.get(name)
        # Claude sometimes returns "Title (2024)" instead of just "Title".
        if movie is None and " (" in name:
            movie = by_title.get(name.split(" (")[0].strip())
        if movie is not None and movie not in picked:
            picked.append(movie)

    reply = str(answer.get("reply", "")).strip()
    return (picked or candidates)[:limit], reply or "Here are your matches."


def split_entries(text):
    """Read one hidden form field back into a list."""
    return [part.strip() for part in str(text or "").split("||") if part.strip()]


def join_entries(entries):
    """Write a list into one hidden form field."""
    return "||".join(entries)


def title_of(entry):
    """The movie title is the part before '::'."""
    return str(entry).split("::")[0].strip()


def titles_of(entries):
    return [title_of(entry) for entry in entries]
