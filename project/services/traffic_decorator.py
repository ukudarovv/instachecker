"""
Traffic monitoring decorator for proxy requests.
Automatically tracks data usage for decorated functions.
"""

import asyncio
import time
import uuid
from functools import wraps
from typing import Callable, Any, Optional
import aiohttp
from .traffic_monitor import get_traffic_monitor


def monitor_traffic(func: Callable) -> Callable:
    """
    Decorator to monitor traffic for proxy requests.
    
    Usage:
        @monitor_traffic
        async def make_request(url, proxy_url, **kwargs):
            # Your request code here
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract proxy information from arguments
        proxy_url = kwargs.get('proxy_url') or (args[1] if len(args) > 1 else None)
        url = kwargs.get('url') or (args[0] if len(args) > 0 else 'unknown')
        
        # Extract proxy IP from proxy URL
        proxy_ip = 'unknown'
        if proxy_url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(proxy_url)
                proxy_ip = parsed.hostname or 'unknown'
            except:
                proxy_ip = 'unknown'
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Get traffic monitor
        monitor = get_traffic_monitor()
        
        # Start monitoring
        monitor.start_request(request_id, proxy_ip, url)
        
        # Track request size (approximate)
        request_size = 0
        if 'headers' in kwargs:
            # Estimate request size
            headers = kwargs['headers']
            request_size += len(str(headers).encode('utf-8'))
        
        # Add URL size
        request_size += len(url.encode('utf-8'))
        
        start_time = time.time()
        success = False
        status_code = 0
        response_size = 0
        
        try:
            # Execute the original function
            result = await func(*args, **kwargs)
            
            # Try to extract response size from result
            if isinstance(result, dict):
                response_size = result.get('response_size', 0)
                status_code = result.get('status_code', 200)
                success = result.get('success', True)
            elif hasattr(result, 'content_length'):
                response_size = result.content_length or 0
            elif hasattr(result, 'status'):
                status_code = result.status
                success = 200 <= status_code < 400
            
            return result
            
        except Exception as e:
            success = False
            status_code = 0
            print(f"[TRAFFIC-MONITOR] ❌ Ошибка в запросе: {e}")
            raise
            
        finally:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # End monitoring
            monitor.end_request(
                request_id=request_id,
                success=success,
                status_code=status_code,
                request_size=request_size,
                response_size=response_size,
                duration_ms=duration_ms
            )
    
    return wrapper


class TrafficAwareSession:
    """
    aiohttp ClientSession wrapper that tracks traffic.
    """
    
    def __init__(self, **kwargs):
        self.session = aiohttp.ClientSession(**kwargs)
        self.monitor = get_traffic_monitor()
    
    async def __aenter__(self):
        return await self.session.__aenter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.session.__aexit__(exc_type, exc_val, exc_tb)
    
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """GET request with traffic monitoring."""
        proxy_url = kwargs.get('proxy')
        proxy_ip = 'unknown'
        
        if proxy_url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(proxy_url)
                proxy_ip = parsed.hostname or 'unknown'
            except:
                proxy_ip = 'unknown'
        
        request_id = str(uuid.uuid4())
        self.monitor.start_request(request_id, proxy_ip, url)
        
        # Estimate request size
        request_size = len(url.encode('utf-8'))
        if 'headers' in kwargs:
            request_size += len(str(kwargs['headers']).encode('utf-8'))
        
        start_time = time.time()
        success = False
        status_code = 0
        response_size = 0
        
        try:
            response = await self.session.get(url, **kwargs)
            status_code = response.status
            success = 200 <= status_code < 400
            
            # Get response size
            if hasattr(response, 'content_length') and response.content_length:
                response_size = response.content_length
            else:
                # Read content to get size
                content = await response.read()
                response_size = len(content)
                # Create a new response with the content
                response._body = content
            
            return response
            
        except Exception as e:
            success = False
            status_code = 0
            print(f"[TRAFFIC-MONITOR] ❌ Ошибка в GET запросе: {e}")
            raise
            
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.monitor.end_request(
                request_id=request_id,
                success=success,
                status_code=status_code,
                request_size=request_size,
                response_size=response_size,
                duration_ms=duration_ms
            )
    
    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """POST request with traffic monitoring."""
        proxy_url = kwargs.get('proxy')
        proxy_ip = 'unknown'
        
        if proxy_url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(proxy_url)
                proxy_ip = parsed.hostname or 'unknown'
            except:
                proxy_ip = 'unknown'
        
        request_id = str(uuid.uuid4())
        self.monitor.start_request(request_id, proxy_ip, url)
        
        # Estimate request size
        request_size = len(url.encode('utf-8'))
        if 'headers' in kwargs:
            request_size += len(str(kwargs['headers']).encode('utf-8'))
        if 'data' in kwargs:
            data = kwargs['data']
            if isinstance(data, str):
                request_size += len(data.encode('utf-8'))
            elif isinstance(data, bytes):
                request_size += len(data)
            elif isinstance(data, dict):
                request_size += len(str(data).encode('utf-8'))
        
        start_time = time.time()
        success = False
        status_code = 0
        response_size = 0
        
        try:
            response = await self.session.post(url, **kwargs)
            status_code = response.status
            success = 200 <= status_code < 400
            
            # Get response size
            if hasattr(response, 'content_length') and response.content_length:
                response_size = response.content_length
            else:
                content = await response.read()
                response_size = len(content)
                response._body = content
            
            return response
            
        except Exception as e:
            success = False
            status_code = 0
            print(f"[TRAFFIC-MONITOR] ❌ Ошибка в POST запросе: {e}")
            raise
            
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.monitor.end_request(
                request_id=request_id,
                success=success,
                status_code=status_code,
                request_size=request_size,
                response_size=response_size,
                duration_ms=duration_ms
            )
