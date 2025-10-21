"""
Instagram Header Detector - автоматическое определение высоты header профиля.
Решение DeepSeek с OpenCV и детекцией элементов.
"""

import cv2
import numpy as np
from PIL import Image
import os
from typing import Optional, Tuple, Dict, List


class InstagramHeaderDetector:
    """Класс для автоматического определения высоты header Instagram профиля"""
    
    def __init__(self):
        self.header_templates = self._load_header_templates()
    
    def _load_header_templates(self) -> Dict:
        """Загрузка шаблонов для определения header"""
        return {
            'avatar_region': (50, 150, 150, 250),  # Примерные координаты аватара
            'username_region': (200, 150, 500, 200),  # Область имени пользователя
            'stats_region': (200, 220, 500, 280),  # Область статистики
        }
    
    def detect_header_height(self, screenshot_path: str) -> int:
        """
        Автоматическое определение высоты header
        Возвращает высоту в пикселях для обрезки
        """
        try:
            print(f"[HEADER-DETECTOR] 🔍 Анализ скриншота: {screenshot_path}")
            
            # Метод 1: Поиск по цветам и контрасту
            height = self._detect_by_contrast(screenshot_path)
            if height:
                print(f"[HEADER-DETECTOR] ✅ Найдено по контрасту: {height}px")
                return height
            
            # Метод 2: Поиск элементов header
            height = self._detect_by_elements(screenshot_path)
            if height:
                print(f"[HEADER-DETECTOR] ✅ Найдено по элементам: {height}px")
                return height
            
            # Метод 3: Поиск UI элементов Instagram
            height = self._detect_by_ui_elements(screenshot_path)
            if height:
                print(f"[HEADER-DETECTOR] ✅ Найдено по UI: {height}px")
                return height
            
            # Метод 4: Фиксированная высота по умолчанию
            default_height = self._get_default_height(screenshot_path)
            print(f"[HEADER-DETECTOR] ⚠️ Используем высоту по умолчанию: {default_height}px")
            return default_height
            
        except Exception as e:
            print(f"[HEADER-DETECTOR] ❌ Ошибка определения высоты header: {e}")
            return 600  # Высота по умолчанию
    
    def _detect_by_contrast(self, screenshot_path: str) -> Optional[int]:
        """Определение высоты header по контрасту и цветам"""
        try:
            img = cv2.imread(screenshot_path)
            if img is None:
                return None
            
            height, width = img.shape[:2]
            print(f"[HEADER-DETECTOR] 📐 Размер изображения: {width}x{height}")
            
            # Конвертируем в grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Применяем детекцию краев
            edges = cv2.Canny(gray, 50, 150)
            
            # Ищем горизонтальные линии (границы header)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, 
                                  minLineLength=width*0.3, maxLineGap=20)
            
            if lines is not None:
                horizontal_lines = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    # Фильтруем горизонтальные линии
                    if abs(y2 - y1) < 10 and abs(x2 - x1) > width * 0.3:
                        horizontal_lines.append(y1)
                
                if horizontal_lines:
                    # Берем самую нижнюю горизонтальную линию как границу header
                    header_bottom = max(horizontal_lines)
                    result = min(header_bottom + 100, height)  # Добавляем отступ
                    
                    # Ограничиваем максимальную высоту header
                    max_header_height = int(height * 0.3)  # Максимум 30% экрана
                    result = min(result, max_header_height)
                    
                    print(f"[HEADER-DETECTOR] 📏 Найдена граница header: {result}px")
                    return result
            
            return None
            
        except Exception as e:
            print(f"[HEADER-DETECTOR] ⚠️ Ошибка в contrast detection: {e}")
            return None
    
    def _detect_by_elements(self, screenshot_path: str) -> Optional[int]:
        """Определение высоты по элементам header"""
        try:
            img = Image.open(screenshot_path)
            width, height = img.size
            
            # Преобразуем в numpy array для OpenCV
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # Ищем характерные элементы header
            elements_found = []
            
            # 1. Поиск круглого аватара
            circles = self._detect_circles(img_cv)
            if circles is not None:
                avatar_y = int(circles[0, 0, 1])
                elements_found.append(avatar_y + 200)  # Аватар + отступ
                print(f"[HEADER-DETECTOR] 🔵 Найден аватар на Y: {avatar_y}")
            
            # 2. Поиск кнопок (обычно яркие элементы)
            buttons_y = self._detect_buttons(img_cv)
            if buttons_y:
                elements_found.append(buttons_y + 100)
                print(f"[HEADER-DETECTOR] 🔘 Найдены кнопки на Y: {buttons_y}")
            
            # 3. Поиск текста био
            bio_y = self._detect_bio_text(img_cv)
            if bio_y:
                elements_found.append(bio_y + 50)
                print(f"[HEADER-DETECTOR] 📝 Найден bio на Y: {bio_y}")
            
            if elements_found:
                result = min(max(elements_found), height - 100)
                print(f"[HEADER-DETECTOR] 📏 Найдено по элементам: {result}px")
                return result
            
            return None
            
        except Exception as e:
            print(f"[HEADER-DETECTOR] ⚠️ Ошибка в element detection: {e}")
            return None
    
    def _detect_circles(self, img) -> Optional[float]:
        """Детекция круглого аватара"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 5)
            
            circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 50,
                                     param1=50, param2=30, minRadius=40, maxRadius=80)
            
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                # Возвращаем Y координату первого круга (аватар)
                return float(circles[0][1])
            return None
        except:
            return None
    
    def _detect_buttons(self, img) -> Optional[float]:
        """Детекция кнопок (яркие прямоугольные области)"""
        try:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            # Маска для синих кнопок (Подписаться)
            blue_lower = np.array([100, 150, 50])
            blue_upper = np.array([140, 255, 255])
            blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
            
            # Маска для белых/серых кнопок
            white_lower = np.array([0, 0, 200])
            white_upper = np.array([180, 50, 255])
            white_mask = cv2.inRange(hsv, white_lower, white_upper)
            
            combined_mask = cv2.bitwise_or(blue_mask, white_mask)
            
            # Находим контуры
            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            button_positions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # Фильтруем по размеру (кнопки обычно широкие и невысокие)
                if w > 100 and h > 30 and h < 80:
                    button_positions.append(y)
            
            if button_positions:
                return float(min(button_positions))  # Самая верхняя кнопка
            
            return None
        except:
            return None
    
    def _detect_bio_text(self, img) -> Optional[float]:
        """Детекция текста био"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Применяем threshold для выделения текста
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
            
            # Морфологические операции для объединения текста
            kernel = np.ones((3, 20), np.uint8)
            dilated = cv2.dilate(thresh, kernel, iterations=2)
            
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            text_positions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # Фильтруем по размеру (длинные текстовые блоки)
                if w > 200 and h > 15 and h < 50:
                    text_positions.append(y)
            
            if text_positions:
                return float(max(text_positions))  # Самый нижний текстовый блок
            
            return None
        except:
            return None
    
    def _detect_by_ui_elements(self, screenshot_path: str) -> Optional[int]:
        """Определение по UI элементам Instagram"""
        try:
            img = cv2.imread(screenshot_path)
            if img is None:
                return None
            
            height, width = img.shape[:2]
            
            # Поиск характерных элементов Instagram UI
            elements = {
                'bottom_nav': self._find_bottom_navigation(img),
                'stories': self._find_stories_line(img),
                'posts_grid': self._find_posts_grid(img)
            }
            
            print(f"[HEADER-DETECTOR] 🔍 UI элементы: {elements}")
            
            # Находим самый верхний элемент контента
            content_starts = []
            for element_name, element_y in elements.items():
                if element_y:
                    content_starts.append(element_y)
                    print(f"[HEADER-DETECTOR] 📍 {element_name}: Y={element_y}")
            
            if content_starts:
                header_height = min(content_starts) - 50  # Отступ от контента
                result = max(400, min(header_height, height - 200))
                print(f"[HEADER-DETECTOR] 📏 Найдено по UI: {result}px")
                return result
            
            return None
            
        except Exception as e:
            print(f"[HEADER-DETECTOR] ⚠️ Ошибка UI detection: {e}")
            return None
    
    def _find_bottom_navigation(self, img) -> Optional[int]:
        """Поиск нижней навигации Instagram"""
        try:
            height, width = img.shape[:2]
            # Нижняя часть изображения (последние 150px)
            bottom_region = img[height-150:height, :]
            
            # Ищем темную панель навигации
            gray_bottom = cv2.cvtColor(bottom_region, cv2.COLOR_BGR2GRAY)
            avg_brightness = np.mean(gray_bottom)
            
            if avg_brightness < 100:  # Темная панель
                return height - 150
            
            return None
        except:
            return None
    
    def _find_stories_line(self, img) -> Optional[int]:
        """Поиск линии Stories"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Ищем горизонтальные линии в верхней части
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=30,
                                  minLineLength=100, maxLineGap=10)
            
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    if abs(y2 - y1) < 5 and 200 < y1 < 600:  # Горизонтальная линия в области stories
                        return y1
            
            return None
        except:
            return None
    
    def _find_posts_grid(self, img) -> Optional[int]:
        """Поиск начала grid с постами"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Ищем регулярный pattern grid (3 колонки)
            # Простая реализация - ищем область с высокой текстурой
            kernel = np.ones((5,5), np.uint8)
            gradient = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)
            
            # Сканируем сверху вниз для нахождения начала grid
            height, width = gradient.shape
            step = 10
            
            for y in range(400, height - 100, step):
                row_region = gradient[y:y+step, :]
                row_variance = np.var(row_region)
                
                # Высокая вариация указывает на текстуру grid
                if row_variance > 1000:
                    return y
            
            return None
        except:
            return None
    
    def _get_default_height(self, screenshot_path: str) -> int:
        """Получение высоты по умолчанию на основе размера скриншота"""
        try:
            with Image.open(screenshot_path) as img:
                width, height = img.size
                
                # Для мобильных скриншотов определяем высоту header
                if height > 1500:  # Длинный скриншот
                    return min(700, int(height * 0.25))  # Максимум 25%
                elif height > 1000:  # Средний скриншот
                    return min(600, int(height * 0.3))   # Максимум 30%
                else:  # Короткий скриншот
                    return min(500, int(height * 0.35))  # Максимум 35%
        except:
            return 600
    
    def crop_to_header(self, screenshot_path: str, output_path: str = None) -> str:
        """
        Основная функция обрезки скриншота до header
        """
        if output_path is None:
            name, ext = os.path.splitext(screenshot_path)
            output_path = f"{name}_header{ext}"
        
        try:
            print(f"[HEADER-DETECTOR] 🔍 Анализ скриншота: {screenshot_path}")
            
            # Определяем высоту header
            header_height = self.detect_header_height(screenshot_path)
            
            # Открываем и обрезаем изображение
            with Image.open(screenshot_path) as img:
                width, height = img.size
                
                # Обрезаем до определенной высоты
                crop_box = (0, 0, width, min(header_height, height))
                cropped_img = img.crop(crop_box)
                
                # Сохраняем результат
                cropped_img.save(output_path, quality=95)
                
                print(f"[HEADER-DETECTOR] ✅ Скриншот обрезан: {header_height}px -> {output_path}")
                return output_path
                
        except Exception as e:
            print(f"[HEADER-DETECTOR] ❌ Ошибка обрезки скриншота: {e}")
            # В случае ошибки возвращаем оригинальный путь
            return screenshot_path
    
    def batch_crop_screenshots(self, screenshot_paths: list, output_dir: str = None) -> list:
        """Пакетная обрезка скриншотов"""
        results = []
        
        for screenshot_path in screenshot_paths:
            if not os.path.exists(screenshot_path):
                print(f"[HEADER-DETECTOR] ⚠️ Файл не найден: {screenshot_path}")
                continue
            
            if output_dir:
                filename = os.path.basename(screenshot_path)
                name, ext = os.path.splitext(filename)
                output_path = os.path.join(output_dir, f"{name}_header{ext}")
            else:
                output_path = None
            
            try:
                result_path = self.crop_to_header(screenshot_path, output_path)
                results.append(result_path)
            except Exception as e:
                print(f"[HEADER-DETECTOR] ❌ Ошибка обработки {screenshot_path}: {e}")
                results.append(screenshot_path)
        
        return results
