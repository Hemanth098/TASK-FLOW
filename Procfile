web: python -c "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all()" && gunicorn run:app --bind 0.0.0.0:$PORT --workers 4 --threads 4 --timeout 120
