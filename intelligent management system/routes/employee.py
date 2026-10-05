from datetime import datetime, date, time
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models import db, Employee, Task, Attendance, LeaveRequest, EmployeeSkill, Skill
from routes.auth import login_required, role_required
from services.intelligence import calculate_employee_workload, evaluate_leave_impact
from services.notification_service import notify_task_completed

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')


@employee_bp.before_request
@login_required
@role_required(['employee', 'team_lead', 'manager', 'admin'])
def before_request():
    pass


@employee_bp.route('/', strict_slashes=False)
def index():
    return redirect(url_for('employee.dashboard'))


def _get_current_emp():
    emp_id = session.get('employee_id')
    if not emp_id:
        return None
    return db.session.get(Employee, emp_id)


@employee_bp.route('/dashboard')
def dashboard():
    emp = _get_current_emp()
    if not emp:
        flash('Employee profile not found.', 'warning')
        return redirect(url_for('auth.logout'))

    today = date.today()

    # Today's attendance
    today_att = Attendance.query.filter_by(employee_id=emp.id, date=today).first()

    # Workload
    workload = calculate_employee_workload(emp.id)

    # Tasks
    tasks_query = Task.query.filter_by(assigned_to=emp.id)
    all_tasks = tasks_query.order_by(Task.due_date.asc()).all()
    pending_tasks = [t for t in all_tasks if t.status not in ['Completed']]
    completed_tasks = [t for t in all_tasks if t.status == 'Completed']

    # Upcoming deadlines (due in next 5 days and not completed)
    upcoming_deadlines = [t for t in pending_tasks if 0 <= (t.due_date - today).days <= 5]

    # Recent leave requests & balance
    leaves = LeaveRequest.query.filter_by(employee_id=emp.id).order_by(LeaveRequest.created_at.desc()).limit(5).all()

    # Completed tasks count
    total_assigned = len(all_tasks)
    completion_rate = round((len(completed_tasks) / max(1, total_assigned)) * 100, 1)

    return render_template(
        'employee/dashboard.html',
        employee=emp,
        today_att=today_att,
        workload=workload,
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        upcoming_deadlines=upcoming_deadlines,
        leaves=leaves,
        completion_rate=completion_rate,
        date=date  # pass date class for template calculations
    )


@employee_bp.route('/attendance', methods=['GET', 'POST'])
def attendance():
    emp = _get_current_emp()
    if not emp:
        return redirect(url_for('auth.logout'))

    today = date.today()
    att_record = Attendance.query.filter_by(employee_id=emp.id, date=today).first()

    if request.method == 'POST':
        action = request.form.get('action')
        now_time = datetime.now().time().replace(microsecond=0)

        if action == 'check_in':
            if att_record and att_record.check_in:
                flash("You have already checked in today at " + att_record.check_in.strftime('%H:%M:%S'), 'info')
            else:
                if not att_record:
                    att_record = Attendance(
                        employee_id=emp.id,
                        date=today,
                        check_in=now_time,
                        status='Present'
                    )
                    db.session.add(att_record)
                else:
                    att_record.check_in = now_time
                db.session.commit()
                flash(f"Check-in recorded successfully at {now_time.strftime('%H:%M:%S')}!", 'success')

        elif action == 'check_out':
            if not att_record or not att_record.check_in:
                flash("Please check in before checking out.", 'warning')
            elif att_record.check_out:
                flash(f"You have already checked out today at {att_record.check_out.strftime('%H:%M:%S')}.", 'info')
            else:
                att_record.check_out = now_time
                att_record.calculate_hours()
                db.session.commit()
                flash(f"Checked out at {now_time.strftime('%H:%M:%S')}! Total hours: {att_record.working_hours}h.", 'success')

        return redirect(url_for('employee.attendance'))

    # Attendance history (last 30 records)
    history = Attendance.query.filter_by(employee_id=emp.id).order_by(Attendance.date.desc()).limit(30).all()

    return render_template(
        'employee/attendance.html',
        employee=emp,
        today_att=att_record,
        history=history,
        today_date=today
    )


@employee_bp.route('/tasks', methods=['GET', 'POST'])
def tasks():
    emp = _get_current_emp()
    if not emp:
        return redirect(url_for('auth.logout'))

    if request.method == 'POST':
        task_id = request.form.get('task_id')
        progress = int(request.form.get('progress', 0))
        remarks = request.form.get('remarks', '').strip()
        status = request.form.get('status')

        task = Task.query.filter_by(id=task_id, assigned_to=emp.id).first()
        if not task:
            flash('Task not found or not assigned to you.', 'danger')
            return redirect(url_for('employee.tasks'))

        task.progress = min(100, max(0, progress))
        if remarks:
            task.remarks = remarks

        if status:
            task.status = status

        if task.progress == 100 or status == 'Completed':
            task.status = 'Completed'
            task.completed_at = datetime.utcnow()
            notify_task_completed(task)
            flash(f"🎉 Congratulations! Task '{task.title}' marked as Completed!", 'success')
        else:
            if task.progress > 0 and task.status == 'Assigned':
                task.status = 'In Progress'
            flash(f"Progress for '{task.title}' updated to {task.progress}%.", 'info')

        db.session.commit()
        return redirect(url_for('employee.tasks'))

    # List tasks
    status_filter = request.args.get('status')
    query = Task.query.filter_by(assigned_to=emp.id)
    if status_filter:
        query = query.filter_by(status=status_filter)

    my_tasks = query.order_by(Task.due_date.asc()).all()

    return render_template(
        'employee/tasks.html',
        employee=emp,
        tasks=my_tasks,
        status_filter=status_filter
    )


@employee_bp.route('/leaves', methods=['GET', 'POST'])
def leaves():
    emp = _get_current_emp()
    if not emp:
        return redirect(url_for('auth.logout'))

    if request.method == 'POST':
        leave_type = request.form.get('leave_type', 'Casual Leave')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        reason = request.form.get('reason', '').strip()

        if not start_date_str or not end_date_str or not reason:
            flash('All fields (Leave Type, Start Date, End Date, Reason) are required.', 'danger')
            return redirect(url_for('employee.leaves'))

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            if end_date < start_date:
                flash('End date cannot be earlier than start date.', 'danger')
                return redirect(url_for('employee.leaves'))

            days_count = (end_date - start_date).days + 1

            # Run Leave Impact evaluation
            impact = evaluate_leave_impact(emp.id, start_date, end_date)
            impact_summary = impact['summary'] if impact['has_impact'] else None

            new_leave = LeaveRequest(
                employee_id=emp.id,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                days_count=days_count,
                reason=reason,
                status='Pending',
                impact_warning=impact_summary
            )
            db.session.add(new_leave)
            db.session.commit()

            flash(f"Leave application submitted successfully for {days_count} day(s). Awaiting review.", 'success')
            return redirect(url_for('employee.leaves'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error applying for leave: {str(e)}', 'danger')
            return redirect(url_for('employee.leaves'))

    leaves_history = LeaveRequest.query.filter_by(employee_id=emp.id).order_by(LeaveRequest.created_at.desc()).all()
    return render_template('employee/leaves.html', employee=emp, leaves=leaves_history)


@employee_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    emp = _get_current_emp()
    if not emp:
        return redirect(url_for('auth.logout'))

    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        if phone:
            emp.phone = phone
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        return redirect(url_for('employee.profile'))

    workload = calculate_employee_workload(emp.id)
    completed_count = Task.query.filter_by(assigned_to=emp.id, status='Completed').count()
    active_count = Task.query.filter(Task.assigned_to == emp.id, Task.status != 'Completed').count()

    return render_template(
        'employee/profile.html',
        employee=emp,
        workload=workload,
        completed_count=completed_count,
        active_count=active_count
    )
