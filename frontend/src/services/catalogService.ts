interface Product {
    id: number;
    name: string;
    description: string;
    price: number;
    quantity: number;
}

export class CatalogService {
    static async getProducts(): Promise<Product[]> {
        return [];
    }

    static async getProduct(id: number): Promise<Product | null> {
        return null;
    }
}
