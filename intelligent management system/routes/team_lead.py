from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models import db, Employee, Team, Task, TaskReassignment, Skill, LeaveRequest, Notification
from routes.auth import login_required, role_required
from services.intelligence import (
    calculate_employee_workload,
    detect_team_workload_imbalance,
    evaluate_leave_impact,
    recommend_employees_for_task,
    detect_deadline_risks
)
from services.notification_service import notify_leave_status, notify_task_assignment

team_lead_bp = Blueprint('team_lead', __name__, url_prefix='/team-lead')


@team_lead_bp.before_request
@login_required
@role_required(['team_lead', 'manager', 'admin'])
def before_request():
    pass


@team_lead_bp.route('/', strict_slashes=False)
def index():
    return redirect(url_for('team_lead.dashboard'))


def _get_lead_context():
    emp_id = session.get('employee_id')
    lead_emp = db.session.get(Employee, emp_id) if emp_id else None
    team = None
    if lead_emp:
        # Check team led by employee or team assigned to
        team = Team.query.filter_by(team_lead_id=lead_emp.id).first()
        if not team and lead_emp.team_id:
            team = db.session.get(Team, lead_emp.team_id)
    if not team:
        # Fallback to first team if not set
        team = Team.query.first()
    return lead_emp, team


@team_lead_bp.route('/dashboard')
def dashboard():
    lead_emp, team = _get_lead_context()
    team_id = team.id if team else None

    # Members & Workloads
    members = Employee.query.filter_by(team_id=team_id, status='Active').all() if team_id else []
    members_data = []
    for m in members:
        wl = calculate_employee_workload(m.id)
        members_data.append({'employee': m, 'workload': wl})

    # Tasks
    tasks_query = Task.query.filter_by(team_id=team_id) if team_id else Task.query
    total_tasks = tasks_query.count()
    active_tasks = tasks_query.filter(Task.status.notin_(['Completed'])).all()
    completed_tasks_count = tasks_query.filter_by(status='Completed').count()

    # Pending Leave Requests for Team Members
    member_ids = [m.id for m in members]
    pending_leaves = LeaveRequest.query.filter(
        LeaveRequest.employee_id.in_(member_ids),
        LeaveRequest.status == 'Pending'
    ).all() if member_ids else []

    # Leave requests decorated with live Leave Impact Assessment
    leaves_with_impact = []
    for lr in pending_leaves:
        impact = evaluate_leave_impact(lr.employee_id, lr.start_date, lr.end_date)
        leaves_with_impact.append({
            'leave': lr,
            'impact': impact
        })

    # Workload Imbalance check
    imbalance = detect_team_workload_imbalance(team_id) if team_id else {'has_imbalance': False}

    # Deadline Risks
    deadline_risks = detect_deadline_risks(team_id=team_id)

    return render_template(
        'team_lead/dashboard.html',
        team=team,
        members_data=members_data,
        total_tasks=total_tasks,
        active_tasks_count=len(active_tasks),
        completed_tasks_count=completed_tasks_count,
        pending_leaves_count=len(pending_leaves),
        leaves_with_impact=leaves_with_impact,
        imbalance=imbalance,
        deadline_risks=deadline_risks
    )


@team_lead_bp.route('/assign-task', methods=['GET', 'POST'])
def assign_task():
    lead_emp, team = _get_lead_context()
    team_id = team.id if team else None

    skills = Skill.query.all()
    members = Employee.query.filter_by(team_id=team_id, status='Active').all() if team_id else Employee.query.filter_by(status='Active').all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        skill_id = request.form.get('skill_id')
        priority = request.form.get('priority', 'Medium')
        due_date_str = request.form.get('due_date')
        assigned_to_id = request.form.get('assigned_to')

        if not title or not due_date_str or not assigned_to_id:
            flash('Title, Due Date, and Assigned Employee are required.', 'danger')
            return redirect(url_for('team_lead.assign_task'))

        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            if due_date < date.today():
                flash('Due date cannot be in the past.', 'warning')
                return redirect(url_for('team_lead.assign_task'))

            # Generate unique task code
            code_prefix = "TSK"
            count = Task.query.count() + 1
            task_code = f"{code_prefix}-{count:04d}"

            creator_id = lead_emp.id if lead_emp else int(assigned_to_id)

            new_task = Task(
                task_code=task_code,
                title=title,
                description=description,
                required_skill_id=int(skill_id) if skill_id else None,
                priority=priority,
                status='Assigned',
                progress=0,
                assigned_to=int(assigned_to_id),
                team_id=team_id,
                created_by=creator_id,
                start_date=date.today(),
                due_date=due_date
            )
            db.session.add(new_task)
            db.session.commit()

            # Trigger notification
            notify_task_assignment(new_task)

            flash(f'Task {task_code} ("{title}") created and assigned successfully!', 'success')
            return redirect(url_for('team_lead.tasks'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error assigning task: {str(e)}', 'danger')
            return redirect(url_for('team_lead.assign_task'))

    # If requested with preselected skill/priority for recommendation preview
    sel_skill = request.args.get('skill_id')
    sel_priority = request.args.get('priority', 'Medium')
    sel_due = request.args.get('due_date', (date.today() + datetime.resolution * 86400 * 5).strftime('%Y-%m-%d'))
    
    recommendations = []
    if sel_skill and sel_skill.isdigit():
        recommendations = recommend_employees_for_task(int(sel_skill), sel_priority, sel_due, team_id)

    return render_template(
        'team_lead/assign_task.html',
        team=team,
        skills=skills,
        members=members,
        recommendations=recommendations,
        selected_skill=sel_skill,
        selected_priority=sel_priority,
        selected_due=sel_due
    )


@team_lead_bp.route('/tasks')
def tasks():
    lead_emp, team = _get_lead_context()
    team_id = team.id if team else None

    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    search_q = request.args.get('q', '').strip()

    query = Task.query.filter_by(team_id=team_id) if team_id else Task.query

    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    if search_q:
        query = query.filter(Task.title.ilike(f"%{search_q}%") | Task.task_code.ilike(f"%{search_q}%"))

    team_tasks = query.order_by(Task.due_date.asc()).all()
    members = Employee.query.filter_by(team_id=team_id, status='Active').all() if team_id else []

    return render_template(
        'team_lead/tasks.html',
        team=team,
        tasks=team_tasks,
        members=members,
        status_filter=status_filter,
        priority_filter=priority_filter,
        search_q=search_q
    )


@team_lead_bp.route('/tasks/<int:task_id>/reassign', methods=['POST'])
def reassign_task(task_id):
    lead_emp, team = _get_lead_context()
    task = db.session.get(Task, task_id)
    if not task:
        flash('Task not found.', 'danger')
        return redirect(url_for('team_lead.tasks'))

    new_emp_id = request.form.get('new_employee_id')
    reason = request.form.get('reason', 'Workload balancing').strip()

    if not new_emp_id or not new_emp_id.isdigit():
        flash('Invalid target employee.', 'danger')
        return redirect(url_for('team_lead.tasks'))

    new_emp = db.session.get(Employee, int(new_emp_id))
    if not new_emp:
        flash('Target employee not found.', 'danger')
        return redirect(url_for('team_lead.tasks'))

    prev_emp = task.assignee
    task.assigned_to = new_emp.id

    # Create audit log
    reassign_log = TaskReassignment(
        task_id=task.id,
        previous_employee_id=prev_emp.id if prev_emp else None,
        new_employee_id=new_emp.id,
        reassigned_by=lead_emp.id if lead_emp else new_emp.id,
        reason=reason
    )
    db.session.add(reassign_log)
    db.session.commit()

    # Notify both employees
    notify_task_assignment(task, previous_assignee=prev_emp)

    flash(f"Task '{task.title}' successfully reassigned to {new_emp.full_name}!", 'success')
    return redirect(url_for('team_lead.tasks'))


@team_lead_bp.route('/leaves')
def leaves():
    lead_emp, team = _get_lead_context()
    team_id = team.id if team else None

    members = Employee.query.filter_by(team_id=team_id).all() if team_id else []
    member_ids = [m.id for m in members]

    leaves_query = LeaveRequest.query.filter(LeaveRequest.employee_id.in_(member_ids)) if member_ids else LeaveRequest.query
    all_leaves = leaves_query.order_by(LeaveRequest.created_at.desc()).all()

    # Compute live impact assessment for every pending request
    leaves_with_impact = []
    for lr in all_leaves:
        impact = evaluate_leave_impact(lr.employee_id, lr.start_date, lr.end_date)
        leaves_with_impact.append({
            'leave': lr,
            'impact': impact
        })

    return render_template('team_lead/leaves.html', team=team, leaves_with_impact=leaves_with_impact)


@team_lead_bp.route('/leaves/<int:leave_id>/action', methods=['POST'])
def handle_leave(leave_id):
    lead_emp, _ = _get_lead_context()
    leave_req = db.session.get(LeaveRequest, leave_id)
    if not leave_req:
        flash('Leave request not found.', 'danger')
        return redirect(url_for('team_lead.leaves'))

    action = request.form.get('action') # 'accept' or 'reject'
    rejection_reason = request.form.get('rejection_reason', '').strip()

    if action == 'accept':
        leave_req.status = 'Approved'
        leave_req.reviewed_by = lead_emp.id if lead_emp else None
        leave_req.rejection_reason = None
        db.session.commit()
        notify_leave_status(leave_req)
        flash(f"Leave request for {leave_req.applicant.full_name} has been APPROVED.", 'success')
    elif action == 'reject':
        leave_req.status = 'Rejected'
        leave_req.reviewed_by = lead_emp.id if lead_emp else None
        leave_req.rejection_reason = rejection_reason or 'Workload capacity conflict'
        db.session.commit()
        notify_leave_status(leave_req)
        flash(f"Leave request for {leave_req.applicant.full_name} has been REJECTED.", 'danger')

    return redirect(url_for('team_lead.leaves'))


@team_lead_bp.route('/workload')
def workload():
    lead_emp, team = _get_lead_context()
    team_id = team.id if team else None
    imbalance = detect_team_workload_imbalance(team_id) if team_id else {'has_imbalance': False, 'members_data': []}
    return render_template('team_lead/workload.html', team=team, imbalance=imbalance)
