import { AuthService } from '../../services/authService.js';
import NotificationManager from '../../utils/notifications.js';
import { showPreferencesForm } from '../preferences/preferences.js';
import LoaderManager from '../../utils/loader.js';

const handleError = (error: unknown) =>
    NotificationManager.error(error instanceof Error ? error.message : 'An unknown error occurred');

const validateEmail = (email: string): boolean => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

const validateFormInput = (input: HTMLInputElement) => {
    if (input.type === 'email') input.classList.toggle('invalid', !validateEmail(input.value));
};

const validateAuthFields = (form: HTMLFormElement, fields: string[]): Record<string, string> | null => {
    const values: Record<string, string> = {};
    for (const name of fields) {
        const input = form[name] as HTMLInputElement;
        if (!input?.value.trim()) {
            NotificationManager.error('This field is required.');
            input.focus();
            return null;
        }
        values[name] = input.value;
    }
    return values;
};

const handleLogin = async (form: HTMLFormElement) => {
    const values = validateAuthFields(form, ['loginEmail', 'loginPassword']);
    if (!values || !validateEmail(values.loginEmail)) {
        NotificationManager.error('Please enter a valid email address');
        return;
    }

    const submitButton = form.querySelector<HTMLButtonElement>('button[type="submit"]');
    submitButton?.setAttribute('aria-busy', 'true');
    if (submitButton) submitButton.disabled = true;

    try {
        const { access_token, refresh_token } = await LoaderManager.wrap(AuthService.login(values.loginEmail, values.loginPassword));
        localStorage.setItem('access_token', access_token);
        if (refresh_token) localStorage.setItem('refresh_token', refresh_token);

        const { has_preferences, categories } = await LoaderManager.wrap(AuthService.checkPreferences());
        if (!has_preferences && categories) {
            NotificationManager.success('Successful entry! Please fill out the preference form.');
            await showPreferencesForm(categories);
        } else {
            NotificationManager.success('Successful entry!');
            window.location.href = '/pages/profile/index.html';
        }
    } catch (error) {
        handleError(error);
    } finally {
        submitButton?.removeAttribute('aria-busy');
        if (submitButton) submitButton.disabled = false;
    }
};

const handleRegister = async (form: HTMLFormElement) => {
    const values = validateAuthFields(form, ['registerName', 'registerEmail', 'registerPassword', 'confirmPassword']);
    if (!values || !validateEmail(values.registerEmail)) {
        NotificationManager.error('Please enter a valid email address');
        return;
    }

    if (values.registerPassword !== values.confirmPassword) {
        NotificationManager.error('Passwords do not match');
        return;
    }

    const submitButton = form.querySelector<HTMLButtonElement>('button[type="submit"]');
    submitButton?.setAttribute('aria-busy', 'true');
    if (submitButton) submitButton.disabled = true;

    try {
        await LoaderManager.wrap(AuthService.register({
            email: values.registerEmail,
            password: values.registerPassword,
            name: values.registerName,
        }));

        NotificationManager.success('Registration successful! You can now login.');
        form.reset();
        document.querySelector<HTMLElement>('[data-tab="login"]')?.click();
    } catch (error) {
        handleError(error);
    } finally {
        submitButton?.removeAttribute('aria-busy');
        if (submitButton) submitButton.disabled = false;
    }
};

export function initializeAuth() {
    const forms = {
        login: document.getElementById('loginForm') as HTMLFormElement,
        register: document.getElementById('registerForm') as HTMLFormElement,
    };

    Object.values(forms).forEach(form => {
        form.setAttribute('novalidate', 'true');
        form.querySelectorAll('input').forEach(input =>
            input.addEventListener('input', () => validateFormInput(input))
        );
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            form === forms.login ? handleLogin(form) : handleRegister(form);
        });
    });

    const tabButtons = Array.from(document.querySelectorAll<HTMLButtonElement>('.tab-btn'));
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const activeTab = document.querySelector<HTMLButtonElement>('.tab-btn.active');
            activeTab?.classList.remove('active');
            activeTab?.setAttribute('aria-selected', 'false');
            button.classList.add('active');
            button.setAttribute('aria-selected', 'true');

            const tabName = button.getAttribute('data-tab');
            forms.login.classList.toggle('hidden', tabName !== 'login');
            forms.register.classList.toggle('hidden', tabName !== 'register');
            forms.login.setAttribute('aria-hidden', String(tabName !== 'login'));
            forms.register.setAttribute('aria-hidden', String(tabName !== 'register'));
        });
        button.addEventListener('keydown', (event) => {
            if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
            event.preventDefault();
            const currentIndex = tabButtons.indexOf(button);
            const direction = event.key === 'ArrowRight' ? 1 : -1;
            const nextButton = tabButtons[(currentIndex + direction + tabButtons.length) % tabButtons.length];
            nextButton.focus();
            nextButton.click();
        });
    });
}
