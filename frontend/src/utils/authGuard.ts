import { AuthService } from '../services/authService.js';

export async function authGuard() {
    const token = localStorage.getItem('access_token')?.trim();
    if (!token) return redirectToLogin();

    try {
        await AuthService.getProfile();
        return true;
    } catch {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        return redirectToLogin();
    }
}

function redirectToLogin() {
    window.location.assign('/');
    return false;
}
