# Movie Recommender

A web-based movie recommender with a Claude-powered chatbot. Filter by genre, runtime, and language, describe what you're in the mood for, then rate the picks with thumbs up/down so the chatbot learns your taste. Built on [The Movie Database (TMDB)](https://www.themoviedb.org/) and [Anthropic Claude](https://www.anthropic.com/).

## Features

- Filter movies by genre, runtime range, and language
- Natural-language chat — tell Claude the vibe you're after
- Thumbs up/down feedback that carries across requests
- Deployable as a Flask app on [Vercel](https://vercel.com/)
- Core logic in `recommender.py`, chat layer in `chatbot.py`, UI in `page_builder.py`

## Prerequisites

- Python 3.12+
- A free [TMDB API key](https://www.themoviedb.org/settings/api)
- An [Anthropic API key](https://console.anthropic.com/) (optional — without it the app falls back to top TMDB matches)

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/ariana-song/movie-recommender.git
cd movie-recommender
```

### 2. Create and activate a virtual environment

```bash
conda create -n movie-recommender python=3.12
conda activate movie-recommender
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your environment variables

Copy `.env.example` to `.env` and fill in your keys:

```
TMDB_API_KEY=your_actual_key_here
ANTHROPIC_API_KEY=your_actual_key_here
```

The `.env` file is excluded from version control and will never be committed.

### 5. Run locally

```bash
python api/index.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Testing

```bash
pytest
```

Tests mock all external API calls, so no keys or network access are required.

## Deployment

The app is configured for Vercel via `vercel.json`. Set `TMDB_API_KEY` and `ANTHROPIC_API_KEY` as environment variables in your Vercel project settings.
