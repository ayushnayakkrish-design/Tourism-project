"""
Root conftest.py — configures test environment.

Sets ALLOWED_HOSTS to include 'testserver' so FastAPI's TrustedHostMiddleware
accepts requests from the Starlette TestClient (which uses http://testserver).
"""
import os

# Must be set before any app import
os.environ.setdefault("ALLOWED_HOSTS", "127.0.0.1,localhost,testserver")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_tourism.db")
os.environ.setdefault("AUTO_CREATE_DB", "false")
os.environ.setdefault("AUTH_SECRET", "test-only-secret-4ea1cf72ee3f5af0bd19f77c1e9c6902")
