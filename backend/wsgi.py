"""
WSGI entry point for The Dreamer's Cave backend.
Used by Gunicorn in production.

Usage:
    gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app

Development:
    flask run
    or
    python wsgi.py
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=5000, debug=True)
