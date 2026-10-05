from flask import Blueprint

# Blueprints will be registered in app.py
from .auth import auth_bp
from .admin import admin_bp
from .manager import manager_bp
from .team_lead import team_lead_bp
from .employee import employee_bp
from .api import api_bp
