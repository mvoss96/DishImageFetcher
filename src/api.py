from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from database import ImageCacheDB
from image_fetcher import ImageFetcher
import os
import logging

def init_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] [%(filename)s] %(message)s ",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)

def init_config():
    load_dotenv()
    db_path = os.getenv("DB_PATH")
    api_key = os.getenv("API_KEY")
    cse_id = os.getenv("CSE_ID")
    if db_path is None:
        raise RuntimeError("DB_PATH environment variable is not set.")
    if api_key is None or cse_id is None:
        raise RuntimeError("API_KEY and CSE_ID environment variables must be set.")
    return db_path, api_key, cse_id

logger = init_logging()
db_path, api_key, cse_id = init_config()
db = ImageCacheDB(db_path)
app = FastAPI()

class ImageResponse(BaseModel):
    keyword: str
    image_url: str | None

@app.get("/image", response_model=ImageResponse)
def get_image(keyword: str):
    logger.info(f"Searching for keyword: '{keyword}'")
    cached_url = db.get_image_url(keyword)
    image_url = None
    if cached_url:
        logger.info(f"Found cached image URL for '{keyword}'")
        image_url = cached_url
    else:
        google_fetcher = ImageFetcher(api_key, cse_id)
        image_url = google_fetcher.fetch_image_url(keyword)
        if image_url:
            if db.save_image_url(keyword, image_url):
                logger.info(f"Successfully cached image URL for '{keyword}'")
            else:
                logger.error(f"Failed to cache image URL for '{keyword}'")
    logger.info(f"Image URL: {image_url}")
    if not image_url:
        raise HTTPException(status_code=404, detail="No image found for keyword")
    return ImageResponse(keyword=keyword, image_url=image_url)
