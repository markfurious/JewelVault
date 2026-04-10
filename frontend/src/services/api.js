/**
 * API Service
 * Handles all HTTP requests to the backend
 */

const API_BASE = '/api/v1';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchApi(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;

  // Get token from localStorage
  const token = localStorage.getItem('access_token');

  const config = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = { detail: `HTTP ${response.status}: ${response.statusText}` };
      }
      // Extract error message from various formats
      let errorMsg = errorData.detail || errorData.message || `HTTP ${response.status}`;
      if (typeof errorMsg !== 'string') {
        errorMsg = JSON.stringify(errorMsg);
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

// ============ Products API ============

export const productsApi = {
  list: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return fetchApi(`/products${queryString ? `?${queryString}` : ''}`);
  },

  get: (id) => fetchApi(`/products/${id}`),

  getBySku: (sku) => fetchApi(`/products/sku/${sku}`),

  create: (data) => fetchApi('/products', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  update: (id, data) => fetchApi(`/products/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),

  delete: (id) => fetchApi(`/products/${id}`, {
    method: 'DELETE',
  }),

  bulkUpload: (file, initialQuantity = 0, initialLocation = null) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('initial_quantity', initialQuantity.toString());
    if (initialLocation) {
      formData.append('initial_location', initialLocation);
    }
    return fetch('/api/v1/products/bulk-upload', {
      method: 'POST',
      body: formData,
    }).then(async (response) => {
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail));
      }
      return response.json();
    });
  },
};

// ============ Inventory API ============

export const inventoryApi = {
  list: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return fetchApi(`/inventory${queryString ? `?${queryString}` : ''}`);
  },

  get: (productId) => fetchApi(`/inventory/${productId}`),

  update: (productId, data) => fetchApi(`/inventory/${productId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),

  adjust: (productId, data) => fetchApi(`/inventory/${productId}/adjust`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  restock: (productId, quantity, notes) =>
    fetchApi(`/inventory/${productId}/restock?quantity=${quantity}${notes ? `&notes=${encodeURIComponent(notes)}` : ''}`, {
      method: 'POST',
    }),

  getTransactions: (productId, params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return fetchApi(`/inventory/${productId}/transactions${queryString ? `?${queryString}` : ''}`);
  },
};

// ============ Sales API ============

export const salesApi = {
  list: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return fetchApi(`/sales${queryString ? `?${queryString}` : ''}`);
  },

  get: (id) => fetchApi(`/sales/${id}`),

  create: (data) => fetchApi('/sales', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  cancel: (id) => fetchApi(`/sales/${id}/cancel`, {
    method: 'POST',
  }),

  requestReturn: (saleId, data) => fetchApi(`/sales/${saleId}/return`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  approveReturn: (returnId) => fetchApi(`/sales/returns/${returnId}/approve`, {
    method: 'POST',
  }),

  rejectReturn: (returnId, data) => fetchApi(`/sales/returns/${returnId}/reject`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  getReturns: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return fetchApi(`/sales/returns${queryString ? `?${queryString}` : ''}`);
  },
};

// ============ Analytics API ============

export const analyticsApi = {
  getReorderSuggestions: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return fetchApi(`/analytics/reorder-suggestions${queryString ? `?${queryString}` : ''}`);
  },

  getSalesVelocity: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return fetchApi(`/analytics/sales-velocity${queryString ? `?${queryString}` : ''}`);
  },

  getInventorySummary: () => fetchApi('/analytics/inventory/summary'),

  getTopProducts: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return fetchApi(`/analytics/top-products${queryString ? `?${queryString}` : ''}`);
  },

  query: (data) => fetchApi('/analytics/query', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
};

// ============ Stock API ============

export const stockApi = {
  list: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return fetchApi(`/stock${queryString ? `?${queryString}` : ''}`);
  },

  get: (id) => fetchApi(`/stock/${id}`),

  getSummary: () => fetchApi('/stock/summary'),

  bulkAction: (action, ids, notes = '') => fetchApi('/stock/action', {
    method: 'POST',
    body: JSON.stringify({ action, ids, notes }),
  }),
};

// ============ Authentication API ============

async function fetchWithAuth(endpoint, options = {}) {
  const token = localStorage.getItem('access_token');
  return fetchApi(endpoint, {
    ...options,
    headers: {
      ...options.headers,
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
  });
}

export const authApi = {
  login: (username, password) => fetchApi('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  }),

  refresh: (refreshToken) => fetchApi('/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  }),

  me: () => fetchWithAuth('/auth/me'),

  register: (userData) => fetchWithAuth('/auth/register', {
    method: 'POST',
    body: JSON.stringify(userData),
  }),

  getUsers: () => fetchWithAuth('/auth/users'),

  getUser: (userId) => fetchWithAuth(`/auth/users/${userId}`),

  updateUser: (userId, userData) => fetchWithAuth(`/auth/users/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(userData),
  }),

  changeUserRole: (userId, role) => fetchWithAuth(`/auth/users/${userId}/role?role=${role}`, {
    method: 'PATCH',
  }),

  toggleUserActive: (userId) => fetchWithAuth(`/auth/users/${userId}/toggle-active`, {
    method: 'PATCH',
  }),

  toggleUserLocked: (userId) => fetchWithAuth(`/auth/users/${userId}/toggle-locked`, {
    method: 'PATCH',
  }),

  deleteUser: (userId) => fetchWithAuth(`/auth/users/${userId}`, {
    method: 'DELETE',
  }),
};

// ============ Companies API ============

export const companiesApi = {
  list: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return fetchApi(`/companies${queryString ? `?${queryString}` : ''}`);
  },

  get: (id) => fetchApi(`/companies/${id}`),

  create: (data) => fetchApi('/companies', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  update: (id, data) => fetchApi(`/companies/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),

  delete: (id) => fetchApi(`/companies/${id}`, {
    method: 'DELETE',
  }),
};

// ============ Jewelry / AR Try-On API ============

export const jewelryApi = {
  list: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return fetchApi(`/jewelry${queryString ? `?${queryString}` : ''}`);
  },

  get: (id) => fetchApi(`/jewelry/${id}`),

  create: (data) => fetchApi('/jewelry', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  update: (id, data) => fetchApi(`/jewelry/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),

  delete: (id) => fetchApi(`/jewelry/${id}`, {
    method: 'DELETE',
  }),

  uploadModel: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetch('/api/v1/jewelry/upload-model', {
      method: 'POST',
      body: formData,
    }).then(async (response) => {
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail));
      }
      return response.json();
    });
  },

  generate3DBatch: () => fetchApi('/jewelry/generate-3d-batch', {
    method: 'POST',
  }),

  check3DGenerator: () => fetchApi('/jewelry/check-3d-generator'),

  uploadExcelAndGenerate: (formData) => {
    return fetch('/api/v1/jewelry/upload-excel-and-generate', {
      method: 'POST',
      body: formData,
    }).then(async (response) => {
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail));
      }
      return response.json();
    });
  },

  logTryOn: (data) => fetchApi('/jewelry/tryon/log', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  getTryOnLogs: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return fetchApi(`/jewelry/tryon/logs${queryString ? `?${queryString}` : ''}`);
  },

  getTryOnStats: (productId) => fetchApi(`/jewelry/tryon/stats${productId ? `?product_id=${productId}` : ''}`),
};
