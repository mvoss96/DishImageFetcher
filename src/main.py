import logging
import re
import unicodedata
from typing import List

from fastapi import FastAPI, HTTPException, Query
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

def _fetch_image_for_keyword(keyword: str) -> ImageResponse:
    """
    Helper function to fetch image for a single keyword.
    Returns ImageResponse with image_url=None if no image is found or validation fails.
    """
    try:
        normalized = normalize(keyword)
        if not normalized or len(normalized) < 2 or len(normalized) > 100:
            logger.warning(f"Invalid keyword: '{keyword}' (normalized: '{normalized}')")
            return ImageResponse(keyword=keyword, image_url=None)
        
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
        
        logger.info(f"Image URL for '{normalized}': {image_url}")
        return ImageResponse(keyword=normalized, image_url=image_url)
        
    except Exception as e:
        logger.error(f"Error processing keyword '{keyword}': {str(e)}")
        return ImageResponse(keyword=keyword, image_url=None)

app = FastAPI()
image_fetcher = ImageFetcher(settings.API_KEY, settings.CSE_ID)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/images", response_model=List[ImageResponse])
def get_multiple_images(keyword: List[str] = Query(..., description="List of keywords to search for")):
    """
    Returns image URLs for multiple keywords at once. Gets images from cache or from Google Images.
    Returns 400 if API key or CSE ID are missing.
    Returns 422 if no keywords provided or too many keywords.
    For individual keywords that fail, returns None as image_url but still includes them in results.
    All keywords are normalized before processing.
    """
    if not keyword:
        raise HTTPException(status_code=422, detail="At least one keyword must be provided.")
    
    if len(keyword) > 50:  # Limit to prevent abuse
        raise HTTPException(status_code=422, detail="Too many keywords provided. Maximum 50 keywords allowed.")
    
    try:
        # Normalize all keywords before processing
        normalized_keywords = [normalize(kw) for kw in keyword]
        results = [_fetch_image_for_keyword(kw) for kw in normalized_keywords]
        return results
    except Exception as e:
        logger.error(f"Unexpected error in get_multiple_images: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error occurred while processing keywords.")

