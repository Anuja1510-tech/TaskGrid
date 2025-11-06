// TaskGrid Configuration
const CONFIG = {
    API_BASE_URL: 'https://taskgrid-yd65.onrender.com',
    APP_NAME: 'TaskGrid',
    VERSION: '1.0.0',
    STORAGE_PREFIX: 'taskgrid_',
    
    // API Endpoints
    ENDPOINTS: {
        AUTH: {
            LOGIN: '/auth/login',
            REGISTER: '/auth/register',
            PROFILE: '/auth/profile'
        },
        DATA: {
            DASHBOARD: '/data/dashboard',
            PROJECTS: '/data/projects',
            TASKS: '/data/tasks',
            USERS: '/data/users',
            WORK_LOGS: '/data/work-logs'
        }
    },
    
    // UI Settings
    UI: {
        TOAST_DURATION: 5000,
        ANIMATION_DURATION: 300,
        DEBOUNCE_DELAY: 500
    }
};

// Make config globally available
window.CONFIG = CONFIG;