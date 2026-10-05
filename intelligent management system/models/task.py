from datetime import datetime, date
from . import db

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    task_code = db.Column(db.String(30), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    required_skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=True)
    priority = db.Column(db.String(20), default='Medium') # Low, Medium, High, Critical
    status = db.Column(db.String(30), default='Assigned') # Not Started, Assigned, In Progress, Blocked, Completed, Delayed
    progress = db.Column(db.Integer, default=0) # 0 to 100
    assigned_to = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Audit log
    reassignments = db.relationship('TaskReassignment', backref='task', cascade='all, delete-orphan', lazy=True)
    
    @property
    def is_overdue(self):
        if self.status != 'Completed' and self.due_date < date.today():
            return True
        return False
        
    @property
    def days_remaining(self):
        return (self.due_date - date.today()).days
        
    @property
    def is_deadline_risk(self):
        # Approaching deadline (<= 2 days) while incomplete and progress < 60%
        if self.status not in ['Completed'] and 0 <= self.days_remaining <= 2 and self.progress < 60:
            return True
        return False
        
    @property
    def priority_badge_class(self):
        mapping = {
            'Critical': 'badge-danger',
            'High': 'badge-warning-alt',
            'Medium': 'badge-info',
            'Low': 'badge-secondary'
        }
        return mapping.get(self.priority, 'badge-info')

    @property
    def status_badge_class(self):
        mapping = {
            'Completed': 'badge-success',
            'In Progress': 'badge-primary',
            'Assigned': 'badge-info',
            'Blocked': 'badge-danger',
            'Delayed': 'badge-warning',
            'Not Started': 'badge-secondary'
        }
        return mapping.get(self.status, 'badge-secondary')

    def __repr__(self):
        return f"<Task {self.task_code}: {self.title}>"


class TaskReassignment(db.Model):
    __tablename__ = 'task_reassignments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    previous_employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    new_employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    reassigned_by = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    prev_emp = db.relationship('Employee', foreign_keys=[previous_employee_id])
    new_emp = db.relationship('Employee', foreign_keys=[new_employee_id])
    actor = db.relationship('Employee', foreign_keys=[reassigned_by])
    
    def __repr__(self):
        return f"<TaskReassignment Task#{self.task_id} -> Emp#{self.new_employee_id}>"
