"""Instagram profile parsing for logged-in sessions."""

from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
import re

RE_FOLLOWERS = re.compile(r'"edge_followed_by"\s*:\s*\{"count"\s*:\s*(\d+)\}', re.I)
RE_FOLLOWING = re.compile(r'"edge_follow"\s*:\s*\{"count"\s*:\s*(\d+)\}', re.I)
RE_POSTS = re.compile(r'"edge_owner_to_timeline_media"\s*:\s*\{"count"\s*:\s*(\d+)\}', re.I)


def parse_profile_html(username: str, html: str) -> Dict[str, Any]:
    """Parse Instagram profile HTML for logged-in session."""
    result = {
        "username": username,
        "exists": None,
        "full_name": None,
        "avatar_url": None,
        "followers": None,
        "following": None,
        "posts": None,
        "error": None
    }
    
    if not html:
        result["error"] = "empty_html"
        return result

    if "page not found" in html.lower():
        result["exists"] = False
        return result

    soup = BeautifulSoup(html, "html.parser")

    # meta og:url часто указывает профиль
    og = soup.find("meta", {"property": "og:url"})
    if og and og.get("content"):
        if username.lower().strip("@") in og["content"].lower():
            result["exists"] = True

    # имя + аватар из ld+json
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            import json
            obj = json.loads(tag.text)
            cand = obj if isinstance(obj, dict) else (obj[0] if isinstance(obj, list) and obj else None)
            if isinstance(cand, dict):
                if not result["full_name"] and cand.get("name"):
                    result["full_name"] = cand["name"]
                if not result["avatar_url"] and cand.get("image"):
                    result["avatar_url"] = cand["image"]
        except Exception:
            pass

    # counts из inline JSON
    m = RE_FOLLOWERS.search(html)
    if m: 
        result["followers"] = int(m.group(1))
    m = RE_FOLLOWING.search(html)
    if m: 
        result["following"] = int(m.group(1))
    m = RE_POSTS.search(html)
    if m: 
        result["posts"] = int(m.group(1))

    # финальный exists
    if result["exists"] is None:
        if result["avatar_url"] or result["followers"] is not None or result["following"] is not None or result["posts"] is not None:
            result["exists"] = True
        else:
            result["exists"] = None
    
    return result
