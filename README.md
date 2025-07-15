# Menu Image Analyzer

A full-stack web application that analyzes menu images using OCR and AI, then enhances them with high-quality dish images from Google Images. Upload a menu photo and get back a formatted menu with images for each dish.

## Features
- **Web Interface**: Simple drag-and-drop interface for menu image uploads
- **OCR Text Extraction**: Uses Tesseract OCR to extract text from menu images
- **AI Menu Parsing**: Leverages OpenAI-compatible models to parse menu items, descriptions, and prices
- **Intelligent Image Fetching**: Automatically finds relevant dish images using Google Custom Search
- **Smart Caching**: Caches image URLs in a local database to reduce API usage
- **Enhanced Menu Display**: Generates a beautiful HTML menu with images and formatting

## How It Works
1. **Upload**: Upload a menu image through the web interface
2. **OCR**: The app extracts text from the image using Tesseract OCR
3. **AI Analysis**: An AI model parses the text to identify menu items, descriptions, and prices
4. **Image Enhancement**: For each menu item, the app searches for a relevant dish image using Google Custom Search
5. **Display**: A formatted HTML menu is generated with images and original menu information

## API Endpoints
- `GET /` - Web interface for uploading menu images
- `POST /upload` - Upload and analyze a menu image, returns HTML with enhanced menu
- `GET /images?keyword=pizza&keyword=pasta` - Fetch image URLs for multiple keywords (bulk API)

## Technologies Used
- **Backend**: FastAPI (Python)
- **Frontend**: HTML/CSS with modern styling
- **OCR**: Tesseract OCR with pytesseract
- **AI**: OpenAI-compatible models for menu parsing
- **Image Search**: Google Custom Search API
- **Database**: SQLite for image URL caching

## Dev Container
This project includes a `devcontainer.json` for easy setup in VS Code or compatible environments. The container installs all dependencies automatically and provides a ready-to-use Python development environment.

## Requirements
- Google Custom Search API key and CSE ID (for image fetching)
- OpenAI-compatible API key (for menu parsing)
- Tesseract OCR (automatically installed in dev container)

## Setup
Copy `.env.example` to `.env` and set your API credentials:
```env
# Google Custom Search API
CSE_API_KEY=your_google_api_key
CSE_ID=your_custom_search_engine_id

# AI Model Configuration (OpenAI-compatible)
AI_MODEL=gpt-4o-mini, llama-3.1-8b-instant or similar
AI_API_KEY=your_ai_api_key
AI_BASE_URL=https://api.openai.com/v1

# Database
DB_PATH=cache.db
```

### Option 1: Dev Container (Recommended)
If you use VS Code or a compatible editor, simply open the project in a dev container. All dependencies (including Tesseract OCR) are installed automatically and you get a ready-to-use Python development environment.

### Option 2: Manual Setup
If you do not use a dev container, follow these steps:
1. Install Python 3.10+
2. Install Tesseract OCR:
   - Ubuntu/Debian: `sudo apt-get install tesseract-ocr tesseract-ocr-eng`
   - macOS: `brew install tesseract`
   - Windows: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application
Start the FastAPI server:
```bash
fastapi dev src/main.py
```
Or with Uvicorn:
```bash
uvicorn src.main:app --reload
```

The application will be available at `http://localhost:8000`

## Usage
### Web Interface
1. Open `http://localhost:8000` in your browser
2. Upload a menu image using the file input
3. Wait for processing (OCR + AI analysis + image fetching)
4. View the enhanced menu with images

### API Usage
For bulk image fetching, you can use the API directly:
```bash
curl "http://localhost:8000/images?keyword=pizza&keyword=pasta&keyword=salad"
```

Response:
```json
[
  {
    "keyword": "pizza",
    "image_url": "https://..."
  },
  {
    "keyword": "pasta", 
    "image_url": "https://..."
  },
  {
    "keyword": "salad",
    "image_url": "https://..."
  }
]
```

## Caching System
The application uses a local SQLite database to cache image URLs for dish keywords:

- When processing a menu item, the system first normalizes the keyword and checks if an image URL is already cached
- If a cached image URL exists, it is used immediately (faster response)
- If no cached image URL is found, a new image is fetched from Google Custom Search and cached
- All cache operations are case-insensitive and use normalized keywords
- This reduces API usage and speeds up repeated requests for the same dishes

## Text Normalization
All dish keywords are normalized before searching for images:
- Converts to lowercase
- Removes accents and diacritics (e.g. "é" → "e")  
- Replaces German umlauts (e.g. "ä" → "ae")
- Reduces multiple spaces to a single space
- Rejects empty, too short (<2), or too long (>100) normalized names

Example:
- Input: `Crème brûlée`  
- Normalized: `creme brulee`

## Project Structure
```
src/
├── main.py           # FastAPI application entry point
├── routes.py         # API endpoints (/upload, /images)  
├── image_analyser.py # OCR and AI menu parsing
├── image_fetcher.py  # Google Images search
├── database.py       # SQLite caching layer
├── models.py         # Pydantic data models
├── text_utils.py     # Text normalization utilities
├── settings.py       # Configuration management
└── static/           # Frontend files
    ├── index.html    # Upload interface
    └── style.css     # Modern styling
```
