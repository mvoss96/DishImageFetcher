import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError, Field
from typing import Optional
from pydantic_settings import BaseSettings

from database import ImageCacheDB
from image_fetcher import ImageFetcher

def init_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] [%(filename)s] %(message)s ",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)

class Settings(BaseSettings):
    DB_PATH: str = Field(default="cache.db")
    API_KEY: str = Field(default="")
    CSE_ID: str = Field(default="")

    class Config:
        env_file = ".env"

class ImageResponse(BaseModel):
    """Response model for the /image endpoint."""
    keyword: str
    image_url: Optional[str]


# App
try:
    settings = Settings()
except ValidationError as e:
    raise RuntimeError(f"Config Error: {e}")

logger = init_logging()
db = ImageCacheDB(settings.DB_PATH)

# Enable CORS (all origins allowed, for demo purposes)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Initialize ImageFetcher only once
image_fetcher = None
if settings.API_KEY and settings.CSE_ID:
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
    """
    logger.info(f"Searching for keyword: '{keyword}'")
    cached_url = db.get_image_url(keyword)
    image_url = None
    if cached_url:
        logger.info(f"Found cached image URL for '{keyword}'")
        image_url = cached_url
    else:
        global image_fetcher
        if image_fetcher is None:
            image_fetcher = ImageFetcher(settings.API_KEY, settings.CSE_ID)
        image_url = image_fetcher.fetch_image_url(keyword)
        if image_url:
            if db.save_image_url(keyword, image_url):
                logger.info(f"Successfully cached image URL for '{keyword}'")
            else:
                logger.error(f"Failed to cache image URL for '{keyword}'")
    logger.info(f"Image URL: {image_url}")
    if not image_url:
        raise HTTPException(status_code=404, detail="No image found for keyword")
    return ImageResponse(keyword=keyword, image_url=image_url)
