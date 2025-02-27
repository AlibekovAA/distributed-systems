import { AuthService } from '../../services/authService.js';
import NotificationManager from '../../utils/notifications.js';

export async function initializeProfile() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/';
        return;
    }

    try {
        const profile = await AuthService.getProfile();

        const userEmail = document.getElementById('userEmail');
        const userName = document.getElementById('userName');
        const userBalance = document.getElementById('userBalance');

        if (userEmail) userEmail.textContent = profile.email;
        if (userName) userName.textContent = profile.name;
        if (userBalance) userBalance.textContent = `${profile.balance} ₽`;
    } catch (error) {
        if (error instanceof Error) {
            NotificationManager.error(error.message);
        } else {
            NotificationManager.error('Error loading profile');
        }
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/';
    }
}

export function initializeLogout() {
    const logoutButton = document.createElement('button');
    logoutButton.textContent = 'Logout';
    logoutButton.className = 'btn logout-btn';

    logoutButton.addEventListener('click', () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/';
    });

    const profileCard = document.querySelector('.profile-card');
    if (profileCard) {
        profileCard.appendChild(logoutButton);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initializeProfile();
    initializeLogout();
});
