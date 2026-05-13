from app import create_app, db
from app.models import User, Project, Task
import os

app = create_app(os.environ.get('FLASK_ENV', 'default'))

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Project': Project, 'Task': Task}

@app.cli.command('seed')
def seed_db():
    """Seed the database with sample data."""
    from app.models import project_members
    import random
    from datetime import datetime, timedelta

    print("Creating sample data...")

    # Create users
    u1 = User(name='Alice Admin', email='alice@example.com', avatar_color='#6366f1')
    u1.set_password('password123')
    u2 = User(name='Bob Member', email='bob@example.com', avatar_color='#10b981')
    u2.set_password('password123')
    u3 = User(name='Carol Dev', email='carol@example.com', avatar_color='#ec4899')
    u3.set_password('password123')

    db.session.add_all([u1, u2, u3])
    db.session.flush()

    # Create project
    p = Project(name='Website Redesign', description='Redesign the company website Q2 2025', owner_id=u1.id, color='#6366f1')
    db.session.add(p)
    db.session.flush()

    # Add members
    for uid, role in [(u1.id, 'admin'), (u2.id, 'member'), (u3.id, 'member')]:
        db.session.execute(project_members.insert().values(user_id=uid, project_id=p.id, role=role))

    # Create tasks
    tasks_data = [
        ('Design new homepage', 'Create wireframes and mockups', 'done', 'high', u2.id),
        ('Set up CI/CD pipeline', 'Configure GitHub Actions for deployment', 'in_progress', 'urgent', u3.id),
        ('Write API documentation', 'Document all REST endpoints', 'todo', 'medium', u2.id),
        ('Fix login page bug', 'Users getting 500 on mobile', 'in_progress', 'high', u3.id),
        ('Add dark mode', 'Implement system-preference aware dark mode', 'todo', 'low', None),
    ]

    for i, (title, desc, status, priority, assigned) in enumerate(tasks_data):
        t = Task(
            title=title, description=desc, status=status, priority=priority,
            project_id=p.id, created_by=u1.id, assigned_to=assigned,
            due_date=datetime.now() + timedelta(days=i-2)
        )
        db.session.add(t)

    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
