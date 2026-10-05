from datetime import datetime
from . import db

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info') # info, success, warning, danger
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def icon_class(self):
        mapping = {
            'success': 'fas fa-check-circle text-emerald-400',
            'danger': 'fas fa-exclamation-circle text-rose-400',
            'warning': 'fas fa-exclamation-triangle text-amber-400',
            'info': 'fas fa-info-circle text-sky-400'
        }
        return mapping.get(self.type, 'fas fa-bell text-indigo-400')
        
    @property
    def time_ago(self):
        diff = datetime.utcnow() - self.created_at
        seconds = diff.total_seconds()
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours}h ago"
        else:
            days = int(seconds / 86400)
            return f"{days}d ago"

    def __repr__(self):
        return f"<Notification User#{self.user_id}: {self.title}>"
