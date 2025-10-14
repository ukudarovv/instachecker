/**
 * Instagram Cookies Export Script (УЛУЧШЕННАЯ ВЕРСИЯ)
 * 
 * ⚠️ ВАЖНО: Используйте расширение EditThisCookie для гарантированного получения ВСЕХ cookies!
 * 
 * Этот скрипт использует cookieStore API для получения httpOnly cookies.
 * Если API не поддерживается, установите расширение EditThisCookie.
 * 
 * Как использовать:
 * 1. Откройте instagram.com в браузере и войдите в аккаунт
 * 2. Нажмите F12 (откроется DevTools)
 * 3. Перейдите на вкладку Console
 * 4. Скопируйте и вставьте этот скрипт целиком
 * 5. Нажмите Enter
 * 6. Cookies автоматически скопируются в буфер обмена
 * 7. Вставьте в бот
 */

(async function() {
    console.log('🍪 Instagram Cookies Exporter v2.0');
    console.log('━'.repeat(60));
    
    // Проверяем что мы на Instagram
    if (!window.location.hostname.includes('instagram.com')) {
        console.error('❌ Ошибка: этот скрипт нужно запускать на instagram.com');
        alert('❌ Откройте instagram.com и запустите скрипт там');
        return;
    }
    
    let cookies = [];
    let method = '';
    
    // Способ 1: Попробовать cookieStore API (получает httpOnly cookies)
    try {
        if (typeof cookieStore !== 'undefined') {
            console.log('🔍 Используется cookieStore API (получит ВСЕ cookies)...');
            const allCookies = await cookieStore.getAll({domain: 'instagram.com'});
            
            cookies = allCookies.map(c => ({
                name: c.name,
                value: c.value,
                domain: c.domain,
                path: c.path,
                expires: c.expires ? Math.floor(c.expires / 1000) : -1,
                secure: c.secure || false,
                sameSite: c.sameSite || 'None'
            }));
            
            method = 'cookieStore API';
            console.log('✅ cookieStore API успешно!');
        } else {
            throw new Error('cookieStore API не поддерживается');
        }
    } catch(e) {
        // Способ 2: Fallback на document.cookie (может пропустить httpOnly)
        console.warn('⚠️ cookieStore API недоступен, используется document.cookie');
        console.warn('⚠️ httpOnly cookies (включая sessionid) могут отсутствовать!');
        console.warn('⚠️ РЕКОМЕНДАЦИЯ: Используйте расширение EditThisCookie!');
        
        const cookiesString = document.cookie;
        
        if (!cookiesString) {
            console.error('❌ Cookies не найдены');
            alert('❌ Cookies не найдены. Убедитесь что вы вошли в Instagram.');
            return;
        }
        
        cookies = cookiesString.split('; ').map(cookieStr => {
            const [name, value] = cookieStr.split('=');
            return {
                name: name,
                value: decodeURIComponent(value),
                domain: '.instagram.com',
                path: '/'
            };
        });
        
        method = 'document.cookie (может быть неполно)';
    }
    
    console.log(`\n📊 Найдено cookies: ${cookies.length}`);
    console.log(`📡 Метод: ${method}`);
    
    // Проверяем наличие sessionid
    const hasSessionId = cookies.some(c => c.name === 'sessionid');
    const sessionIdCookie = cookies.find(c => c.name === 'sessionid');
    
    if (hasSessionId) {
        console.log('\n✅ sessionid найден - отлично!');
        console.log(`   Значение: ${sessionIdCookie.value.substring(0, 20)}...`);
    } else {
        console.error('\n❌ sessionid НЕ НАЙДЕН!');
        console.error('   Возможные причины:');
        console.error('   1. Вы не вошли в Instagram');
        console.error('   2. sessionid имеет флаг httpOnly');
        console.error('');
        console.error('   РЕШЕНИЕ:');
        console.error('   → Установите расширение EditThisCookie');
        console.error('   → Или используйте DevTools → Application → Cookies');
        console.error('');
        alert('❌ sessionid НЕ НАЙДЕН!\n\nИспользуйте расширение EditThisCookie для получения ВСЕХ cookies.\n\nПодробнее: GET_ALL_COOKIES_GUIDE.md');
        return;
    }
    
    // Показываем список cookies
    console.log('\n📋 Список cookies:');
    cookies.forEach((c, i) => {
        const preview = c.value.length > 30 
            ? c.value.substring(0, 30) + '...' 
            : c.value;
        console.log(`  ${i + 1}. ${c.name}: ${preview}`);
    });
    
    // Конвертируем в JSON
    const cookiesJson = JSON.stringify(cookies, null, 2);
    
    // Копируем в буфер обмена
    try {
        // Современный способ (работает в большинстве браузеров)
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(cookiesJson).then(() => {
                console.log('\n✅ Cookies скопированы в буфер обмена!');
                console.log('━'.repeat(50));
                console.log('👉 Теперь вставьте их в Telegram бот');
                alert('✅ Cookies скопированы!\n\nТеперь вставьте их в Telegram бот.');
            }).catch(err => {
                console.error('❌ Ошибка копирования:', err);
                showCookiesManually(cookiesJson);
            });
        } 
        // Старый способ (для старых браузеров)
        else if (typeof copy === 'function') {
            copy(cookiesJson);
            console.log('\n✅ Cookies скопированы в буфер обмена!');
            console.log('━'.repeat(50));
            console.log('👉 Теперь вставьте их в Telegram бот');
            alert('✅ Cookies скопированы!\n\nТеперь вставьте их в Telegram бот.');
        } else {
            showCookiesManually(cookiesJson);
        }
    } catch (err) {
        console.error('❌ Ошибка:', err);
        showCookiesManually(cookiesJson);
    }
    
    function showCookiesManually(json) {
        console.log('\n⚠️ Автоматическое копирование не удалось');
        console.log('📋 Скопируйте вручную этот JSON:');
        console.log('━'.repeat(50));
        console.log(json);
        console.log('━'.repeat(50));
        
        // Показываем в alert для удобства копирования
        const userChoice = confirm(
            'Автоматическое копирование не сработало.\n\n' +
            'Нажмите OK чтобы открыть окно с cookies для копирования,\n' +
            'или Cancel чтобы скопировать из консоли.'
        );
        
        if (userChoice) {
            prompt('Скопируйте этот JSON и вставьте в бот:', json);
        }
    }
})();

