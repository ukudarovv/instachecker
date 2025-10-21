"""Proxy parser for batch import."""

import re
from typing import List, Dict, Tuple
from urllib.parse import urlparse


def parse_proxy_url(proxy_url: str) -> Dict[str, any]:
    """
    Parse proxy URL into components.
    
    Supports formats:
    - scheme://host:port
    - scheme://user:pass@host:port
    - host:port:user:pass
    - host:port
    
    Args:
        proxy_url: Proxy URL string
        
    Returns:
        dict with proxy components or None if invalid
    """
    proxy_url = proxy_url.strip()
    
    if not proxy_url:
        return None
    
    # Try URL format first (http://user:pass@host:port)
    if '://' in proxy_url:
        try:
            parsed = urlparse(proxy_url)
            
            scheme = parsed.scheme.lower()
            if scheme not in ['http', 'https', 'socks5']:
                return None
            
            # Extract host and port
            host = parsed.hostname
            port = parsed.port
            
            if not host or not port:
                return None
            
            # Extract credentials
            username = parsed.username
            password = parsed.password
            
            return {
                'scheme': scheme,
                'host': f"{host}:{port}",
                'username': username,
                'password': password
            }
        except Exception:
            return None
    
    # Try colon-separated format (host:port:user:pass)
    parts = proxy_url.split(':')
    
    if len(parts) == 2:
        # host:port
        host, port = parts
        try:
            int(port)  # Validate port is number
            return {
                'scheme': 'http',
                'host': f"{host}:{port}",
                'username': None,
                'password': None
            }
        except ValueError:
            return None
    
    elif len(parts) == 4:
        # host:port:user:pass
        host, port, username, password = parts
        try:
            int(port)  # Validate port is number
            return {
                'scheme': 'http',
                'host': f"{host}:{port}",
                'username': username,
                'password': password
            }
        except ValueError:
            return None
    
    return None


def parse_proxy_list(text: str) -> Tuple[List[Dict], List[str]]:
    """
    Parse list of proxies from text.
    
    Args:
        text: Text with proxies (one per line)
        
    Returns:
        Tuple of (valid_proxies, errors)
        - valid_proxies: List of parsed proxy dicts
        - errors: List of error messages for invalid lines
    """
    valid_proxies = []
    errors = []
    
    lines = text.strip().split('\n')
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        
        # Try to parse
        proxy_data = parse_proxy_url(line)
        
        if proxy_data:
            valid_proxies.append(proxy_data)
        else:
            errors.append(f"Строка {line_num}: Неверный формат - {line[:50]}")
    
    return valid_proxies, errors


def validate_proxy_data(proxy_data: Dict) -> Tuple[bool, str]:
    """
    Validate proxy data.
    
    Args:
        proxy_data: Proxy dict
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    if not proxy_data.get('scheme'):
        return False, "Отсутствует схема (http/https/socks5)"
    
    if not proxy_data.get('host'):
        return False, "Отсутствует хост:порт"
    
    # Validate scheme
    if proxy_data['scheme'] not in ['http', 'https', 'socks5']:
        return False, f"Неподдерживаемая схема: {proxy_data['scheme']}"
    
    # Validate host:port format
    if ':' not in proxy_data['host']:
        return False, "Неверный формат host:port"
    
    try:
        host, port = proxy_data['host'].rsplit(':', 1)
        port = int(port)
        if port < 1 or port > 65535:
            return False, f"Неверный порт: {port}"
    except (ValueError, AttributeError):
        return False, "Неверный формат host:port"
    
    # Validate credentials (if present)
    if proxy_data.get('username') and not proxy_data.get('password'):
        return False, "Указан username но нет password"
    
    if proxy_data.get('password') and not proxy_data.get('username'):
        return False, "Указан password но нет username"
    
    return True, "OK"


def format_proxy_examples() -> str:
    """
    Get examples of supported proxy formats.
    
    Returns:
        Formatted examples string
    """
    return (
        "📝 <b>Поддерживаемые форматы:</b>\n\n"
        "1. <code>http://proxy.com:8080</code>\n"
        "2. <code>http://user:pass@proxy.com:8080</code>\n"
        "3. <code>socks5://user:pass@proxy.com:1080</code>\n"
        "4. <code>proxy.com:8080</code> (будет http)\n"
        "5. <code>proxy.com:8080:user:pass</code>\n\n"
        "💡 <b>Примеры:</b>\n"
        "<code>http://74276e667af9:d9754cc35e1e@proxy.resi.gg:12321</code>\n"
        "<code>proxy.resi.gg:12321:74276e667af9:d9754cc35e1e</code>\n"
        "<code>192.168.1.1:8080</code>\n\n"
        "⚠️ <b>Правила:</b>\n"
        "• Один прокси на строку\n"
        "• Строки начинающиеся с # игнорируются\n"
        "• Пустые строки игнорируются\n"
        "• Поддерживаются http, https, socks5"
    )


def deduplicate_proxies(
    existing_proxies: List[Dict],
    new_proxies: List[Dict]
) -> Tuple[List[Dict], int]:
    """
    Remove duplicates from new proxies.
    
    Args:
        existing_proxies: Existing proxies in DB
        new_proxies: New proxies to add
        
    Returns:
        Tuple of (unique_proxies, duplicates_count)
    """
    # Create set of existing proxy identifiers
    existing = set()
    for p in existing_proxies:
        identifier = f"{p['scheme']}://{p['host']}"
        existing.add(identifier)
    
    # Filter out duplicates
    unique = []
    duplicates = 0
    
    for p in new_proxies:
        identifier = f"{p['scheme']}://{p['host']}"
        if identifier not in existing:
            unique.append(p)
            existing.add(identifier)  # Prevent duplicates within new list
        else:
            duplicates += 1
    
    return unique, duplicates

