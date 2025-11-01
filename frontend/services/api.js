const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  /**
   * Get user profile
   */
  async getUser(userId) {
    try {
      const response = await fetch(`${this.baseURL}/users/${userId}`, {
        method: 'GET',
        headers: this.defaultHeaders,
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get all user listings
   */
  async getUserListings(userId) {
    try {
      const response = await fetch(`${this.baseURL}/listings/user/${userId}`, {
        method: 'GET',
        headers: this.defaultHeaders,
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Create listing with categories
   */
  async createListing(data) {
    try {
      const response = await fetch(`${this.baseURL}/listings/create-by-categories`, {
        method: 'POST',
        headers: this.defaultHeaders,
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Create wants-only listing
   */
  async createWantsOnly(userId, wants, locations) {
    try {
      const response = await fetch(`${this.baseURL}/listings/wants-only`, {
        method: 'POST',
        headers: this.defaultHeaders,
        body: JSON.stringify({
          user_id: userId,
          wants,
          locations,
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Create offers-only listing
   */
  async createOffersOnly(userId, offers, locations) {
    try {
      const response = await fetch(`${this.baseURL}/listings/offers-only`, {
        method: 'POST',
        headers: this.defaultHeaders,
        body: JSON.stringify({
          user_id: userId,
          offers,
          locations,
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
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

      const response = await fetch(`${this.baseURL}${url}`, {
        method: 'GET',
        headers: this.defaultHeaders,
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Find matches by category
   */
  async findMatchesByCategory(userId, category) {
    try {
      const response = await fetch(`${this.baseURL}/listings/find-matches/${userId}/category/${category}`, {
        method: 'GET',
        headers: this.defaultHeaders,
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get user ratings/statistics
   */
  async getUserStats(userId) {
    try {
      const response = await fetch(`${this.baseURL}/users/${userId}/stats`, {
        method: 'GET',
        headers: this.defaultHeaders,
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Health check
   */
  async healthCheck() {
    try {
      const response = await fetch(`${this.baseURL}/health`, {
        method: 'GET',
        headers: this.defaultHeaders,
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Error handler
   */
  handleError(error) {
    if (error.message && error.message.includes('HTTP')) {
      // Already formatted error from fetch
      return { status: 0, message: error.message };
    }
    return { status: 0, message: String(error) };
  }
}

// API functions for listings
export const getWants = async () => {
  try {
    const response = await fetch('/api/wants/');
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
    const response = await fetch('/api/offers/');
    if (!response.ok) throw new Error('Failed to fetch offers');
    const data = await response.json();
    return data.items || [];
  } catch (error) {
    console.error('Error fetching offers:', error);
    throw error;
  }
};

/**
 * Create new listing
 */
export const createListing = async (listingData) => {
  try {
    const response = await fetch('/api/listings/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(listingData),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error creating listing:', error);
    throw error;
  }
};

export const apiService = new ApiService();
export default apiService;
