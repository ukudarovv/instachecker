"""
🎨 ГЕНЕРАЦИЯ ШАПКИ ПРОФИЛЯ INSTAGRAM (API V2)
Полностью синхронизировано с design_test.py
"""

import asyncio
import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageOps
from datetime import datetime
from io import BytesIO
from typing import Optional
import aiohttp

# ============================================================================
# 📐 ПАРАМЕТРЫ ДИЗАЙНА - ЗДЕСЬ МЕНЯЙТЕ РАСПОЛОЖЕНИЕ И РАЗМЕРЫ
# Полностью синхронизировано с design_test.py
# ============================================================================
DESIGN = {
    # === РАЗМЕР ХОЛСТА ===
    "canvas_width": 1000,        # Ширина изображения
    "canvas_height": 450,       # Высота изображения компактная
    "background": "#000000",    # Цвет фона (черный)
    
    # === ОТСТУПЫ ===
    "pad_left": 60,             # Отступ слева
    "pad_top": 145,              # Отступ сверху
    "pad_right": 16,            # Отступ справа
    
    # === АВАТАР ===
    "avatar_size": 180,          # Размер аватара ~90px
    "avatar_border": 0,         # Тонкая белая обводка
    "avatar_x": 100,             # X позиция аватара
    "avatar_y": 130,             # Y позиция аватара (вертикально центрирован)
    
    # === USERNAME (имя пользователя) ===
    "username_x_offset": 40,    # Отступ username от аватара
    "username_y_offset": 0,     # Вертикально центрирован с аватаром
    "username_font_size": 35,   # Размер шрифта username жирный 22-28px
    
    # === ГАЛОЧКА ВЕРИФИКАЦИИ ===
    "verified_size": 30,         # Размер галочки (18x18px как в Instagram)
    "verified_offset_x": 8,      # Отступ от username
    "verified_offset_y": 4,      # Смещение по Y
    "verified_inner_padding": 3, # Отступ внутренней галочки от края
    "verified_line_width": 2,    # Толщина линий галочки
    "verified_spacing_after": 12, # Отступ после галочки для следующих элементов
    
    # === ЗАМОК (для приватных) ===
    "lock_offset_x": 22,        # Отступ замка от галочки
    
    # === КНОПКА FOLLOW ===
    "button_width": 76,         # Ширина кнопки Follow 88-100px
    "button_height": 34,        # Высота кнопки 34px
    "button_radius": 8,         # Радиус скругления углов
    "button_offset_right": 15,  # Отступ кнопки от правого края
    "button_offset_y": 5,       # Вертикально центрирована с username
    "button_font_size": 18,     # Размер текста на кнопке
    
    # === ТРИ ТОЧКИ ===
    "dots_width": 34,           # Ширина кнопки с точками
    "dots_offset_x": 8,         # Отступ от кнопки Follow
    "dots_radius": 2,           # Радиус каждой точки
    "dots_spacing": 12,         # Расстояние между точками
    "dots_center_offset_x": 20, # Смещение центра точек
    
    # === СТАТИСТИКА (posts/followers/following) ===
    "stats_x": 320,               # X позиция статистики (0 = под username, или укажите точное значение)
    "stats_y": 0,               # Y позиция статистики (0 = относительно аватара, или укажите точное значение)
    "stats_y_offset": 60,       # Y позиция статистики относительно аватара (если stats_y = 0)
    "stats_spacing": 20,        # Равные отступы между элементами
    "stats_number_size": 20,    # Размер шрифта цифр ЖИРНЫЙ
    "stats_label_size": 20,     # Размер шрифта подписей
    "stats_line_gap": 5,        # Расстояние между цифрой и подписью
    
    # === ИМЯ И БИОГРАФИЯ ===
    "name_x": 320,                # X позиция имени (0 = под username, или точное значение)
    "name_y": 0,                # Y позиция имени (0 = относительно статистики, или точное значение)
    "name_y_offset": 40,        # Y отступ имени от статистики (если name_y = 0)
    "name_font_size": 20,       # Размер шрифта имени
    "bio_x": 320,                 # X позиция биографии (0 = под username, или точное значение)
    "bio_y": 0,                 # Y позиция биографии (0 = относительно имени, или точное значение)
    "bio_y_offset": 30,         # Y отступ биографии от имени (если bio_y = 0)
    "bio_line_gap": 18,         # Расстояние между строками биографии
    "bio_font_size": 20,        # Размер шрифта биографии
    "bio_max_lines": 2,         # Максимум 2 строки биографии
    
    # === ЦВЕТА ===
    "color_text_primary": "#ffffff",    # Основной текст (белый)
    "color_text_secondary": "#a8a8a8",  # Второстепенный текст (серый)
    "color_button": "#0095f6",          # Кнопка Follow (синий)
    "color_button_dark": "#262626",     # Серая кнопка (Requested/точки)
    "color_verified": "#0095f6",        # Цвет галочки (синий)
    
    # === ЖИРНОСТЬ ШРИФТОВ ===
    "username_bold": False,             # Username жирный (True/False)
    "name_bold": False,                 # Имя жирное (True/False)
    "stat_num_bold": False,             # Числа статистики жирные (True/False)
    "stat_label_bold": False,           # Подписи статистики жирные (True/False)
    "bio_bold": False,                  # Биография жирная (True/False)
    "button_bold": True,               # Кнопка жирная (True/False)
    
    # === ВНУТРЕННИЕ ОТСТУПЫ КНОПКИ ===
    "button_padding_top": 4,            # Отступ сверху внутри кнопки
    "button_padding_bottom": 18,         # Отступ снизу внутри кнопки
    "button_padding_left": 16,          # Отступ слева внутри кнопки
    "button_padding_right": 16,         # Отступ справа внутри кнопки
}


# ============================================================================
# 🔧 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def load_verified_badge_image(size: int) -> Optional[Image.Image]:
    """Загружает готовое изображение галочки верификации"""
    try:
        # Создаем простое изображение галочки программно
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Рисуем синий круг
        draw.ellipse([0, 0, size, size], fill="#0095f6")
        
        # Рисуем белую галочку
        check_size = size * 0.6
        check_x = (size - check_size) // 2
        check_y = (size - check_size) // 2
        
        # Галочка из линий
        line_width = max(2, size // 8)
        check_points = [
            (check_x + check_size * 0.2, check_y + check_size * 0.5),  # Начало
            (check_x + check_size * 0.45, check_y + check_size * 0.75), # Середина
            (check_x + check_size * 0.8, check_y + check_size * 0.25)   # Конец
        ]
        
        for i in range(len(check_points) - 1):
            draw.line([check_points[i], check_points[i + 1]], fill="#ffffff", width=line_width)
        
        return img
    except Exception as e:
        print(f"Ошибка создания галочки: {e}")
        return None

def format_number_with_spaces(n: int) -> str:
    """Форматирует число с пробелами: 3959 -> '3 959'"""
    try:
        return f"{int(n):,}".replace(",", " ")
    except Exception:
        return str(n)

def format_count_posts(count: int) -> str:
    """Посты — полное число с пробелами"""
    return format_number_with_spaces(count)

def format_count_followers(count: int) -> str:
    """Подписчики: до 9999 с пробелами, потом K/M/B"""
    try:
        n = int(count)
        if n <= 9_999:
            return format_number_with_spaces(n)
        if n >= 1_000_000_000:
            return f"{n // 1_000_000_000}B"
        if n >= 1_000_000:
            return f"{n // 1_000_000}M"
        if n >= 1_000:
            return f"{n // 1_000}K"
        return str(n)
    except Exception:
        return str(count)

def format_count_following(count: int) -> str:
    """Подписки: K/M/B"""
    try:
        n = int(count)
        if n <= 9_999:
            return format_number_with_spaces(n)
        if n >= 1_000_000_000:
            return f"{n // 1_000_000_000}B"
        if n >= 1_000_000:
            return f"{n // 1_000_000}M"
        if n >= 1_000:
            return f"{n // 1_000}K"
        return str(n)
    except Exception:
        return str(count)

def load_fonts():
    """Загрузка шрифтов с учетом настроек жирности из DESIGN"""
    fonts = {}
    tries = [
        ("arialbd.ttf", "arial.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    
    for bold_path, reg_path in tries:
        try:
            # Выбираем жирный или обычный шрифт в зависимости от настроек
            username_font = bold_path if DESIGN["username_bold"] else reg_path
            name_font = bold_path if DESIGN["name_bold"] else reg_path
            stat_num_font = bold_path if DESIGN["stat_num_bold"] else reg_path
            stat_label_font = bold_path if DESIGN["stat_label_bold"] else reg_path
            bio_font = bold_path if DESIGN["bio_bold"] else reg_path
            button_font = bold_path if DESIGN["button_bold"] else reg_path
            
            fonts["username"] = ImageFont.truetype(username_font, DESIGN["username_font_size"])
            fonts["name"] = ImageFont.truetype(name_font, DESIGN["name_font_size"])
            fonts["stat_num"] = ImageFont.truetype(stat_num_font, DESIGN["stats_number_size"])
            fonts["stat_label"] = ImageFont.truetype(stat_label_font, DESIGN["stats_label_size"])
            fonts["bio"] = ImageFont.truetype(bio_font, DESIGN["bio_font_size"])
            fonts["button"] = ImageFont.truetype(button_font, DESIGN["button_font_size"])
            return fonts
        except:
            continue
    
    # Fallback
    default = ImageFont.load_default()
    return {
        "username": default, "name": default, "stat_num": default,
        "stat_label": default, "bio": default, "button": default
    }


async def download_profile_image(url: str) -> Image.Image:
    """Загружает фото профиля"""
    if not url or "YOUR_IMAGE" in url:
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    return Image.open(BytesIO(content)).convert("RGBA")
    except:
        pass
    return None


def make_circular_avatar(image: Image.Image, size: int, border_px: int = 4) -> Image.Image:
    """Создает круглый аватар с обводкой"""
    avatar = ImageOps.fit(image.convert("RGBA"), (size, size), centering=(0.5, 0.5))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    avatar.putalpha(mask)
    
    # Обводка
    total = size + border_px * 2
    bg = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    ImageDraw.Draw(bg).ellipse((0, 0, total, total), fill="#ffffff")
    bg.paste(avatar, (border_px, border_px), avatar)
    return bg


# ============================================================================
# 🎨 ГЛАВНАЯ ФУНКЦИЯ ГЕНЕРАЦИИ
# ============================================================================

async def generate_instagram_profile_image_improved(
    username: str,
    full_name: str = "",
    posts: int = 0,
    followers: int = 0,
    following: int = 0,
    is_private: bool = False,
    is_verified: bool = False,
    biography: str = "",
    profile_pic_url: str = "",
    output_path: Optional[str] = None
) -> dict:
    """
    Генерирует шапку профиля Instagram с использованием всех параметров из DESIGN
    """
    try:
        print(f"🎨 Генерирую профиль @{username}...")
        
        # Создаем папку для сохранения
        out_dir = "generated_profiles"
        os.makedirs(out_dir, exist_ok=True)
        if not output_path:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(out_dir, f"{username}_profile_{ts}.png")
        
        # Создаем холст
        W, H = DESIGN["canvas_width"], DESIGN["canvas_height"]
        canvas = Image.new("RGB", (W, H), color=DESIGN["background"])
        draw = ImageDraw.Draw(canvas)
        
        # Загружаем шрифты
        fonts = load_fonts()
        
        # Позиции
        avatar_x = DESIGN["avatar_x"]
        avatar_y = DESIGN["avatar_y"]
        avatar_size = DESIGN["avatar_size"]
        
        # === 1. АВАТАР ===
        print("🖼️  Рисуем аватар...")
        profile_img = await download_profile_image(profile_pic_url)
        if profile_img:
            avatar = make_circular_avatar(profile_img, avatar_size, DESIGN["avatar_border"])
            canvas.paste(avatar, (avatar_x, avatar_y), avatar)
        else:
            # Placeholder
            tmp = Image.new("RGBA", (avatar_size, avatar_size), "#262626")
            mask = Image.new("L", (avatar_size, avatar_size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
            tmp.putalpha(mask)
            avatar = make_circular_avatar(tmp, avatar_size, DESIGN["avatar_border"])
            canvas.paste(avatar, (avatar_x, avatar_y), avatar)
        
        # === 2. USERNAME ===
        print("✍️  Добавляем username...")
        text_x = avatar_x + avatar_size + DESIGN["username_x_offset"]
        username_y = avatar_y + DESIGN["username_y_offset"]
        
        draw.text((text_x, username_y), username, 
                  fill=DESIGN["color_text_primary"], font=fonts["username"])
        
        # Измеряем ширину username
        bbox = draw.textbbox((text_x, username_y), username, font=fonts["username"])
        username_width = bbox[2] - bbox[0]
        
        # === 3. ГАЛОЧКА ВЕРИФИКАЦИИ (сразу после username) ===
        if is_verified:
            print("✓  Добавляем галочку верификации...")
            
            # Позиция галочки сразу после username
            check_x = text_x + username_width + DESIGN["verified_offset_x"]
            check_y = username_y + DESIGN["verified_offset_y"]
            
            # Размер галочки из настроек
            check_size = DESIGN["verified_size"]
            
            # Загружаем и вставляем готовое изображение галочки
            verified_image = load_verified_badge_image(check_size)
            if verified_image:
                canvas.paste(verified_image, (check_x, check_y), verified_image)
            
            # Обновляем позицию для следующих элементов
            badge_x = check_x + check_size + DESIGN["verified_spacing_after"]
        else:
            badge_x = text_x + username_width + DESIGN["verified_offset_x"]
        
        # === 4. ЗАМОК — отключен по требованию ===
        # (Не рисуем замок для приватных аккаунтов)
        
        # === 5. КНОПКА FOLLOW (после галочки) ===
        print("🔘 Рисуем кнопку Follow...")
        btn_w = DESIGN["button_width"]
        btn_h = DESIGN["button_height"]
        btn_x = badge_x + DESIGN["button_offset_right"]
        btn_y = username_y + DESIGN["button_offset_y"]
        
        # Всегда синяя кнопка Follow (игнорируем is_private)
        btn_color = DESIGN["color_button"]
        draw.rounded_rectangle([btn_x, btn_y, btn_x + btn_w, btn_y + btn_h], 
                              radius=DESIGN["button_radius"], fill=btn_color)
        
        # Всегда текст "Follow"
        button_text = "Follow"
        bt_bbox = draw.textbbox((0, 0), button_text, font=fonts["button"])
        bt_w = bt_bbox[2] - bt_bbox[0]
        bt_h = bt_bbox[3] - bt_bbox[1]
        
        # Позиционирование текста с учетом внутренних отступов
        text_btn_x = btn_x + DESIGN["button_padding_left"]
        text_btn_y = btn_y + DESIGN["button_padding_top"]
        
        # Если текст не помещается, центрируем
        available_w = btn_w - DESIGN["button_padding_left"] - DESIGN["button_padding_right"]
        available_h = btn_h - DESIGN["button_padding_top"] - DESIGN["button_padding_bottom"]
        
        if bt_w <= available_w and bt_h <= available_h:
            draw.text((text_btn_x, text_btn_y), button_text, fill="#ffffff", font=fonts["button"])
        else:
            draw.text((btn_x + (btn_w - bt_w) / 2, btn_y + (btn_h - bt_h) / 2 - 2), 
                      button_text, fill="#ffffff", font=fonts["button"])
        
        # === 6. ТРИ ТОЧКИ (без фона) ===
        print("⋯  Рисуем три точки...")
        dd_x = btn_x + btn_w + DESIGN["dots_offset_x"]
        
        # Рисуем три отдельные точки без фона
        dot_radius = DESIGN["dots_radius"]
        dot_spacing = DESIGN["dots_spacing"]
        center_x = dd_x + DESIGN["dots_center_offset_x"]
        center_y = btn_y + btn_h // 2
        
        # Три точки по горизонтали
        for i in range(3):
            dot_x = center_x - dot_spacing + (i * dot_spacing)
            draw.ellipse([dot_x - dot_radius, center_y - dot_radius, 
                         dot_x + dot_radius, center_y + dot_radius], 
                        fill=DESIGN["color_text_primary"])
        
        # === 7. СТАТИСТИКА (в одну строку, с настраиваемыми позициями) ===
        print("📊 Добавляем статистику...")
        
        # Определяем позицию X
        if DESIGN["stats_x"] == 0:
            stats_x = text_x  # Под username
        else:
            stats_x = DESIGN["stats_x"]  # Точная позиция
        
        # Определяем позицию Y
        if DESIGN["stats_y"] == 0:
            stats_y = avatar_y + DESIGN["stats_y_offset"]  # Относительно аватара
        else:
            stats_y = DESIGN["stats_y"]  # Точная позиция
        
        # Формируем элементы статистики
        stats_items = [
            (posts, "posts", format_count_posts),
            (followers, "followers", format_count_followers),
            (following, "following", format_count_following)
        ]
        
        for i, (count, label, formatter) in enumerate(stats_items):
            count_str = formatter(count)
            draw.text((stats_x, stats_y), count_str, 
                      fill=DESIGN["color_text_primary"], font=fonts["stat_num"])
            
            # Измеряем ширину числа
            count_bbox = draw.textbbox((0, 0), count_str, font=fonts["stat_num"])
            count_w = count_bbox[2] - count_bbox[0]
            
            # Подпись сразу после числа
            label_x = stats_x + count_w + 4
            draw.text((label_x, stats_y + 1), label, 
                      fill=DESIGN["color_text_secondary"], font=fonts["stat_label"])
            
            # Измеряем ширину подписи для следующего элемента
            label_bbox = draw.textbbox((0, 0), label, font=fonts["stat_label"])
            label_w = label_bbox[2] - label_bbox[0]
            
            # Равные отступы между элементами
            stats_x = label_x + label_w + DESIGN["stats_spacing"]
        
        # === 8. ИМЯ (с настраиваемыми позициями) ===
        if full_name:
            print("👤 Добавляем полное имя...")
            
            # Определяем позицию X для имени
            if DESIGN["name_x"] == 0:
                name_x = text_x  # Под username
            else:
                name_x = DESIGN["name_x"]  # Точная позиция
            
            # Определяем позицию Y для имени
            if DESIGN["name_y"] == 0:
                name_y = stats_y + DESIGN["name_y_offset"]  # Относительно статистики
            else:
                name_y = DESIGN["name_y"]  # Точная позиция
            
            draw.text((name_x, name_y), full_name, 
                      fill=DESIGN["color_text_primary"], font=fonts["name"])
        
        # === 9. БИОГРАФИЯ (с настраиваемыми позициями) ===
        if biography:
            print("📝 Добавляем биографию...")
            
            # Определяем позицию X для биографии
            if DESIGN["bio_x"] == 0:
                bio_x = text_x  # Под username
            else:
                bio_x = DESIGN["bio_x"]  # Точная позиция
            
            # Определяем позицию Y для биографии
            if DESIGN["bio_y"] == 0:
                bio_y = name_y + DESIGN["bio_y_offset"] if full_name else stats_y + DESIGN["name_y_offset"]
            else:
                bio_y = DESIGN["bio_y"]  # Точная позиция
            
            lines = biography.split("\n")[:DESIGN["bio_max_lines"]]
            for line in lines:
                draw.text((bio_x, bio_y), line, 
                          fill=DESIGN["color_text_secondary"], font=fonts["bio"])
                bio_y += DESIGN["bio_line_gap"]
        
        # === СОХРАНЕНИЕ ===
        canvas.save(output_path, format="PNG", optimize=True)
        
        print(f"✅ Готово!")
        print(f"📁 Файл сохранен: {output_path}")
        print(f"📏 Размер: {W}x{H} px\n")
        
        return {"success": True, "image_path": output_path}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


# ============================================================================
# 🚀 ТЕСТОВЫЙ ЗАПУСК
# ============================================================================

async def main_demo():
    """Простой тест для демонстрации"""
    result = await generate_instagram_profile_image_improved(
        username="ukudarov",
        full_name="Umar",
        posts=0,
        followers=153,
        following=109,
        is_private=False,
        is_verified=True,
        biography="Эксперт в области дизайна",
        profile_pic_url="",
    )
    print(result)

if __name__ == "__main__":
    try:
        asyncio.run(main_demo())
    except KeyboardInterrupt:
        print("Прервано.")
