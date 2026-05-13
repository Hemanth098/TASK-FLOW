from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Project, Task, project_members
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__)


def get_project_or_403(project_id):
    project = Project.query.get_or_404(project_id)
    if current_user not in project.members:
        abort(403)
    return project


@tasks_bp.route('/project/<int:project_id>/create', methods=['GET', 'POST'])
@login_required
def create(project_id):
    project = get_project_or_403(project_id)
    user_role = current_user.get_role_in_project(project_id)

    if user_role != 'admin':
        flash('Only admins can create tasks.', 'error')
        return redirect(url_for('projects.detail', project_id=project_id))

    members = project.get_members_with_roles()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'medium')
        status = request.form.get('status', 'todo')
        assigned_to = request.form.get('assigned_to')
        due_date_str = request.form.get('due_date', '')

        errors = []
        if not title or len(title) < 2:
            errors.append('Task title must be at least 2 characters.')
        if priority not in Task.PRIORITY_CHOICES:
            errors.append('Invalid priority.')
        if status not in Task.STATUS_CHOICES:
            errors.append('Invalid status.')

        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                errors.append('Invalid date format.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('tasks/create.html', project=project, members=members,
                                   priorities=Task.PRIORITY_CHOICES, statuses=Task.STATUS_CHOICES)

        task = Task(
            title=title,
            description=description,
            priority=priority,
            status=status,
            due_date=due_date,
            project_id=project_id,
            created_by=current_user.id,
            assigned_to=int(assigned_to) if assigned_to else None
        )
        db.session.add(task)
        db.session.commit()

        flash(f'Task "{title}" created!', 'success')
        return redirect(url_for('projects.detail', project_id=project_id))

    return render_template('tasks/create.html', project=project, members=members,
                           priorities=Task.PRIORITY_CHOICES, statuses=Task.STATUS_CHOICES)


@tasks_bp.route('/<int:task_id>')
@login_required
def detail(task_id):
    task = Task.query.get_or_404(task_id)
    project = get_project_or_403(task.project_id)
    user_role = current_user.get_role_in_project(task.project_id)

    # Members can only view their assigned tasks
    if user_role != 'admin' and task.assigned_to != current_user.id:
        abort(403)

    return render_template('tasks/detail.html', task=task, project=project, user_role=user_role)


@tasks_bp.route('/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(task_id):
    task = Task.query.get_or_404(task_id)
    project = get_project_or_403(task.project_id)
    user_role = current_user.get_role_in_project(task.project_id)

    # Members can only update status of their assigned tasks
    if user_role != 'admin' and task.assigned_to != current_user.id:
        abort(403)

    members = project.get_members_with_roles()

    if request.method == 'POST':
        status = request.form.get('status', task.status)

        if user_role == 'admin':
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            priority = request.form.get('priority', task.priority)
            assigned_to = request.form.get('assigned_to')
            due_date_str = request.form.get('due_date', '')

            if not title or len(title) < 2:
                flash('Task title must be at least 2 characters.', 'error')
                return render_template('tasks/edit.html', task=task, project=project,
                                       members=members, priorities=Task.PRIORITY_CHOICES,
                                       statuses=Task.STATUS_CHOICES, user_role=user_role)

            task.title = title
            task.description = description
            task.priority = priority
            task.assigned_to = int(assigned_to) if assigned_to else None

            if due_date_str:
                try:
                    task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                except ValueError:
                    flash('Invalid date format.', 'error')
                    return render_template('tasks/edit.html', task=task, project=project,
                                           members=members, priorities=Task.PRIORITY_CHOICES,
                                           statuses=Task.STATUS_CHOICES, user_role=user_role)
            else:
                task.due_date = None

        if status in Task.STATUS_CHOICES:
            task.status = status

        task.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('projects.detail', project_id=task.project_id))

    return render_template('tasks/edit.html', task=task, project=project,
                           members=members, priorities=Task.PRIORITY_CHOICES,
                           statuses=Task.STATUS_CHOICES, user_role=user_role)


@tasks_bp.route('/<int:task_id>/update-status', methods=['POST'])
@login_required
def update_status(task_id):
    task = Task.query.get_or_404(task_id)
    get_project_or_403(task.project_id)
    user_role = current_user.get_role_in_project(task.project_id)

    if user_role != 'admin' and task.assigned_to != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403

    status = request.json.get('status')
    if status not in Task.STATUS_CHOICES:
        return jsonify({'error': 'Invalid status'}), 400

    task.status = status
    task.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True, 'status': status})


@tasks_bp.route('/<int:task_id>/delete', methods=['POST'])
@login_required
def delete(task_id):
    task = Task.query.get_or_404(task_id)
    project_id = task.project_id
    get_project_or_403(project_id)
    user_role = current_user.get_role_in_project(project_id)

    if user_role != 'admin':
        abort(403)

    db.session.delete(task)
    db.session.commit()
    flash('Task deleted.', 'success')
    return redirect(url_for('projects.detail', project_id=project_id))
