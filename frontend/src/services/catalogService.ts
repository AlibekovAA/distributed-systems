export interface Product {
    id: number;
    name: string;
    description: string;
    price: number;
    quantity: number;
}

interface OrderHistoryResponse {
    order_number: number;
    items: Product[];
    total_price: number;
}

interface ApiErrorPayload {
    detail?: string;
    error?: string;
}

export class CatalogApiError extends Error {
    constructor(message: string, readonly payload: ApiErrorPayload) {
        super(message);
        this.name = 'CatalogApiError';
    }
}

export class CatalogService {
    private static readonly BASE_URL = '/api';
    private static readonly TOKEN_KEY = 'access_token';
    private static readonly HEADERS_JSON = { 'Content-Type': 'application/json', Accept: 'application/json' };

    private static async handleResponse<T>(response: Response): Promise<T> {
        const data: unknown = await response.json().catch(() => null);
        if (!response.ok) {
            const payload = data && typeof data === 'object' ? data as ApiErrorPayload : {};
            throw new CatalogApiError(payload.detail || 'Request failed', payload);
        }
        return data as T;
    }

    private static async request<T>(url: string, options: RequestInit = {}): Promise<T> {
        const token = localStorage.getItem(this.TOKEN_KEY);
        const response = await fetch(`${this.BASE_URL}${url}`, {
            ...options,
            credentials: 'include',
            headers: {
                ...this.HEADERS_JSON,
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
                ...options.headers,
            },
            mode: 'cors',
        });
        return this.handleResponse<T>(response);
    }

    private static getAuthEmail(): string {
        const token = localStorage.getItem(this.TOKEN_KEY);
        if (!token) throw new Error('Not authenticated');

        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (!payload.sub) throw new Error('Email not found in token');
            return payload.sub;
        } catch {
            throw new Error('Invalid authentication token');
        }
    }

    static getProducts(): Promise<Product[]> {
        return this.request(`/products/${encodeURIComponent(this.getAuthEmail())}`);
    }

    static getCart(): Promise<Product[]> {
        return this.request(`/order/${encodeURIComponent(this.getAuthEmail())}`);
    }

    static addToCart(productId: number): Promise<void> {
        return this.request('/order/add', {
            method: 'POST',
            body: JSON.stringify({ product_id: productId, email: this.getAuthEmail() }),
        });
    }

    static removeFromCart(productId: number): Promise<void> {
        return this.request(`/order/${encodeURIComponent(this.getAuthEmail())}/${productId}`, { method: 'DELETE' });
    }

    static clearCart(): Promise<void> {
        return this.request(`/order/${encodeURIComponent(this.getAuthEmail())}/clear`, { method: 'POST' });
    }

    static payForOrder(): Promise<void> {
        return this.request(`/order/${encodeURIComponent(this.getAuthEmail())}/pay`, {
            method: 'POST',
            body: JSON.stringify({}),
        });
    }

    static getOrderHistory(): Promise<OrderHistoryResponse[]> {
        return this.request(`/orders/${encodeURIComponent(this.getAuthEmail())}/history`);
    }
}
