// TaskGrid API Functions
const api = {
    // Get auth token
    getToken() {
        return localStorage.getItem('taskgrid_token');
    },

    // Set auth token
    setToken(token) {
        localStorage.setItem('taskgrid_token', token);
    },

    // Remove auth token
    removeToken() {
        localStorage.removeItem('taskgrid_token');
    },

    // Make API request
    async request(endpoint, options = {}) {
        const url = CONFIG.API_BASE_URL + endpoint;
        const token = this.getToken();
        
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // Add auth token if available
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    },

    // Authentication methods
    async login(credentials) {
        const response = await this.request(CONFIG.ENDPOINTS.AUTH.LOGIN, {
            method: 'POST',
            body: JSON.stringify(credentials)
        });

        if (response.access_token) {
            this.setToken(response.access_token);
        }

        return response;
    },

    async register(userData) {
        const response = await this.request(CONFIG.ENDPOINTS.AUTH.REGISTER, {
            method: 'POST',
            body: JSON.stringify(userData)
        });

        return response;
    },

    async getProfile() {
        return await this.request(CONFIG.ENDPOINTS.AUTH.PROFILE);
    },

    // Data methods
    async getDashboard() {
        return await this.request(CONFIG.ENDPOINTS.DATA.DASHBOARD);
    },

    async getProjects() {
        return await this.request(CONFIG.ENDPOINTS.DATA.PROJECTS);
    },

    async createProject(projectData) {
        return await this.request(CONFIG.ENDPOINTS.DATA.PROJECTS, {
            method: 'POST',
            body: JSON.stringify(projectData)
        });
    },

    async getTasks() {
        return await this.request(CONFIG.ENDPOINTS.DATA.TASKS);
    },

    async createTask(taskData) {
        return await this.request(CONFIG.ENDPOINTS.DATA.TASKS, {
            method: 'POST',
            body: JSON.stringify(taskData)
        });
    },

    async getUsers() {
        return await this.request(CONFIG.ENDPOINTS.DATA.USERS);
    },

    async getWorkLogs() {
        return await this.request(CONFIG.ENDPOINTS.DATA.WORK_LOGS);
    }
};

// Make api globally available
window.api = api;