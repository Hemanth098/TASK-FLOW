from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Project, Task, project_members
import random

projects_bp = Blueprint('projects', __name__)

PROJECT_COLORS = ['#6366f1', '#ec4899', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ef4444', '#06b6d4', '#84cc16']


@projects_bp.route('/')
@login_required
def index():
    projects = current_user.projects
    return render_template('projects/index.html', projects=projects)


@projects_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        color = request.form.get('color', random.choice(PROJECT_COLORS))

        if not name or len(name) < 2:
            flash('Project name must be at least 2 characters.', 'error')
            return render_template('projects/create.html', colors=PROJECT_COLORS)

        project = Project(
            name=name,
            description=description,
            owner_id=current_user.id,
            color=color
        )
        db.session.add(project)
        db.session.flush()

        # Add creator as admin
        db.session.execute(project_members.insert().values(
            user_id=current_user.id,
            project_id=project.id,
            role='admin'
        ))
        db.session.commit()

        flash(f'Project "{name}" created successfully!', 'success')
        return redirect(url_for('projects.detail', project_id=project.id))

    return render_template('projects/create.html', colors=PROJECT_COLORS)


@projects_bp.route('/<int:project_id>')
@login_required
def detail(project_id):
    project = Project.query.get_or_404(project_id)

    if current_user not in project.members:
        abort(403)

    user_role = current_user.get_role_in_project(project_id)
    members_with_roles = project.get_members_with_roles()
    stats = project.task_stats()

    # Filter tasks based on role
    if user_role == 'admin':
        tasks = Task.query.filter_by(project_id=project_id).order_by(Task.created_at.desc()).all()
    else:
        tasks = Task.query.filter_by(project_id=project_id, assigned_to=current_user.id).all()

    return render_template('projects/detail.html',
                           project=project,
                           tasks=tasks,
                           user_role=user_role,
                           members_with_roles=members_with_roles,
                           stats=stats)


@projects_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(project_id):
    project = Project.query.get_or_404(project_id)

    if current_user not in project.members or not current_user.is_admin_of(project):
        abort(403)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        color = request.form.get('color', project.color)

        if not name or len(name) < 2:
            flash('Project name must be at least 2 characters.', 'error')
            return render_template('projects/edit.html', project=project, colors=PROJECT_COLORS)

        project.name = name
        project.description = description
        project.color = color
        db.session.commit()

        flash('Project updated successfully!', 'success')
        return redirect(url_for('projects.detail', project_id=project.id))

    return render_template('projects/edit.html', project=project, colors=PROJECT_COLORS)


@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
def delete(project_id):
    project = Project.query.get_or_404(project_id)

    if project.owner_id != current_user.id:
        abort(403)

    db.session.delete(project)
    db.session.commit()
    flash(f'Project "{project.name}" deleted.', 'success')
    return redirect(url_for('projects.index'))


@projects_bp.route('/<int:project_id>/add-member', methods=['POST'])
@login_required
def add_member(project_id):
    project = Project.query.get_or_404(project_id)

    if not current_user.is_admin_of(project):
        abort(403)

    email = request.form.get('email', '').strip().lower()
    role = request.form.get('role', 'member')

    if role not in ['admin', 'member']:
        role = 'member'

    user = User.query.filter_by(email=email).first()
    if not user:
        flash(f'No user found with email "{email}".', 'error')
        return redirect(url_for('projects.detail', project_id=project_id))

    if user in project.members:
        flash(f'{user.name} is already a member of this project.', 'warning')
        return redirect(url_for('projects.detail', project_id=project_id))

    db.session.execute(project_members.insert().values(
        user_id=user.id,
        project_id=project.id,
        role=role
    ))
    db.session.commit()
    flash(f'{user.name} added to the project as {role}.', 'success')
    return redirect(url_for('projects.detail', project_id=project_id))


@projects_bp.route('/<int:project_id>/remove-member/<int:user_id>', methods=['POST'])
@login_required
def remove_member(project_id, user_id):
    project = Project.query.get_or_404(project_id)

    if not current_user.is_admin_of(project):
        abort(403)

    if user_id == project.owner_id:
        flash('Cannot remove the project owner.', 'error')
        return redirect(url_for('projects.detail', project_id=project_id))

    user = User.query.get_or_404(user_id)
    db.session.execute(
        project_members.delete().where(
            project_members.c.user_id == user_id,
            project_members.c.project_id == project_id
        )
    )
    db.session.commit()
    flash(f'{user.name} removed from the project.', 'success')
    return redirect(url_for('projects.detail', project_id=project_id))


@projects_bp.route('/<int:project_id>/update-role/<int:user_id>', methods=['POST'])
@login_required
def update_role(project_id, user_id):
    project = Project.query.get_or_404(project_id)

    if not current_user.is_admin_of(project):
        abort(403)

    if user_id == project.owner_id:
        flash('Cannot change the role of the project owner.', 'error')
        return redirect(url_for('projects.detail', project_id=project_id))

    new_role = request.form.get('role', 'member')
    if new_role not in ['admin', 'member']:
        new_role = 'member'

    db.session.execute(
        project_members.update().where(
            project_members.c.user_id == user_id,
            project_members.c.project_id == project_id
        ).values(role=new_role)
    )
    db.session.commit()

    user = User.query.get(user_id)
    flash(f"{user.name}'s role updated to {new_role}.", 'success')
    return redirect(url_for('projects.detail', project_id=project_id))
