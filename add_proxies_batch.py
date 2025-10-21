#!/usr/bin/env python3
"""
Массовое добавление прокси в базу данных
"""

import sys
import os
import sqlite3

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = "bot.db"


def add_proxies_batch():
    """Добавление списка прокси в базу данных"""
    
    # Список прокси в формате host:port:username:password
    proxies_list = """
82.24.225.134:7975:aiiigauk:pi8vftb70eic
46.202.227.191:6185:aiiigauk:pi8vftb70eic
66.78.34.158:5777:aiiigauk:pi8vftb70eic
107.181.141.85:6482:aiiigauk:pi8vftb70eic
192.186.151.73:8574:aiiigauk:pi8vftb70eic
50.114.84.92:7331:aiiigauk:pi8vftb70eic
198.20.191.196:5266:aiiigauk:pi8vftb70eic
23.26.71.34:5517:aiiigauk:pi8vftb70eic
142.202.255.240:6480:aiiigauk:pi8vftb70eic
23.26.71.65:5548:aiiigauk:pi8vftb70eic
45.41.179.139:6674:aiiigauk:pi8vftb70eic
104.224.90.37:6198:aiiigauk:pi8vftb70eic
38.154.195.53:9141:aiiigauk:pi8vftb70eic
82.27.245.163:6486:aiiigauk:pi8vftb70eic
37.44.218.83:5766:aiiigauk:pi8vftb70eic
194.38.18.233:7295:aiiigauk:pi8vftb70eic
23.26.95.14:5496:aiiigauk:pi8vftb70eic
50.114.93.168:6152:aiiigauk:pi8vftb70eic
154.30.241.93:9804:aiiigauk:pi8vftb70eic
192.186.172.84:9084:aiiigauk:pi8vftb70eic
45.43.83.10:6293:aiiigauk:pi8vftb70eic
140.99.202.120:5998:aiiigauk:pi8vftb70eic
147.124.198.105:5964:aiiigauk:pi8vftb70eic
148.135.148.97:6090:aiiigauk:pi8vftb70eic
191.101.121.76:6350:aiiigauk:pi8vftb70eic
107.174.136.194:6136:aiiigauk:pi8vftb70eic
23.129.253.141:6759:aiiigauk:pi8vftb70eic
82.23.235.74:5398:aiiigauk:pi8vftb70eic
84.33.224.111:6135:aiiigauk:pi8vftb70eic
154.29.87.239:6660:aiiigauk:pi8vftb70eic
31.59.13.2:6272:aiiigauk:pi8vftb70eic
31.59.15.60:6327:aiiigauk:pi8vftb70eic
92.112.236.158:6590:aiiigauk:pi8vftb70eic
92.113.242.230:6814:aiiigauk:pi8vftb70eic
206.206.124.243:6824:aiiigauk:pi8vftb70eic
82.29.233.236:8093:aiiigauk:pi8vftb70eic
64.64.110.24:6547:aiiigauk:pi8vftb70eic
104.252.71.237:6165:aiiigauk:pi8vftb70eic
198.37.118.84:5543:aiiigauk:pi8vftb70eic
23.27.196.200:6569:aiiigauk:pi8vftb70eic
94.46.206.53:6826:aiiigauk:pi8vftb70eic
154.6.83.105:6576:aiiigauk:pi8vftb70eic
67.227.112.8:6048:aiiigauk:pi8vftb70eic
204.217.245.164:6755:aiiigauk:pi8vftb70eic
31.57.41.74:5650:aiiigauk:pi8vftb70eic
45.151.161.55:6146:aiiigauk:pi8vftb70eic
192.186.186.144:6186:aiiigauk:pi8vftb70eic
104.239.39.43:5972:aiiigauk:pi8vftb70eic
45.131.101.178:6445:aiiigauk:pi8vftb70eic
92.112.238.214:7093:aiiigauk:pi8vftb70eic
185.202.175.92:6880:aiiigauk:pi8vftb70eic
38.170.158.199:5475:aiiigauk:pi8vftb70eic
45.39.50.226:6644:aiiigauk:pi8vftb70eic
45.41.171.108:6144:aiiigauk:pi8vftb70eic
166.88.169.117:6724:aiiigauk:pi8vftb70eic
38.225.2.46:5829:aiiigauk:pi8vftb70eic
82.24.249.181:6018:aiiigauk:pi8vftb70eic
192.241.125.169:8213:aiiigauk:pi8vftb70eic
31.58.26.93:6676:aiiigauk:pi8vftb70eic
104.238.50.53:6599:aiiigauk:pi8vftb70eic
145.223.47.47:6629:aiiigauk:pi8vftb70eic
198.37.116.183:6142:aiiigauk:pi8vftb70eic
38.154.199.195:5349:aiiigauk:pi8vftb70eic
82.27.247.218:5552:aiiigauk:pi8vftb70eic
142.202.253.60:5735:aiiigauk:pi8vftb70eic
45.61.127.42:5981:aiiigauk:pi8vftb70eic
82.21.238.162:7965:aiiigauk:pi8vftb70eic
82.25.213.147:5499:aiiigauk:pi8vftb70eic
104.238.37.221:6778:aiiigauk:pi8vftb70eic
161.123.101.18:6644:aiiigauk:pi8vftb70eic
64.64.115.125:5760:aiiigauk:pi8vftb70eic
64.137.60.2:5066:aiiigauk:pi8vftb70eic
45.43.64.9:6267:aiiigauk:pi8vftb70eic
166.0.7.232:5693:aiiigauk:pi8vftb70eic
38.154.194.168:9581:aiiigauk:pi8vftb70eic
82.22.245.89:5913:aiiigauk:pi8vftb70eic
191.101.121.41:6315:aiiigauk:pi8vftb70eic
45.41.178.54:6275:aiiigauk:pi8vftb70eic
59.152.61.55:5495:aiiigauk:pi8vftb70eic
64.137.93.49:6506:aiiigauk:pi8vftb70eic
92.112.174.134:5718:aiiigauk:pi8vftb70eic
109.196.160.100:5846:aiiigauk:pi8vftb70eic
92.113.3.134:6143:aiiigauk:pi8vftb70eic
104.252.28.73:6011:aiiigauk:pi8vftb70eic
45.38.107.124:6041:aiiigauk:pi8vftb70eic
45.61.98.204:5888:aiiigauk:pi8vftb70eic
185.15.179.104:6070:aiiigauk:pi8vftb70eic
188.68.1.212:6081:aiiigauk:pi8vftb70eic
193.239.176.24:5430:aiiigauk:pi8vftb70eic
23.236.216.192:6222:aiiigauk:pi8vftb70eic
181.214.32.239:6253:aiiigauk:pi8vftb70eic
45.43.65.12:6526:aiiigauk:pi8vftb70eic
92.112.136.162:6106:aiiigauk:pi8vftb70eic
104.238.50.29:6575:aiiigauk:pi8vftb70eic
107.181.142.13:5606:aiiigauk:pi8vftb70eic
38.170.158.99:5375:aiiigauk:pi8vftb70eic
45.61.124.31:6360:aiiigauk:pi8vftb70eic
82.23.215.198:7525:aiiigauk:pi8vftb70eic
166.88.83.178:6835:aiiigauk:pi8vftb70eic
107.172.116.224:5680:aiiigauk:pi8vftb70eic
""".strip().split('\n')
    
    print("=" * 80)
    print("📝 ДОБАВЛЕНИЕ ПРОКСИ В БАЗУ ДАННЫХ")
    print("=" * 80)
    print(f"\n📊 Всего прокси для добавления: {len(proxies_list)}")
    print()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    added_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        for proxy_str in proxies_list:
            try:
                # Парсинг прокси: host:port:username:password
                parts = proxy_str.strip().split(':')
                if len(parts) != 4:
                    print(f"⚠️ Неправильный формат: {proxy_str}")
                    error_count += 1
                    continue
                
                host, port, username, password = parts
                host_with_port = f"{host}:{port}"
                
                # Проверяем, существует ли уже
                cursor.execute("SELECT id FROM proxies WHERE host = ?", (host_with_port,))
                existing = cursor.fetchone()
                
                if existing:
                    print(f"⏭️ Пропущен (уже существует): {host_with_port}")
                    skipped_count += 1
                    continue
                
                # Добавляем новый прокси (user_id = 1972775559 - ваш ID)
                cursor.execute("""
                    INSERT INTO proxies (user_id, scheme, host, username, password, is_active, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (1972775559, 'http', host_with_port, username, password, True, 5))
                
                conn.commit()
                
                print(f"✅ Добавлен: {host}:{port}")
                added_count += 1
                
            except Exception as e:
                print(f"❌ Ошибка при добавлении {proxy_str}: {e}")
                error_count += 1
                conn.rollback()
    
    finally:
        conn.close()
    
    print()
    print("=" * 80)
    print("📊 ИТОГИ")
    print("=" * 80)
    print(f"✅ Добавлено: {added_count}")
    print(f"⏭️ Пропущено: {skipped_count}")
    print(f"❌ Ошибок: {error_count}")
    print(f"📊 Всего: {len(proxies_list)}")
    print()
    
    return added_count, skipped_count, error_count


if __name__ == "__main__":
    print("\n🚀 Запуск массового добавления прокси...\n")
    added, skipped, errors = add_proxies_batch()
    
    if added > 0:
        print(f"🎉 Успешно добавлено {added} прокси!")
    
    if skipped > 0:
        print(f"ℹ️ {skipped} прокси уже существовали в базе")
    
    if errors > 0:
        print(f"⚠️ {errors} ошибок при добавлении")

