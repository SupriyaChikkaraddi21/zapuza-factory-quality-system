# Factory Operations & Quality Control System

A full-stack web application for managing factory production batches, quality inspections, manufacturing workflows, supervisor approvals, and audit history.

Developed as part of the **Python Django Developer Intern assessment for Zapuza Technologies LLP**.

## Overview

The Factory Operations & Quality Control System helps track production batches through manufacturing stages while enforcing quality checks and controlled workflow transitions.

The system provides a centralized interface for monitoring batch status, recording inspection measurements, reviewing quality results, and tracking important workflow actions.

## Features

### Production Management
- Create and track production batches.
- Monitor the current manufacturing stage and batch status.
- Track batches through the production lifecycle.
- Support batch hold, release, rejection, and completion workflows.

### Quality Control
- Record quality inspection parameters and measurement limits.
- Enter measured values and automatically evaluate results.
- Determine PASS or FAIL based on configured tolerance limits.
- Track pending, approved, and rejected inspection reviews.

### Workflow Management
- Control batch progression through manufacturing stages.
- Prevent progression when required quality checks are incomplete or unsuccessful.
- Support supervisor review and approval of inspections.
- Record reasons for workflow actions.

### Audit Trail
- Record important workflow and inspection-review actions.
- Capture contextual information for traceability.
- Protect existing audit records against ordinary application-level modification and deletion.

### Dashboard
- View production and inspection summaries.
- Monitor batch statuses and quality results.
- Access production, inspection, workflow, and supervisor-review sections.

## Manufacturing Workflow

The application models the following production stages:

1. Raw Material
2. Machining
3. Heat Treatment
4. Grinding
5. Final Inspection
6. Packing
7. Dispatched

Batch progression is controlled by workflow rules and the applicable quality-inspection requirements.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Django |
| API | Django REST Framework |
| Authentication | Django REST Framework Token Authentication |
| Frontend | React, Vite |
| Styling | CSS |
| Database | SQLite for local development |
| Testing | Django automated tests |
| Version Control | Git and GitHub |

## Project Structure

```text
zapuza-quality-system/
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── production/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── migrations/
├── inspections/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── migrations/
├── workflow/
│   ├── models.py
│   ├── services.py
│   ├── views.py
│   ├── tests.py
│   └── migrations/
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── api.js
│   │   └── main.jsx
│   ├── package.json
│   └── package-lock.json
├── manage.py
├── .gitignore
└── README.md
```

## Prerequisites

Install the following before running the project:

- Python 3.14 or a compatible Python version
- Node.js and npm
- Git

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/SupriyaChikkaraddi21/zapuza-factory-quality-system.git
cd zapuza-factory-quality-system
```

### 2. Set up the backend

Create and activate a virtual environment.

**Windows PowerShell:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```bat
venv\Scripts\activate.bat
```

Install the backend dependencies:

```bash
pip install -r requirements.txt
```

Apply database migrations:

```bash
python manage.py migrate
```

Create an administrator account:

```bash
python manage.py createsuperuser
```

Start the Django development server:

```bash
python manage.py runserver
```

Backend URL: `http://127.0.0.1:8000/`

Django administration: `http://127.0.0.1:8000/admin/`

### 3. Set up the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173/`

Keep both development servers running while using the application.

## API Endpoints

The backend exposes REST API endpoints for production, inspections, workflow actions, and authentication.

| Endpoint | Purpose |
|---|---|
| `/api/production/batches/` | List and create production batches |
| `/api/quality/inspections/` | List and create quality inspections |
| `/api/quality/inspections/<id>/measurement/` | Record an inspection measurement |
| `/api/workflow/batches/<id>/advance/` | Advance a production batch |
| `/api/workflow/inspections/<id>/review/` | Review an inspection |
| `/api/auth/login/` | Authenticate a user |

Additional workflow actions support batch hold, release, and rejection.

Authenticated API requests use the configured authentication mechanism. Consult the URL configuration and view implementations for the exact request formats and permission requirements.

## Running Tests

From the project root, activate the virtual environment and run:

```bash
python manage.py check
python manage.py test
```

The current development test suite contains **16 workflow tests**, which passed during development.

## Security Notes

- The local SQLite database and Python virtual environment are excluded from version control.
- Keep production secret keys and credentials out of source control.
- Configure `DJANGO_SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` appropriately before production deployment.
- Review authentication, role-based permissions, and audit-trail controls before exposing the application publicly.

## Current Status

The application is under development. The backend workflow tests pass, and the React frontend is connected to the Django API for local development.

Production deployment, environment-specific configuration, and additional hardening should be completed before using the application in a real factory environment.

## Author

**Supriya Chikkaraddi**

Computer Science and Engineering

GitHub: [SupriyaChikkaraddi21](https://github.com/SupriyaChikkaraddi21)

## License

No license has been specified yet. Contact the repository owner for permission to reuse or distribute this project.
