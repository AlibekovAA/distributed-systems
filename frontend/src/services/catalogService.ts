export interface Product {
    id: number;
    name: string;
    description: string;
    price: number;
    quantity: number;
}

export interface OrderHistoryItem extends Product {
    order_number: number;
}

interface OrderHistoryResponse {
    order_number: number;
    items: Product[];
    total_price: number;
}

export class CatalogService {
    private static readonly BASE_URL = '/api';
    private static readonly TOKEN_KEY = 'access_token';
    private static readonly HEADERS_JSON = { 'Content-Type': 'application/json', Accept: 'application/json' };

    private static async handleResponse<T>(response: Response): Promise<T> {
        const data = await response.json();
        if (!response.ok) {
            console.error('Response error:', data);
            throw new Error(data.detail || 'Request failed');
        }
        return data;
    }

    private static async request<T>(url: string, options: RequestInit = {}): Promise<T> {
        const response = await fetch(`${this.BASE_URL}${url}`, {
            ...options,
            credentials: 'include',
            headers: { ...this.HEADERS_JSON, ...options.headers },
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

    static async getCart(): Promise<Product[]> {
        try {
            return await this.request(`/order/${encodeURIComponent(this.getAuthEmail())}`) ?? [];
        } catch (error) {
            console.error('Error fetching cart:', error);
            return [];
        }
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

    static async payForOrder(): Promise<void> {
        try {
            await this.request(`/order/${this.getAuthEmail()}/pay`, {
                method: 'POST',
                body: JSON.stringify({}),
            });
        } catch (error) {
            if (error instanceof Error) {
                try {
                    const errorData = JSON.parse(error.message);
                    if (errorData.error === 'insufficient_funds') {
                        throw new Error(JSON.stringify(errorData));
                    }
                } catch {
                    throw new Error('Failed to pay for order');
                }
            }
            throw error;
        }
    }

    static getProduct(id: number): Promise<Product | null> {
        return this.request(`/products/${id}`);
    }

    static getOrderHistory(): Promise<OrderHistoryResponse[]> {
        return this.request(`/orders/${encodeURIComponent(this.getAuthEmail())}/history`);
    }
}
