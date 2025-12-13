"""Response caching layer for Predictive Propositions Service."""
import hashlib
import json
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from functools import wraps
import logging

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

logger = logging.getLogger(__name__)


class CacheConfig:
    """Cache configuration."""
    def __init__(
        self,
        ttl_seconds: int = 300,
        max_size: int = 10000,
        use_redis: bool = True,
        redis_url: str = "redis://localhost:6379/0"
    ):
        """Initialize cache config.
        
        Args:
            ttl_seconds: Time to live in seconds
            max_size: Maximum cache size for in-memory cache
            use_redis: Whether to use Redis
            redis_url: Redis connection URL
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.use_redis = use_redis
        self.redis_url = redis_url


class CacheManager:
    """Unified cache manager with Redis and in-memory fallback."""

    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize cache manager.
        
        Args:
            config: CacheConfig instance
        """
        self.config = config or CacheConfig()
        self.in_memory_cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        self.redis_client = None
        
        if self.config.use_redis and HAS_REDIS:
            try:
                self.redis_client = redis.from_url(self.config.redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("Redis cache connected successfully")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using in-memory cache.")
                self.redis_client = None
        elif self.config.use_redis and not HAS_REDIS:
            logger.warning("Redis requested but not installed. Using in-memory cache.")

    def _generate_key(self, namespace: str, **kwargs) -> str:
        """Generate cache key from namespace and arguments.
        
        Args:
            namespace: Cache namespace
            **kwargs: Key-value pairs for hashing
        
        Returns:
            Cache key
        """
        key_str = f"{namespace}:{json.dumps(kwargs, sort_keys=True, default=str)}"
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"cache:{namespace}:{key_hash}"

    def get(self, namespace: str, **kwargs) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            namespace: Cache namespace
            **kwargs: Key-value pairs for lookup
        
        Returns:
            Cached value or None
        """
        key = self._generate_key(namespace, **kwargs)
        
        # Try Redis first
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    logger.debug(f"Cache hit from Redis: {namespace}")
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis read error: {e}")
        
        # Fall back to in-memory cache
        if key in self.in_memory_cache:
            timestamp = self.cache_timestamps.get(key)
            if timestamp and (datetime.utcnow() - timestamp).total_seconds() < self.config.ttl_seconds:
                logger.debug(f"Cache hit from memory: {namespace}")
                return self.in_memory_cache[key]
            else:
                # Expired
                del self.in_memory_cache[key]
                del self.cache_timestamps[key]
        
        logger.debug(f"Cache miss: {namespace}")
        return None

    def set(self, namespace: str, value: Any, **kwargs) -> None:
        """Set value in cache.
        
        Args:
            namespace: Cache namespace
            value: Value to cache
            **kwargs: Key-value pairs for storage
        """
        key = self._generate_key(namespace, **kwargs)
        
        # Store in Redis
        if self.redis_client:
            try:
                self.redis_client.setex(
                    key,
                    self.config.ttl_seconds,
                    json.dumps(value, default=str)
                )
                logger.debug(f"Cached in Redis: {namespace}")
            except Exception as e:
                logger.warning(f"Redis write error: {e}")
        
        # Always store in in-memory cache
        if len(self.in_memory_cache) >= self.config.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache_timestamps, key=self.cache_timestamps.get)
            del self.in_memory_cache[oldest_key]
            del self.cache_timestamps[oldest_key]
        
        self.in_memory_cache[key] = value
        self.cache_timestamps[key] = datetime.utcnow()
        logger.debug(f"Cached in memory: {namespace}")

    def delete(self, namespace: str, **kwargs) -> None:
        """Delete value from cache.
        
        Args:
            namespace: Cache namespace
            **kwargs: Key-value pairs for deletion
        """
        key = self._generate_key(namespace, **kwargs)
        
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
        
        if key in self.in_memory_cache:
            del self.in_memory_cache[key]
            del self.cache_timestamps[key]

    def clear(self) -> None:
        """Clear all cache."""
        self.in_memory_cache.clear()
        self.cache_timestamps.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache statistics
        """
        return {
            "in_memory_size": len(self.in_memory_cache),
            "in_memory_max": self.config.max_size,
            "ttl_seconds": self.config.ttl_seconds,
            "redis_connected": self.redis_client is not None
        }


def cached(cache_manager: CacheManager, namespace: str, ttl: Optional[int] = None) -> Callable:
    """Decorator to cache function results.
    
    Args:
        cache_manager: CacheManager instance
        namespace: Cache namespace
        ttl: Time to live (overrides config)
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = {
                "args": str(args),
                "kwargs": str(kwargs)
            }
            
            # Try cache
            cached_value = cache_manager.get(namespace, **cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache_manager.set(namespace, result, **cache_key)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = {
                "args": str(args),
                "kwargs": str(kwargs)
            }
            
            # Try cache
            cached_value = cache_manager.get(namespace, **cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache_manager.set(namespace, result, **cache_key)
            return result
        
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global cache manager instance
default_cache_manager = CacheManager(CacheConfig(ttl_seconds=300))
