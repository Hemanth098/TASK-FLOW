# TaskFlow — Team Task Manager

A full-stack collaborative task management web application built with **Flask**, **SQLAlchemy**, and a polished dark-mode UI. Teams can create projects, assign tasks, and track progress with role-based access control.

---

## Live Demo

> **Deploy URL**: *(fill in after Railway deployment)*
> **Demo credentials**:
> - Admin: `alice@example.com` / `password123`
> - Member: `bob@example.com` / `password123`
> - Member: `carol@example.com` / `password123`

---

## Features

### Authentication
- Signup with Name, Email, Password (bcrypt-hashed)
- Session-based login with Flask-Login (optional "remember me")
- Profile management + password change

### Project Management
- Create projects (creator auto-assigned as Admin)
- Admin: add/remove members, change roles (Admin ↔ Member)
- Color-coded projects with progress tracking

### Task Management
- Create tasks with Title, Description, Priority, Due Date, Status, Assignee
- **Priorities**: Low, Medium, High, Urgent
- **Statuses**: To Do, In Progress, Done
- Overdue detection with visual alerts

### Dashboard
- Total tasks, In Progress, Done, Overdue counters
- Tasks per team member breakdown
- Recent tasks feed
- Per-project progress bars

### Role-Based Access
| Feature | Admin | Member |
|---|---|---|
| Create tasks | ✅ | ❌ |
| Delete tasks | ✅ | ❌ |
| Edit full task | ✅ | ❌ |
| Update own task status | ✅ | ✅ |
| Add/remove members | ✅ | ❌ |
| View all project tasks | ✅ | ❌ |
| View assigned tasks | ✅ | ✅ |

### Views
- **List View** — sortable task rows with priority/status badges
- **Board View** — Kanban-style 3-column layout (To Do / In Progress / Done)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask 3.0, Python 3.11+ |
| ORM | SQLAlchemy + Flask-Migrate |
| Auth | Flask-Login + Flask-Bcrypt |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Frontend | Jinja2 templates, Vanilla CSS/JS |
| Server | Gunicorn |
| Deploy | Railway |

---

## Project Structure

```
task-manager/
├── app/
│   ├── __init__.py          # App factory
│   ├── models.py            # User, Project, Task models
│   ├── routes/
│   │   ├── auth.py          # Signup, login, logout, profile
│   │   ├── projects.py      # CRUD + member management
│   │   ├── tasks.py         # CRUD + status updates
│   │   └── dashboard.py     # Analytics dashboard
│   └── templates/
│       ├── base.html        # Shared layout + design system
│       ├── auth/            # login, signup, profile
│       ├── projects/        # index, detail, create, edit
│       ├── tasks/           # create, edit
│       └── dashboard/       # index
├── config.py                # Dev/Prod config classes
├── run.py                   # Entry point + CLI commands
├── requirements.txt
├── Procfile                 # Railway/Heroku deployment
└── .env.example
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- pip

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/your-username/task-manager.git
cd task-manager

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your values

# 5. Initialize the database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 6. (Optional) Seed with sample data
flask seed

# 7. Run the development server
python run.py
```

Visit: [http://localhost:5000](http://localhost:5000)

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Flask session secret | `dev-secret-key` |
| `JWT_SECRET_KEY` | JWT signing key | `jwt-secret` |
| `DATABASE_URL` | Database connection string | `sqlite:///taskmanager.db` |
| `FLASK_ENV` | `development` or `production` | `development` |

---

## Deployment on Railway

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/task-manager.git
git push -u origin main
```
---

## Database Schema

```
Users
├── id, name, email, password_hash
├── avatar_color, created_at
└── → projects (many-to-many via project_members)

Projects
├── id, name, description, color
├── owner_id (FK → users)
└── → tasks (one-to-many)

project_members (junction table)
├── user_id (FK), project_id (FK)
└── role ('admin' | 'member')

Tasks
├── id, title, description
├── status ('todo' | 'in_progress' | 'done')
├── priority ('low' | 'medium' | 'high' | 'urgent')
├── due_date, created_at, updated_at
├── project_id (FK), assigned_to (FK), created_by (FK)
```

---

## API Endpoints

| Method | URL | Description | Auth |
|---|---|---|---|
| GET/POST | `/auth/signup` | Create account | — |
| GET/POST | `/auth/login` | Sign in | — |
| GET | `/auth/logout` | Sign out | ✅ |
| GET/POST | `/auth/profile` | View/edit profile | ✅ |
| GET | `/` | Redirect to dashboard | ✅ |
| GET | `/dashboard` | Analytics dashboard | ✅ |
| GET | `/projects/` | List user's projects | ✅ |
| GET/POST | `/projects/create` | Create project | ✅ |
| GET | `/projects/<id>` | Project detail + tasks | ✅ |
| GET/POST | `/projects/<id>/edit` | Edit project | Admin |
| POST | `/projects/<id>/delete` | Delete project | Owner |
| POST | `/projects/<id>/add-member` | Add member | Admin |
| POST | `/projects/<id>/remove-member/<uid>` | Remove member | Admin |
| POST | `/projects/<id>/update-role/<uid>` | Change member role | Admin |
| GET/POST | `/tasks/project/<id>/create` | Create task | Admin |
| GET | `/tasks/<id>` | Task detail | ✅ |
| GET/POST | `/tasks/<id>/edit` | Edit task | ✅ |
| POST | `/tasks/<id>/update-status` | Update status (JSON) | ✅ |
| POST | `/tasks/<id>/delete` | Delete task | Admin |

---

