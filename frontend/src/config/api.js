// API configuration for the application
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// API endpoints
export const API_ENDPOINTS = {
  // Missing persons
  REPORT_MISSING: `${API_BASE_URL}/api/report-missing`,
  GET_MISSING_PERSONS: `${API_BASE_URL}/api/missing-persons`,
  
  // Found persons
  REPORT_FOUND: `${API_BASE_URL}/api/report-found`,
  GET_FOUND_PERSONS: `${API_BASE_URL}/api/found-persons`,
  // Video-based found reporting
  REPORT_FOUND_VIDEO: `${API_BASE_URL}/api/report-found-video`,
  UPLOAD_VIDEO: `${API_BASE_URL}/upload-video`,
  PROCESS_VIDEO: `${API_BASE_URL}/process-video`,
  
  // Matches
  GET_MATCHES: `${API_BASE_URL}/api/matches`,
  UPDATE_MATCH: (matchId) => `${API_BASE_URL}/api/matches/${matchId}`,
  
  // Reports
  GET_ALL_REPORTS: `${API_BASE_URL}/api/reports`,
  // Aggregated results alias
  RESULTS: `${API_BASE_URL}/results`,
  
  // Geocoding
  GEOCODE: `${API_BASE_URL}/api/geocode`,
  REVERSE_GEOCODE: `${API_BASE_URL}/api/reverse-geocode`,
};

// Google Maps configuration
export const GOOGLE_MAPS_CONFIG = {
  API_KEY: process.env.REACT_APP_GOOGLE_MAPS_API_KEY || '',
  DEFAULT_CENTER: { lat: 40.7128, lng: -74.0060 },
  DEFAULT_ZOOM: 10,
};

export default API_BASE_URL;
