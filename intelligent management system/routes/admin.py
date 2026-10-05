from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models import db, User, Role, Department, Team, Employee, Skill, EmployeeSkill, Task, Attendance, LeaveRequest
from routes.auth import login_required, role_required
from services.analytics_service import get_hr_workforce_analytics
from services.intelligence import calculate_employee_workload

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.before_request
@login_required
@role_required(['admin'])
def before_request():
    pass


@admin_bp.route('/', strict_slashes=False)
def index():
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/dashboard')
def dashboard():
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter_by(status='Active').count()
    total_depts = Department.query.count()
    total_teams = Team.query.count()
    
    pending_leaves = LeaveRequest.query.filter_by(status='Pending').count()
    today_atts = Attendance.query.filter_by(date=date.today()).all()
    today_present = sum(1 for a in today_atts if a.status in ['Present', 'Half Day'])
    
    open_tasks = Task.query.filter(Task.status.notin_(['Completed'])).count()
    completed_tasks = Task.query.filter_by(status='Completed').count()
    
    # Recent leave requests & high-priority tasks
    recent_leaves = LeaveRequest.query.order_by(LeaveRequest.created_at.desc()).limit(5).all()
    critical_tasks = Task.query.filter(Task.priority.in_(['High', 'Critical']), Task.status != 'Completed').limit(5).all()
    
    analytics_data = get_hr_workforce_analytics()

    return render_template(
        'admin/dashboard.html',
        total_employees=total_employees,
        active_employees=active_employees,
        total_depts=total_depts,
        total_teams=total_teams,
        pending_leaves=pending_leaves,
        today_present=today_present,
        open_tasks=open_tasks,
        completed_tasks=completed_tasks,
        recent_leaves=recent_leaves,
        critical_tasks=critical_tasks,
        analytics=analytics_data
    )


@admin_bp.route('/employees', methods=['GET', 'POST'])
def employees():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip()
            emp_code = request.form.get('emp_code', '').strip()
            role_name = request.form.get('role_name', 'employee')
            dept_id = request.form.get('department_id') or None
            team_id = request.form.get('team_id') or None
            manager_id = request.form.get('manager_id') or None
            team_lead_id = request.form.get('team_lead_id') or None
            phone = request.form.get('phone', '').strip()
            designation = request.form.get('designation', '').strip()
            password = request.form.get('password', 'workforce123').strip()
            selected_skills = request.form.getlist('skills')

            # Validation
            if not full_name or not email or not emp_code:
                flash('Full Name, Email, and Employee Code are required.', 'danger')
                return redirect(url_for('admin.employees'))

            if User.query.filter_by(email=email).first():
                flash(f'An account with email {email} already exists.', 'danger')
                return redirect(url_for('admin.employees'))

            if Employee.query.filter_by(emp_code=emp_code).first():
                flash(f'Employee Code {emp_code} is already in use.', 'danger')
                return redirect(url_for('admin.employees'))

            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role.query.filter_by(name='employee').first()

            try:
                username = email.split('@')[0]
                # Ensure unique username
                base_user = username
                idx = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base_user}{idx}"
                    idx += 1

                new_user = User(
                    username=username,
                    email=email,
                    role_id=role.id,
                    is_active=True
                )
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.flush()

                new_emp = Employee(
                    user_id=new_user.id,
                    emp_code=emp_code,
                    full_name=full_name,
                    phone=phone,
                    designation=designation or role_name.replace('_', ' ').title(),
                    department_id=int(dept_id) if dept_id else None,
                    team_id=int(team_id) if team_id else None,
                    manager_id=int(manager_id) if manager_id else None,
                    team_lead_id=int(team_lead_id) if team_lead_id else None,
                    joining_date=date.today(),
                    status='Active',
                    avatar='default_avatar.png'
                )
                db.session.add(new_emp)
                db.session.flush()

                # Add skills
                for s_id in selected_skills:
                    if s_id.isdigit():
                        es = EmployeeSkill(employee_id=new_emp.id, skill_id=int(s_id), proficiency='Intermediate')
                        db.session.add(es)

                db.session.commit()
                flash(f'Employee {full_name} ({emp_code}) created successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating employee: {str(e)}', 'danger')

            return redirect(url_for('admin.employees'))

        elif action == 'edit':
            emp_id = request.form.get('employee_id')
            emp = db.session.get(Employee, int(emp_id)) if emp_id else None
            if emp:
                emp.full_name = request.form.get('full_name', emp.full_name).strip()
                emp.phone = request.form.get('phone', emp.phone).strip()
                emp.designation = request.form.get('designation', emp.designation).strip()
                dept_id = request.form.get('department_id')
                emp.department_id = int(dept_id) if dept_id else None
                team_id = request.form.get('team_id')
                emp.team_id = int(team_id) if team_id else None
                manager_id = request.form.get('manager_id')
                emp.manager_id = int(manager_id) if manager_id else None
                team_lead_id = request.form.get('team_lead_id')
                emp.team_lead_id = int(team_lead_id) if team_lead_id else None
                
                # Update role
                new_role_name = request.form.get('role_name')
                if new_role_name and emp.user_account:
                    r = Role.query.filter_by(name=new_role_name).first()
                    if r:
                        emp.user_account.role_id = r.id

                # Update skills
                selected_skills = request.form.getlist('skills')
                EmployeeSkill.query.filter_by(employee_id=emp.id).delete()
                for s_id in selected_skills:
                    if s_id.isdigit():
                        db.session.add(EmployeeSkill(employee_id=emp.id, skill_id=int(s_id), proficiency='Intermediate'))

                db.session.commit()
                flash(f'Employee {emp.full_name} updated successfully!', 'success')
            return redirect(url_for('admin.employees'))

        elif action == 'toggle_status':
            emp_id = request.form.get('employee_id')
            emp = db.session.get(Employee, int(emp_id)) if emp_id else None
            if emp:
                emp.status = 'Inactive' if emp.status == 'Active' else 'Active'
                if emp.user_account:
                    emp.user_account.is_active = (emp.status == 'Active')
                db.session.commit()
                flash(f"Employee {emp.full_name} is now {emp.status}.", 'info')
            return redirect(url_for('admin.employees'))

    # GET request: Filtering & Listing
    dept_filter = request.args.get('dept')
    status_filter = request.args.get('status')
    search_query = request.args.get('search', '').strip()

    query = Employee.query
    if dept_filter and dept_filter.isdigit():
        query = query.filter_by(department_id=int(dept_filter))
    if status_filter:
        query = query.filter_by(status=status_filter)
    if search_query:
        query = query.filter(
            (Employee.full_name.ilike(f"%{search_query}%")) |
            (Employee.emp_code.ilike(f"%{search_query}%")) |
            (Employee.designation.ilike(f"%{search_query}%"))
        )

    employees_list = query.order_by(Employee.emp_code).all()
    departments = Department.query.all()
    teams = Team.query.all()
    roles = Role.query.all()
    skills = Skill.query.all()
    managers = Employee.query.join(User).join(Role).filter(Role.name.in_(['manager', 'admin']), Employee.status == 'Active').all()
    team_leads = Employee.query.join(User).join(Role).filter(Role.name == 'team_lead', Employee.status == 'Active').all()

    return render_template(
        'admin/employees.html',
        employees=employees_list,
        departments=departments,
        teams=teams,
        roles=roles,
        skills=skills,
        managers=managers,
        team_leads=team_leads,
        selected_dept=dept_filter,
        selected_status=status_filter,
        search_query=search_query
    )


@admin_bp.route('/departments', methods=['GET', 'POST'])
def departments():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_department':
            name = request.form.get('name', '').strip()
            code = request.form.get('code', '').strip().upper()
            description = request.form.get('description', '').strip()
            if name and code:
                if not Department.query.filter((Department.name == name) | (Department.code == code)).first():
                    d = Department(name=name, code=code, description=description)
                    db.session.add(d)
                    db.session.commit()
                    flash(f'Department "{name}" created.', 'success')
                else:
                    flash('A department with that name or code already exists.', 'warning')
        elif action == 'add_team':
            name = request.form.get('name', '').strip()
            dept_id = request.form.get('department_id')
            manager_id = request.form.get('manager_id') or None
            team_lead_id = request.form.get('team_lead_id') or None
            if name and dept_id:
                t = Team(
                    name=name,
                    department_id=int(dept_id),
                    manager_id=int(manager_id) if manager_id else None,
                    team_lead_id=int(team_lead_id) if team_lead_id else None,
                    status='Active'
                )
                db.session.add(t)
                db.session.commit()
                flash(f'Team "{name}" added successfully.', 'success')
        return redirect(url_for('admin.departments'))

    departments_list = Department.query.all()
    teams_list = Team.query.all()
    managers = Employee.query.join(User).join(Role).filter(Role.name.in_(['manager', 'admin'])).all()
    team_leads = Employee.query.join(User).join(Role).filter(Role.name == 'team_lead').all()

    return render_template(
        'admin/departments.html',
        departments=departments_list,
        teams=teams_list,
        managers=managers,
        team_leads=team_leads
    )


@admin_bp.route('/attendance')
def attendance():
    selected_date_str = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except Exception:
        selected_date = date.today()

    attendances_list = Attendance.query.filter_by(date=selected_date).all()
    all_employees = Employee.query.filter_by(status='Active').all()

    # Map who attended vs who hasn't checked in
    attended_ids = {a.employee_id for a in attendances_list}
    not_checked_in = [e for e in all_employees if e.id not in attended_ids]

    return render_template(
        'admin/attendance.html',
        attendances=attendances_list,
        not_checked_in=not_checked_in,
        selected_date=selected_date.strftime('%Y-%m-%d')
    )


@admin_bp.route('/leaves')
def leaves():
    status_filter = request.args.get('status')
    query = LeaveRequest.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    all_leaves = query.order_by(LeaveRequest.created_at.desc()).all()
    return render_template('admin/leaves.html', leaves=all_leaves, status_filter=status_filter)


@admin_bp.route('/tasks')
def tasks():
    priority_filter = request.args.get('priority')
    status_filter = request.args.get('status')
    query = Task.query
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)
    all_tasks = query.order_by(Task.due_date.asc()).all()
    return render_template('admin/tasks.html', tasks=all_tasks, priority_filter=priority_filter, status_filter=status_filter)


@admin_bp.route('/analytics')
def analytics():
    data = get_hr_workforce_analytics()
    skills = Skill.query.all()
    return render_template('admin/analytics.html', analytics=data, skills=skills)
