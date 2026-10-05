from models import db, Notification, User

def create_notification(user_id, title, message, notif_type='info', link=None):
    """
    Creates and commits a new notification for a specific user.
    Types: 'info', 'success', 'warning', 'danger'
    """
    if not user_id:
        return None
    user = db.session.get(User, user_id)
    if not user:
        return None

    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notif_type,
        link=link,
        is_read=False
    )
    db.session.add(notif)
    try:
        db.session.commit()
        return notif
    except Exception as e:
        db.session.rollback()
        print(f"Error creating notification: {e}")
        return None


def notify_leave_status(leave_request):
    """Notifies the employee of leave approval or rejection."""
    employee = leave_request.applicant
    if not employee or not employee.user_account:
        return
        
    user_id = employee.user_account.id
    status = leave_request.status
    notif_type = 'success' if status == 'Approved' else 'danger'
    
    title = f"Leave Request {status}"
    if status == 'Approved':
        msg = f"Your {leave_request.leave_type} request for {leave_request.start_date.strftime('%d %b')} to {leave_request.end_date.strftime('%d %b')} has been APPROVED."
    else:
        reason = f" Reason: {leave_request.rejection_reason}" if leave_request.rejection_reason else ""
        msg = f"Your {leave_request.leave_type} request for {leave_request.start_date.strftime('%d %b')} to {leave_request.end_date.strftime('%d %b')} was REJECTED.{reason}"
        
    create_notification(user_id, title, msg, notif_type=notif_type, link="/employee/leaves")


def notify_task_assignment(task, previous_assignee=None):
    """Notifies the employee(s) about new task assignment or reassignment."""
    if task.assignee and task.assignee.user_account:
        title = "New Task Assigned" if not previous_assignee else "Task Reassigned To You"
        msg = f"You have been assigned to task: '{task.title}' (Priority: {task.priority}, Due: {task.due_date.strftime('%d %b %Y')})."
        create_notification(task.assignee.user_account.id, title, msg, notif_type='info', link="/employee/tasks")
        
    if previous_assignee and previous_assignee.user_account:
        title = "Task Reassigned"
        msg = f"Task '{task.title}' was reassigned to {task.assignee.full_name if task.assignee else 'another team member'}."
        create_notification(previous_assignee.user_account.id, title, msg, notif_type='warning', link="/employee/tasks")


def notify_task_completed(task):
    """Notifies the task creator/team lead when an employee completes a task."""
    if task.creator and task.creator.user_account:
        emp_name = task.assignee.full_name if task.assignee else "An employee"
        title = "Task Completed"
        msg = f"{emp_name} marked task '{task.title}' as 100% completed."
        create_notification(task.creator.user_account.id, title, msg, notif_type='success', link=f"/team-lead/tasks")
