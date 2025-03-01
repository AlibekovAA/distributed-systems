import { AuthService } from '../../services/authService.js';
import NotificationManager from '../../utils/notifications.js';
import { authGuard } from '../../utils/authGuard.js';

const performLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/';
};

export async function initializeProfile() {
    if (!authGuard()) return;

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
    const logoutButton = document.getElementById('logoutBtn');
    if (logoutButton) {
        logoutButton.addEventListener('click', performLogout);
    }
}

function initializeChangePassword() {
    const form = document.getElementById('changePasswordForm') as HTMLFormElement;
    if (!form) return;

    form.setAttribute('novalidate', 'true');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const oldPasswordInput = form.elements.namedItem('oldPassword') as HTMLInputElement;
        const newPasswordInput = form.elements.namedItem('newPassword') as HTMLInputElement;
        const confirmNewPasswordInput = form.elements.namedItem('confirmNewPassword') as HTMLInputElement;

        const oldPassword = oldPasswordInput.value;
        const newPassword = newPasswordInput.value;
        const confirmNewPassword = confirmNewPasswordInput.value;

        if (!oldPassword) {
            NotificationManager.error('This field is required.');
            oldPasswordInput.focus();
            return;
        }

        if (!newPassword) {
            NotificationManager.error('This field is required.');
            newPasswordInput.focus();
            return;
        }

        if (!confirmNewPassword) {
            NotificationManager.error('This field is required.');
            confirmNewPasswordInput.focus();
            return;
        }

        if (newPassword !== confirmNewPassword) {
            NotificationManager.error('Passwords do not match');
            return;
        }

        if (newPassword.length < 8) {
            NotificationManager.error('Password must be at least 8 characters long');
            return;
        }

        try {
            await AuthService.changePassword(oldPassword, newPassword);
            NotificationManager.success('Password changed successfully');
            form.reset();
        } catch (error) {
            if (error instanceof Error) {
                NotificationManager.error(error.message);
            } else {
                NotificationManager.error('An unknown error occurred');
            }
        }
    });
}

function initializeAddBalance() {
    const addBalanceBtn = document.getElementById('addBalanceBtn');
    if (!addBalanceBtn) return;

    addBalanceBtn.addEventListener('click', async () => {
        try {
            const result = await AuthService.addBalance(10000);
            if (result.success) {
                const balanceElement = document.getElementById('userBalance');
                if (balanceElement) {
                    balanceElement.textContent = `${result.new_balance} ₽`;
                }
                NotificationManager.success('Balance updated successfully');
            }
        } catch (error) {
            if (error instanceof Error) {
                NotificationManager.error(error.message);
            } else {
                NotificationManager.error('Failed to update balance');
            }
        }
    });
}

function initializeNavigation() {
    const profileLink = document.querySelector('.menu-item.active');
    if (profileLink) {
        profileLink.addEventListener('click', (e) => {
            if (window.location.pathname.includes('/pages/profile/')) {
                e.preventDefault();
            }
        });
    }
}

const init = () => {
    initializeProfile();
    initializeLogout();
    initializeChangePassword();
    initializeAddBalance();
    initializeNavigation();
};

document.addEventListener('DOMContentLoaded', init);
