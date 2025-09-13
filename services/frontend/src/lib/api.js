import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1/analytics';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API service class
export class AnimeAnalyticsAPI {
  // Get database overview stats
  static async getOverviewStats(snapshotType = 'top') {
    try {
      const response = await api.get(
        `/stats/overview?snapshot_type=${snapshotType}`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch overview stats:', error);
      throw error;
    }
  }

  // Get top-rated anime
  static async getTopRatedAnime(limit = 10, snapshotType = 'top') {
    try {
      const response = await api.get(
        `/anime/top-rated?limit=${limit}&snapshot_type=${snapshotType}`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch top rated anime:', error);
      throw error;
    }
  }

  // Get genre distribution
  static async getGenreDistribution(snapshotType = 'top') {
    try {
      const response = await api.get(
        `/anime/genre-distribution?snapshot_type=${snapshotType}`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch genre distribution:', error);
      throw error;
    }
  }

  // Get seasonal trends
  static async getSeasonalTrends() {
    try {
      const response = await api.get('/trends/seasonal');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch seasonal trends:', error);
      throw error;
    }
  }

  // Health check
  static async healthCheck() {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.error('API health check failed:', error);
      throw error;
    }
  }
}

export default AnimeAnalyticsAPI;
