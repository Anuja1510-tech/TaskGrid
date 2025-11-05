# TaskGrid API Documentation

## Overview
TaskGrid is a Work Log Management System API built with Flask. It provides comprehensive project management, task tracking, and time logging capabilities.

## Base URL
```
http://localhost:5000
```

## Authentication
The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## User Roles
- **admin**: Full system access
- **manager**: Can manage projects and view all data
- **team_member**: Can view assigned projects/tasks and log work

---

## Authentication Endpoints

### POST /auth/register
Register a new user.

**Request Body:**
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe",
    "role": "team_member"
}
```

**Response:**
```json
{
    "message": "User registered successfully",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "team_member",
        "is_active": true,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }
}
```

### POST /auth/login
Login and receive JWT token.

**Request Body:**
```json
{
    "username": "john_doe",
    "password": "password123"
}
```

**Response:**
```json
{
    "message": "Login successful",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "team_member"
    }
}
```

### GET /auth/profile
Get current user profile. (Requires authentication)

### PUT /auth/profile
Update current user profile. (Requires authentication)

### POST /auth/change-password
Change user password. (Requires authentication)

---

## Project Endpoints

### GET /data/projects
Get all projects (filtered by user role).

**Query Parameters:**
- None

**Response:**
```json
{
    "projects": [
        {
            "id": 1,
            "name": "Website Redesign",
            "description": "Complete redesign of company website",
            "status": "active",
            "priority": "high",
            "start_date": "2024-01-01",
            "end_date": "2024-03-01",
            "deadline": "2024-02-28",
            "budget": 10000.0,
            "owner_id": 1,
            "owner_name": "John Manager",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "task_count": 5
        }
    ]
}
```

### POST /data/projects
Create a new project. (Requires manager/admin role)

**Request Body:**
```json
{
    "name": "New Project",
    "description": "Project description",
    "status": "active",
    "priority": "medium",
    "start_date": "2024-01-01",
    "end_date": "2024-06-01",
    "deadline": "2024-05-31",
    "budget": 5000.0
}
```

### GET /data/projects/{project_id}
Get a specific project.

### PUT /data/projects/{project_id}
Update a project. (Requires appropriate permissions)

---

## Task Endpoints

### GET /data/tasks
Get tasks (filtered by permissions).

**Query Parameters:**
- `project_id`: Filter by project ID
- `status`: Filter by task status
- `assigned_to`: Filter by assigned user ID

**Response:**
```json
{
    "tasks": [
        {
            "id": 1,
            "title": "Design Homepage",
            "description": "Create new homepage design",
            "status": "in_progress",
            "priority": "high",
            "estimated_hours": 20.0,
            "start_date": "2024-01-01",
            "due_date": "2024-01-15",
            "completion_date": null,
            "project_id": 1,
            "project_name": "Website Redesign",
            "assigned_to": 2,
            "assignee_name": "Jane Designer",
            "created_by": 1,
            "creator_name": "John Manager",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "total_hours_logged": 8.5
        }
    ]
}
```

### POST /data/tasks
Create a new task.

**Request Body:**
```json
{
    "title": "New Task",
    "description": "Task description",
    "status": "todo",
    "priority": "medium",
    "estimated_hours": 10.0,
    "project_id": 1,
    "assigned_to": 2,
    "start_date": "2024-01-01",
    "due_date": "2024-01-15"
}
```

### PUT /data/tasks/{task_id}
Update a task.

---

## Work Log Endpoints

### GET /data/work-logs
Get work logs.

**Query Parameters:**
- `task_id`: Filter by task ID
- `project_id`: Filter by project ID
- `user_id`: Filter by user ID
- `start_date`: Filter by start date (YYYY-MM-DD)
- `end_date`: Filter by end date (YYYY-MM-DD)

**Response:**
```json
{
    "work_logs": [
        {
            "id": 1,
            "task_id": 1,
            "task_title": "Design Homepage",
            "project_id": 1,
            "project_name": "Website Redesign",
            "user_id": 2,
            "user_name": "Jane Designer",
            "hours_logged": 4.0,
            "work_date": "2024-01-01",
            "start_time": "09:00:00",
            "end_time": "13:00:00",
            "description": "Worked on initial design concepts",
            "is_billable": true,
            "hourly_rate": 75.0,
            "total_cost": 300.0,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
    ]
}
```

### POST /data/work-logs
Create a new work log.

**Request Body:**
```json
{
    "task_id": 1,
    "hours_logged": 4.0,
    "work_date": "2024-01-01",
    "start_time": "09:00:00",
    "end_time": "13:00:00",
    "description": "Worked on task implementation",
    "is_billable": true,
    "hourly_rate": 75.0
}
```

### PUT /data/work-logs/{log_id}
Update a work log.

---

## Dashboard & Analytics Endpoints

### GET /data/dashboard
Get dashboard data with statistics.

**Response:**
```json
{
    "dashboard": {
        "projects": {
            "total": 5,
            "active": 3,
            "completed": 2
        },
        "tasks": {
            "total": 25,
            "completed": 15,
            "in_progress": 8,
            "overdue": 2
        },
        "work_logs": {
            "total_hours": 120.5,
            "this_week_hours": 32.0,
            "total_entries": 45
        },
        "recent_tasks": [...],
        "recent_work_logs": [...]
    }
}
```

### GET /data/reports/time-summary
Get time summary report.

**Query Parameters:**
- `start_date`: Start date for report (YYYY-MM-DD)
- `end_date`: End date for report (YYYY-MM-DD)
- `project_id`: Filter by project ID

---

## User Management Endpoints

### GET /data/users
Get all users. (Requires admin/manager role)

---

## Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or invalid
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Error Response Format

```json
{
    "error": "Error message description"
}
```

## Data Validation

### User Roles
- `admin`, `manager`, `team_member`

### Project/Task Status
- Project: `active`, `completed`, `on_hold`, `cancelled`
- Task: `todo`, `in_progress`, `completed`, `cancelled`

### Priority Levels
- `low`, `medium`, `high`, `urgent`

### Date Formats
- Date: `YYYY-MM-DD`
- Time: `HH:MM:SS`
- DateTime: ISO format

## Default Admin Account
- Username: `admin`
- Password: `admin123`
- Role: `admin`

**Note:** Change the default admin password in production!