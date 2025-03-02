import { AuthService } from '../../services/authService.js';
import NotificationManager from '../../utils/notifications.js';
import { authGuard } from '../../utils/authGuard.js';
import { initializeLogout as initLogout } from '../../utils/logout.js';

const handleError = (error: unknown, logout = false) => {
    NotificationManager.error(error instanceof Error ? error.message : 'An error occurred');
    if (logout) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/';
    }
};

export async function initializeProfile() {
    if (!authGuard()) return;

    try {
        const { email, name, balance } = await AuthService.getProfile();

        const elements: Record<string, HTMLElement | null> = {
            email: document.getElementById('userEmail'),
            name: document.getElementById('userName'),
            balance: document.getElementById('userBalance'),
        };

        if (elements.email) elements.email.textContent = email;
        if (elements.name) elements.name.textContent = name;
        if (elements.balance) elements.balance.textContent = `${balance} ₽`;
    } catch (error) {
        handleError(error, true);
    }
}

function validatePasswordFields(form: HTMLFormElement): { oldPassword: string; newPassword: string; confirmNewPassword: string } | null {
    const fields = ['oldPassword', 'newPassword', 'confirmNewPassword'].map((name) => form.elements.namedItem(name) as HTMLInputElement);

    for (const field of fields) {
        if (!field.value.trim()) {
            NotificationManager.error('This field is required.');
            field.focus();
            return null;
        }
    }

    const [oldPassword, newPassword, confirmNewPassword] = fields.map((field) => field.value);

    if (newPassword !== confirmNewPassword) {
        NotificationManager.error('Passwords do not match');
        return null;
    }

    if (newPassword.length < 8) {
        NotificationManager.error('Password must be at least 8 characters long');
        return null;
    }

    return { oldPassword, newPassword, confirmNewPassword };
}

function initializeChangePassword() {
    const form = document.getElementById('changePasswordForm') as HTMLFormElement;
    if (!form) return;

    form.setAttribute('novalidate', 'true');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const passwords = validatePasswordFields(form);
        if (!passwords) return;

        try {
            await AuthService.changePassword(passwords.oldPassword, passwords.newPassword);
            NotificationManager.success('Password changed successfully');
            form.reset();
        } catch (error) {
            handleError(error);
        }
    });
}

function initializeAddBalance() {
    document.getElementById('addBalanceBtn')?.addEventListener('click', async () => {
        try {
            const { success, new_balance } = await AuthService.addBalance(100000);
            if (success) {
                const balanceElement = document.getElementById('userBalance');
                if (balanceElement) balanceElement.textContent = `${new_balance} ₽`;
                NotificationManager.success('Balance updated successfully');
            }
        } catch (error) {
            handleError(error);
        }
    });
}

function initializeNavigation() {
    document.querySelector('.menu-item.active')?.addEventListener('click', (e) => {
        if (window.location.pathname.includes('/pages/profile/')) e.preventDefault();
    });
}

const init = () => {
    initializeProfile();
    initLogout();
    initializeChangePassword();
    initializeAddBalance();
    initializeNavigation();
};

document.addEventListener('DOMContentLoaded', init);
