import sys
import os
import logging
from dotenv import load_dotenv
from database import ImageCacheDB
from image_fetcher import ImageFetcher


def main() -> None:
    """Main function to handle command line arguments and execute the search."""
    # Logging initialisieren
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] [%(filename)s] %(message)s ",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger: logging.Logger = logging.getLogger(__name__)

    # .env laden
    load_dotenv()
    db_path: str | None = os.getenv("DB_PATH")
    api_key: str | None = os.getenv("API_KEY")
    cse_id: str | None = os.getenv("CSE_ID")

    if db_path is None:
        logger.error("DB_PATH environment variable is not set.")
        sys.exit(1)

    if api_key is None or cse_id is None:
        logger.error("API_KEY and CSE_ID environment variables must be set.")
        sys.exit(1)

    # Initialize database instance
    db: ImageCacheDB = ImageCacheDB(db_path)

    # Get keyword from command line argument
    if len(sys.argv) < 2:
        logger.error("Usage: python3 app.py <keyword>")
        sys.exit(1)

    # Join all arguments to handle multi-word keywords
    keyword: str = " ".join(sys.argv[1:])
    logger.info(f"Searching for keyword: '{keyword}'")

    # Check cache first
    cached_url: str | None = db.get_image_url(keyword)
    image_url: str | None
    if cached_url:
        logger.info(f"Found cached image URL for '{keyword}'")
        image_url = cached_url
    else:
        # Fetch from Google API if not cached
        google_fetcher: ImageFetcher = ImageFetcher(api_key, cse_id)
        image_url = google_fetcher.fetch_image_url(keyword)

        # Save to cache if we got a result
        if image_url:
            if db.save_image_url(keyword, image_url):
                logger.info(f"Successfully cached image URL for '{keyword}'")
            else:
                logger.error(f"Failed to cache image URL for '{keyword}'")

    logger.info(f"Image URL: {image_url}")


if __name__ == "__main__":
    main()
