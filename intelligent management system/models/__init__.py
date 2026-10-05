from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import Role, User, Department, Team
from .employee import Employee, Skill, EmployeeSkill
from .task import Task, TaskReassignment
from .attendance import Attendance
from .leave import LeaveRequest
from .notification import Notification
