"""
Быстрый тест генератора профилей Instagram.
Можно запустить без БД для тестирования самой генерации изображения.
"""

import asyncio
from test_api_with_profile_gen import generate_instagram_profile_image


async def test_generate_profile():
    """Тест генерации профиля с тестовыми данными"""
    
    print("\n" + "="*60)
    print("🎨 БЫСТРЫЙ ТЕСТ: Генерация профиля Instagram")
    print("="*60 + "\n")
    
    test_profiles = [
        {
            "username": "cristiano",
            "full_name": "Cristiano Ronaldo",
            "posts": 3670,
            "followers": 619000000,
            "following": 567,
            "is_private": False,
            "is_verified": True,
            "biography": "SIUUUbscribe on my Youtube Channel 🔔"
        },
        {
            "username": "test_private_user",
            "full_name": "Private Account",
            "posts": 142,
            "followers": 523,
            "following": 891,
            "is_private": True,
            "is_verified": False,
            "biography": "This is a private test account"
        },
        {
            "username": "verified_user",
            "full_name": "Verified Test User",
            "posts": 89,
            "followers": 12500,
            "following": 234,
            "is_private": False,
            "is_verified": True,
            "biography": "Official verified account for testing purposes. Follow me for more updates!"
        }
    ]
    
    print("📋 Будет создано 3 тестовых профиля:\n")
    
    for idx, profile in enumerate(test_profiles, 1):
        print(f"[{idx}/3] Генерируем @{profile['username']}...")
        
        result = await generate_instagram_profile_image(
            username=profile['username'],
            full_name=profile['full_name'],
            posts=profile['posts'],
            followers=profile['followers'],
            following=profile['following'],
            is_private=profile['is_private'],
            is_verified=profile['is_verified'],
            biography=profile['biography']
        )
        
        if result.get('success'):
            print(f"   ✅ Успешно: {result['image_path']}\n")
        else:
            print(f"   ❌ Ошибка: {result.get('error')}\n")
    
    print("="*60)
    print("✅ ТЕСТ ЗАВЕРШЕН!")
    print("📁 Проверьте папку 'generated_profiles/'")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(test_generate_profile())
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

