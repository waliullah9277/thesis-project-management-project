# University Project and Thesis Management System - Backend

A RESTful backend for the **University Project and Thesis Management System** developed using **Django** and **Django REST Framework**. The system provides secure authentication and role-based APIs for managing university projects, theses, viva schedules, evaluations, industrial training, notices, and notifications.

## Features

### Authentication

* JWT Authentication
* Role-based Authorization
* Login
* Logout
* Profile API
* Change Password
* First Login Password Change

### User Management

* Create Student
* Create Supervisor
* Create Examiner
* Activate/Deactivate Users
* User Profile Management

### Project Management

* Team Creation
* Project/Thesis Submission
* Assign Supervisor
* Update Project Status
* View Assigned Projects
* Supervisor Feedback

### Progress Report

* Submit Weekly Progress Reports
* Supervisor Review
* Review Status Tracking

### Viva Management

* Create Viva Schedule
* Assign Examiner
* Update Viva Status
* View Assigned Viva

### Evaluation

* Submit Evaluation Marks
* Publish Results
* Student Result API

### Industrial Training

* Company Management
* Student Training Submission
* Assign Supervisor
* Training Feedback
* Training Status Update

### Notice & Notification

* Publish Notices
* Role-based Notice Distribution
* Personal Notifications
* Mark Notification as Read

### Dashboard APIs

* Super Admin Dashboard
* Student Dashboard
* Supervisor Dashboard
* Examiner Dashboard

---

## Technology Stack

* Python 3
* Django
* Django REST Framework
* Simple JWT
* SQLite (Development)
* PostgreSQL (Production Ready)

---

## Project Structure

```text
backend/
│
├── accounts/
├── dashboard/
├── projects/
├── reports/
├── viva/
├── evaluation/
├── training/
├── notifications/
├── config/
├── manage.py
└── requirements.txt
```

---

## Installation

Clone the repository

```bash
git clone <repository-url>
```

Move into the project

```bash
cd backend
```

Create virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Apply migrations

```bash
python manage.py migrate
```

Create Superuser

```bash
python manage.py createsuperuser
```

Run the development server

```bash
python manage.py runserver
```

Backend URL

```text
http://127.0.0.1:8000/
```

---

## API Modules

* Authentication
* Dashboard
* User Management
* Team Management
* Project Management
* Progress Reports
* Viva Management
* Evaluation
* Industrial Training
* Notice Management
* Notification System

---

## Authentication

The backend uses **JWT Authentication**.

Protected endpoints require:

```text
Authorization: Bearer <access_token>
```

---

## User Roles

* SUPER_ADMIN
* STUDENT
* SUPERVISOR
* EXAMINER

Each API is protected with custom role-based permissions.

---

## Main API Endpoints

### Authentication

* Login
* Logout
* Profile
* Change Password

### Dashboard

* Super Admin Dashboard
* Student Dashboard
* Supervisor Dashboard
* Examiner Dashboard

### Users

* Create User
* User List
* Update User Status

### Projects

* Team APIs
* Project APIs
* Supervisor Assignment
* Feedback APIs

### Reports

* Submit Report
* Review Report

### Viva

* Schedule Viva
* Assign Examiner
* Update Viva Status

### Evaluation

* Submit Evaluation
* Publish Result
* Student Result

### Industrial Training

* Company Management
* Student Training
* Supervisor Assignment
* Feedback

### Notice

* Create Notice
* View Notices

### Notification

* User Notifications
* Mark Notification as Read

---

## Security Features

* JWT Authentication
* Role-based Access Control
* Custom Permissions
* Password Hashing
* Protected APIs
* Authenticated CRUD Operations

---

## Future Improvements

* Email Verification
* Forgot Password with OTP
* Super Admin Registration
* File Uploads
* API Documentation (Swagger)
* Docker Support
* CI/CD Pipeline
* Automated Testing

---

## Project Status

The backend is feature-complete with all core modules implemented. Remaining work includes deployment, documentation improvements, and optional advanced features.

---

## Developed By

**Waliullah**

Department of Computer Science and Engineering (CSE)

Green University of Bangladesh
