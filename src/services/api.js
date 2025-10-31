import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class ApiService {
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
      (error) => {
        console.error('API Error:', error.message);
        return Promise.reject(error);
      }
    );
  }

  /**
   * Get user profile
   */
  async getUser(userId) {
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
  async getUserListings(userId) {
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
  async createListing(data) {
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
  async createWantsOnly(userId, wants, locations) {
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
  async createOffersOnly(userId, offers, locations) {
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
  async findMatches(userId, exchangeType, minScore) {
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
  async findMatchesByCategory(userId, category) {
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
  async getUserStats(userId) {
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
  handleError(error) {
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

// Legacy API functions for backward compatibility
export const getWants = async () => {
  try {
    const response = await fetch('/api/market-listings/wants/all');
    if (!response.ok) throw new Error('Failed to fetch wants');
    const data = await response.json();
    return data.items || [];
  } catch (error) {
    console.error('Error fetching wants:', error);
    throw error;
  }
};

export const getOffers = async () => {
  try {
    const response = await fetch('/api/market-listings/offers/all');
    if (!response.ok) throw new Error('Failed to fetch offers');
    const data = await response.json();
    return data.items || [];
  } catch (error) {
    console.error('Error fetching offers:', error);
    throw error;
  }
};

export const apiService = new ApiService();
export default apiService;
