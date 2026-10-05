from datetime import datetime
from . import db

class Skill(db.Model):
    __tablename__ = 'skills'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50), default='Technical') # Technical, Soft Skill, Domain
    description = db.Column(db.String(255))
    
    tasks = db.relationship('Task', backref='required_skill', lazy=True)
    employee_skills = db.relationship('EmployeeSkill', backref='skill', cascade='all, delete-orphan', lazy=True)
    
    def __repr__(self):
        return f"<Skill {self.name}>"


class EmployeeSkill(db.Model):
    __tablename__ = 'employee_skills'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    proficiency = db.Column(db.String(30), default='Intermediate') # Beginner, Intermediate, Advanced, Expert
    
    __table_args__ = (db.UniqueConstraint('employee_id', 'skill_id', name='uq_emp_skill'),)
    
    def __repr__(self):
        return f"<EmployeeSkill {self.employee_id}:{self.skill_id}>"


class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    emp_code = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30))
    designation = db.Column(db.String(100))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    team_lead_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    joining_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Active') # Active, Inactive
    avatar = db.Column(db.String(255), default='default_avatar.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Skills association
    skills = db.relationship('EmployeeSkill', backref='employee', cascade='all, delete-orphan', lazy='joined')
    
    # Tasks
    tasks_assigned = db.relationship('Task', backref='assignee', foreign_keys='Task.assigned_to', lazy='dynamic')
    tasks_created = db.relationship('Task', backref='creator', foreign_keys='Task.created_by', lazy='dynamic')
    
    # Attendance & Leave
    attendances = db.relationship('Attendance', backref='employee', cascade='all, delete-orphan', lazy='dynamic')
    leaves = db.relationship('LeaveRequest', backref='applicant', foreign_keys='LeaveRequest.employee_id', cascade='all, delete-orphan', lazy='dynamic')
    
    # Self-referential hierarchies
    subordinates = db.relationship('Employee', backref=db.backref('manager', remote_side=[id]), foreign_keys=[manager_id])
    team_members = db.relationship('Employee', backref=db.backref('team_lead', remote_side=[id]), foreign_keys=[team_lead_id])
    
    @property
    def skill_names(self):
        return [es.skill.name for es in self.skills if es.skill]

    @property
    def email(self):
        return self.user_account.email if self.user_account else ''

    @property
    def role_name(self):
        return self.user_account.role_name if self.user_account else 'employee'

    def __repr__(self):
        return f"<Employee {self.emp_code} - {self.full_name}>"
