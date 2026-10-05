from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # admin, manager, team_lead, employee
    description = db.Column(db.String(255))
    
    users = db.relationship('User', backref='role', lazy=True)
    
    def __repr__(self):
        return f"<Role {self.name}>"


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    employee_profile = db.relationship('Employee', backref='user_account', uselist=False, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='recipient', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    @property
    def role_name(self):
        return self.role.name if self.role else 'unknown'
        
    def __repr__(self):
        return f"<User {self.username} ({self.role_name})>"


class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    teams = db.relationship('Team', backref='department', lazy=True)
    employees = db.relationship('Employee', backref='department', lazy=True)
    
    def __repr__(self):
        return f"<Department {self.name}>"


class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('employees.id', use_alter=True, name='fk_team_mgr'), nullable=True)
    team_lead_id = db.Column(db.Integer, db.ForeignKey('employees.id', use_alter=True, name='fk_team_lead'), nullable=True)
    capacity = db.Column(db.Integer, default=100) # baseline capacity index
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    members = db.relationship('Employee', backref='team', foreign_keys='Employee.team_id', lazy=True)
    tasks = db.relationship('Task', backref='team', lazy=True)
    manager = db.relationship('Employee', foreign_keys=[manager_id], lazy=True)
    team_lead = db.relationship('Employee', foreign_keys=[team_lead_id], lazy=True)
    
    def __repr__(self):
        return f"<Team {self.name}>"
