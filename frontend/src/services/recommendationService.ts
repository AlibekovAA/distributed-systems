interface Recommendation {
    productId: number;
    score: number;
}

export class RecommendationService {
    static async getRecommendations(userId: number): Promise<Recommendation[]> {
        return [];
    }

    static async addUserPreference(userId: number, productId: number, rating: number): Promise<void> {
        return;
    }
}
