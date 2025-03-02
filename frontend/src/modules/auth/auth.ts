import { AuthService } from '../../services/authService.js';
import NotificationManager from '../../utils/notifications.js';

const handleError = (error: unknown) => {
    NotificationManager.error(error instanceof Error ? error.message : 'An unknown error occurred');
};

const validateEmail = (email: string): boolean => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

const debounceMap = new Map<Function, NodeJS.Timeout>();
const debounce = (fn: Function, delay: number = 300) => {
    return (...args: any[]) => {
        if (debounceMap.has(fn)) clearTimeout(debounceMap.get(fn));
        debounceMap.set(fn, setTimeout(() => fn(...args), delay));
    };
};

const validateFormInput = debounce((input: HTMLInputElement) => {
    input.classList.toggle('invalid', input.type === 'email' && !validateEmail(input.value));
});

const validateAuthFields = (form: HTMLFormElement, fields: string[]): Record<string, string> | null => {
    const values: Record<string, string> = {};
    for (const name of fields) {
        const input = form.elements.namedItem(name) as HTMLInputElement;
        if (!input.value.trim()) {
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
    if (!values) return;

    if (!validateEmail(values.loginEmail)) {
        NotificationManager.error('Please enter a valid email address');
        return;
    }

    try {
        const response = await AuthService.login(values.loginEmail, values.loginPassword);
        localStorage.setItem('access_token', response.access_token);
        if (response.refresh_token) localStorage.setItem('refresh_token', response.refresh_token);
        NotificationManager.success('Successfully logged in!');
        window.location.href = '/pages/profile/index.html';
    } catch (error) {
        handleError(error);
    }
};

const handleRegister = async (form: HTMLFormElement) => {
    const values = validateAuthFields(form, ['registerEmail', 'registerPassword', 'confirmPassword']);
    if (!values) return;

    if (!validateEmail(values.registerEmail)) {
        NotificationManager.error('Please enter a valid email address');
        return;
    }

    if (values.registerPassword !== values.confirmPassword) {
        NotificationManager.error('Passwords do not match');
        return;
    }

    try {
        await AuthService.register({
            email: values.registerEmail,
            password: values.registerPassword,
            name: values.registerEmail.split('@')[0],
        });

        NotificationManager.success('Registration successful! You can now login.');
        form.reset();

        document.querySelector<HTMLElement>('[data-tab="login"]')?.click();
    } catch (error) {
        handleError(error);
    }
};

export function initializeAuth() {
    const forms = {
        login: document.getElementById('loginForm') as HTMLFormElement,
        register: document.getElementById('registerForm') as HTMLFormElement,
    };

    Object.values(forms).forEach(form => {
        form.setAttribute('novalidate', 'true');
        form.querySelectorAll('input').forEach(input => {
            input.addEventListener('input', () => validateFormInput(input));
        });
    });

    document.querySelectorAll('.tab-btn').forEach(button => {
        button.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            const tabName = button.getAttribute('data-tab');
            forms.login.classList.toggle('hidden', tabName !== 'login');
            forms.register.classList.toggle('hidden', tabName !== 'register');
        });
    });

    forms.login.addEventListener('submit', (e) => {
        e.preventDefault();
        handleLogin(forms.login);
    });

    forms.register.addEventListener('submit', (e) => {
        e.preventDefault();
        handleRegister(forms.register);
    });
}
