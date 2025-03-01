import { AuthService } from '../services/authService.js';

export async function authGuard() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/';
        return false;
    }

    try {
        await AuthService.getProfile();
        return true;
    } catch (error) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/';
        return false;
    }
}
