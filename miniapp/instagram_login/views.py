"""Views for Instagram login Mini App."""

import json
import os
import sys
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

# Add parent directory to path to import bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from project.database import get_engine, get_session_factory
    from project.services.ig_sessions import save_session
    from project.utils.encryptor import OptionalFernet
    from project.config import get_settings
    from project.utils.access import get_or_create_user
except ImportError:
    print("Warning: Could not import bot modules")


def index(request):
    """Serve the Mini App main page."""
    return render(request, 'instagram_login/index.html')


@csrf_exempt
def save_cookies(request):
    """
    Save Instagram cookies received from Mini App.
    
    Expected POST data:
    {
        "telegram_user_id": 12345,
        "ig_username": "username",
        "cookies": [...]
    }
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        telegram_user_id = data.get('telegram_user_id')
        ig_username = data.get('ig_username', 'webapp_user')
        cookies = data.get('cookies', [])
        
        if not telegram_user_id:
            return JsonResponse({'success': False, 'error': 'telegram_user_id required'}, status=400)
        
        if not cookies or len(cookies) == 0:
            return JsonResponse({'success': False, 'error': 'No cookies provided'}, status=400)
        
        # Check for sessionid
        has_sessionid = any(c.get('name') == 'sessionid' for c in cookies)
        if not has_sessionid:
            return JsonResponse({
                'success': False, 
                'error': 'sessionid cookie missing - please log in to Instagram first'
            }, status=400)
        
        print(f"📱 Received cookies from Telegram user {telegram_user_id}")
        print(f"🍪 Cookies count: {len(cookies)}")
        print(f"📝 IG Username: @{ig_username}")
        
        # Initialize bot database and save session
        try:
            settings = get_settings()
            fernet = OptionalFernet(settings.encryption_key)
            engine = get_engine(settings.db_url)
            session_factory = get_session_factory(engine)
            
            with session_factory() as session:
                # Create or get user
                from project.models import User
                user = session.query(User).filter(User.id == telegram_user_id).first()
                
                if not user:
                    # Create new user
                    user = User(
                        id=telegram_user_id,
                        username=f"user_{telegram_user_id}",
                        is_active=True
                    )
                    session.add(user)
                    session.commit()
                    session.refresh(user)
                
                # Save Instagram session
                ig_session = save_session(
                    session=session,
                    user_id=user.id,
                    ig_username=ig_username,
                    cookies_json=cookies,
                    fernet=fernet,
                )
                
                print(f"✅ Instagram session saved (id={ig_session.id})")
                
                return JsonResponse({
                    'success': True,
                    'session_id': ig_session.id,
                    'ig_username': ig_username,
                    'cookies_count': len(cookies)
                })
                
        except Exception as e:
            print(f"❌ Error saving session to database: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Database error: {str(e)}'
            }, status=500)
        
    except json.JSONDecodeError as e:
        return JsonResponse({'success': False, 'error': f'Invalid JSON: {str(e)}'}, status=400)
    except Exception as e:
        print(f"❌ Error in save_cookies: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

