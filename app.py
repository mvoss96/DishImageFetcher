import sys
import os
from dotenv import load_dotenv
from database import ImageCacheDB
from image_fetcher import ImageFetcher


def main():
    """Main function to handle command line arguments and execute the search."""
    # .env laden
    load_dotenv()

    # Umgebungsvariablen nach load_dotenv() auslesen
    db_path = os.getenv("DB_PATH")
    api_key = os.getenv("API_KEY")
    cse_id = os.getenv("CSE_ID")

    # Initialize database instance
    if db_path is None:
        print("Error: DB_PATH environment variable is not set.")
        sys.exit(1)
    db = ImageCacheDB(db_path)

    # Get keyword from command line argument
    if len(sys.argv) < 2:
        print("Usage: python3 test.py <keyword>")
        sys.exit(1)

    # Join all arguments to handle multi-word keywords
    keyword = " ".join(sys.argv[1:])

    # Initialize Google Images fetcher
    if api_key is None or cse_id is None:
        print("Error: API_KEY and CSE_ID environment variables must be set.")
        sys.exit(1)
    
    google_fetcher = ImageFetcher(api_key, cse_id)
    
    # Check cache first
    cached_url = db.get_image_url(keyword)
    if cached_url:
        print(f"Found cached image URL for '{keyword}'")
        image_url = cached_url
    else:
        # Fetch from Google API if not cached
        image_url = google_fetcher.fetch_image_url(keyword)
        
        # Save to cache if we got a result
        if image_url:
            if db.save_image_url(keyword, image_url):
                print(f"Successfully cached image URL for '{keyword}'")
            else:
                print(f"Failed to cache image URL for '{keyword}'")
    
    print(f"Image URL: {image_url}")


if __name__ == "__main__":
    main()
