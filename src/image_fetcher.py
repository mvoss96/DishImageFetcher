"""Google Images Search functionality for image URL retrieval."""

import logging
from google_images_search import GoogleImagesSearch
from typing import Optional

logger = logging.getLogger("image_fetcher")

class ImageFetcher:
    """Class to handle Google Images search."""

    api_key: str
    cse_id: str

    def __init__(self, api_key: str, cse_id: str) -> None:
        """Initialize with Google API credentials."""
        self.api_key = api_key
        self.cse_id = cse_id

    def fetch_image_url(self, keyword: str) -> Optional[str]:
        """
        Fetch image URL for a keyword from Google Images.
        
        Args:
            keyword: The search term for the image
            
        Returns:
            Image URL if found, None otherwise
        """
        try:
            logger.info(f"Fetching image URL for '{keyword}' from Google API")
            gis: GoogleImagesSearch = GoogleImagesSearch(self.api_key, self.cse_id)
            search_query: str = keyword + " dish"
            logger.debug(f"Using search query: '{search_query}'")
            gis.search({'q': search_query, 'num': 1})

            for image in gis.results():
                logger.info(f"Found image URL: {image.url}")
                return image.url

            logger.warning(f"No images found for '{keyword}'")
            return None

        except Exception as e:
            logger.error(f"Error fetching image for '{keyword}': {e}")
            return None
