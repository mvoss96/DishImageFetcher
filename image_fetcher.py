"""Google Images Search functionality for image URL retrieval."""

from google_images_search import GoogleImagesSearch
from typing import Optional


class ImageFetcher:
    """Class to handle Google Images search."""
    
    def __init__(self, api_key: str, cse_id: str):
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
            print(f"Fetching image URL for '{keyword}' from Google API")
            gis = GoogleImagesSearch(self.api_key, self.cse_id)
            gis.search({'q': keyword + " dish", 'num': 1})

            for image in gis.results():
                return image.url

            print(f"No images found for '{keyword}'")
            return None

        except Exception as e:
            print(f"Error fetching image for '{keyword}': {e}")
            return None
