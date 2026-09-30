/**
 * Centralized API client for AI Resume Analyzer.
 * Handles token storage, auth headers, and response parsing.
 */
const API_BASE_URL = window.location.origin;

class ApiClient {
  constructor() {
    this.tokenKey = "ai_resume_token";
    this.userKey = "ai_resume_user";
  }

  getToken() {
    return localStorage.getItem(this.tokenKey);
  }

  setToken(token) {
    localStorage.setItem(this.tokenKey, token);
  }

  getUser() {
    const u = localStorage.getItem(this.userKey);
    return u ? JSON.parse(u) : null;
  }

  setUser(user) {
    localStorage.setItem(this.userKey, JSON.stringify(user));
  }

  clearAuth() {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
  }

  getHeaders(isMultipart = false) {
    const headers = {};
    if (!isMultipart) {
      headers["Content-Type"] = "application/json";
    }
    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = options.isMultipart
      ? this.getHeaders(true)
      : { ...this.getHeaders(false), ...(options.headers || {}) };

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorDetail = data.detail || response.statusText || "Request failed";
        const err = new Error(errorDetail);
        err.status = response.status;
        err.detail = errorDetail;
        throw err;
      }

      return data;
    } catch (err) {
      // If 401 Unauthorized, prompt auth session refresh if needed
      if (err.status === 401) {
        console.warn("Session expired or unauthorized.");
      }
      throw err;
    }
  }

  get(endpoint) {
    return this.request(endpoint, { method: "GET" });
  }

  post(endpoint, data) {
    return this.request(endpoint, {
      method: "POST",
      body: JSON.stringify(data)
    });
  }

  put(endpoint, data) {
    return this.request(endpoint, {
      method: "PUT",
      body: JSON.stringify(data)
    });
  }

  delete(endpoint) {
    return this.request(endpoint, { method: "DELETE" });
  }

  upload(endpoint, file) {
    const formData = new FormData();
    formData.append("file", file);
    return this.request(endpoint, {
      method: "POST",
      body: formData,
      isMultipart: true
    });
  }
}

const api = new ApiClient();
