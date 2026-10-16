"""
Domain models for The Dreamer's Cave.

Each model wraps a single database table and exposes the queries that the
service / route layers need. mysql-connector-python is the only DB driver --
no SQLAlchemy (per CLAUDE.md hard rule).
"""
