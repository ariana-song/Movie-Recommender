"""
page_builder.py was generated using AI.

Builds the HTML page: filters, chat box, results with thumbs up/down.
"""

from html import escape

from chatbot import join_entries, titles_of
from recommender import GENRE_IDS, LANGUAGE_MAP

STYLES = """
body { font-family: Georgia, "Times New Roman", serif; max-width: 720px; margin: 0 auto;
       padding: 24px; background: #0a0a0c; color: #e8e4dc;
       min-height: 100vh;
       background-image: radial-gradient(ellipse at top, #1a1510 0%, #0a0a0c 70%); }
h1 { margin-bottom: 4px; color: #d4af37; letter-spacing: 0.02em;
     text-shadow: 0 0 24px rgba(212, 175, 55, 0.25); }
.sub { color: #9a958a; margin-top: 0; }
.box { background: #141418; border: 1px solid #2a2820; border-radius: 8px;
       padding: 16px; margin: 16px 0;
       box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
label { display: block; margin-top: 12px; font-weight: bold; font-size: 14px;
        color: #c9c4b8; }
select, input[type="number"], textarea { width: 100%; padding: 10px; margin-top: 4px;
       font-family: inherit; font-size: 15px; box-sizing: border-box;
       border: 1px solid #3a3830; border-radius: 4px;
       background: #0f0f12; color: #e8e4dc; }
select:focus, textarea:focus { outline: 2px solid #d4af37; outline-offset: 1px; }
textarea { min-height: 80px; }
textarea::placeholder { color: #6a655c; }
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
button { margin-top: 14px; padding: 10px 16px; border: 0; border-radius: 4px;
       background: linear-gradient(180deg, #d4af37 0%, #b8941f 100%);
       color: #0a0a0c; font-size: 15px; font-weight: bold; cursor: pointer;
       box-shadow: 0 2px 8px rgba(212, 175, 55, 0.3); }
button:hover { background: linear-gradient(180deg, #e0bc4a 0%, #c9a227 100%); }
.step { color: #d4af37; font-size: 13px; margin: 0 0 8px 0;
        text-transform: uppercase; letter-spacing: 0.08em; }
.runtime-display { display: inline-block; background: #1f1d18; color: #d4af37;
       border: 1px solid #3a3830; padding: 6px 12px; border-radius: 20px;
       font-size: 14px; margin: 8px 0 12px 0; }
.runtime-sliders { display: grid; gap: 10px; }
.slider-row { display: grid; grid-template-columns: 36px 1fr 48px; align-items: center; gap: 8px; }
.slider-label { font-size: 13px; color: #9a958a; font-weight: normal; margin: 0; }
.slider-value { font-size: 13px; color: #d4af37; text-align: right; }
input[type="range"] { width: 100%; margin: 0; accent-color: #d4af37; cursor: pointer; }
.reply { background: #1a1814; border-left: 3px solid #d4af37; border-radius: 4px;
         padding: 12px 14px; margin: 16px 0; color: #c9c4b8; }
.reply strong { color: #d4af37; }
.problem { color: #f0a0a0; background: #2a1515; border: 1px solid #8b3030;
           border-radius: 4px; padding: 10px; margin: 16px 0; }
.card { background: #141418; border: 1px solid #2a2820; border-radius: 8px;
        padding: 14px; margin-bottom: 15px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.35); }
.card h3 { margin: 0 0 6px 0; color: #f0ece4; }
.card p { margin: 2px 0; line-height: 1.5; color: #b0aaa0; }
.facts { color: #9a958a; font-size: 14px; margin: 0 0 8px 0; }
.rating { display: inline-block; background: #d4af37; color: #0a0a0c;
          padding: 2px 8px; border-radius: 4px; font-size: 13px; font-weight: bold; }
.results-heading { color: #c9c4b8; }
.thumbs { margin-top: 12px; }
.thumbs form { display: inline; margin-right: 8px; }
.thumbs button { background: #0f0f12; color: #e8e4dc; border: 1px solid #3a3830;
       border-radius: 4px; padding: 6px 12px; font-size: 14px; margin-top: 0;
       font-weight: normal; box-shadow: none; }
.thumbs button:hover { background: #1f1d18; border-color: #d4af37; color: #d4af37; }
.memory { color: #6a655c; font-size: 13px; margin-top: 20px; padding-top: 16px;
          border-top: 1px solid #2a2820; }
@media (max-width: 600px) { .row { grid-template-columns: 1fr; } }
"""

RUNTIME_SCRIPT = """
<script>
(function () {
  var minSlider = document.getElementById("min_runtime");
  var maxSlider = document.getElementById("max_runtime");
  var display = document.getElementById("runtime_display");
  var minLabel = document.getElementById("min_runtime_value");
  var maxLabel = document.getElementById("max_runtime_value");
  if (!minSlider || !maxSlider) return;

  function sync() {
    var min = parseInt(minSlider.value, 10);
    var max = parseInt(maxSlider.value, 10);
    if (min > max) {
      if (this === minSlider) maxSlider.value = min;
      else minSlider.value = max;
      min = parseInt(minSlider.value, 10);
      max = parseInt(maxSlider.value, 10);
    }
    display.textContent = min + " – " + max + " min";
    minLabel.textContent = min;
    maxLabel.textContent = max;
  }

  minSlider.addEventListener("input", sync);
  maxSlider.addEventListener("input", sync);
  sync.call(minSlider);
})();
</script>
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
    html += '<label>Runtime (minutes)</label>'
    html += (f'<p class="runtime-display" id="runtime_display">'
             f'{min_runtime} – {max_runtime} min</p>')
    html += '<div class="runtime-sliders">'
    html += ('<div class="slider-row"><span class="slider-label">Min</span>'
             f'<input type="range" name="min_runtime" id="min_runtime" '
             f'min="0" max="400" step="5" value="{min_runtime}">'
             f'<span class="slider-value" id="min_runtime_value">{min_runtime}</span></div>')
    html += ('<div class="slider-row"><span class="slider-label">Max</span>'
             f'<input type="range" name="max_runtime" id="max_runtime" '
             f'min="0" max="400" step="5" value="{max_runtime}">'
             f'<span class="slider-value" id="max_runtime_value">{max_runtime}</span></div>')
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
    html += f'<div class="facts"><span class="rating">&#9733; {safe(movie["rating"])}</span></div>'
    html += f'<p>{safe(movie["overview"])}</p>'
    html += '<div class="thumbs">'
    html += thumb_form(movie, state, "like", "&#128077; More like this")
    html += thumb_form(movie, state, "dislike", "&#128078; Not for me")
    return html + "</div></div>"


def build_results(state, movies, reply, error):
    if error:
        return f'<div class="problem">&#10060; Error: {safe(error)}</div>'

    html = ""
    if reply:
        html += f'<div class="reply"><strong>Chatbot:</strong> {safe(reply)}</div>'
    if movies is None:
        return html
    if len(movies) == 0:
        return html + '<div class="problem">No movies matched. Try other filters.</div>'

    html += f'<p class="results-heading"><strong>{len(movies)} recommendation(s)</strong> — rate them:</p>'
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
    page += RUNTIME_SCRIPT
    return page + "</body></html>"
