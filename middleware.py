from fastapi import Request
import time
import json
from datetime import datetime, timezone

class LoggingMiddleware:
    """Optimized logging middleware"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # Store request info without reading body yet
        request_info = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": scope["method"],
            "path": scope["path"],
            "query_string": scope.get("query_string", b"").decode(),
        }
        
        # Log basic request info immediately
        print(f"[REQUEST] {request_info['method']} {request_info['path']} - Started")
        
        # Create response wrapper to capture status code
        response_data = {"status_code": None, "body": b""}
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                response_data["status_code"] = message["status"]
            elif message["type"] == "http.response.body":
                response_data["body"] += message.get("body", b"")
            await send(message)
        
        # Process request
        await self.app(scope, receive, send_wrapper)
        
        # Log response summary
        process_time = time.time() - start_time
        print(f"[RESPONSE] {request_info['method']} {request_info['path']} - "
              f"Status: {response_data['status_code']} - "
              f"Time: {process_time:.3f}s")

# =============================================================================
# OPTIMIZED SERVICES.PY (Database optimizations)
# =============================================================================

from sqlalchemy.orm import Session
from database import URLMapping, ClickLog
from models import CreateShortURLRequest, CreateShortURLResponse, URLStatistics, ClickData
from utils import generate_shortcode, calculate_expiry, is_expired, format_iso8601, extract_location_from_ip
from config import config
from fastapi import HTTPException
from datetime import datetime, timezone
import random

class URLShortenerService:
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_short_url(self, request: CreateShortURLRequest) -> CreateShortURLResponse:
        """Optimized create_short_url method"""
        
        # Handle custom shortcode
        if request.shortcode:
            # Single query to check existence
            existing = self.db.query(URLMapping.id).filter(
                URLMapping.shortcode == request.shortcode
            ).first()
            if existing:
                raise HTTPException(status_code=409, detail="Shortcode already exists")
            shortcode = request.shortcode
        else:
            shortcode = self.generate_unique_shortcode_fast()
        
        # Calculate expiry
        validity = request.validity or config.DEFAULT_VALIDITY_MINUTES
        expires_at = calculate_expiry(validity)
        
        # Create URL mapping with single commit
        url_mapping = URLMapping(
            shortcode=shortcode,
            original_url=request.url,
            expires_at=expires_at
        )
        
        self.db.add(url_mapping)
        self.db.commit()
        
        # Create response
        short_link = f"{config.BASE_URL}/{shortcode}"
        expiry = format_iso8601(expires_at)
        
        return CreateShortURLResponse(
            shortLink=short_link,
            expiry=expiry
        )
    
    def generate_unique_shortcode_fast(self) -> str:
        """Faster shortcode generation with reduced database queries"""
        
        # Try a few random shortcodes first
        for _ in range(3):
            shortcode = generate_shortcode()
            # Use EXISTS query which is faster
            exists = self.db.query(
                self.db.query(URLMapping).filter(URLMapping.shortcode == shortcode).exists()
            ).scalar()
            if not exists:
                return shortcode
        
        # If we still haven't found one, use timestamp-based approach
        timestamp_suffix = str(int(time.time() * 1000))[-6:]  # Last 6 digits of timestamp
        shortcode_base = generate_shortcode(4)  # Shorter base
        shortcode = f"{shortcode_base}{timestamp_suffix}"
        
        return shortcode
    
    # ... rest of the methods remain the same ...
    
    def get_original_url(self, shortcode: str, request_info: dict) -> str:
        """Get original URL and log the click"""
        
        url_mapping = self.db.query(URLMapping).filter(
            URLMapping.shortcode == shortcode
        ).first()
        
        if not url_mapping:
            raise HTTPException(status_code=404, detail="Shortcode not found")
        
        if is_expired(url_mapping.expires_at):
            raise HTTPException(status_code=410, detail="Short link has expired")
        
        # Update click count immediately (don't wait for click log)
        url_mapping.click_count += 1
        
        # Log the click asynchronously (don't block the redirect)
        try:
            self.log_click(shortcode, request_info)
        except:
            # Don't fail the redirect if logging fails
            pass
        
        self.db.commit()
        
        return url_mapping.original_url
    
    def log_click(self, shortcode: str, request_info: dict):
        """Optimized click logging"""
        
        click_log = ClickLog(
            shortcode=shortcode,
            referrer=request_info.get('referrer'),
            user_agent=request_info.get('user_agent'),
            ip_address=request_info.get('ip_address'),
            location=extract_location_from_ip(request_info.get('ip_address'))
        )
        
        self.db.add(click_log)
        # Use try-except to prevent logging failures from breaking the app
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Click logging failed: {e}")

# =============================================================================
# OPTIMIZED MODELS.PY (Faster validation)
# =============================================================================

from pydantic import BaseModel, validator
from datetime import datetime, timezone
from typing import Optional, List
import re

class CreateShortURLRequest(BaseModel):
    url: str
    validity: Optional[int] = None
    shortcode: Optional[str] = None
    
    @validator('url')
    def validate_url(cls, v):
        # Simple regex validation (faster than validators library)
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(v):
            raise ValueError('Invalid URL format')
        return v
    
    @validator('validity')
    def validate_validity(cls, v):
        if v is not None and (v <= 0 or v > 10080):  # max 1 week
            raise ValueError('Validity must be between 1 and 10080 minutes')
        return v
    
    @validator('shortcode')
    def validate_shortcode(cls, v):
        if v is not None:
            if len(v) < 1 or len(v) > 50:
                raise ValueError('Shortcode must be between 1 and 50 characters')
            # Simple alphanumeric check (faster)
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Shortcode must be alphanumeric with optional hyphens and underscores')
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

# =============================================================================
# DEBUGGING SCRIPT
# =============================================================================

import requests
import time

def debug_post_performance():
    """Debug script to measure POST request performance"""
    
    url = "http://localhost:8000/shorturls"
    payload = {"url": "https://www.google.com"}
    
    print("Testing POST request performance...")
    
    # Test multiple requests
    times = []
    for i in range(5):
        start = time.time()
        try:
            response = requests.post(url, json=payload, timeout=10)
            end = time.time()
            duration = end - start
            times.append(duration)
            print(f"Request {i+1}: {duration:.3f}s - Status: {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"Request {i+1}: TIMEOUT (>10s)")
        except Exception as e:
            print(f"Request {i+1}: ERROR - {e}")
        
        time.sleep(0.5)  # Small delay between requests
    
    if times:
        avg_time = sum(times) / len(times)
        print(f"\nAverage response time: {avg_time:.3f}s")
        if avg_time > 2.0:
            print("⚠️  Response time is too slow!")
        else:
            print("✅ Response time is acceptable")

if __name__ == "__main__":
    debug_post_performance()