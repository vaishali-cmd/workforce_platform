from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort, jsonify
from models import db, User, Role, Employee

auth_bp = Blueprint('auth', __name__, url_prefix='')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def role_required(allowed_roles):
    """
    Enforces Role-Based Access Control on backend routes.
    Prevents unauthorized URL tampering.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to continue.', 'warning')
                return redirect(url_for('auth.login', next=request.path))
            
            user_role = session.get('role')
            if user_role not in allowed_roles:
                flash(f'Access Denied: You do not have permission to view this resource ({user_role}).', 'danger')
                # Redirect user safely to their authorized dashboard
                redirect_map = {
                    'admin': 'admin.dashboard',
                    'manager': 'manager.dashboard',
                    'team_lead': 'team_lead.dashboard',
                    'employee': 'employee.dashboard'
                }
                target = redirect_map.get(user_role, 'auth.login')
                return redirect(url_for(target))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        password = request.form.get('password', '').strip()
        expected_role = request.form.get('role', '').strip()  # Optional role filter
        remember = bool(request.form.get('remember_me'))

        if not login_id or not password:
            flash('Please provide both username/email and password.', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter(
            (User.email == login_id) | (User.username == login_id)
        ).first()

        if not user or not user.check_password(password):
            flash('Invalid email/username or password. Please try again.', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('Your account has been deactivated. Please contact HR.', 'danger')
            return render_template('auth/login.html')

        # If user explicitly picked a role on the login screen, verify match
        if expected_role and user.role_name != expected_role:
            flash(f'Account role mismatch: This user is registered as {user.role_name.replace("_", " ").title()}, not {expected_role.replace("_", " ").title()}.', 'warning')
            return render_template('auth/login.html')

        # Establish session
        session.clear()
        session['user_id'] = user.id
        session['username'] = user.username
        session['email'] = user.email
        session['role'] = user.role_name
        
        emp = user.employee_profile
        if emp:
            session['employee_id'] = emp.id
            session['full_name'] = emp.full_name
            session['designation'] = emp.designation or 'Team Member'
            session['avatar'] = emp.avatar
            session['team_id'] = emp.team_id
        else:
            session['employee_id'] = None
            session['full_name'] = user.username
            session['designation'] = 'System Administrator'
            session['avatar'] = 'default_avatar.png'
            session['team_id'] = None

        session.permanent = remember

        flash(f'Welcome back, {session["full_name"]}!', 'success')
        
        # Role-based redirection to their specific dashboard
        redirect_map = {
            'admin': 'admin.dashboard',
            'manager': 'manager.dashboard',
            'team_lead': 'team_lead.dashboard',
            'employee': 'employee.dashboard'
        }
        role_prefix_map = {
            'admin': '/admin',
            'manager': '/manager',
            'team_lead': '/team-lead',
            'employee': '/employee'
        }
        next_page = request.args.get('next')
        expected_prefix = role_prefix_map.get(user.role_name)
        if next_page and next_page.startswith('/') and expected_prefix and next_page.startswith(expected_prefix):
            return redirect(next_page)
        return redirect(url_for(redirect_map.get(user.role_name, 'auth.login')))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    resp = redirect(url_for('auth.login'))
    resp.delete_cookie('session')
    return resp
