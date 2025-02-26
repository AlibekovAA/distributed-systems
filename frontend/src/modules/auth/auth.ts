import { AuthService } from '../../services/authService.js';

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

        try {
            const response = await AuthService.login(email, password);
            localStorage.setItem('access_token', response.access_token);
            alert('Successfully logged in!');
        } catch (error) {
            if (error instanceof Error) {
                alert(error.message);
            } else {
                alert('An unknown error occurred');
            }
        }
    });

    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = (document.getElementById('registerEmail') as HTMLInputElement).value;
        const password = (document.getElementById('registerPassword') as HTMLInputElement).value;
        const name = (document.getElementById('fullName') as HTMLInputElement).value;

        try {
            await AuthService.register({
                email,
                password,
                name
            });
            alert('Registration successful! You can now login.');

            const loginTab = tabButtons[0] as HTMLElement;
            loginTab.click();
        } catch (error) {
            if (error instanceof Error) {
                alert(error.message);
            } else {
                alert('An unknown error occurred');
            }
        }
    });
}
