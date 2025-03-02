interface Recommendation {
    productId: number;
    score: number;
}

export class RecommendationService {
    static async getRecommendations(_userId: number): Promise<Recommendation[]> {
        return [];
    }

    static async addUserPreference(_userId: number, _productId: number, _rating: number): Promise<void> {
        return;
    }
}
