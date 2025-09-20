from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from database import get_db, create_tables
from models import CreateShortURLRequest, CreateShortURLResponse, URLStatistics, ErrorResponse
from services import URLShortenerService
from middleware import LoggingMiddleware
from datetime import datetime, timezone
import uvicorn
from config import config

# Create FastAPI app
app = FastAPI(
    title="URL Shortener Microservice",
    description="A robust HTTP URL Shortener Microservice with analytics",
    version="1.0.0"
)

# Add custom logging middleware
app.add_middleware(LoggingMiddleware)

# Create database tables
create_tables()

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=f"HTTP {exc.status_code}",
            message=exc.detail,
            timestamp=datetime.now(timezone.utc).isoformat()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            message="An unexpected error occurred",
            timestamp=datetime.now(timezone.utc).isoformat()
        ).dict()
    )

@app.get("/")
async def root():
    return {"message": "URL Shortener Microservice", "status": "running"}

@app.post("/shorturls", response_model=CreateShortURLResponse, status_code=201)
async def create_short_url(
    request: CreateShortURLRequest,
    db: Session = Depends(get_db)
):
    """Create a new shortened URL"""
    service = URLShortenerService(db)
    return service.create_short_url(request)

@app.get("/shorturls/{shortcode}")
async def get_url_statistics(
    shortcode: str,
    db: Session = Depends(get_db)
) -> URLStatistics:
    """Retrieve statistics for a shortened URL"""
    service = URLShortenerService(db)
    return service.get_statistics(shortcode)

@app.get("/{shortcode}")
async def redirect_to_original_url(
    shortcode: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Redirect to the original URL"""
    
    # Extract request information for analytics
    request_info = {
        'referrer': request.headers.get('referer'),
        'user_agent': request.headers.get('user-agent'),
        'ip_address': request.client.host if request.client else None
    }
    
    service = URLShortenerService(db)
    original_url = service.get_original_url(shortcode, request_info)
    
    return RedirectResponse(url=original_url, status_code=302)

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=config.HOST,
        port=config.PORT,
        reload=True
    )
