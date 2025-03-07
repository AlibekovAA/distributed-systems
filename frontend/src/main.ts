import { initializeAuth } from './modules/auth/auth.js';
import { authGuard } from './utils/authGuard.js';

document.addEventListener('DOMContentLoaded', async () => {
    if (!window.location.pathname.endsWith('/index.html') && !window.location.pathname.endsWith('/')) {
        if (!await authGuard()) {
            return;
        }
    }

    if (window.location.pathname.endsWith('/index.html') || window.location.pathname.endsWith('/')) {
        initializeAuth();
    }
});
