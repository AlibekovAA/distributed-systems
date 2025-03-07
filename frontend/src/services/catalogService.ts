interface Product {
    id: number;
    name: string;
    description: string;
    price: number;
    quantity: number;
}

export class CatalogService {
    private static readonly BASE_URL = 'http://localhost:8080';

    private static async request<T>(url: string, options: RequestInit = {}): Promise<T> {
        try {
            const response = await fetch(`${this.BASE_URL}${url}`, {
                ...options,
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    ...options.headers,
                },
                mode: 'cors'
            });

            if (!response.ok) {
                const error = await response.json();
                console.error('Response error:', error);
                throw new Error(error.detail || 'Error fetching products');
            }

            return response.json();
        } catch (error) {
            console.error('Request error:', error);
            throw error;
        }
    }

    private static getEmailFromToken(token: string): string {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (!payload.sub) {
                throw new Error('Email not found in token');
            }
            return payload.sub;
        } catch (error) {
            console.error('Error decoding token:', error);
            throw new Error('Invalid authentication token');
        }
    }

    static async getProducts(): Promise<Product[]> {
        const token = localStorage.getItem('access_token');
        if (!token) throw new Error('Not authenticated');

        const email = this.getEmailFromToken(token);
        if (!email) {
            throw new Error('User email not found');
        }

        return this.request<Product[]>(`/products/${encodeURIComponent(email)}`);
    }

    static async getProduct(id: number): Promise<Product | null> {
        return this.request<Product>(`/products/${id}`);
    }
}
