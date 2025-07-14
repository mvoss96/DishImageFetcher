from typing import List
import logging

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse

from .models import ImageResponse
from .text_utils import normalize
from .database import ImageCacheDB
from .image_fetcher import ImageFetcher
from .image_analyser import ImageAnalyser
from .settings import Settings

router = APIRouter()
settings = Settings()
logger = logging.getLogger(__name__)
db = ImageCacheDB(settings.DB_PATH)
image_fetcher = ImageFetcher(settings.CSE_API_KEY, settings.CSE_ID)
image_analyser = ImageAnalyser(
    ai_model=settings.AI_MODEL,
    api_key=settings.AI_API_KEY,
    base_url=settings.AI_BASE_URL
)


def _fetch_image_for_keyword(keyword: str) -> ImageResponse:
    image_url = None
    result_keyword = keyword
    try:
        normalized = normalize(keyword)
        if normalized and len(normalized) >= 2 and len(normalized) <= 100:
            result_keyword = normalized
            logger.info(
                f"Searching for keyword: '{keyword}' (normalized: '{normalized}')")
            cached_url = db.get_image_url(normalized)
            if cached_url:
                logger.info(f"Found cached image URL for '{normalized}'")
                image_url = cached_url
            else:
                image_url = image_fetcher.fetch_image_url(normalized)
                if image_url:
                    if db.save_image_url(normalized, image_url):
                        logger.info(
                            f"Successfully cached image URL for '{normalized}'")
                    else:
                        logger.error(
                            f"Failed to cache image URL for '{normalized}'")
            logger.info(f"Image URL for '{normalized}': {image_url}")
        else:
            logger.warning(
                f"Invalid keyword: '{keyword}' (normalized: '{normalized}')")
    except Exception as e:
        logger.error(f"Error processing keyword '{keyword}': {str(e)}")
    return ImageResponse(keyword=result_keyword, image_url=image_url)


@router.get("/images", response_model=List[ImageResponse])
def get_multiple_images(keyword: List[str] = Query(..., description="List of keywords to search for")):
    if not keyword:
        raise HTTPException(
            status_code=422, detail="At least one keyword must be provided.")
    if len(keyword) > 50:
        raise HTTPException(
            status_code=422, detail="Too many keywords provided. Maximum 50 keywords allowed.")
    try:
        normalized_keywords = [normalize(kw) for kw in keyword]
        results = [_fetch_image_for_keyword(kw) for kw in normalized_keywords]
        return results
    except Exception as e:
        logger.error(f"Unexpected error in get_multiple_images: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error occurred while processing keywords.")


@router.post("/upload")
async def upload_file(image: UploadFile = File(...)):
    """Route for uploading images"""
    try:
        # Log information about the uploaded file
        logger.info(f"File uploaded: {image.filename}")
        logger.info(f"Content-Type: {image.content_type}")
        logger.info(
            f"File size: {image.size if hasattr(image, 'size') else 'Unknown'} Bytes")

        # Validate the content type
        if not image.content_type or not image.content_type.startswith('image/'):
            logger.warning(f"Invalid content type: {image.content_type}")
            raise HTTPException(
                status_code=400, detail="Only image files are allowed")

        # Read the file content
        content = await image.read()
        actual_size = len(content)
        logger.info(f"Actual file size: {actual_size} Bytes")

        # Analyze the image directly from bytes
        result = image_analyser.analyse_image(content)
        logger.info(f"Analysis result: {result}")


        # Fetch image URLs for each menu item
        enhanced_result = []
        for item in result:
            # Use keyword from AI response for image fetching, fallback to name if no keyword
            search_keyword = item.get("keyword", item.get("name", ""))
            if search_keyword:
                # Fetch image URL using the keyword from AI response
                image_response = _fetch_image_for_keyword(search_keyword)
                # Create enhanced item with image URL
                enhanced_item = {
                    "name": item.get("name"),
                    "description": item.get("description"),
                    "price": item.get("price"),
                    "image_url": image_response.image_url
                }
                enhanced_result.append(enhanced_item)
                logger.info(f"Added image URL for keyword '{search_keyword}' (dish: '{item.get('name')}'): {image_response.image_url}")
            else:
                # If no keyword or name, add item without image URL
                enhanced_item = {
                    "name": item.get("name"),
                    "description": item.get("description"),
                    "price": item.get("price"),
                    "image_url": None
                }
                enhanced_result.append(enhanced_item)

        # Generate HTML for the menu items
        html_content = _generate_menu_html(enhanced_result)
        return HTMLResponse(content=html_content, status_code=200)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error while uploading the file")


def _generate_menu_html(menu_items: List[dict]) -> str:
    """Generate HTML page for menu items"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Menu</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
                color: #333;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            h1 {
                text-align: center;
                color: #2c3e50;
                margin-bottom: 30px;
                font-size: 2.5em;
            }
            .menu-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 20px;
                padding: 20px 0;
            }
            .menu-item {
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            .menu-item:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
            }
            .item-image {
                width: 100%;
                height: 200px;
                object-fit: cover;
                background-color: #e9ecef;
            }
            .item-content {
                padding: 20px;
            }
            .item-name {
                font-size: 1.4em;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
            .item-description {
                color: #666;
                line-height: 1.5;
                margin-bottom: 15px;
                font-size: 0.95em;
            }
            .item-price {
                font-size: 1.3em;
                font-weight: bold;
                color: #e74c3c;
                text-align: right;
            }
            .no-image {
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: #ecf0f1;
                color: #95a5a6;
                font-size: 0.9em;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Menu</h1>
            <div class="menu-grid">
    """
    
    for item in menu_items:
        name = item.get("name", "Unknown Item")
        description = item.get("description", "")
        price = item.get("price", "")
        image_url = item.get("image_url")
        
        html += f"""
                <div class="menu-item">
        """
        
        if image_url:
            html += f"""
                    <img src="{image_url}" alt="{name}" class="item-image" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                    <div class="no-image" style="display:none;">No Image Available</div>
            """
        else:
            html += """
                    <div class="item-image no-image">No Image Available</div>
            """
        
        html += f"""
                    <div class="item-content">
                        <div class="item-name">{name}</div>
        """
        
        if description:
            html += f"""
                        <div class="item-description">{description}</div>
            """
        
        if price:
            html += f"""
                        <div class="item-price">{price}</div>
            """
        
        html += """
                    </div>
                </div>
        """
    
    html += """
            </div>
        </div>
    </body>
    </html>
    """
    
    return html
