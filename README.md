# BlueThink Employee Portal

A Django-based employee portal for internal company use. It combines a server-rendered portal, an admin/reviewer workflow, and REST APIs with Swagger.

## Simplified Project Structure

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
└── venv/                      # virtual environment



## What this project does

Employees can:
- log in with employee ID and password
- view dashboard and profile
- apply for leave / short leave / work from home
- submit claims with receipt upload
- fill timesheets
- view salary slips, policies, and shared documents
- sign off daily work and log out separately

Reviewers (staff / HR / manager) can:
- open the approval center
- approve or reject leave, short leave, timesheet, claims, and WFH requests
- add remarks

Admins can:
- manage users, projects, salary slips, policies, and documents from Django admin

## Main tech used

- **Django** - main backend framework
- **PostgreSQL** - database
- **Django Templates + CSS + JS** - portal UI
- **Django REST Framework** - APIs
- **drf-spectacular** - Swagger / OpenAPI docs
- **Simple JWT** - JWT auth for API testing

## Project structure

Main apps:
- `accounts` - custom user, portal login/logout
- `dashboard` - employee dashboard
- `profiles` - employee profile details
- `leave_management` - leave and short leave
- `timesheet` - projects and timesheet entries
- `claims` - reimbursement claims and receipts
- `wfh` - work from home requests
- `approvals` - reviewer approval center
- `documents` - salary slips, policies, shared documents
- `attendance` - daily sign off / work log
- `portal_api` - DRF APIs for portal + Swagger

## Authentication

This project uses two auth styles:

### 1. Portal auth
Used by the employee portal UI.
- session login
- session logout
- session sign off

### 2. API auth
Used for Swagger / Postman / external API testing.
- JWT access token
- JWT refresh token

## Main workflow

### Employee side
1. User logs in with employee ID, password, and work mode.
2. Dashboard loads employee data.
3. User performs actions like leave, short leave, claim, timesheet, and WFH.
4. Requests are saved with `pending` status.
5. Reviewer approves or rejects them.
6. Employee sees updated status in history pages.

### Reviewer side
1. Reviewer logs in.
2. Approval center shows pending requests.
3. Reviewer approves/rejects records with remarks.
4. Original request status updates in the database.

### Sign Off vs Log Out
- **Sign Off**: ends the workday, stores first login time, sign off time, and total worked hours for that date.
- **Log Out**: only ends the session.

## API + Swagger

Swagger is available for API testing and docs.

Typical API groups:
- profile
- leave requests
- short leave requests
- timesheet entries
- claims
- WFH requests
- salary slips
- policies
- shared documents
- dashboard summary
- session login / logout / sign off

Swagger path:
- `/api/schema/docs/`

## Portal behavior

The project uses a hybrid approach:
- pages are rendered with Django templates
- many form actions and page data loads use REST APIs through JavaScript `fetch()`
- these requests appear in browser DevTools under **Fetch/XHR**

## Important roles

Custom user fields support business roles:
- `is_staff`
- `is_hr`
- `is_manager`

Used for approval access and reviewer dashboard behavior.

## Running the project

1. Create and activate virtual environment
2. Install dependencies
3. Configure PostgreSQL in `settings.py` or `.env`
4. Run migrations
5. Create superuser
6. Start server

Example:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Main URLs

- Portal login: `/`
- Dashboard: `/dashboard/`
- Django admin: `/admin/`
- Swagger docs: `/api/schema/docs/`

## Summary

BlueThink Employee Portal is a full internal employee management system built with Django. It supports employee self-service, reviewer approvals, admin management, REST APIs, Swagger testing, and daily work sign off tracking.

## NG Rock

Bluthink Portal is also using NG Rock to use a local generated URL, So that Portal is Accessable for 
others too 
```bash
ngrok http 8000
```
Then Url is Ready to use:
https://unvaunting-india-retributively.ngrok-free.dev/