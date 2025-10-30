import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export interface ListingData {
  user_id: number;
  locations: string[];
  wants: Record<string, any[]>;
  offers: Record<string, any[]>;
}

export interface Match {
  match_id: number;
  user_id: number;
  partner_name: string;
  partner_telegram: string;
  partner_rating: number;
  final_score: number;
  quality: string;
  location_overlap: boolean;
  matching_categories: string[];
  category_scores: Record<string, number>;
  permanent_items: Record<string, any[]>;
  temporary_items: Record<string, any[]>;
}

export interface MatchesResponse {
  total_matches: number;
  matches: Match[];
}

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('API Error:', error.message);
        return Promise.reject(error);
      }
    );
  }

  /**
   * Get user profile
   */
  async getUser(userId: number) {
    try {
      const response = await this.api.get(`/users/${userId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get all user listings
   */
  async getUserListings(userId: number) {
    try {
      const response = await this.api.get(`/listings/user/${userId}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Create listing with categories
   */
  async createListing(data: ListingData) {
    try {
      const response = await this.api.post(`/listings/create-by-categories`, data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Create wants-only listing
   */
  async createWantsOnly(userId: number, wants: Record<string, any[]>, locations?: string[]) {
    try {
      const response = await this.api.post(`/listings/wants-only`, {
        user_id: userId,
        wants,
        locations,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Create offers-only listing
   */
  async createOffersOnly(userId: number, offers: Record<string, any[]>, locations?: string[]) {
    try {
      const response = await this.api.post(`/listings/offers-only`, {
        user_id: userId,
        offers,
        locations,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Find matches for user
   */
  async findMatches(userId: number, exchangeType?: string, minScore?: number): Promise<MatchesResponse> {
    try {
      let url = `/listings/find-matches/${userId}`;
      const params = new URLSearchParams();

      if (exchangeType) {
        params.append('exchange_type', exchangeType);
      }
      if (minScore !== undefined) {
        params.append('min_score', minScore.toString());
      }

      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await this.api.get(url);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Find matches by category
   */
  async findMatchesByCategory(userId: number, category: string): Promise<MatchesResponse> {
    try {
      const response = await this.api.get(
        `/listings/find-matches/${userId}/category/${category}`
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get user ratings/statistics
   */
  async getUserStats(userId: number) {
    try {
      const response = await this.api.get(`/users/${userId}/stats`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Health check
   */
  async healthCheck() {
    try {
      const response = await this.api.get('/health');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Error handler
   */
  private handleError(error: any) {
    if (axios.isAxiosError(error)) {
      const { response, message } = error;
      if (response) {
        return {
          status: response.status,
          message: response.data?.detail || response.statusText,
          data: response.data,
        };
      }
      return { status: 0, message };
    }
    return { status: 0, message: String(error) };
  }
}

export const apiService = new ApiService();
export default apiService;
