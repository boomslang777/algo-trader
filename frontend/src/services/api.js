import axios from 'axios';

const BASE_URL = 'http://your-aws-ip:8000';

export const api = {
  getSettings: async () => {
    const response = await axios.get(`${BASE_URL}/api/settings`);
    return response.data;
  },
  
  updateSettings: async (settings) => {
    const response = await axios.post(`${BASE_URL}/api/settings`, settings);
    return response.data;
  },
  
  getPositions: async () => {
    const response = await axios.get(`${BASE_URL}/api/positions`);
    return response.data;
  },
  
  getOrders: async () => {
    const response = await axios.get(`${BASE_URL}/api/orders`);
    return response.data;
  },
  
  closePosition: async (data) => {
    const response = await axios.post(`${BASE_URL}/api/close-position`, data);
    return response.data;
  },
  
  cancelOrder: async (data) => {
    const response = await axios.post(`${BASE_URL}/api/cancel-order`, data);
    return response.data;
  },
  
  getSpyPrice: async () => {
    const response = await axios.get(`${BASE_URL}/api/spy-price`);
    return response.data;
  },

  sendSignal: async (signal) => {
    const response = await axios.post(`${BASE_URL}/api/signal`, signal);
    return response.data;
  }
}; 