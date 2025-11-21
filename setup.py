"""
Setup script for API Forge.

Enables installation with: pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name="api-forge",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi>=0.121.3",
        "uvicorn[standard]>=0.38.0",
        "pydantic>=2.12.4",
        "pydantic-settings>=2.12.0",
        "sqlalchemy>=2.0.44",
        "asyncpg>=0.30.0",
        "alembic>=1.17.2",
        "python-jose[cryptography]>=3.5.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart>=0.0.20",
        "httpx>=0.28.1",
        "redis>=7.1.0",
        "typer[all]>=0.20.0",
        "rich>=14.2.0",
        "jinja2>=3.1.6",
        "pyyaml>=6.0.3",
        "anthropic>=0.74.0",
    ],
    entry_points={
        "console_scripts": [
            "api-forge=api_forge.cli.main:app",
        ],
    },
    python_requires=">=3.11",
)