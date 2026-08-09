"""
chatbot.py was generated using AI. We were interested in how Claude would recommend movies.

Also added a thumbs up/ thumbs down feature to the chatbot to improve recommendations over time.

Simple Claude chatbot layer on top of recommender.py.

"""

import json
import os
import re

import requests
from dotenv import load_dotenv

from recommender import GENRE_IDS, LANGUAGE_MAP

load_dotenv()

CLAUDE_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-5"
CLAUDE_VERSION = "2023-06-01"


def get_claude_key():
    """Return the Anthropic API key, or "" if it is missing."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if key is None:
        return ""
    return key.strip()


def ask_claude(system_prompt, user_prompt):
    """
    Send one question to Claude and return the text answer.

    NOTE: the book uses requests.get. Claude needs requests.post because we
    are sending a question in the request body, not just reading a URL.
    """
    api_key = get_claude_key()
    if api_key == "":
        raise ValueError(
            "Missing ANTHROPIC_API_KEY. Add it to .env (local) or "
            "Vercel Environment Variables."
        )

    headers = {
        "x-api-key": api_key,
        "anthropic-version": CLAUDE_VERSION,
        "content-type": "application/json",
    }
    body = {
        "model": CLAUDE_MODEL,
        "max_tokens": 2000,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    response = requests.post(CLAUDE_URL, headers=headers, json=body, timeout=60)
    if response.status_code != 200:
        raise ValueError(
            f"Claude returned an error (status {response.status_code}). "
            "Check your API key and try again."
        )

    data = response.json()
    # Claude returns a list of content blocks; we only want the text ones.
    parts = []
    for block in data.get("content", []):
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts).strip()


def extract_json(text):
    """
    Pull the first JSON object out of Claude's answer.
    Claude sometimes wraps JSON in ```json ... ``` fences.
    """
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        return json.loads(fence.group(1))

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Claude did not return usable JSON.")
    return json.loads(text[start:end + 1])


def default_plan(user_message):
    """Safe fallback filters if Claude is unavailable."""
    return {
        "genre": "Comedy",
        "language": "English",
        "min_runtime": 0,
        "max_runtime": 150,
        "reply": (
            "Claude is offline, so I used default Comedy filters. "
            "Add ANTHROPIC_API_KEY to enable the chatbot. "
            f"(You said: {user_message})"
        ),
    }


def validate_plan(plan):
    """
    Make sure Claude's filters are ones our app actually supports.
    Never trust the AI blindly — check every field.
    """
    genres = list(GENRE_IDS.keys())
    languages = list(LANGUAGE_MAP.keys())

    genre = str(plan.get("genre", "Comedy")).strip()
    if genre not in GENRE_IDS:
        # try case-insensitive match
        matched = None
        for name in genres:
            if name.lower() == genre.lower():
                matched = name
                break
        genre = matched if matched else "Comedy"

    language = str(plan.get("language", "English")).strip()
    if language not in LANGUAGE_MAP:
        matched = None
        for name in languages:
            if name.lower() == language.lower():
                matched = name
                break
        language = matched if matched else "English"

    try:
        min_runtime = int(plan.get("min_runtime", 0))
    except (TypeError, ValueError):
        min_runtime = 0
    try:
        max_runtime = int(plan.get("max_runtime", 150))
    except (TypeError, ValueError):
        max_runtime = 150

    if min_runtime < 0:
        min_runtime = 0
    if max_runtime > 400:
        max_runtime = 400
    if min_runtime > max_runtime:
        min_runtime, max_runtime = 0, 150

    reply = str(plan.get("reply", "Here are some movies you might like.")).strip()
    if reply == "":
        reply = "Here are some movies you might like."

    return {
        "genre": genre,
        "language": language,
        "min_runtime": min_runtime,
        "max_runtime": max_runtime,
        "reply": reply,
    }


def plan_search(user_message, liked_titles, disliked_titles, already_shown):
    """
    Ask Claude how to search, using the user's message AND their thumbs feedback.

    Params:
        user_message : what the user typed in the chat
        liked_titles : list of movie titles they thumbs-upped
        disliked_titles : list of movie titles they thumbs-downed
        already_shown : titles we already showed (avoid repeats)
    Returns:
        dict with genre, language, min_runtime, max_runtime, reply
    """
    if get_claude_key() == "":
        return default_plan(user_message)

    genres = ", ".join(sorted(GENRE_IDS.keys()))
    languages = ", ".join(sorted(LANGUAGE_MAP.keys()))

    system_prompt = f"""
You are a friendly movie recommendation chatbot.
Turn the user's request into search filters for The Movie Database.

Rules:
- genre MUST be one of: {genres}
- language MUST be one of: {languages}
- min_runtime and max_runtime are integers in minutes (0 to 400)
- Prefer movies similar to the liked list
- Avoid movies on the disliked list, and suggest something different
- Do not recommend titles already shown
- reply should be 1-3 short friendly sentences explaining your picks

Return ONLY JSON like:
{{
  "genre": "Comedy",
  "language": "English",
  "min_runtime": 0,
  "max_runtime": 120,
  "reply": "Looking for short comedies based on what you liked!"
}}
""".strip()

    user_prompt = (
        f"User message: {user_message}\n\n"
        f"Liked (thumbs up): {liked_titles if liked_titles else 'none yet'}\n"
        f"Disliked (thumbs down): {disliked_titles if disliked_titles else 'none yet'}\n"
        f"Already shown (do not repeat): {already_shown if already_shown else 'none yet'}\n"
    )

    try:
        answer = ask_claude(system_prompt, user_prompt)
        plan = extract_json(answer)
        return validate_plan(plan)
    except Exception as err:
        fallback = default_plan(user_message)
        fallback["reply"] = (
            f"I had trouble talking to Claude ({err}), "
            "so I used default Comedy filters instead."
        )
        return fallback


def split_titles(text):
    """Turn a hidden-field string into a list of titles."""
    if text is None or str(text).strip() == "":
        return []
    titles = []
    for part in str(text).split("||"):
        title = part.strip()
        if title != "" and title not in titles:
            titles.append(title)
    return titles


def join_titles(titles):
    """Turn a list of titles into a hidden-field string."""
    clean = []
    for title in titles:
        title = str(title).strip()
        if title != "" and title not in clean:
            clean.append(title)
    return "||".join(clean)
