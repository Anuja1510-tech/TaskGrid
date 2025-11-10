// ✅ /js/api.js
window.apiCall = async function (endpoint, arg1 = 'GET', arg2 = null) {
    // Determine method/data from either (method, data) or ({method, data})
    let method = 'GET', data = null;
    if (typeof arg1 === 'object' && arg1 !== null && !Array.isArray(arg1)) {
        method = (arg1.method || 'GET').toUpperCase();
        data = arg1.data || null;
    } else {
        method = (arg1 || 'GET').toUpperCase();
        data = arg2;
    }

    const tokenKey = `${CONFIG.STORAGE_PREFIX}token`;
    const userKey = `${CONFIG.STORAGE_PREFIX}user`;
    const token = localStorage.getItem(tokenKey);
    const headers = { 'Content-Type': 'application/json' };

    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${CONFIG.API_BASE_URL}${endpoint}`, {
        method,
        headers,
        body: data ? JSON.stringify(data) : null
    });

    let payload = null;
    try { payload = await res.json(); } catch (_) {}

    if (res.status === 401) {
        // Token expired/invalid — force re-login
        localStorage.removeItem(tokenKey);
        localStorage.removeItem(userKey);
        // If your hosted frontend uses a subpath, adjust '/login.html' accordingly
        window.location.href = '/login.html';
        throw new Error('Unauthorized');
    }

    if (!res.ok) {
        throw new Error((payload && (payload.error || payload.message)) || `HTTP ${res.status}`);
    }

    return payload;
};
