"""
page_builder.py was generated using AI.

Simple chatbot page: chat box + Claude reply + movies with thumbs up/down.

NOTE: HTML/CSS here is not from the Python course book. Kept plain on purpose.
"""

from html import escape

from chatbot import join_titles


def safe(text):
    if text is None:
        return ""
    return escape(str(text))


PAGE_STYLES = """
body {
    font-family: Georgia, serif;
    max-width: 720px;
    margin: 0 auto;
    padding: 24px;
    background: #f7f5f0;
    color: #1c1c1c;
}
h1 { margin-bottom: 4px; }
.sub { color: #555; margin-top: 0; }
.chat-box {
    background: #fff;
    border: 1px solid #ddd;
    padding: 16px;
    margin: 20px 0;
}
textarea {
    width: 100%;
    min-height: 80px;
    padding: 10px;
    font-family: inherit;
    font-size: 15px;
}
button {
    margin-top: 10px;
    padding: 10px 16px;
    border: 0;
    background: #1c1c1c;
    color: #fff;
    font-size: 15px;
    cursor: pointer;
}
.reply {
    background: #ebe7df;
    border-left: 3px solid #1c1c1c;
    padding: 12px 14px;
    margin: 16px 0;
}
.note.problem { background: #f3e0e0; border-left: 3px solid #a33; padding: 12px; }
.card {
    background: #fff;
    border: 1px solid #ddd;
    padding: 14px;
    margin-bottom: 12px;
}
.card h3 { margin: 0 0 6px 0; }
.facts { color: #666; font-size: 14px; margin-bottom: 8px; }
.thumbs { margin-top: 10px; }
.thumbs form { display: inline; margin-right: 8px; }
.thumbs button {
    background: #fff;
    color: #1c1c1c;
    border: 1px solid #bbb;
    padding: 6px 12px;
    font-size: 14px;
}
.thumbs button:hover { background: #f0f0f0; }
.memory { color: #777; font-size: 13px; margin-top: 20px; }
"""


def hidden_fields(state):
    """Keep chat memory (likes/dislikes/shown) across form submits."""
    html = ""
    html += f'<input type="hidden" name="liked" value="{safe(join_titles(state["liked"]))}">'
    html += f'<input type="hidden" name="disliked" value="{safe(join_titles(state["disliked"]))}">'
    html += f'<input type="hidden" name="shown" value="{safe(join_titles(state["shown"]))}">'
    html += f'<input type="hidden" name="last_message" value="{safe(state["last_message"])}">'
    return html


def build_chat_form(state):
    html = '<div class="chat-box"><form method="post" action="/">'
    html += '<input type="hidden" name="action" value="chat">'
    html += hidden_fields(state)
    html += '<label for="message"><strong>What are you in the mood for?</strong></label>'
    html += (
        '<textarea name="message" id="message" '
        'placeholder="e.g. something funny and short for a weeknight">'
        f'{safe(state["last_message"])}</textarea>'
    )
    html += '<button type="submit">Ask the movie chatbot</button>'
    html += "</form></div>"
    return html


def build_movie_card(movie, state):
    title = movie["title"]
    html = '<div class="card">'
    html += f'<h3>{safe(title)} ({safe(movie["year"])})</h3>'
    html += f'<div class="facts">Rating: {safe(movie["rating"])}</div>'
    html += f'<p>{safe(movie["overview"])}</p>'

    # Thumbs up: remember this movie as liked, ask for more like it
    html += '<div class="thumbs">'
    html += '<form method="post" action="/">'
    html += '<input type="hidden" name="action" value="like">'
    html += f'<input type="hidden" name="movie_title" value="{safe(title)}">'
    html += hidden_fields(state)
    html += '<button type="submit">👍 More like this</button>'
    html += "</form>"

    # Thumbs down: remember as disliked, ask for different movies
    html += '<form method="post" action="/">'
    html += '<input type="hidden" name="action" value="dislike">'
    html += f'<input type="hidden" name="movie_title" value="{safe(title)}">'
    html += hidden_fields(state)
    html += '<button type="submit">👎 Not for me</button>'
    html += "</form>"
    html += "</div></div>"
    return html


def build_results(state, movies=None, reply=None, error=None):
    if error:
        return f'<div class="note problem">{safe(error)}</div>'

    html = ""
    if reply:
        html += f'<div class="reply"><strong>Chatbot:</strong> {safe(reply)}</div>'

    if movies is None:
        return html

    if len(movies) == 0:
        html += '<div class="note problem">No movies matched. Try another message.</div>'
        return html

    html += f"<p><strong>{len(movies)} recommendation(s)</strong> — rate them so I can improve:</p>"
    for movie in movies:
        html += build_movie_card(movie, state)
    return html


def build_memory_note(state):
    liked = ", ".join(state["liked"]) if state["liked"] else "none yet"
    disliked = ", ".join(state["disliked"]) if state["disliked"] else "none yet"
    return (
        '<div class="memory">'
        f"<div>👍 Liked: {safe(liked)}</div>"
        f"<div>👎 Disliked: {safe(disliked)}</div>"
        "</div>"
    )


def build_page(state, movies=None, reply=None, error=None):
    page = "<!DOCTYPE html><html><head>"
    page += '<meta charset="utf-8">'
    page += '<meta name="viewport" content="width=device-width, initial-scale=1">'
    page += "<title>Movie Chatbot</title>"
    page += f"<style>{PAGE_STYLES}</style>"
    page += "</head><body>"
    page += "<h1>Movie Chatbot</h1>"
    page += '<p class="sub">Tell Claude what you want. Thumbs up/down teach it your taste.</p>'
    page += build_chat_form(state)
    page += build_results(state, movies=movies, reply=reply, error=error)
    page += build_memory_note(state)
    page += "</body></html>"
    return page
