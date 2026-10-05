
from datetime import date, timedelta
from models import db, Employee, Department, Team, Task, Attendance, LeaveRequest

def get_hr_workforce_analytics():
    """Calculates organization-level workforce metrics using Pandas."""
    employees = Employee.query.all()
    tasks = Task.query.all()
    attendances = Attendance.query.all()
    leaves = LeaveRequest.query.all()
    departments = Department.query.all()

    # Default structure
    dept_distribution = {'labels': [d.name for d in departments], 'counts': [len(d.employees) for d in departments]}

    # Role distribution
    role_counts = {}
    for emp in employees:
        rname = emp.role_name.capitalize()
        role_counts[rname] = role_counts.get(rname, 0) + 1
    role_distribution = {'labels': list(role_counts.keys()), 'counts': list(role_counts.values())}

    # Tasks distribution without Pandas
    task_status_distribution = {'labels': [], 'counts': []}
    if tasks:
        status_counts = {}
        for t in tasks:
            status = t.status
            status_counts[status] = status_counts.get(status, 0) + 1
        task_status_distribution = {
            'labels': list(status_counts.keys()),
            'counts': [int(c) for c in status_counts.values()]
        }

    # Attendance 7-day trend
    today = date.today()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    attendance_trend = {'dates': [d.strftime('%d %b') for d in last_7_days], 'present': [], 'late': [], 'absent': []}

    total_active_emps = sum(1 for e in employees if e.status == 'Active')
    for d in last_7_days:
        day_atts = Attendance.query.filter_by(date=d).all()
        present = sum(1 for a in day_atts if a.status == 'Present')
        late = sum(1 for a in day_atts if a.status == 'Late')
        half = sum(1 for a in day_atts if a.status == 'Half Day')
        present_total = present + half
        attendance_trend['present'].append(present_total)
        attendance_trend['late'].append(late)
        attendance_trend['absent'].append(max(0, total_active_emps - len(day_atts)))

    # Leave status distribution
    leave_data = {'Pending': 0, 'Approved': 0, 'Rejected': 0}
    for l in leaves:
        if l.status in leave_data:
            leave_data[l.status] += 1
    leave_distribution = {'labels': list(leave_data.keys()), 'counts': list(leave_data.values())}

    return {
        'dept_distribution': dept_distribution,
        'role_distribution': role_distribution,
        'task_status_distribution': task_status_distribution,
        'attendance_trend': attendance_trend,
        'leave_distribution': leave_distribution
    }


def get_manager_team_comparison():
    """
    Computes capacity vs assigned work and team performance metrics for Manager.
    Capacity is benchmarked at 100% per active team member.
    Assigned work is calculated from active task weights and progress.
    """
    teams = Team.query.filter_by(status='Active').all()
    comparison = []

    for t in teams:
        active_members = [m for m in t.members if m.status == 'Active']
        member_count = len(active_members)
        
        # Base team capacity = 100 units per member
        total_capacity_units = max(100, member_count * 100)
        
        team_tasks = Task.query.filter_by(team_id=t.id).all()
        active_tasks = [task for task in team_tasks if task.status not in ['Completed']]
        completed_tasks = [task for task in team_tasks if task.status == 'Completed']
        delayed_tasks = [task for task in active_tasks if task.is_overdue]

        # Calculate assigned workload units
        assigned_units = 0.0
        for task in active_tasks:
            weight = 30.0 if task.priority == 'Critical' else (25.0 if task.priority == 'High' else 15.0)
            assigned_units += weight * (1.0 - (task.progress or 0)/100.0)

        # Assigned percentage relative to team capacity
        assigned_pct = min(120.0, round((assigned_units / float(total_capacity_units)) * 100.0, 1))

        # Completion rate
        total_tasks_count = len(team_tasks)
        completion_rate = round((len(completed_tasks) / total_tasks_count * 100.0), 1) if total_tasks_count > 0 else 0.0

        comparison.append({
            'team': t,
            'member_count': member_count,
            'total_tasks': total_tasks_count,
            'active_tasks': len(active_tasks),
            'completed_tasks': len(completed_tasks),
            'delayed_tasks': len(delayed_tasks),
            'capacity_pct': 100,
            'assigned_pct': assigned_pct,
            'completion_rate': completion_rate,
            'status': 'Over-Allocated' if assigned_pct > 90 else ('Balanced' if assigned_pct >= 40 else 'Under-Allocated')
        })

    return comparison
