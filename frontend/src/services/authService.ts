interface AuthResponse {
    access_token: string;
    token_type: string;
    refresh_token?: string;
}

interface UserData {
    email: string;
    password: string;
    name: string;
}

export class AuthService {
    private static BASE_URL = '/auth';

    static async register(userData: UserData): Promise<void> {
        const response = await fetch(`${this.BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData),
            credentials: 'include'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }
    }

    static async login(email: string, password: string): Promise<AuthResponse> {
        const response = await fetch(`${this.BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
            credentials: 'include'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }

        return await response.json();
    }

    static async getProfile(): Promise<any> {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${this.BASE_URL}/profile`, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            throw new Error('Failed to fetch profile');
        }

        return await response.json();
    }

    static async refreshToken(refresh_token: string): Promise<AuthResponse> {
        const response = await fetch(`${this.BASE_URL}/token/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token }),
        });

        if (!response.ok) {
            throw new Error('Failed to refresh token');
        }

        return await response.json();
    }
}
