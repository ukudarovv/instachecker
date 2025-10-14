/**
 * Полный экспорт ВСЕХ cookies Instagram (включая httpOnly)
 * 
 * ВАЖНО: Этот скрипт нужно запускать в консоли РАСШИРЕНИЯ браузера,
 * а не на странице instagram.com, потому что только расширения имеют
 * доступ к cookies API, который показывает httpOnly cookies.
 * 
 * СПОСОБ 1: Через расширение (рекомендуется)
 * ===========================================
 * Установите расширение "EditThisCookie" или "Cookie-Editor" и экспортируйте через него.
 * 
 * СПОСОБ 2: Через DevTools Application (работает всегда)
 * =======================================================
 * 1. Откройте instagram.com и войдите
 * 2. F12 → Application → Cookies → https://www.instagram.com
 * 3. Вручную скопируйте значения или используйте этот скрипт:
 */

// Вариант 1: Для обычной консоли (может пропустить httpOnly cookies)
(function exportCookiesFromDocumentCookie() {
    console.log('🍪 Instagram Cookies Exporter (document.cookie version)');
    console.log('━'.repeat(60));
    console.warn('⚠️ ВНИМАНИЕ: document.cookie НЕ ПОКАЗЫВАЕТ httpOnly cookies!');
    console.warn('⚠️ sessionid может отсутствовать, если у него флаг httpOnly.');
    console.warn('⚠️ Используйте СПОСОБ 2 или установите расширение!');
    console.log('━'.repeat(60));
    
    if (!window.location.hostname.includes('instagram.com')) {
        console.error('❌ Запустите на instagram.com');
        return;
    }
    
    const cookies = document.cookie.split('; ').map(cookieStr => {
        const [name, value] = cookieStr.split('=');
        return {
            name: name,
            value: decodeURIComponent(value),
            domain: '.instagram.com',
            path: '/'
        };
    });
    
    console.log(`📦 Получено cookies: ${cookies.length}`);
    
    const hasSessionId = cookies.some(c => c.name === 'sessionid');
    if (!hasSessionId) {
        console.error('❌ sessionid НЕ НАЙДЕН!');
        console.error('   Это означает что sessionid имеет флаг httpOnly.');
        console.error('   ИСПОЛЬЗУЙТЕ один из способов ниже:');
        console.error('');
        console.error('   1. Расширение EditThisCookie (Chrome/Edge)');
        console.error('   2. Расширение Cookie-Editor (Firefox)');
        console.error('   3. DevTools → Application → Cookies (вручную)');
        console.error('');
        return null;
    }
    
    const json = JSON.stringify(cookies, null, 2);
    
    try {
        navigator.clipboard.writeText(json).then(() => {
            console.log('✅ Cookies скопированы в буфер!');
        });
    } catch {
        console.log(json);
    }
    
    return cookies;
})();

// Вариант 2: Для консоли расширения (получает ВСЕ cookies)
// Этот код нужно запускать в background.js расширения или в popup.js
/*
chrome.cookies.getAll({domain: '.instagram.com'}, function(cookies) {
    const formatted = cookies.map(cookie => ({
        name: cookie.name,
        value: cookie.value,
        domain: cookie.domain,
        path: cookie.path,
        expires: cookie.expirationDate ? Math.floor(cookie.expirationDate) : -1,
        httpOnly: cookie.httpOnly || false,
        secure: cookie.secure || false,
        sameSite: cookie.sameSite || 'None'
    }));
    
    const json = JSON.stringify(formatted, null, 2);
    console.log('✅ Получено ВСЕ cookies (включая httpOnly):', formatted.length);
    console.log(json);
    
    // Копирование в буфер
    navigator.clipboard.writeText(json);
});
*/

