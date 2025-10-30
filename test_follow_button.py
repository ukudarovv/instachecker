"""
Тест кнопки Follow для приватного аккаунта
"""
import asyncio
from test_api_with_profile_gen import generate_instagram_profile_image_improved

async def test_private_account():
    """Тест с приватным аккаунтом - должна быть кнопка Follow"""
    
    print("="*70)
    print("🧪 ТЕСТ: Приватный аккаунт с кнопкой Follow")
    print("="*70)
    
    result = await generate_instagram_profile_image_improved(
        username="fullstack_developers",
        full_name="ТЫЖПРОГРАММИСТ",
        posts=488,
        followers=2095,
        following=3,
        is_private=True,  # ⚠️ ПРИВАТНЫЙ АККАУНТ
        is_verified=False,
        biography="Мемы про программистов",
        profile_pic_url="",
    )
    
    if result.get("success"):
        print(f"\n✅ Изображение создано: {result['image_path']}")
        print("✅ Кнопка должна быть синей с текстом 'Follow'")
    else:
        print(f"\n❌ Ошибка: {result.get('error')}")
    
    print("="*70)

async def test_public_account():
    """Тест с публичным аккаунтом - тоже должна быть кнопка Follow"""
    
    print("\n" + "="*70)
    print("🧪 ТЕСТ: Публичный аккаунт с кнопкой Follow")
    print("="*70)
    
    result = await generate_instagram_profile_image_improved(
        username="instagram",
        full_name="Instagram",
        posts=7500,
        followers=667000000,
        following=25,
        is_private=False,  # ✅ ПУБЛИЧНЫЙ АККАУНТ
        is_verified=True,
        biography="Bringing you closer",
        profile_pic_url="",
    )
    
    if result.get("success"):
        print(f"\n✅ Изображение создано: {result['image_path']}")
        print("✅ Кнопка должна быть синей с текстом 'Follow'")
    else:
        print(f"\n❌ Ошибка: {result.get('error')}")
    
    print("="*70)

async def main():
    await test_private_account()
    await test_public_account()
    
    print("\n" + "🎉"*35)
    print("✅ Оба теста завершены!")
    print("   Теперь всегда отображается синяя кнопка 'Follow'")
    print("   независимо от статуса приватности аккаунта")
    print("🎉"*35 + "\n")

if __name__ == "__main__":
    asyncio.run(main())

