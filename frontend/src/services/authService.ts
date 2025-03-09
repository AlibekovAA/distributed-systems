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
    private static readonly HEADERS_JSON = { 'Content-Type': 'application/json' };

    private static getAuthHeaders(): HeadersInit {
        const token = localStorage.getItem(this.TOKEN_KEY);
        return token ? { ...this.HEADERS_JSON, Authorization: `Bearer ${token}` } : this.HEADERS_JSON;
    }

    private static async handleResponse<T>(response: Response): Promise<T> {
        const data = await response.json();
        if (!response.ok) {
            console.error('Request error:', data);
            throw new Error(data.detail || 'Request failed');
        }
        return data;
    }

    private static async request<T>(url: string, options: RequestInit = {}): Promise<T> {
        const response = await fetch(`${this.BASE_URL}${url}`, {
            ...options,
            headers: { ...this.getAuthHeaders(), ...(options.headers || {}) },
            credentials: 'include',
        });
        return this.handleResponse<T>(response);
    }

    private static validateUserData({ email, password, name }: UserData): void {
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw new Error('Invalid email format');
        if (password.length < 8) throw new Error('Password must be at least 8 characters long');
        if (!name.trim()) throw new Error('Name is required');
    }

    static register(userData: UserData): Promise<void> {
        this.validateUserData(userData);
        return this.request('/register', { method: 'POST', body: JSON.stringify(userData) });
    }

    static async login(email: string, password: string): Promise<AuthResponse> {
        const data = await this.request<AuthResponse>('/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
        localStorage.setItem(this.TOKEN_KEY, data.access_token);
        return data;
    }

    static getProfile(): Promise<any> {
        return this.request('/profile');
    }

    static refreshToken(refresh_token: string): Promise<AuthResponse> {
        return this.request<AuthResponse>('/token/refresh', {
            method: 'POST',
            body: JSON.stringify({ refresh_token }),
        });
    }

    static changePassword(oldPassword: string, newPassword: string): Promise<void> {
        return this.request('/change-password', {
            method: 'POST',
            body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
        });
    }

    static addBalance(amount: number): Promise<BalanceResponse> {
        return this.request<BalanceResponse>('/add-balance', {
            method: 'POST',
            body: JSON.stringify({ amount }),
        });
    }

    static checkPreferences(): Promise<PreferenceCheck> {
        return this.request<PreferenceCheck>('/preferences/check');
    }

    static savePreferences(preferences: Preference[]): Promise<void> {
        return this.request('/preferences/save', { method: 'POST', body: JSON.stringify(preferences) });
    }
}
