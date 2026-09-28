/**
 * EcoGreen Centralized API Client Wrapper
 * Automatically manages JWT authorization headers and standard JSON requests.
 */

const API = {
    getToken() {
        return localStorage.getItem('access_token');
    },

    setToken(token) {
        if (token) {
            localStorage.setItem('access_token', token);
        } else {
            localStorage.removeItem('access_token');
        }
    },

    getHeaders(extraHeaders = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...extraHeaders
        };
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        return headers;
    },

    async request(url, options = {}) {
        const config = {
            method: options.method || 'GET',
            headers: this.getHeaders(options.headers),
            ...options
        };

        if (options.body && typeof options.body === 'object') {
            config.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(data.message || data.error || `HTTP error! status: ${response.status}`);
            }
            return data;
        } catch (error) {
            console.error(`API Error [${options.method || 'GET'} ${url}]:`, error);
            throw error;
        }
    },

    get(url, headers = {}) {
        return this.request(url, { method: 'GET', headers });
    },

    post(url, body, headers = {}) {
        return this.request(url, { method: 'POST', body, headers });
    },

    put(url, body, headers = {}) {
        return this.request(url, { method: 'PUT', body, headers });
    },

    delete(url, headers = {}) {
        return this.request(url, { method: 'DELETE', headers });
    }
};

window.API = API;
