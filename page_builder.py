"""
page_builder.py was generated using AI.

Builds the HTML page: filters, chat box, results with thumbs up/down.
"""

from html import escape

from chatbot import join_entries, titles_of
from recommender import GENRE_IDS, LANGUAGE_MAP

STYLES = """
body { font-family: Georgia, serif; max-width: 720px; margin: 0 auto;
       padding: 24px; background: #f7f5f0; color: #1c1c1c; }
h1 { margin-bottom: 4px; }
.sub { color: #555; margin-top: 0; }
.box { background: #fff; border: 1px solid #ddd; padding: 16px; margin: 16px 0; }
label { display: block; margin-top: 12px; font-weight: bold; font-size: 14px; }
select, input[type="number"], textarea { width: 100%; padding: 10px; margin-top: 4px;
       font-family: inherit; font-size: 15px; box-sizing: border-box; }
textarea { min-height: 80px; }
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
button { margin-top: 14px; padding: 10px 16px; border: 0; background: #1c1c1c;
       color: #fff; font-size: 15px; cursor: pointer; }
.step { color: #777; font-size: 13px; margin: 0 0 8px 0; text-transform: uppercase; }
.reply { background: #ebe7df; border-left: 3px solid #1c1c1c; padding: 12px 14px; margin: 16px 0; }
.problem { background: #f3e0e0; border-left: 3px solid #a33; padding: 12px; margin: 16px 0; }
.card { background: #fff; border: 1px solid #ddd; padding: 14px; margin-bottom: 12px; }
.card h3 { margin: 0 0 6px 0; }
.facts { color: #666; font-size: 14px; margin-bottom: 8px; }
.thumbs form { display: inline; margin-right: 8px; }
.thumbs button { background: #fff; color: #1c1c1c; border: 1px solid #bbb;
       padding: 6px 12px; font-size: 14px; }
.memory { color: #777; font-size: 13px; margin-top: 20px; }
@media (max-width: 600px) { .row { grid-template-columns: 1fr; } }
"""


def safe(text):
    return escape(str(text)) if text is not None else ""


def hidden(name, value):
    return f'<input type="hidden" name="{name}" value="{safe(value)}">'


def dropdown(name, options, selected):
    html = f'<select name="{name}" id="{name}">'
    for option in options:
        chosen = " selected" if str(option) == str(selected) else ""
        html += f'<option value="{safe(option)}"{chosen}>{safe(option)}</option>'
    return html + "</select>"


def memory_fields(state, with_filters=False):
    """Carry the thumbs memory (and optionally the filters) into the next post."""
    html = ""
    for name in ["liked", "disliked", "shown"]:
        html += hidden(name, join_entries(state[name]))
    if with_filters:
        for name in ["genre", "language", "min_runtime", "max_runtime",
                     "last_message"]:
            html += hidden(name, state[name])
    return html


def build_form(state):
    """Filters first, chatbot second, submitted together."""
    html = '<form method="post" action="/">'
    html += hidden("action", "chat")
    html += memory_fields(state)

    html += '<div class="box"><p class="step">Step 1 - set your filters</p>'
    html += '<label for="genre">Genre</label>'
    html += dropdown("genre", sorted(GENRE_IDS), state["genre"])
    html += '<label for="language">Language</label>'
    html += dropdown("language", sorted(LANGUAGE_MAP), state["language"])

    min_runtime = safe(state["min_runtime"])
    max_runtime = safe(state["max_runtime"])
    html += '<div class="row">'
    html += ('<div><label for="min_runtime">Min runtime</label>'
             f'<input type="number" name="min_runtime" id="min_runtime" '
             f'min="0" max="400" value="{min_runtime}"></div>')
    html += ('<div><label for="max_runtime">Max runtime</label>'
             f'<input type="number" name="max_runtime" id="max_runtime" '
             f'min="0" max="400" value="{max_runtime}"></div>')
    html += "</div></div>"

    html += '<div class="box"><p class="step">Step 2 - tell the chatbot</p>'
    html += '<label for="message">What are you in the mood for?</label>'
    html += ('<textarea name="message" id="message" '
             'placeholder="e.g. funny live-action, nothing animated">'
             f'{safe(state["last_message"])}</textarea>')
    html += '<button type="submit">Find movies</button></div></form>'
    return html


def thumb_form(movie, state, action, label):
    """One thumbs button, carrying the movie details so Claude learns the taste."""
    html = '<form method="post" action="/">'
    html += hidden("action", action)
    html += hidden("movie_title", movie["title"])
    html += hidden("movie_year", movie["year"])
    html += hidden("movie_rating", movie["rating"])
    html += hidden("movie_overview", movie["overview"][:160])
    html += memory_fields(state, with_filters=True)
    return html + f"<button type=\"submit\">{label}</button></form>"


def build_card(movie, state):
    html = '<div class="card">'
    html += f'<h3>{safe(movie["title"])} ({safe(movie["year"])})</h3>'
    html += f'<div class="facts">Rating: {safe(movie["rating"])}</div>'
    html += f'<p>{safe(movie["overview"])}</p>'
    html += '<div class="thumbs">'
    html += thumb_form(movie, state, "like", "&#128077; More like this")
    html += thumb_form(movie, state, "dislike", "&#128078; Not for me")
    return html + "</div></div>"


def build_results(state, movies, reply, error):
    if error:
        return f'<div class="problem">{safe(error)}</div>'

    html = ""
    if reply:
        html += f'<div class="reply"><strong>Chatbot:</strong> {safe(reply)}</div>'
    if movies is None:
        return html
    if len(movies) == 0:
        return html + '<div class="problem">No movies matched. Try other filters.</div>'

    html += f"<p><strong>{len(movies)} recommendation(s)</strong> - rate them:</p>"
    for movie in movies:
        html += build_card(movie, state)
    return html


def build_page(state, movies=None, reply=None, error=None):
    liked = ", ".join(titles_of(state["liked"])) or "none yet"
    disliked = ", ".join(titles_of(state["disliked"])) or "none yet"

    page = "<!DOCTYPE html><html><head><meta charset='utf-8'>"
    page += '<meta name="viewport" content="width=device-width, initial-scale=1">'
    page += f"<title>Movie Chatbot</title><style>{STYLES}</style></head><body>"
    page += "<h1>Movie Chatbot</h1>"
    page += ('<p class="sub">Set your filters, tell Claude the vibe, '
             "then rate the picks.</p>")
    page += build_form(state)
    page += build_results(state, movies, reply, error)
    page += (f'<div class="memory"><div>Liked: {safe(liked)}</div>'
             f"<div>Disliked: {safe(disliked)}</div></div>")
    return page + "</body></html>"
