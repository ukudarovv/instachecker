#!/usr/bin/env python3
"""
Тест автоматического исправления username.
"""

def test_username_fix():
    """Тест функции исправления username."""
    
    # Тестовые данные
    test_usernames = [
        "lavenderhayz_",  # Заканчивается на _
        "milibubs_",      # Заканчивается на _
        "test.user",      # Заканчивается на .
        "_baduser",       # Начинается с _
        ".baduser",       # Начинается с .
        "good_user",      # Нормальный username
        "normal.user",    # Нормальный username
        "___bad___",      # Множественные _
        "...bad...",      # Множественные .
        "valid_user",     # Валидный username
    ]
    
    print("🧪 Тест автоматического исправления username")
    print("=" * 50)
    
    auto_fixed_usernames = []
    
    for username_input in test_usernames:
        # Clean username
        username = username_input.replace('@', '').strip().lower()
        if not username:
            continue
        
        # Auto-fix username: remove trailing underscores and dots
        original_username = username
        while username.endswith('_') or username.endswith('.'):
            username = username.rstrip('_.')
        
        # Also remove leading underscores and dots
        while username.startswith('_') or username.startswith('.'):
            username = username.lstrip('_.')
        
        # If username was modified, add info message
        if username != original_username:
            print(f"🔧 Auto-fixed: {original_username} → {username}")
            auto_fixed_usernames.append(f"{original_username} → {username}")
        else:
            print(f"✅ Valid: {username}")
    
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТА:")
    print("=" * 50)
    
    print(f"✅ Всего username: {len(test_usernames)}")
    print(f"🔧 Автоматически исправлено: {len(auto_fixed_usernames)}")
    print(f"✅ Валидных: {len(test_usernames) - len(auto_fixed_usernames)}")
    
    if auto_fixed_usernames:
        print(f"\n🔧 <b>Автоматически исправлены username:</b>")
        for fix in auto_fixed_usernames:
            print(f"  • {fix}")
    
    return auto_fixed_usernames

if __name__ == "__main__":
    test_username_fix()
