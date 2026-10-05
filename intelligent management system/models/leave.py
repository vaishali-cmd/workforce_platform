from datetime import datetime, date
from . import db

class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False) # Casual Leave, Sick Leave, Earned Leave, etc.
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days_count = db.Column(db.Integer, default=1)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, Rejected
    reviewed_by = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    impact_warning = db.Column(db.Text, nullable=True) # Cached or calculated leave impact details
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    reviewer = db.relationship('Employee', foreign_keys=[reviewed_by], backref='leaves_reviewed')
    
    @property
    def status_badge_class(self):
        mapping = {
            'Approved': 'badge-success',
            'Rejected': 'badge-danger',
            'Pending': 'badge-warning'
        }
        return mapping.get(self.status, 'badge-secondary')
        
    def __repr__(self):
        return f"<LeaveRequest Emp#{self.employee_id} ({self.leave_type}): {self.status}>"
