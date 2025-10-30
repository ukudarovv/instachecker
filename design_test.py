"""
🎨 ТЕСТОВЫЙ ФАЙЛ ДЛЯ НАСТРОЙКИ ДИЗАЙНА ПРОФИЛЯ INSTAGRAM
Быстро меняйте параметры и смотрите результат!
"""

import asyncio
import math
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO
import aiohttp
from datetime import datetime
import os
from typing import Optional
import argparse

# ============================================================================
# 🎯 ИСТОЧНИК ДАННЫХ
# ============================================================================
# data_source: "test" — использовать TEST_DATA; "api" — запросить реальный профиль через proxy
DATA_SOURCE = "test"  # "api" | "test"

# Параметры для API-режима
API_USERNAME = "instagram"  # кого запрашивать при DATA_SOURCE="api"
PROXY_URL = ""  # пример: "http://user:pass@ip:port" или "http://ip:port"

# Тестовые данные, когда DATA_SOURCE="test"
TEST_DATA = {
    "username": "ukudarov",
    "full_name": "Umar",
    "posts": 0,
    "followers": 153,
    "following": 109,
    "is_verified": True,        # Верифицирован?
    "is_private": False,        # Приватный аккаунт?
    "biography": "Эксперт в области дизайна и разработки сайтов",
    # Вставьте URL фото профиля или оставьте пустым:
    "profile_pic_url": "https://scontent-mrs2-1.cdninstagram.com/v/t51.2885-19/464760996_1254146839119862_3605321457742435801_n.png?stp=dst-jpg_e0_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xNTAuYzIifQ&_nc_ht=scontent-mrs2-1.cdninstagram.com&_nc_cat=1&_nc_oc=Q6cZ2QG7K4DSRkrpLAguLZAQKs28dy9P9CQHl4OmFm-SIacLYE2Z_aaodmsqdw7WahY-R955lUkPlOZPlpqP7J2Lbnoe&_nc_ohc=yiYqVz4MkooQ7kNvwF1Mz7D&_nc_gid=0cRTbEKurKyrTyahkYli2A&edm=ALlQn9MBAAAA&ccb=7-5&ig_cache_key=YW5vbnltb3VzX3Byb2ZpbGVfcGlj.3-ccb7-5&oh=00_AferQg2_du6xaXxC3JUueUPA2zkR9zXyPN5AuBxoe8jIpw&oe=690702A8&_nc_sid=e7f676"
}

# ============================================================================
# 🌐 Получение профиля через Instagram web_profile_info c proxy
# ============================================================================
async def fetch_profile_via_proxy(username: str, proxy: Optional[str] = None, timeout_sec: int = 20) -> dict:
    """Возвращает словарь с полями: username, full_name, posts, followers, following,
    is_verified, is_private, biography, profile_pic_url. Пустые значения при ошибке."""
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "X-IG-App-ID": "936619743392459",
    }
    try:
        timeout = aiohttp.ClientTimeout(total=timeout_sec)
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.get(url, proxy=proxy) as resp:
                if resp.status != 200:
                    return {}
                data = await resp.json()
                user = data.get("data", {}).get("user", {})
                if not user:
                    return {}
                return {
                    "username": user.get("username") or username,
                    "full_name": user.get("full_name") or "",
                    "posts": (user.get("edge_owner_to_timeline_media", {}) or {}).get("count", 0),
                    "followers": (user.get("edge_followed_by", {}) or {}).get("count", 0),
                    "following": (user.get("edge_follow", {}) or {}).get("count", 0),
                    "is_verified": bool(user.get("is_verified")),
                    "is_private": bool(user.get("is_private")),
                    "biography": user.get("biography") or "",
                    "profile_pic_url": user.get("profile_pic_url_hd") or user.get("profile_pic_url") or "",
                }
    except Exception as e:
        print(f"⚠️ Ошибка запроса профиля через proxy: {e}")
        return {}

# ============================================================================
# 📐 ПАРАМЕТРЫ ДИЗАЙНА - ЗДЕСЬ МЕНЯЙТЕ РАСПОЛОЖЕНИЕ И РАЗМЕРЫ
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

def draw_instagram_verified_badge(draw, x: int, y: int, size: int, color: str):
    """Рисует настоящую галочку Instagram с зубчатыми краями"""
    # Создаем зубчатый контур как в Instagram
    # Координаты для зубчатого круга (упрощенная версия)
    center_x = x + size // 2
    center_y = y + size // 2
    radius = size // 2
    
    # Создаем зубчатый контур
    points = []
    num_teeth = 12  # Количество зубцов
    
    for i in range(num_teeth * 2):
        angle = (i * 180) / (num_teeth * 2)  # 0 to 180 degrees
        if i % 2 == 0:
            # Внешний зуб
            r = radius
        else:
            # Внутренний зуб
            r = radius * 0.7
        
        px = center_x + r * math.cos(math.radians(angle))
        py = center_y + r * math.sin(math.radians(angle))
        points.append((px, py))
    
    # Рисуем зубчатый круг
    if len(points) > 2:
        draw.polygon(points, fill=color)
    
    # Рисуем белую галочку внутри
    check_size = size * 0.4
    check_x = center_x - check_size // 2
    check_y = center_y - check_size // 2
    
    # Галочка из линий
    line_width = max(2, size // 10)
    check_points = [
        (check_x + check_size * 0.2, check_y + check_size * 0.5),  # Начало
        (check_x + check_size * 0.45, check_y + check_size * 0.75), # Середина
        (check_x + check_size * 0.8, check_y + check_size * 0.25)   # Конец
    ]
    
    for i in range(len(check_points) - 1):
        draw.line([check_points[i], check_points[i + 1]], fill="#ffffff", width=line_width)

def format_count_words(value: int) -> str:
    """667,223,696 -> '667M'; 25,430 -> '25K'; <1000 그대로."""
    try:
        n = int(value)
    except Exception:
        return str(value)
    if n >= 1_000_000_000:
        return f"{n // 1_000_000_000}B"
    if n >= 1_000_000:
        return f"{n // 1_000_000}M"
    if n >= 1_000:
        return f"{n // 1_000}K"
    return str(n)

def format_int_spaced(value: int) -> str:
    """Возвращает число с пробелом как разделителем тысяч: 3959 -> '3 959'."""
    try:
        n = int(value)
    except Exception:
        return str(value)
    return f"{n:,}".replace(",", " ")

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


def format_count(count: int) -> str:
    """Форматирует числа: 38.5k, 1.2M"""
    if count >= 1_000_000:
        val = count / 1_000_000
        s = f"{val:.1f}M"
    elif count >= 1000:
        val = count / 1000
        s = f"{val:.1f}k"
        if s.endswith(".0k"):
            s = s.replace(".0k", "k")
    else:
        s = str(count)
    return s


# ============================================================================
# 🎨 ГЛАВНАЯ ФУНКЦИЯ ГЕНЕРАЦИИ
# ============================================================================

async def generate_test_profile():
    """Генерирует профиль. Источник данных задаётся DATA_SOURCE."""
    # Подготовим данные
    data = TEST_DATA
    if DATA_SOURCE == "api":
        print("🌐 Режим API: загружаю профиль через proxy...")
        fetched = await fetch_profile_via_proxy(API_USERNAME, PROXY_URL or None)
        if fetched:
            data = {
                "username": fetched.get("username") or TEST_DATA["username"],
                "full_name": fetched.get("full_name", ""),
                "posts": fetched.get("posts", 0),
                "followers": fetched.get("followers", 0),
                "following": fetched.get("following", 0),
                "is_verified": fetched.get("is_verified", False),
                "is_private": fetched.get("is_private", False),
                "biography": fetched.get("biography", ""),
                "profile_pic_url": fetched.get("profile_pic_url", ""),
            }
        else:
            print("⚠️ Не удалось получить профиль через API, использую TEST_DATA")
            data = TEST_DATA
    
    print("\n" + "="*70)
    print("🎨 ГЕНЕРАЦИЯ ТЕСТОВОГО ПРОФИЛЯ")
    print("="*70)
    print(f"\n📊 Данные:")
    print(f"   Username: @{data['username']}")
    print(f"   Подписчиков: {data['followers']:,}")
    print(f"   Верифицирован: {'Да' if data['is_verified'] else 'Нет'}")
    print(f"\n📐 Размер холста: {DESIGN['canvas_width']}x{DESIGN['canvas_height']} px\n")
    
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
    profile_img = await download_profile_image(data["profile_pic_url"])
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
    
    # Используем username_y_offset из DESIGN
    bbox_temp = draw.textbbox((0, 0), data["username"], font=fonts["username"])
    username_h = bbox_temp[3] - bbox_temp[1]
    username_y = avatar_y + DESIGN["username_y_offset"]
    
    draw.text((text_x, username_y), data["username"], 
              fill=DESIGN["color_text_primary"], font=fonts["username"])
    
    # Измеряем ширину username
    bbox = draw.textbbox((text_x, username_y), data["username"], font=fonts["username"])
    username_width = bbox[2] - bbox[0]
    
    # === 3. ГАЛОЧКА ВЕРИФИКАЦИИ (сразу после username) ===
    if data["is_verified"]:
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
        else:
            # Fallback - рисуем простую галочку
            draw_instagram_verified_badge(draw, check_x, check_y, check_size, DESIGN["color_verified"])
        
        # Обновляем позицию для следующих элементов
        badge_x = check_x + check_size + DESIGN["verified_spacing_after"]
    else:
        badge_x = text_x + username_width + DESIGN["verified_offset_x"]
    
    # === 4. ЗАМОК — отключен по требованию ===
    if False:
        pass
    
    # === 5. КНОПКА FOLLOW (после галочки/замка) ===
    print("🔘 Рисуем кнопку Follow...")
    btn_w = DESIGN["button_width"]
    btn_h = DESIGN["button_height"]
    # Позиция кнопки после галочки/замка
    btn_x = badge_x + DESIGN["button_offset_right"]  # отступ от галочки/замка
    btn_y = username_y + DESIGN["button_offset_y"]  # вертикальный отступ от username
    
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
    text_x = btn_x + DESIGN["button_padding_left"]
    text_y = btn_y + DESIGN["button_padding_top"]
    
    # Если текст не помещается, центрируем
    available_w = btn_w - DESIGN["button_padding_left"] - DESIGN["button_padding_right"]
    available_h = btn_h - DESIGN["button_padding_top"] - DESIGN["button_padding_bottom"]
    
    if bt_w <= available_w and bt_h <= available_h:
        # Текст помещается, используем отступы
        draw.text((text_x, text_y), button_text, fill="#ffffff", font=fonts["button"])
    else:
        # Текст не помещается, центрируем
        draw.text((btn_x + (btn_w - bt_w) / 2, btn_y + (btn_h - bt_h) / 2 - 2), 
                  button_text, fill="#ffffff", font=fonts["button"])
    
    # === 6. ТРИ ТОЧКИ (без фона) ===
    print("⋯  Рисуем три точки...")
    dd_x = btn_x + btn_w + DESIGN["dots_offset_x"]
    
    # Рисуем три отдельные точки без фона
    dot_radius = 2  # Меньше размер
    dot_spacing = 12  # Расстояние 15px между точками
    center_x = dd_x + 20  # Центр области для точек
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
        (data['posts'], "posts"),
        (data['followers'], "followers"),
        (data['following'], "following")
    ]
    for i, (count, label) in enumerate(stats_items):
        # Форматируем по правилам:
        # - posts: оставляем короткий формат (k/M)
        # - followers: если <= 9999 — показываем как есть; иначе слова (million/thousand)
        # - following: используем слова (как для крупного числа)
        if label == "posts":
            count_str = format_int_spaced(count)
        elif label == "followers":
            count_str = format_int_spaced(count) if count <= 9_999 else format_count_words(count)
        else:
            # following: если маленькое число — с пробелами; иначе K/M/B
            count_str = format_int_spaced(count) if count <= 9_999 else format_count_words(count)
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
    if data["full_name"]:
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
        
        draw.text((name_x, name_y), data["full_name"], 
                  fill=DESIGN["color_text_primary"], font=fonts["name"])
    
    # === 9. БИОГРАФИЯ (с настраиваемыми позициями) ===
    if data["biography"]:
        print("📝 Добавляем биографию...")
        
        # Определяем позицию X для биографии
        if DESIGN["bio_x"] == 0:
            bio_x = text_x  # Под username
        else:
            bio_x = DESIGN["bio_x"]  # Точная позиция
        
        # Определяем позицию Y для биографии
        if DESIGN["bio_y"] == 0:
            bio_y = name_y + DESIGN["bio_y_offset"]  # Относительно имени
        else:
            bio_y = DESIGN["bio_y"]  # Точная позиция
        
        lines = data["biography"].split("\n")[:DESIGN["bio_max_lines"]]
        for line in lines:
            draw.text((bio_x, bio_y), line, 
                      fill=DESIGN["color_text_secondary"], font=fonts["bio"])
            bio_y += DESIGN["bio_line_gap"]
    
    # === СОХРАНЕНИЕ ===
    os.makedirs("design_tests", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"design_tests/test_{ts}.png"
    canvas.save(output_path, format="PNG", optimize=True)
    
    print(f"\n✅ Готово!")
    print(f"📁 Файл сохранен: {output_path}")
    print(f"📏 Размер: {W}x{H} px")
    print("="*70 + "\n")
    
    return output_path


# ============================================================================
# 🚀 ЗАПУСК
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instagram profile header generator")
    parser.add_argument("--username", dest="username", help="Username to fetch via API")
    parser.add_argument("--proxy", dest="proxy", help="Proxy string like http://user:pass@host:port")
    parser.add_argument("--api", dest="api", action="store_true", help="Force API data source")
    args = parser.parse_args()

    # Configure from CLI
    if args.username:
        API_USERNAME = args.username
        DATA_SOURCE = "api"
    if args.proxy:
        PROXY_URL = args.proxy
    if args.api:
        DATA_SOURCE = "api"

    print("\n" + "🎨"*35)
    print(" "*15 + "ДИЗАЙН ТЕСТЕР")
    print("🎨"*35)
    if DATA_SOURCE == "api":
        masked = PROXY_URL
        if masked and "@" in masked:
            creds, host = masked.split("@", 1)
            if ":" in creds:
                u, p = creds.split(":", 1)
                masked = f"http://{u}:******@{host}"
        print(f"\n🌐 Источник: API | username={API_USERNAME} | proxy={masked or 'none'}")
    else:
        print("\n🔧 Источник: TEST_DATA")

    asyncio.run(generate_test_profile())

