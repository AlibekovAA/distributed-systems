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

interface BalanceResponse {
    success: boolean;
    new_balance: number;
}

interface Category {
    id: number;
    name: string;
}

interface PreferenceCheck {
    has_preferences: boolean;
    categories?: Category[];
}

interface Preference {
    category_id: number;
    score: number;
}

export class AuthService {
    private static readonly BASE_URL = 'http://localhost:8000/auth';
    private static readonly TOKEN_KEY = 'access_token';

    private static getAuthHeaders(): HeadersInit {
        const token = localStorage.getItem(this.TOKEN_KEY);
        return {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {})
        };
    }

    private static async fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
        return fetch(`${this.BASE_URL}${url}`, {
            ...options,
            headers: { ...this.getAuthHeaders(), ...(options.headers || {}) },
            credentials: 'include',
        });
    }

    private static async handleResponse<T>(response: Response): Promise<T> {
        if (!response.ok) {
            const error = await response.json();
            console.error('Request error:', error);
            throw new Error(error.detail || 'Request failed');
        }
        return response.json();
    }

    static validateUserData({ email, password, name }: UserData): void {
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            throw new Error('Invalid email format');
        }
        if (password.length < 8) {
            throw new Error('Password must be at least 8 characters long');
        }
        if (!name.trim()) {
            throw new Error('Name is required');
        }
    }

    static async register(userData: UserData): Promise<void> {
        this.validateUserData(userData);
        const response = await this.fetchWithAuth('/register', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
        await this.handleResponse(response);
    }

    static async login(email: string, password: string): Promise<AuthResponse> {
        const response = await this.fetchWithAuth('/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });

        const data = await this.handleResponse<AuthResponse>(response);
        localStorage.setItem(this.TOKEN_KEY, data.access_token);
        return data;
    }

    static async getProfile(): Promise<any> {
        const response = await this.fetchWithAuth('/profile');
        return this.handleResponse(response);
    }

    static async refreshToken(refresh_token: string): Promise<AuthResponse> {
        const response = await this.fetchWithAuth('/token/refresh', {
            method: 'POST',
            body: JSON.stringify({ refresh_token }),
        });

        return this.handleResponse<AuthResponse>(response);
    }

    static async changePassword(oldPassword: string, newPassword: string): Promise<void> {
        const response = await this.fetchWithAuth('/change-password', {
            method: 'POST',
            body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
        });

        await this.handleResponse(response);
    }

    static async addBalance(amount: number): Promise<BalanceResponse> {
        const response = await this.fetchWithAuth('/add-balance', {
            method: 'POST',
            body: JSON.stringify({ amount }),
        });

        return this.handleResponse<BalanceResponse>(response);
    }

    static async checkPreferences(): Promise<PreferenceCheck> {
        const response = await this.fetchWithAuth('/preferences/check');
        return this.handleResponse<PreferenceCheck>(response);
    }

    static async savePreferences(preferences: Preference[]): Promise<void> {
        const response = await this.fetchWithAuth('/preferences/save', {
            method: 'POST',
            body: JSON.stringify(preferences),
        });
        await this.handleResponse(response);
    }
}
