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
    private static FULL_URL = 'http://localhost:8000/auth';
    private static TOKEN_KEY = 'access_token';

    private static async fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
        const defaultOptions: RequestInit = {
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include'
        };

        return fetch(`${this.FULL_URL}${url}`, { ...defaultOptions, ...options });
    }

    private static async handleResponse<T>(response: Response): Promise<T> {
        if (!response.ok) {
            const error = await response.json();
            console.error('Registration error details:', error);
            throw new Error(error.detail || 'Registration failed');
        }
        return response.json();
    }

    static validateUserData(userData: UserData): boolean {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!emailRegex.test(userData.email)) {
            throw new Error('Invalid email format');
        }

        if (userData.password.length < 8) {
            throw new Error('Password must be at least 8 characters long');
        }

        if (!userData.name || userData.name.trim().length === 0) {
            throw new Error('Name is required');
        }

        return true;
    }

    static async register(userData: UserData): Promise<void> {
        try {
            this.validateUserData(userData);
            console.log('Sending registration data:', userData);
            const response = await this.fetchWithAuth('/register', {
                method: 'POST',
                body: JSON.stringify({
                    email: userData.email,
                    password: userData.password,
                    name: userData.name
                })
            });
            await this.handleResponse(response);
        } catch (error) {
            console.error('Validation error:', error);
            throw error;
        }
    }

    static async login(email: string, password: string): Promise<AuthResponse> {
        const response = await this.fetchWithAuth('/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        const data = await this.handleResponse<AuthResponse>(response);
        localStorage.setItem(this.TOKEN_KEY, data.access_token);
        return data;
    }

    static async getProfile(): Promise<any> {
        const token = localStorage.getItem(this.TOKEN_KEY);
        if (!token) {
            throw new Error('No authentication token found');
        }

        try {
            const response = await this.fetchWithAuth('/profile', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            return this.handleResponse(response);
        } catch (error) {
            console.error('Profile fetch error:', error);
            throw new Error('Failed to fetch profile');
        }
    }

    static async refreshToken(refresh_token: string): Promise<AuthResponse> {
        const response = await this.fetchWithAuth('/token/refresh', {
            method: 'POST',
            body: JSON.stringify({ refresh_token })
        });
        return this.handleResponse<AuthResponse>(response);
    }
}
