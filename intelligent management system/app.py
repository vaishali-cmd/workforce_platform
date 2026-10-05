import os
from datetime import datetime, date
from flask import Flask, render_template, request, session, redirect, url_for
from config import Config
from models import db, User, Employee, Notification
from routes import auth_bp, admin_bp, manager_bp, team_lead_bp, employee_bp, api_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(team_lead_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(api_bp)

    # Custom Jinja filters
    @app.template_filter('format_date')
    def format_date(value, fmt='%d %b %Y'):
        if not value:
            return '—'
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d').date()
            except Exception:
                return value
        return value.strftime(fmt)

    @app.template_filter('format_time')
    def format_time(value, fmt='%I:%M %p'):
        if not value:
            return '—'
        if isinstance(value, str):
            return value
        return value.strftime(fmt)

    # Jinja environment globals
    app.jinja_env.globals.update(min=min, max=max)

    # Prevent stale browser back/forward cache on authenticated pages
    @app.after_request
    def set_cache_headers(response):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # Global context processor
    @app.context_processor
    def inject_globals():
        user = None
        employee = None
        unread_notifications_count = 0
        if 'user_id' in session:
            user = db.session.get(User, session['user_id'])
            if user:
                employee = user.employee_profile
                unread_notifications_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
        return {
            'current_user': user,
            'current_employee': employee,
            'current_role': session.get('role', 'guest'),
            'unread_notifications_count': unread_notifications_count,
            'now': datetime.utcnow(),
            'today': date.today()
        }

    # Friendly error handling
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/error.html', code=403, title="Access Forbidden", message="You do not have the required permissions to access this page."), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/error.html', code=404, title="Page Not Found", message="The page or resource you requested could not be located."), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/error.html', code=500, title="Server Processing Error", message="Unable to process your request right now. Our engineering team has been alerted."), 500

    # Auto-create tables if they don't exist yet
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"[DB INIT ERROR] {e}")

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
