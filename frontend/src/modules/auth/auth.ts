import { AuthService } from '../../services/authService.js';
import NotificationManager from '../../utils/notifications.js';

function validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

export function initializeAuth() {
    const loginForm = document.getElementById('loginForm') as HTMLFormElement;
    const registerForm = document.getElementById('registerForm') as HTMLFormElement;
    const tabButtons = document.querySelectorAll('.tab-btn');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            if (tabName === 'login') {
                loginForm.classList.remove('hidden');
                registerForm.classList.add('hidden');
            } else {
                loginForm.classList.add('hidden');
                registerForm.classList.remove('hidden');
            }
        });
    });

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = (document.getElementById('loginEmail') as HTMLInputElement).value;
        const password = (document.getElementById('loginPassword') as HTMLInputElement).value;

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
            window.location.href = '/pages/profile/';
        } catch (error) {
            if (error instanceof Error) {
                NotificationManager.error(error.message);
            } else {
                NotificationManager.error('An unknown error occurred');
            }
        }
    });

    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const emailInput = document.getElementById('registerEmail') as HTMLInputElement;
        const passwordInput = document.getElementById('registerPassword') as HTMLInputElement;
        const confirmPasswordInput = document.getElementById('confirmPassword') as HTMLInputElement;

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
