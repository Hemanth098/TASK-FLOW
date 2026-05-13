from app import db, bcrypt
from flask_login import UserMixin
from datetime import datetime, timezone

# Association table for project members
project_members = db.Table('project_members',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id'), primary_key=True),
    db.Column('role', db.String(20), default='member'),  # 'admin' or 'member'
    db.Column('joined_at', db.DateTime, default=lambda: datetime.now(timezone.utc))
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    avatar_color = db.Column(db.String(7), default='#6366f1')

    # Relationships
    owned_projects = db.relationship('Project', backref='owner', lazy=True, foreign_keys='Project.owner_id')
    projects = db.relationship('Project', secondary=project_members, lazy='subquery',
                               backref=db.backref('members', lazy=True))
    assigned_tasks = db.relationship('Task', backref='assignee', lazy=True, foreign_keys='Task.assigned_to')
    created_tasks = db.relationship('Task', backref='creator', lazy=True, foreign_keys='Task.created_by')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_role_in_project(self, project_id):
        result = db.session.execute(
            db.select(project_members.c.role).where(
                project_members.c.user_id == self.id,
                project_members.c.project_id == project_id
            )
        ).first()
        return result[0] if result else None

    def is_admin_of(self, project):
        return self.get_role_in_project(project.id) == 'admin'

    def __repr__(self):
        return f'<User {self.email}>'


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    color = db.Column(db.String(7), default='#6366f1')

    # Relationships
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')

    def get_member_role(self, user_id):
        result = db.session.execute(
            db.select(project_members.c.role).where(
                project_members.c.user_id == user_id,
                project_members.c.project_id == self.id
            )
        ).first()
        return result[0] if result else None

    def get_members_with_roles(self):
        result = db.session.execute(
            db.select(User, project_members.c.role).join(
                project_members, User.id == project_members.c.user_id
            ).where(project_members.c.project_id == self.id)
        ).all()
        return [(user, role) for user, role in result]

    def task_stats(self):
        total = len(self.tasks)
        todo = sum(1 for t in self.tasks if t.status == 'todo')
        in_progress = sum(1 for t in self.tasks if t.status == 'in_progress')
        done = sum(1 for t in self.tasks if t.status == 'done')
        now = datetime.now(timezone.utc)
        overdue = sum(1 for t in self.tasks if t.due_date and t.due_date.replace(tzinfo=timezone.utc) < now and t.status != 'done')
        return {'total': total, 'todo': todo, 'in_progress': in_progress, 'done': done, 'overdue': overdue}

    def __repr__(self):
        return f'<Project {self.name}>'


class Task(db.Model):
    __tablename__ = 'tasks'

    STATUS_CHOICES = ['todo', 'in_progress', 'done']
    PRIORITY_CHOICES = ['low', 'medium', 'high', 'urgent']

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='todo')
    priority = db.Column(db.String(20), default='medium')
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @property
    def is_overdue(self):
        if self.due_date and self.status != 'done':
            now = datetime.now(timezone.utc)
            due = self.due_date.replace(tzinfo=timezone.utc) if self.due_date.tzinfo is None else self.due_date
            return due < now
        return False

    @property
    def priority_order(self):
        order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        return order.get(self.priority, 2)

    def __repr__(self):
        return f'<Task {self.title}>'
