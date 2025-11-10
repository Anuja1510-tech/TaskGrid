// D:\DBMS\frontend\all_frontend\DBMS-CP\js\config.js

const CONFIG = {
  API_BASE_URL: 'https://taskgrid-yd65.onrender.com',
  APP_NAME: 'TaskGrid',
  VERSION: '1.0.0',
  STORAGE_PREFIX: 'taskgrid_',
  
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
  }

};
window.CONFIG = CONFIG;
