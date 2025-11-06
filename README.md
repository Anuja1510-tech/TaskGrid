# TaskGrid - Work Log Management System

TaskGrid is a comprehensive Work Log Management System designed to help teams organize projects, manage tasks efficiently, and track time through detailed work logs. It centralizes project management and reporting, ensuring better accountability and productivity for individuals and teams.

## 🚀 Features

### Core Features
- **Project Management** – Create and manage multiple projects with clear ownership, deadlines, and progress tracking
- **Task Management** – Assign, prioritize, and monitor tasks within projects
- **Work Logs (Time Tracking)** – Team members can log hours spent on tasks
- **Reporting & Analytics** – Generate insightful reports on tasks, time usage, and team performance
- **User Roles & Permissions** – Different access levels (Admin, Manager, Team Member)
- **Dashboard** – Real-time insights into ongoing projects, pending tasks, and logged work

### Technical Features
- RESTful API built with Flask
- JWT-based authentication
- SQLAlchemy ORM with SQLite database
- Role-based access control
- Comprehensive error handling
- CORS support for frontend integration

## 📁 Project Structure

```
DBMS/
├── backend/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user_model.py          # User database model
│   │   ├── project_model.py       # Project database model
│   │   ├── task_model.py          # Task database model
│   │   └── work_log_model.py      # Work log database model
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py                # Authentication routes
│   │   └── data.py                # Data management routes
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── db.py                  # Database configuration
│   │   ├── validators.py          # Input validation utilities
│   │   └── helpers.py             # Helper functions and decorators
│   ├── app.py                     # Main Flask application
│   ├── requirements.txt           # Python dependencies
│   └── API_DOCUMENTATION.md       # Detailed API documentation
├── database.db                    # SQLite database file
├── frontend/                      # Frontend application (to be implemented)
├── venv/                         # Python virtual environment
└── README.md                     # This file
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd DBMS
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## 🔐 Default Admin Account

When you first run the application, a default admin account is created:
- **Username:** `admin`
- **Password:** `admin123`
- **Role:** `admin`

**⚠️ Important:** Change the default admin password immediately in production!

## 📚 API Usage

### Authentication
1. **Register a new user:**
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe",
    "role": "team_member"
  }'
```

2. **Login to get JWT token:**
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

3. **Use the token for authenticated requests:**
```bash
curl -X GET http://localhost:5000/data/projects \
  -H "Authorization: Bearer <your_jwt_token>"
```

### Example Workflow

1. **Create a Project** (Admin/Manager only):
```bash
curl -X POST http://localhost:5000/data/projects \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Website Redesign",
    "description": "Complete redesign of company website",
    "priority": "high",
    "deadline": "2024-06-01"
  }'
```

2. **Create a Task**:
```bash
curl -X POST http://localhost:5000/data/tasks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Design Homepage",
    "description": "Create new homepage design",
    "project_id": 1,
    "assigned_to": 2,
    "estimated_hours": 20.0,
    "due_date": "2024-01-15"
  }'
```

3. **Log Work Time**:
```bash
curl -X POST http://localhost:5000/data/work-logs \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": 1,
    "hours_logged": 4.0,
    "work_date": "2024-01-01",
    "description": "Worked on initial design concepts",
    "is_billable": true,
    "hourly_rate": 75.0
  }'
```

## 🎯 Use Cases

### Software Development Teams
- Track project deliverables and milestones
- Monitor individual and team productivity
- Generate reports for sprint reviews

### Agencies & Consultancies
- Bill clients based on hours worked
- Track project profitability
- Manage multiple client projects simultaneously

### Corporate Teams
- Monitor internal projects and productivity
- Track resource allocation
- Generate management reports

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the backend directory for production:

```env
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
DATABASE_URL=sqlite:///database.db
FLASK_ENV=production
```

### Database Configuration
The application uses SQLite by default. To use a different database:

1. Update the `SQLALCHEMY_DATABASE_URI` in `utils/db.py`
2. Install the appropriate database driver
3. Update `requirements.txt`

## 📊 API Endpoints Overview

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `GET /auth/profile` - Get user profile
- `PUT /auth/profile` - Update user profile
- `POST /auth/change-password` - Change password

### Projects
- `GET /data/projects` - List projects
- `POST /data/projects` - Create project
- `GET /data/projects/{id}` - Get project details
- `PUT /data/projects/{id}` - Update project

### Tasks
- `GET /data/tasks` - List tasks
- `POST /data/tasks` - Create task
- `PUT /data/tasks/{id}` - Update task

### Work Logs
- `GET /data/work-logs` - List work logs
- `POST /data/work-logs` - Create work log
- `PUT /data/work-logs/{id}` - Update work log

### Analytics
- `GET /data/dashboard` - Dashboard data
- `GET /data/reports/time-summary` - Time summary report

### User Management
- `GET /data/users` - List users (Admin/Manager only)

## 🧪 Testing

### Manual Testing
Use tools like Postman, curl, or any HTTP client to test the API endpoints.

### Health Check
```bash
curl http://localhost:5000/health
```

## 🚀 Deployment

### Production Considerations
1. Change default admin password
2. Use environment variables for secrets
3. Use a production database (PostgreSQL, MySQL)
4. Enable HTTPS
5. Set up proper logging
6. Configure CORS for your frontend domain

### Docker Deployment (Optional)
Create a `Dockerfile` in the backend directory:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Check the API documentation in `backend/API_DOCUMENTATION.md`
- Review the code comments and docstrings
- Create an issue in the repository

## 🔄 Future Enhancements

- Frontend web application
- Mobile app support
- Advanced reporting and analytics
- Integration with external tools (Slack, email notifications)
- File attachments for tasks
- Time tracking with start/stop functionality
- Gantt chart visualization
- Team collaboration features