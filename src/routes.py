from typing import List
import logging

from fastapi import APIRouter, HTTPException, Query

from .models import ImageResponse
from .text_utils import normalize
from .database import ImageCacheDB
from .image_fetcher import ImageFetcher
from .settings import Settings

router = APIRouter()
settings = Settings()
logger = logging.getLogger(__name__)
db = ImageCacheDB(settings.DB_PATH)
image_fetcher = ImageFetcher(settings.API_KEY, settings.CSE_ID)

def _fetch_image_for_keyword(keyword: str) -> ImageResponse:
    image_url = None
    result_keyword = keyword
    try:
        normalized = normalize(keyword)
        if normalized and len(normalized) >= 2 and len(normalized) <= 100:
            result_keyword = normalized
            logger.info(f"Searching for keyword: '{keyword}' (normalized: '{normalized}')")
            cached_url = db.get_image_url(normalized)
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
        else:
            logger.warning(f"Invalid keyword: '{keyword}' (normalized: '{normalized}')")
    except Exception as e:
        logger.error(f"Error processing keyword '{keyword}': {str(e)}")
    return ImageResponse(keyword=result_keyword, image_url=image_url)

@router.get("/images", response_model=List[ImageResponse])
def get_multiple_images(keyword: List[str] = Query(..., description="List of keywords to search for")):
    if not keyword:
        raise HTTPException(status_code=422, detail="At least one keyword must be provided.")
    if len(keyword) > 50:
        raise HTTPException(status_code=422, detail="Too many keywords provided. Maximum 50 keywords allowed.")
    try:
        normalized_keywords = [normalize(kw) for kw in keyword]
        results = [_fetch_image_for_keyword(kw) for kw in normalized_keywords]
        return results
    except Exception as e:
        logger.error(f"Unexpected error in get_multiple_images: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error occurred while processing keywords.")
