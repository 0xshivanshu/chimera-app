// src/api/chimeraApi.ts
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

// IMPORTANT: Replace with your computer's actual local network IP address.
const API_BASE_URL = 'http://192.168.137.1:8000'; // e.g., 'http://192.168.1.10:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// We can add an interceptor to automatically add the Chimera API Key
// This is more efficient than adding it to every call.
apiClient.interceptors.request.use(async (config) => {
  // NOTE: In a real app, the API key should be managed more securely.
  config.headers['X-API-Key'] = 'local-testing-key';
  return config;
});

// --- Auth Functions ---

// The fix is to add `: string` after each parameter name.
export const registerUser = (email: string, password: string) => {
  return apiClient.post('/auth/register', {
    email,
    password,
  });
};

// Add `: string` here as well.
export const loginUser = (email: string, password: string) => {
  return apiClient.post('/auth/login', {
    email,
    password,
  });
};

export const onboardLocation = (userId: string, lat: number, lon: number) => {
  return apiClient.post('/v1/onboard/location', {
    user_id: userId,
    lat,
    lon,
  });
};

interface AlertPayload {
  alert_type: string;
  user_id: string;
  event_data: {
    [key: string]: any;
  };
}

export const sendAlert = (payload: AlertPayload) => {
  return apiClient.post('/v1/alert', payload);
};

// --- We will add the other API calls here later ---

export default apiClient;
