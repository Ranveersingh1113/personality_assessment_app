import time
import threading
from datetime import datetime, timedelta
from collections import deque
import logging

class RateLimitExceeded(Exception):
    """Exception raised when rate limits are exceeded and cannot be resolved by waiting."""
    pass

class RateLimiter:
    """Rate limiter for API calls to prevent quota exceeded errors"""
    
    def __init__(self, max_requests_per_minute=15, max_requests_per_day=1000, delay_between_calls=2.0):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_requests_per_day = max_requests_per_day
        self.delay_between_calls = delay_between_calls
        
        # Track requests
        self.minute_requests = deque()
        self.daily_requests = deque()
        self.last_request_time = 0
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _cleanup_old_requests(self):
        """Remove expired requests from tracking"""
        now = datetime.now()
        
        # Clean minute requests (older than 1 minute)
        while self.minute_requests and (now - self.minute_requests[0]).total_seconds() > 60:
            self.minute_requests.popleft()
        
        # Clean daily requests (older than 24 hours)
        while self.daily_requests and (now - self.daily_requests[0]).total_seconds() > 86400:
            self.daily_requests.popleft()
    
    def wait_if_needed(self, max_retries: int = 10):
        """Wait if rate limits would be exceeded. Uses iteration instead of recursion."""
        with self.lock:
            for attempt in range(max_retries):
                self._cleanup_old_requests()
                now = datetime.now()
                
                # Check daily limit first - cannot wait 24 hours, must raise
                if len(self.daily_requests) >= self.max_requests_per_day:
                    oldest_request = self.daily_requests[0]
                    wait_time = 86400 - (now - oldest_request).total_seconds()
                    if wait_time > 0:
                        raise RateLimitExceeded(
                            f"Daily rate limit of {self.max_requests_per_day} requests exceeded. "
                            f"Resets in {wait_time/3600:.1f} hours. Please try again later."
                        )
                
                # Check minute limit - wait if needed
                if len(self.minute_requests) >= self.max_requests_per_minute:
                    oldest_request = self.minute_requests[0]
                    wait_time = 60 - (now - oldest_request).total_seconds()
                    if wait_time > 0:
                        self.logger.warning(f"Rate limit reached. Waiting {wait_time:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time + 0.1)  # Small buffer
                        continue  # Re-check after waiting
                
                # Ensure minimum delay between calls
                time_since_last = time.time() - self.last_request_time
                if time_since_last < self.delay_between_calls:
                    sleep_time = self.delay_between_calls - time_since_last
                    time.sleep(sleep_time)
                
                # Record this request
                self.minute_requests.append(datetime.now())
                self.daily_requests.append(datetime.now())
                self.last_request_time = time.time()
                return  # Success
            
            # Exhausted retries
            raise RateLimitExceeded(
                f"Rate limit could not be resolved after {max_retries} attempts. "
                "Please wait a moment and try again."
            )
    
    def get_status(self):
        """Get current rate limiting status"""
        with self.lock:
            self._cleanup_old_requests()
            return {
                'minute_requests': len(self.minute_requests),
                'daily_requests': len(self.daily_requests),
                'max_per_minute': self.max_requests_per_minute,
                'max_per_day': self.max_requests_per_day,
                'time_since_last': time.time() - self.last_request_time
            }

# Global rate limiter instance with thread-safe initialization
_rate_limiter = None
_rate_limiter_lock = threading.Lock()

def get_rate_limiter():
    """Get the global rate limiter instance (thread-safe singleton)"""
    global _rate_limiter
    if _rate_limiter is None:
        with _rate_limiter_lock:
            # Double-check pattern for thread safety
            if _rate_limiter is None:
                try:
                    from config import MAX_REQUESTS_PER_MINUTE, MAX_REQUESTS_PER_DAY, RATE_LIMIT_DELAY
                    _rate_limiter = RateLimiter(
                        max_requests_per_minute=MAX_REQUESTS_PER_MINUTE,
                        max_requests_per_day=MAX_REQUESTS_PER_DAY,
                        delay_between_calls=RATE_LIMIT_DELAY
                    )
                except ImportError:
                    # Fallback to conservative defaults
                    _rate_limiter = RateLimiter(
                        max_requests_per_minute=10,
                        max_requests_per_day=500,
                        delay_between_calls=3.0
                    )
    return _rate_limiter

def rate_limited_call(func):
    """Decorator to add rate limiting to API calls"""
    def wrapper(*args, **kwargs):
        rate_limiter = get_rate_limiter()
        rate_limiter.wait_if_needed()
        return func(*args, **kwargs)
    return wrapper

