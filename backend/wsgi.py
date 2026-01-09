"""
WSGI entry point for The Dreamer's Cave backend.
Used by Gunicorn in production.

Usage:
    gunicorn -w 4 -b 0.0.0.0:$FLASK_PORT wsgi:app

Development:
    flask run
    or
    python wsgi.py
"""
import os
from app import create_app
from app.config import Config

app = create_app()

if __name__ == '__main__':
    # Development server - read port from config
    port = int(os.environ.get('FLASK_PORT', Config.FLASK_PORT))
    app.run(host='0.0.0.0', port=port, debug=True)
