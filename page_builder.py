"""
page_builder.py

Bare-bones HTML page for the movie recommender form + results.
"""

from html import escape


def safe(text):
    if text is None:
        return ""
    return escape(str(text))


PAGE_STYLES = """
body { font-family: Georgia, serif; max-width: 720px; margin: 0 auto; padding: 24px; }
label { display: block; margin-top: 12px; font-weight: bold; }
select, input { width: 100%; padding: 8px; margin-top: 4px; }
button { margin-top: 16px; padding: 10px 16px; width: 100%; }
.note { margin: 16px 0; padding: 12px; background: #eee; }
.note.problem { background: #f3e0e0; }
.card { border: 1px solid #ddd; padding: 12px; margin-bottom: 12px; }
.facts { color: #666; font-size: 14px; }
"""


def build_dropdown(field_name, options, selected_value):
    html = f'<select name="{safe(field_name)}" id="{safe(field_name)}">'
    for option in options:
        selected = " selected" if str(option) == str(selected_value) else ""
        html += f'<option value="{safe(option)}"{selected}>{safe(option)}</option>'
    html += "</select>"
    return html


def build_form(answers, genres, languages):
    html = '<form method="post" action="/">'
    html += '<label for="genre">Genre</label>'
    html += build_dropdown("genre", genres, answers["genre"])
    html += '<label for="language">Language</label>'
    html += build_dropdown("language", languages, answers["language"])
    html += '<label for="min_runtime">Min runtime (minutes)</label>'
    html += (
        f'<input type="number" name="min_runtime" id="min_runtime" '
        f'value="{safe(answers["min_runtime"])}">'
    )
    html += '<label for="max_runtime">Max runtime (minutes)</label>'
    html += (
        f'<input type="number" name="max_runtime" id="max_runtime" '
        f'value="{safe(answers["max_runtime"])}">'
    )
    html += '<label for="max_results">How many movies</label>'
    html += build_dropdown("max_results", ["3", "5", "8", "10"], answers["max_results"])
    html += '<button type="submit">Find movies</button>'
    html += "</form>"
    return html


def build_movie_card(movie):
    html = '<div class="card">'
    html += f'<h3>{safe(movie["title"])} ({safe(movie["year"])})</h3>'
    html += f'<div class="facts">Rating: {safe(movie["rating"])}</div>'
    html += f'<p>{safe(movie["overview"])}</p>'
    html += "</div>"
    return html


def build_results(movies=None, error=None):
    if error:
        return f'<div class="note problem">{safe(error)}</div>'
    if movies is None:
        return ""
    html = f'<div class="note">Found {len(movies)} movie(s).</div>'
    for movie in movies:
        html += build_movie_card(movie)
    return html


def build_page(answers, genres, languages, movies=None, error=None):
    page = "<!DOCTYPE html><html><head>"
    page += '<meta charset="utf-8">'
    page += "<title>Movie Recommender</title>"
    page += f"<style>{PAGE_STYLES}</style>"
    page += "</head><body>"
    page += "<h1>Movie Recommender</h1>"
    page += "<p>Pick a genre, runtime, and language.</p>"
    page += build_form(answers, genres, languages)
    page += build_results(movies=movies, error=error)
    page += "</body></html>"
    return page
