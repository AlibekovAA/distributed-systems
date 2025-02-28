import { AuthService } from '../../services/authService.js';
import NotificationManager from '../../utils/notifications.js';

const performLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/';
};

export async function initializeProfile() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        performLogout();
        return;
    }

    try {
        const profile = await AuthService.getProfile();

        const elements = {
            email: document.getElementById('userEmail'),
            name: document.getElementById('userName'),
            balance: document.getElementById('userBalance')
        };

        if (elements.email) elements.email.textContent = profile.email;
        if (elements.name) elements.name.textContent = profile.name;
        if (elements.balance) elements.balance.textContent = `${profile.balance} ₽`;
    } catch (error) {
        NotificationManager.error(error instanceof Error ? error.message : 'Error loading profile');
        performLogout();
    }
}

export function initializeLogout() {
    const logoutButton = document.createElement('button');
    logoutButton.textContent = 'Logout';
    logoutButton.className = 'btn logout-btn';
    logoutButton.addEventListener('click', performLogout);

    document.querySelector('.profile-card')?.appendChild(logoutButton);
}

const init = () => {
    initializeProfile();
    initializeLogout();
};

document.addEventListener('DOMContentLoaded', init);
