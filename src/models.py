from pydantic import BaseModel, ValidationError, Field
from typing import Optional, List

class ImageResponse(BaseModel):
    """Response model for the /image endpoint."""
    keyword: str
    image_url: Optional[str]

class MultipleImageResponse(BaseModel):
    """Response model for the /images endpoint."""
    results: List[ImageResponse]