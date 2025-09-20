import random
import string
from datetime import datetime, timezone, timedelta
from config import config

def generate_shortcode(length: int = None) -> str:
    """Generate a random shortcode"""
    if length is None:
        length = config.SHORTCODE_LENGTH
    
    return ''.join(random.choices(config.SHORTCODE_CHARS, k=length))

def calculate_expiry(validity_minutes: int = None) -> datetime:
    """Calculate expiry datetime"""
    if validity_minutes is None:
        validity_minutes = config.DEFAULT_VALIDITY_MINUTES
    
    return datetime.now(timezone.utc) + timedelta(minutes=validity_minutes)

def is_expired(expires_at: datetime) -> bool:
    """Check if a URL has expired"""
    return datetime.now(timezone.utc) > expires_at

def format_iso8601(dt: datetime) -> str:
    """Format datetime to ISO 8601 string"""
    return dt.isoformat().replace('+00:00', 'Z')

def extract_location_from_ip(ip_address: str) -> str:
    """Extract coarse-grained geographical location from IP"""
    # In a real implementation, you would use a GeoIP service
    # For this example, we'll return a placeholder
    if ip_address and ip_address != "127.0.0.1":
        return f"Location-{ip_address.split('.')[0]}"
    return "Local"