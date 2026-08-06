# Movie Recommender

A movie recommender that lets a user filter by genre, runtime, and language, and returns a list of matching movies. Built on [The Movie Database (TMDB)](https://www.themoviedb.org/) API.

## Features

- Filter movies by genre, runtime range, and language
- Interactive notebook UI built with `ipywidgets`
- Core logic separated into `recommender.py` so it's independently testable

## Prerequisites

- [Anaconda](https://www.anaconda.com/download) (or Miniconda)
- A free [TMDB API key](https://www.themoviedb.org/settings/api)

## Setup

### 1. Clone the repository

git clone https://github.com/ariana-song/movie-recommender.git
cd movie-recommender

### 2. Create and activate a virtual environment (via Anaconda)

conda create -n movie-recommender python=3.12
conda activate movie-recommender

### 3. Install dependencies

pip install -r requirements.txt

### 4. Set your environment variables

Create a file named `.env` in the project root with the following line:

TMDB_API_KEY=your_actual_key_here

Replace `your_actual_key_here` with your own TMDB API key (get one free at https://www.themoviedb.org/settings/api). This file is excluded from version control via `.gitignore` and will never be committed.
