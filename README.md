# DishImageFetcher

This project provides a FastAPI-based backend to fetch and cache image URLs for given keywords using Google Images.

## Features
- Caches image URLs in a local database
- Fetches images using Google Custom Search API

## Dev Container
This project includes a `devcontainer.json` for easy setup in VS Code or compatible environments. The container installs all dependencies automatically and provides a ready-to-use Python development environment.

## Requirements
- API key and CSE ID for Google Custom Search (set in `.env`)

## Setup
Copy `.env.example` to `.env` and set your API credentials:
Example `.env` content:
```
API_KEY=your_google_api_key
CSE_ID=your_custom_search_engine_id
```

### Option 1: Dev Container (Recommended)
If you use VS Code or a compatible editor, simply open the project in a dev container. All dependencies are installed automatically and you get a ready-to-use Python development environment.

### Option 2: Manual Setup
If you do not use a dev container, follow these steps:
1. Install Python 3.10+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Development
Run the FastAPI server in development mode:
```bash
fastapi dev src/main.py
```
Or with Uvicorn:
```bash
uvicorn src.main:app --reload
```

## Usage
Request an image URL for a keyword:
```
GET /image?keyword=pizza
```
Response:
```json
{
  "keyword": "pizza",
  "image_url": "https://..."
}
```

## Input Normalization
All keywords are normalized before searching:
- Converts to lowercase
- Removes accents and diacritics (e.g. "é" → "e")
- Replaces German umlauts (e.g. "ä" → "ae")
- Removes all characters except a-z and spaces
- Reduces multiple spaces to a single space
- Rejects empty, too short (<2), or too long (>100) normalized names with HTTP 422

Example:
- Input: `Crème brûlée`
- Normalized: `creme brulee`

If the normalized keyword is invalid, the API returns:
```json
{
  "detail": "Normalized dish name is empty, too short, or too long."
}
```
