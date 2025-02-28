import { AuthService } from '../../services/authService.js';
import NotificationManager from '../../utils/notifications.js';

function validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

export function initializeAuth() {
    const forms = {
        login: document.getElementById('loginForm') as HTMLFormElement,
        register: document.getElementById('registerForm') as HTMLFormElement
    };

    const debounceTimeout: { [key: string]: NodeJS.Timeout } = {};

    const debounce = (fn: Function, delay: number = 300) => {
        return (...args: any[]) => {
            if (debounceTimeout[fn.name]) {
                clearTimeout(debounceTimeout[fn.name]);
            }
            debounceTimeout[fn.name] = setTimeout(() => fn(...args), delay);
        };
    };

    const validateFormInput = debounce((input: HTMLInputElement) => {
        if (input.type === 'email' && !validateEmail(input.value)) {
            input.classList.add('invalid');
        } else {
            input.classList.remove('invalid');
        }
    });

    Object.values(forms).forEach(form => {
        form.querySelectorAll('input').forEach(input => {
            input.addEventListener('input', () => validateFormInput(input));
        });
    });

    const tabButtons = document.querySelectorAll('.tab-btn');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            if (tabName === 'login') {
                forms.login.classList.remove('hidden');
                forms.register.classList.add('hidden');
            } else {
                forms.login.classList.add('hidden');
                forms.register.classList.remove('hidden');
            }
        });
    });

    forms.login.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = (forms.login.elements.namedItem('loginEmail') as HTMLInputElement).value;
        const password = (forms.login.elements.namedItem('loginPassword') as HTMLInputElement).value;

        if (!validateEmail(email)) {
            NotificationManager.error('Please enter a valid email address');
            return;
        }

        try {
            const response = await AuthService.login(email, password);
            localStorage.setItem('access_token', response.access_token);
            if (response.refresh_token) {
                localStorage.setItem('refresh_token', response.refresh_token);
            }
            NotificationManager.success('Successfully logged in!');
            window.location.href = '/pages/profile/index.html';
        } catch (error) {
            if (error instanceof Error) {
                NotificationManager.error(error.message);
            } else {
                NotificationManager.error('An unknown error occurred');
            }
        }
    });

    forms.register.addEventListener('submit', async (e) => {
        e.preventDefault();

        const emailInput = forms.register.elements.namedItem('registerEmail') as HTMLInputElement;
        const passwordInput = forms.register.elements.namedItem('registerPassword') as HTMLInputElement;
        const confirmPasswordInput = forms.register.elements.namedItem('confirmPassword') as HTMLInputElement;

        const email = emailInput.value;
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;

        if (!validateEmail(email)) {
            NotificationManager.error('Please enter a valid email address');
            return;
        }

        if (password !== confirmPassword) {
            NotificationManager.error('Passwords do not match');
            return;
        }

        try {
            await AuthService.register({
                email,
                password,
                name: email.split('@')[0]
            });
            NotificationManager.success('Registration successful! You can now login.');

            emailInput.value = '';
            passwordInput.value = '';
            confirmPasswordInput.value = '';

            const loginTab = document.querySelector('[data-tab="login"]') as HTMLElement;
            loginTab.click();
        } catch (error) {
            if (error instanceof Error) {
                NotificationManager.error(error.message);
            } else {
                NotificationManager.error('An unknown error occurred');
            }
        }
    });
}
