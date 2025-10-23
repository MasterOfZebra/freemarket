// api.js - API integration functions

// Use relative API base so requests go to the same host (nginx will proxy /api/ to backend)
const API_BASE_URL = '/api';

// Submit user profile
export const submitProfile = async (profileData) => {
    try {
        const response = await fetch(`${API_BASE_URL}/profiles`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(profileData),
        });
        if (!response.ok) {
            throw new Error('Failed to submit profile');
        }
        return await response.json();
    } catch (error) {
        console.error('Error submitting profile:', error);
        throw error;
    }
};

// Get user profiles
export const getUserProfiles = async (userId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/profiles/${userId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch profiles');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching profiles:', error);
        throw error;
    }
};

// Get user matches
export const getUserMatches = async (userId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/matches/${userId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch matches');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching matches:', error);
        throw error;
    }
};

// Get user ratings
export const getUserRatings = async (userId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/ratings/${userId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch ratings');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching ratings:', error);
        throw error;
    }
};

// Submit rating
export const submitRating = async (ratingData) => {
    try {
        const response = await fetch(`${API_BASE_URL}/ratings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(ratingData),
        });
        if (!response.ok) {
            throw new Error('Failed to submit rating');
        }
        return await response.json();
    } catch (error) {
        console.error('Error submitting rating:', error);
        throw error;
    }
};

// Market listings (wants/offers)
export const getMarketListings = async (params = {}) => {
    try {
        const qs = new URLSearchParams(params).toString();
        const url = `${API_BASE_URL}/market-listings/${qs ? `?${qs}` : ''}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch market listings');
        return await response.json();
    } catch (error) {
        console.error('Error fetching market listings:', error);
        throw error;
    }
};

export const getWants = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/market-listings/wants/all`);
        if (!response.ok) throw new Error('Failed to fetch wants');
        const data = await response.json();
        // normalize shape expected by UI
        return { listings: data.items || [], total: data.total || 0 };
    } catch (error) {
        console.error('Error fetching wants:', error);
        throw error;
    }
};

export const getOffers = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/market-listings/offers/all`);
        if (!response.ok) throw new Error('Failed to fetch offers');
        const data = await response.json();
        // normalize shape expected by UI
        return { listings: data.items || [], total: data.total || 0 };
    } catch (error) {
        console.error('Error fetching offers:', error);
        throw error;
    }
};
