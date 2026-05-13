from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Task, Project, User, project_members
from datetime import datetime, timezone
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def landing():
    from flask_login import current_user
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


@dashboard_bp.route('/dashboard')
@login_required
def index():
    user_projects = current_user.projects

    # All tasks user can see (assigned or admin)
    all_visible_tasks = []
    for project in user_projects:
        role = current_user.get_role_in_project(project.id)
        if role == 'admin':
            all_visible_tasks.extend(project.tasks)
        else:
            all_visible_tasks.extend([t for t in project.tasks if t.assigned_to == current_user.id])

    # Stats
    total_tasks = len(all_visible_tasks)
    todo_tasks = [t for t in all_visible_tasks if t.status == 'todo']
    in_progress_tasks = [t for t in all_visible_tasks if t.status == 'in_progress']
    done_tasks = [t for t in all_visible_tasks if t.status == 'done']

    now = datetime.now(timezone.utc)
    overdue_tasks = [
        t for t in all_visible_tasks
        if t.due_date and t.status != 'done' and
        t.due_date.replace(tzinfo=timezone.utc) < now
    ]

    # Tasks per user (for admin projects)
    tasks_per_user = {}
    for project in user_projects:
        role = current_user.get_role_in_project(project.id)
        if role == 'admin':
            for task in project.tasks:
                if task.assignee:
                    name = task.assignee.name
                    tasks_per_user[name] = tasks_per_user.get(name, 0) + 1

    # Recent tasks
    recent_tasks = sorted(all_visible_tasks, key=lambda t: t.updated_at or t.created_at, reverse=True)[:10]

    # Project stats
    project_stats = []
    for p in user_projects:
        s = p.task_stats()
        s['project'] = p
        project_stats.append(s)

    return render_template('dashboard/index.html',
                           projects=user_projects,
                           total_tasks=total_tasks,
                           todo_tasks=todo_tasks,
                           in_progress_tasks=in_progress_tasks,
                           done_tasks=done_tasks,
                           overdue_tasks=overdue_tasks,
                           tasks_per_user=tasks_per_user,
                           recent_tasks=recent_tasks,
                           project_stats=project_stats)
