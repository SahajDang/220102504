from sqlalchemy.orm import Session
from database import URLMapping, ClickLog
from models import CreateShortURLRequest, CreateShortURLResponse, URLStatistics, ClickData
from utils import generate_shortcode, calculate_expiry, is_expired, format_iso8601, extract_location_from_ip
from config import config
from fastapi import HTTPException
from datetime import datetime, timezone

class URLShortenerService:
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_short_url(self, request: CreateShortURLRequest) -> CreateShortURLResponse:
        """Create a new shortened URL"""
        
        # Handle custom shortcode
        if request.shortcode:
            if self.shortcode_exists(request.shortcode):
                raise HTTPException(status_code=409, detail="Shortcode already exists")
            shortcode = request.shortcode
        else:
            shortcode = self.generate_unique_shortcode()
        
        # Calculate expiry
        validity = request.validity or config.DEFAULT_VALIDITY_MINUTES
        expires_at = calculate_expiry(validity)
        
        # Create URL mapping
        url_mapping = URLMapping(
            shortcode=shortcode,
            original_url=request.url,
            expires_at=expires_at
        )
        
        self.db.add(url_mapping)
        self.db.commit()
        self.db.refresh(url_mapping)
        
        # Create response
        short_link = f"{config.BASE_URL}/{shortcode}"
        expiry = format_iso8601(expires_at)
        
        return CreateShortURLResponse(
            shortLink=short_link,
            expiry=expiry
        )
    
    def get_original_url(self, shortcode: str, request_info: dict) -> str:
        """Get original URL and log the click"""
        
        url_mapping = self.db.query(URLMapping).filter(
            URLMapping.shortcode == shortcode
        ).first()
        
        if not url_mapping:
            raise HTTPException(status_code=404, detail="Shortcode not found")
        
        if is_expired(url_mapping.expires_at):
            raise HTTPException(status_code=410, detail="Short link has expired")
        
        # Log the click
        self.log_click(shortcode, request_info)
        
        # Increment click count
        url_mapping.click_count += 1
        self.db.commit()
        
        return url_mapping.original_url
    
    def get_statistics(self, shortcode: str) -> URLStatistics:
        """Get statistics for a shortened URL"""
        
        url_mapping = self.db.query(URLMapping).filter(
            URLMapping.shortcode == shortcode
        ).first()
        
        if not url_mapping:
            raise HTTPException(status_code=404, detail="Shortcode not found")
        
        # Get click logs
        click_logs = self.db.query(ClickLog).filter(
            ClickLog.shortcode == shortcode
        ).all()
        
        click_data = [
            ClickData(
                timestamp=log.clicked_at,
                referrer=log.referrer,
                user_agent=log.user_agent,
                ip_address=log.ip_address,
                location=log.location
            ) for log in click_logs
        ]
        
        return URLStatistics(
            shortcode=shortcode,
            original_url=url_mapping.original_url,
            created_at=url_mapping.created_at,
            expires_at=url_mapping.expires_at,
            total_clicks=url_mapping.click_count,
            click_data=click_data
        )
    
    def shortcode_exists(self, shortcode: str) -> bool:
        """Check if shortcode already exists"""
        return self.db.query(URLMapping).filter(
            URLMapping.shortcode == shortcode
        ).first() is not None
    
    def generate_unique_shortcode(self) -> str:
        """Generate a unique shortcode"""
        max_attempts = 10
        for _ in range(max_attempts):
            shortcode = generate_shortcode()
            if not self.shortcode_exists(shortcode):
                return shortcode
        
        # If we can't generate a unique shortcode, try with longer length
        for length in range(config.SHORTCODE_LENGTH + 1, config.SHORTCODE_LENGTH + 5):
            shortcode = generate_shortcode(length)
            if not self.shortcode_exists(shortcode):
                return shortcode
        
        raise HTTPException(status_code=500, detail="Unable to generate unique shortcode")
    
    def log_click(self, shortcode: str, request_info: dict):
        """Log a click event"""
        
        click_log = ClickLog(
            shortcode=shortcode,
            referrer=request_info.get('referrer'),
            user_agent=request_info.get('user_agent'),
            ip_address=request_info.get('ip_address'),
            location=extract_location_from_ip(request_info.get('ip_address'))
        )
        
        self.db.add(click_log)
        self.db.commit()