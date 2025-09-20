from pydantic import BaseModel, validator
from datetime import datetime, timezone
from typing import Optional, List
import validators

class CreateShortURLRequest(BaseModel):
    url: str
    validity: Optional[int] = None
    shortcode: Optional[str] = None
    
    @validator('url')
    def validate_url(cls, v):
        if not validators.url(v):
            raise ValueError('Invalid URL format')
        return v
    
    @validator('validity')
    def validate_validity(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Validity must be a positive integer')
        return v
    
    @validator('shortcode')
    def validate_shortcode(cls, v):
        if v is not None:
            if len(v) < 1 or len(v) > 50:
                raise ValueError('Shortcode must be between 1 and 50 characters')
            if not v.replace('-', '').replace('_', '').isalnum():
                raise ValueError('Shortcode must be alphanumeric (with optional hyphens and underscores)')
        return v

class CreateShortURLResponse(BaseModel):
    shortLink: str
    expiry: str

class ClickData(BaseModel):
    timestamp: datetime
    referrer: Optional[str]
    user_agent: Optional[str]
    ip_address: Optional[str]
    location: Optional[str]

class URLStatistics(BaseModel):
    shortcode: str
    original_url: str
    created_at: datetime
    expires_at: datetime
    total_clicks: int
    click_data: List[ClickData]

class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: str