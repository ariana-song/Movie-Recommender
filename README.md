# Movie Recommender

A web app that recommends movies from [The Movie Database (TMDB)](https://www.themoviedb.org/) and lets you refine them with [Anthropic Claude](https://www.anthropic.com/). Set genre, language, and runtime first, describe the vibe in plain English, then thumbs-up or thumbs-down the picks so the next batch gets closer to your taste.

Built as a group project by Ariana Song, Kian Assary, and Rishi Haran.

## How it works

1. You choose hard filters (genre, language, runtime).
2. You type what you want, e.g. "funny live-action, nothing animated".
3. Claude turns that into extra TMDB constraints (genres to exclude) plus a short taste note.
4. The app fetches candidate movies from TMDB.
5. Claude ranks those real results and explains the picks.
6. Thumbs up/down are stored in hidden form fields and sent back on the next request, so Claude sees your full like/dislike history.

## Repo layout

| File | Role |
| --- | --- |
| `recommender.py` | TMDB search: genre/language maps, discover, clean results |
| `chatbot.py` | Claude layer: plan the search, then pick from TMDB results |
| `page_builder.py` | HTML page (filters, chat box, movie cards, thumbs) |
| `api/index.py` | Flask app: form state, routing, wiring the pieces together |
| `tests/` | Pytest suite with mocked TMDB and Claude calls |
| `.github/workflows/python-app.yml` | GitHub Actions: run tests on every push and pull request |

The app is MIT licensed. See `LICENSE`.

## Prerequisites

- [Anaconda](https://www.anaconda.com/) (or Miniconda) with Python 3.12
- A free [TMDB API key](https://www.themoviedb.org/settings/api)
- An [Anthropic API key](https://console.anthropic.com/) (optional — without it the app still runs and shows top TMDB matches)

## Setup

Use Anaconda Prompt on Windows, or Terminal on macOS/Linux.

### 1. Clone the repository

```shell
git clone https://github.com/ariana-song/Movie-Recommender.git
cd Movie-Recommender
```

### 2. Create and activate a virtual environment (Anaconda)

```shell
conda create -n movie-recommender python=3.12
conda activate movie-recommender
```

### 3. Install package dependencies (Pip)

```shell
pip install -r requirements.txt
```

This installs Flask, requests, python-dotenv, and pytest.

### 4. Set environment variables (local `.env` file)

Copy the example file, then paste in your real keys. Never put keys in the source code.

macOS / Linux:

```shell
cp .env.example .env
```

Windows (Command Prompt or Anaconda Prompt):

```shell
copy .env.example .env
```

Then edit `.env`:

```
TMDB_API_KEY=your_actual_tmdb_key_here
ANTHROPIC_API_KEY=your_actual_anthropic_key_here
```

`.env` is listed in `.gitignore`, so it will not be committed. On Vercel, add the same two names under Project Settings → Environment Variables instead of using a file.

## Run the program (Flask)

With the conda environment activated and `.env` filled in:

```shell
python api/index.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Run tests (Pytest)

```shell
pytest
```

All TMDB and Claude HTTP calls are mocked, so tests run offline. No API keys and no network access are required.

GitHub Actions runs this same `pytest` command on every push and pull request.

## Deployment

The app is set up for [Vercel](https://vercel.com/) via `vercel.json`. After you connect the GitHub repo, add `TMDB_API_KEY` and `ANTHROPIC_API_KEY` in the Vercel project settings.
