import logging
import re
import unicodedata

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import ImageCacheDB
from image_fetcher import ImageFetcher
from models import ImageResponse
from settings import Settings


def init_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] [%(filename)s] %(message)s ",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)

def normalize(keyword: str) -> str:
    """
    Removes unnecessary whitespaces, punctuation, replaces umlauts and accented characters generically,
    and removes all characters that would not appear in a dish name (only lowercase a-z and spaces).
    """
    # Unicode normalization (decompose accents)
    keyword = unicodedata.normalize('NFKD', keyword)
    # Remove accents (diacritics)
    keyword = ''.join(c for c in keyword if unicodedata.category(c) != 'Mn')
    # Convert to lower case
    keyword = keyword.lower()
    # Replace German umlauts
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss'
    }
    for orig, repl in replacements.items():
        keyword = keyword.replace(orig, repl)
    # Remove all characters except a-z and spaces
    keyword = re.sub(r'[^a-z ]', '', keyword)
    # Reduce multiple whitespaces to a single space
    keyword = re.sub(r'\s+', ' ', keyword).strip()
    return keyword

# App
settings = Settings()
logger = init_logging()
db = ImageCacheDB(settings.DB_PATH)
app = FastAPI()
image_fetcher = ImageFetcher(settings.API_KEY, settings.CSE_ID)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/image", response_model=ImageResponse)
def get_image(keyword: str):
    """
    Returns the image URL for the given keyword. Gets the image from cache or from Google Images.
    Returns 400 if API key or CSE ID are missing.
    Returns 404 if no image is found.
    Returns 422 if normalized keyword is empty, too short, or too long.
    """
    normalized = normalize(keyword)
    if not normalized or len(normalized) < 2 or len(normalized) > 100:
        raise HTTPException(status_code=422, detail="Normalized dish name is empty, too short, or too long.")
    logger.info(f"Searching for keyword: '{keyword}' (normalized: '{normalized}')")
    cached_url = db.get_image_url(normalized)
    image_url = None
    if cached_url:
        logger.info(f"Found cached image URL for '{normalized}'")
        image_url = cached_url
    else:
        image_url = image_fetcher.fetch_image_url(normalized)
        if image_url:
            if db.save_image_url(normalized, image_url):
                logger.info(f"Successfully cached image URL for '{normalized}'")
            else:
                logger.error(f"Failed to cache image URL for '{normalized}'")
    logger.info(f"Image URL: {image_url}")
    if not image_url:
        raise HTTPException(status_code=404, detail="No image found for keyword")
    return ImageResponse(keyword=keyword, image_url=image_url)
