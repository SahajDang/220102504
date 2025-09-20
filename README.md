# URL Shortener Microservice

A robust HTTP URL Shortener Microservice built with FastAPI that provides core URL shortening functionality along with basic analytical capabilities.

## Features

- Create shortened URLs with custom or auto-generated shortcodes
- Configurable link expiry (defaults to 30 minutes)
- Click tracking and analytics
- Comprehensive logging middleware
- RESTful API endpoints
- SQLite database for persistence

## API Endpoints

### 1. Create Short URL
- **POST** `/shorturls`
- Creates a new shortened URL
- Request body:
  ```json
  {
    "url": "https://example.com/very/long/url",
    "validity": 30,
    "shortcode": "custom123"
  }
  ```
- Response (201):
  ```json
  {
    "shortLink": "http://hostname:port/abc123",
    "expiry": "2025-01-01T00:30:00Z"
  }
  ```

### 2. Redirect to Original URL
- **GET** `/{shortcode}`
- Redirects to the original URL and logs the click
- Returns 302 redirect or appropriate error

### 3. Get URL Statistics
- **GET** `/shorturls/{shortcode}`
- Retrieves usage statistics for a shortened URL
- Returns click count, original URL, creation date, expiry, and detailed click data

## Installation and Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python app.py
   ```

3. The service will start on `http://localhost:8000`

## Configuration

Environment variables:
- `DATABASE_URL`: Database connection string (default: sqlite:///./url_shortener.db)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `BASE_URL`: Base URL for shortened links (default: http://hostname:port)

## Requirements Met

✅ Mandatory logging integration with custom middleware

✅ Single microservice architecture

✅ No authentication required

✅ Globally unique short links

✅ Default 30-minute validity

✅ Custom shortcode support

✅ Proper redirection functionality

✅ Comprehensive error handling

✅ Analytics and click tracking
