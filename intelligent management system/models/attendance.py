from datetime import datetime, date
from . import db

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    check_in = db.Column(db.Time, nullable=True)
    check_out = db.Column(db.Time, nullable=True)
    working_hours = db.Column(db.Float, default=0.0) # hours as float
    status = db.Column(db.String(20), default='Present') # Present, Late, Half Day, Absent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('employee_id', 'date', name='uq_emp_date'),)
    
    def calculate_hours(self):
        if self.check_in and self.check_out:
            dummy_date = date(2000, 1, 1)
            start_dt = datetime.combine(dummy_date, self.check_in)
            end_dt = datetime.combine(dummy_date, self.check_out)
            diff = (end_dt - start_dt).total_seconds() / 3600.0
            self.working_hours = round(max(0.0, diff), 2)
            if self.working_hours >= 7.5:
                self.status = 'Present'
            elif self.working_hours >= 4.0:
                self.status = 'Half Day'
            else:
                self.status = 'Late'
        elif self.check_in:
            self.status = 'Present'

    @property
    def status_badge_class(self):
        mapping = {
            'Present': 'badge-success',
            'Late': 'badge-warning',
            'Half Day': 'badge-info',
            'Absent': 'badge-danger'
        }
        return mapping.get(self.status, 'badge-secondary')
        
    def __repr__(self):
        return f"<Attendance Emp#{self.employee_id} {self.date}: {self.status}>"
