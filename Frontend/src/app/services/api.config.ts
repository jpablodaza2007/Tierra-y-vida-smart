const PRODUCTION_API_URL = 'https://tierra-vida-api.onrender.com/api/';

export const API_URL =
  window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? '/api/'
    : PRODUCTION_API_URL;
