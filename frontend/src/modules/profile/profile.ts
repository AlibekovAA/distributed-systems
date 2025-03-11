import { AuthService } from '../../services/authService.js';
import NotificationManager from '../../utils/notifications.js';
import { authGuard } from '../../utils/authGuard.js';
import { initializeLogout as initLogout } from '../../utils/logout.js';
import LoaderManager from '../../utils/loader.js';

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
        const { email, name } = await LoaderManager.wrap(AuthService.getProfile());

        const elements: Record<string, HTMLElement | null> = {
            email: document.getElementById('userEmail'),
            name: document.getElementById('userName'),
        };

        if (elements.email) elements.email.textContent = email;
        if (elements.name) elements.name.textContent = name;
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

async function initializeChangePassword() {
    const form = document.getElementById('changePasswordForm') as HTMLFormElement;
    if (!form) return;

    form.setAttribute('novalidate', 'true');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const passwords = validatePasswordFields(form);
        if (!passwords) return;

        try {
            await LoaderManager.wrap(AuthService.changePassword(passwords.oldPassword, passwords.newPassword));
            NotificationManager.success('Password changed successfully');
            form.reset();
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
    initializeNavigation();
};

document.addEventListener('DOMContentLoaded', init);
