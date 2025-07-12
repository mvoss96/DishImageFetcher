from pydantic import BaseModel, ValidationError, Field
from typing import Optional

class ImageResponse(BaseModel):
    """Response model for the /image endpoint."""
    keyword: str
    image_url: Optional[str]