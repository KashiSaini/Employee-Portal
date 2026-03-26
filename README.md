# BlueThink Employee Portal

BlueThink Employee Portal is a Django-based internal employee management system that combines:

- server-rendered portal pages
- REST APIs with Swagger / OpenAPI docs
- role-based review workflows
- attendance and sign-off tracking
- generated monthly salary slips
- real-time online status through WebSockets

It is built for employee self-service, reviewer approvals, and admin operations in one project.

## Project Structure

```bash
employee_portal/
│
├── manage.py
├── README.md
├── requirements.txt
│
├── config/                    # project settings, urls, wsgi/asgi
│
├── accounts/                  # authentication
├── profiles/                  # employee profiles
├── dashboard/                 # dashboard views
├── attendance/                # attendance and sign off
├── leave_management/          # leave requests
├── wfh/                       # work from home requests
├── timesheet/                 # timesheet management
├── claims/                    # claims and receipts
├── approvals/                 # approval workflows
├── documents/                 # policies, files, salary slips
├── portal_api/                # DRF and API logic
│
├── templates/                 # HTML templates
│   ├── accounts/
│   ├── approvals/
│   ├── attendance/
│   ├── claims/
│   ├── dashboard/
│   ├── documents/
│   ├── leave_management/
│   ├── profiles/
│   ├── timesheet/
│   └── wfh/
│
├── static/                    # css, js, images
│   ├── css/
│   ├── js/
│   └── images/
│
├── media/                     # uploaded files
│   ├── claims/
│   │   └── receipts/
│   ├── company_documents/
│   ├── policy_documents/
│   └── salary_slips/
│
└── venv/
```

## Core Features

### Employee self-service

- Login with employee ID, password, and work mode
- View dashboard and employee profile
- Apply for leave and short leave
- Submit work-from-home requests
- Fill daily timesheets
- Submit claims with receipt uploads
- Sign off daily work separately from logout
- View salary slips, policies, and company documents

### Review and approval flow

- Pending requests are routed to reviewers
- Reviewers can approve or reject:
  - leave requests
  - short leave requests
  - timesheet entries
  - claims
  - work-from-home requests
- Remarks are stored with the review action
- Team managers only review records for their assigned team

### Salary and holiday management

- Superadmin can set each employee's monthly salary
- Superadmin can generate salary slips for one employee or for all configured employees
- Employees can view only their own visible salary slips
- HR and superadmin can add and delete public holidays
- Salary slips are generated automatically from:
  - approved timesheet days
  - Saturdays and Sundays
  - public holidays
- Overlapping dates are counted once in salary calculations

### Attendance and dashboard

- Daily first login is recorded
- Sign-off stores sign-off time and total work duration
- Dashboard shows employee stats, alerts, recent activity, and pending approvals
- Online presence is exposed through WebSocket updates

### API support

- Session APIs for login, logout, and sign-off
- CRUD APIs for employee requests
- Read-only APIs for salary slips, policies, and company documents
- JWT auth for API testing
- Swagger and ReDoc documentation via `drf-spectacular`

## Roles and Access

The project uses a custom user model with additional portal roles.

### Employee

- Can access only personal records
- Can submit requests and view own history
- Can view own salary slips

### Manager

- Can review pending items only for their assigned team
- Can access team-scoped user management when a team is assigned

### HR

- Can review requests
- Can access user management
- Can manage public holidays

### Superadmin

- Full access to portal management
- Can assign portal roles
- Can manage employee salaries
- Can generate salary slips
- Can access Django admin

## Salary Slip Calculation

Salary slips are generated month-wise using the following rule:

```text
payable days =
    approved timesheet working days
  + weekend days
  + public holidays
```

Rules:

- weekend days are always included
- public holidays are included
- if a public holiday falls on a weekend, it is counted once
- if a timesheet exists on a weekend or public holiday, that date is still counted once
- unpaid days = total days in month - payable days
- net salary = monthly salary * payable days / total days in month

## Tech Stack

- Python 3.14
- Django 6
- Django REST Framework
- PostgreSQL
- Channels + Daphne
- Simple JWT
- drf-spectacular
- Django Templates + custom CSS + JavaScript
- Docker / Docker Compose

## Project Structure Explain

```text
bluethink/
|-- accounts/            Custom user, login, user management, WebSocket routing
|-- approvals/           Approval center and review screens
|-- attendance/          Daily work log and sign-off summary
|-- claims/              Employee reimbursement claims
|-- config/              Django settings, ASGI/WSGI, root URLs
|-- dashboard/           Dashboard views and summaries
|-- documents/           Salary slips, policies, public holidays, company documents
|-- leave_management/    Leave and short leave management
|-- portal_api/          REST API endpoints and serializers
|-- profiles/            Employee profile management
|-- timesheet/           Projects and timesheet entries
|-- wfh/                 Work-from-home requests
|-- templates/           Portal templates
|-- static/              CSS, JS, and images
|-- media/               Uploaded files
|-- manage.py
|-- requirements.txt
|-- docker-compose.yaml
|-- dockerfile
```

## Important URLs

### Portal

- Login: `/`
- Dashboard: `/dashboard/`
- Profile: `/profile/`
- Leaves: `/leave/`
- Timesheet: `/timesheet/`
- Claims: `/claims/`
- WFH: `/wfh/`
- Approvals: `/approvals/`
- Salary slips: `/salary-slips/`
- Salary management: `/salary-slips/manage/`
- Public holidays: `/public-holidays/`
- Policies: `/policies/`
- Company documents: `/documents/`
- Django admin: `/admin/`

### API

- API root: `/api/`
- Swagger UI: `/api/schema/docs/`
- ReDoc: `/api/schema/redoc/`
- Schema: `/api/schema/`
- JWT token: `/api/token/`
- JWT refresh: `/api/token/refresh/`

### WebSocket

- Online status: `/ws/online-status/`

## Environment Variables

The project reads configuration from `.env`.

Required database settings:

```env
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432
```

Common app settings:

```env
SECRET_KEY=your_secret_key
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1
```

Important:

- `DEBUG` must be a boolean-like value such as `true` or `false`
- values like `release` will break Django management commands because `python-decouple` casts `DEBUG` as boolean

## Local Development Setup

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure `.env`

Add your PostgreSQL credentials and app settings.

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Create a superuser

```bash
python manage.py createsuperuser
```

### 6. Start the development server

```bash
python manage.py runserver
```

## Docker Setup

The provided `docker-compose.yaml` starts the Django app container and expects your database settings to come from `.env`.

```bash
docker compose up --build
```

Notes:

- the container runs migrations automatically on startup
- static files are collected automatically
- the default app port is `8000`
- make sure your PostgreSQL database is reachable from the container

## Testing

A dedicated SQLite-based test settings module is included at `config/test_settings.py`.

Run tests with:

```bash
python manage.py test --settings=config.test_settings
```

Example:

```bash
python manage.py test portal_api documents --settings=config.test_settings
```

## Authentication Modes

### Portal authentication

Used by the browser-based employee portal:

- session login
- session logout
- session sign-off

### API authentication

Used for Swagger, Postman, or external API testing:

- JWT access token
- JWT refresh token

## Main Apps Overview

### `accounts`

- Custom `User` model
- Employee-ID login
- Role-based user management
- WebSocket routing for online presence

### `dashboard`

- Dashboard summary
- Alerts and activity feed
- Online user widget

### `profiles`

- Employee personal and professional profile data

### `attendance`

- Daily work logs
- First login and sign-off tracking

### `leave_management`

- Leave requests
- Short leave requests

### `timesheet`

- Projects
- Employee timesheet entries
- Approval-based status flow

### `claims`

- Employee claims
- Receipt uploads

### `wfh`

- Work-from-home request flow

### `approvals`

- Unified reviewer dashboard
- Approve/reject screens with remarks

### `documents`

- Generated salary slips
- Employee salary configuration
- Public holiday management
- Policy documents
- Shared company documents

### `portal_api`

- API endpoints for portal features
- serializers and request validation
- dashboard/session/user management APIs

## Optional ngrok Usage

If you want to expose your local app temporarily:

```bash
ngrok http 8000
```

The project already includes trusted origin support for `ngrok-free.dev` and `ngrok-free.app`.

## Summary

BlueThink Employee Portal is a full internal employee portal built on Django with employee workflows, reviewer approvals, attendance tracking, documents, APIs, WebSockets, and generated salary slips based on approved work records and holidays.
