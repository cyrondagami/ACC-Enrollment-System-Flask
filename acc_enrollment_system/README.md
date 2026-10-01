# ACC Enrollment System

A scalable starter enrollment management system for Asian College of Computer Studies (ACC), built with:

- Python 3.11+
- Flask
- Flask-SQLAlchemy
- SQLite
- Flask-Login
- Flask-WTF (CSRF protection)
- Jinja2 + HTML/CSS
- Werkzeug password hashing

## Features

### RBAC
Three roles are implemented:

- **super_admin** — manage users, enrollment records, and system data
- **admin** — manage enrollment records and view students
- **student** — create and view their own enrollment applications

### Enrollment workflow

`DRAFT -> SUBMITTED -> APPROVED / REJECTED`

A student can create an application and submit it. Admins can approve or reject submitted applications. Rejected applications can be edited and resubmitted.

### Security included

- Password hashing with Werkzeug
- Login session management with Flask-Login
- Role-based authorization decorators
- CSRF protection on POST forms
- Server-side validation
- ORM queries through SQLAlchemy
- Secure HTTP-only session cookies
- SameSite=Lax cookies
- No raw passwords stored in the database
- Audit log for important enrollment/user actions
- Environment-based secret key
- Production mode guidance in configuration

## Project structure

```text
acc_enrollment_system/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── decorators.py
│   ├── models.py
│   ├── auth/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── admin/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── student/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── admin/
│   │   └── student/
│   └── static/
│       └── css/style.css
├── instance/
├── run.py
├── seed.py
├── requirements.txt
└── .env.example
```

## 1. Install Python

Use Python 3.11 or newer.

Check:

```powershell
python --version
```

## 2. Open the project

```powershell
cd C:\path\to\acc_enrollment_system
```

## 3. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 4. Install dependencies

```powershell
pip install -r requirements.txt
```

## 5. Create environment variables

Copy `.env.example` to `.env`.

PowerShell:

```powershell
Copy-Item .env.example .env
```

For a stronger secret key, generate one:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Put the generated value into `.env` as `SECRET_KEY=...`.

## 6. Initialize the database and seed demo accounts

```powershell
python seed.py
```

The script creates the SQLite database and these development accounts:

| Role | Email | Password |
|---|---|---|
| Super Admin | superadmin@acc.local | SuperAdmin123! |
| Admin | admin@acc.local | Admin123! |
| Student | student@acc.local | Student123! |

**Change or delete these demo credentials before using the system for real data.**

## 7. Run the application

```powershell
python run.py
```

Open:

http://127.0.0.1:5000

## 8. Test the RBAC

### Student

Login as:

```text
student@acc.local
Student123!
```

Create an enrollment application and submit it.

### Admin

Login as:

```text
admin@acc.local
Admin123!
```

Open the admin dashboard and approve/reject submitted applications.

### Super Admin

Login as:

```text
superadmin@acc.local
SuperAdmin123!
```

Open User Management to activate/deactivate accounts and change roles.

## Business logic

### Student

1. Register or login.
2. Complete enrollment information.
3. Save as draft.
4. Submit application.
5. Application becomes `SUBMITTED`.
6. Student cannot edit a submitted application unless it is rejected.
7. If rejected, student can edit and resubmit.
8. If approved, application becomes read-only.

### Admin

1. View submitted applications.
2. Review application information.
3. Approve or reject.
4. Add an optional review note.
5. The action is recorded in the audit log.

### Super Admin

Everything an admin can do, plus:

1. Manage user accounts.
2. Activate/deactivate accounts.
3. Change user roles.
4. View audit history.

## Scaling notes

SQLite is appropriate for a school project, prototype, and small deployment. For a larger multi-user production system, move to PostgreSQL/MySQL and add:

- database migrations with Flask-Migrate/Alembic
- reverse proxy such as Nginx
- HTTPS
- production WSGI server such as Gunicorn
- centralized logging
- backups
- email verification/password reset
- rate limiting
- object storage for documents
- stronger audit retention
- automated tests/CI
- pagination and indexes for large datasets

The application is structured with Flask blueprints and an application factory so those changes can be introduced without turning the project into one large file.
