"""
Workforce Intelligence Engine
Transparent, rule-based, and explainable decision intelligence algorithms:
1. Smart Task Assignment & Candidate Scoring
2. Leave Impact Conflict Detection
3. Workload Intelligence & Imbalance Detection
4. Task Deadline Risk Detection
5. Skill-Task Matching & Skill Gap Analysis
"""

from datetime import date, datetime, timedelta
from models import db, Employee, Task, Skill, EmployeeSkill, LeaveRequest

PRIORITY_WEIGHTS = {
    'Critical': 35.0,
    'High': 25.0,
    'Medium': 15.0,
    'Low': 10.0
}

PROFICIENCY_SCORES = {
    'Expert': 1.0,
    'Advanced': 0.85,
    'Intermediate': 0.70,
    'Beginner': 0.50
}


def calculate_employee_workload(employee_id):
    """
    Calculates an employee's workload percentage (0% to 100%) and category based on:
    - Active uncompleted tasks
    - Task priority weights
    - Remaining task progress
    - Deadline urgency multiplier
    """
    employee = db.session.get(Employee, employee_id)
    if not employee or employee.status != 'Active':
        return {
            'workload_pct': 0,
            'category': 'Low',
            'badge_class': 'badge-success',
            'active_tasks_count': 0,
            'critical_tasks_count': 0,
            'total_points': 0.0
        }

    active_tasks = Task.query.filter(
        Task.assigned_to == employee_id,
        Task.status.notin_(['Completed', 'Blocked'])
    ).all()

    total_points = 0.0
    critical_count = 0
    today = date.today()

    for task in active_tasks:
        base_weight = PRIORITY_WEIGHTS.get(task.priority, 15.0)
        remaining_ratio = max(0.0, (100 - (task.progress or 0)) / 100.0)
        
        # Urgency multiplier: if due in <= 2 days, apply 1.3x multiplier
        multiplier = 1.0
        if task.due_date:
            days_left = (task.due_date - today).days
            if days_left < 0:
                multiplier = 1.4 # Overdue
            elif days_left <= 2:
                multiplier = 1.25 # Impending deadline

        task_points = base_weight * remaining_ratio * multiplier
        total_points += task_points

        if task.priority in ['High', 'Critical']:
            critical_count += 1

    # Normalize workload points to a 0-100% scale
    # 70 points corresponds to roughly 100% capacity
    normalized_pct = min(100, round((total_points / 70.0) * 100, 1))

    if normalized_pct >= 85:
        category = 'Overloaded'
        badge_class = 'badge-danger'
    elif normalized_pct >= 70:
        category = 'High'
        badge_class = 'badge-warning'
    elif normalized_pct >= 35:
        category = 'Balanced'
        badge_class = 'badge-primary'
    else:
        category = 'Low'
        badge_class = 'badge-success'

    return {
        'workload_pct': normalized_pct,
        'category': category,
        'badge_class': badge_class,
        'active_tasks_count': len(active_tasks),
        'critical_tasks_count': critical_count,
        'total_points': round(total_points, 1)
    }


def detect_team_workload_imbalance(team_id):
    """
    Analyzes team members' workloads and identifies imbalance if the gap
    between highest and lowest utilized employee is significant (>= 40%).
    """
    members = Employee.query.filter_by(team_id=team_id, status='Active').all()
    if len(members) < 2:
        return {
            'has_imbalance': False,
            'summary': 'Team has fewer than 2 active members.',
            'members_data': []
        }

    members_data = []
    for m in members:
        wl = calculate_employee_workload(m.id)
        members_data.append({
            'employee': m,
            'workload': wl
        })

    # Sort descending by workload
    members_data.sort(key=lambda x: x['workload']['workload_pct'], reverse=True)
    highest = members_data[0]
    lowest = members_data[-1]

    gap = highest['workload']['workload_pct'] - lowest['workload']['workload_pct']
    has_imbalance = (gap >= 40.0) or (highest['workload']['workload_pct'] >= 85 and lowest['workload']['workload_pct'] <= 40)

    summary = ""
    if has_imbalance:
        summary = (
            f"Workload Imbalance Detected: {highest['employee'].full_name} is at "
            f"{highest['workload']['workload_pct']}% ({highest['workload']['category']}), while "
            f"{lowest['employee'].full_name} is at {lowest['workload']['workload_pct']}% "
            f"({lowest['workload']['category']}). Disparity: {round(gap, 1)}%. "
            f"Suggested action: Reassign suitable pending tasks to balance capacity."
        )

    return {
        'has_imbalance': has_imbalance,
        'gap': round(gap, 1),
        'highest': highest,
        'lowest': lowest,
        'summary': summary,
        'members_data': members_data
    }


def evaluate_leave_impact(employee_id, start_date, end_date):
    """
    Evaluates business impact when an employee requests leave.
    Checks:
    - Deadlines that occur during leave dates
    - Active high/critical priority tasks
    - Current employee workload
    Returns structured risk warnings for Team Lead review.
    """
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    workload = calculate_employee_workload(employee_id)
    active_tasks = Task.query.filter(
        Task.assigned_to == employee_id,
        Task.status.notin_(['Completed'])
    ).all()

    conflicting_tasks = []
    high_priority_tasks = []

    for t in active_tasks:
        if t.due_date and start_date <= t.due_date <= end_date:
            conflicting_tasks.append(t)
        if t.priority in ['High', 'Critical']:
            high_priority_tasks.append(t)

    has_conflict = len(conflicting_tasks) > 0 or len(high_priority_tasks) > 0 or workload['workload_pct'] >= 75

    severity = 'Low'
    if len(conflicting_tasks) > 0 and len(high_priority_tasks) > 0:
        severity = 'High'
    elif len(conflicting_tasks) > 0 or len(high_priority_tasks) >= 2 or workload['workload_pct'] >= 80:
        severity = 'Medium'

    bullet_points = []
    if len(high_priority_tasks) > 0:
        bullet_points.append(f"{len(high_priority_tasks)} active high/critical priority task(s)")
    if len(conflicting_tasks) > 0:
        bullet_points.append(f"{len(conflicting_tasks)} task deadline(s) falling within leave dates")
    bullet_points.append(f"Current workload: {workload['workload_pct']}% ({workload['category']})")

    summary_text = ""
    if has_conflict:
        summary_text = (
            f"⚠ Leave Impact Detected ({severity} Risk):\n"
            f"• " + "\n• ".join(bullet_points) + "\n"
            f"Recommended action: Review task reassignment or verify delivery before approving."
        )

    return {
        'has_impact': has_conflict,
        'severity': severity,
        'conflicting_tasks': conflicting_tasks,
        'high_priority_tasks': high_priority_tasks,
        'workload': workload,
        'summary': summary_text,
        'bullet_points': bullet_points
    }


def recommend_employees_for_task(required_skill_id, priority, due_date, team_id=None):
    """
    Intelligent rule-based candidate suggestion engine:
    Evaluates team/org candidates based on:
    1. Skill Match (40% weight) - checks proficiency (Expert/Advanced/Intermediate/Beginner)
    2. Available Workload Capacity (35% weight) - inverse of workload
    3. Pending Tasks Queue (15% weight)
    4. Deadline Proximity / Schedule Fit (10% weight)
    Returns transparent ranked candidates with score breakdowns and explanations.
    """
    query = Employee.query.filter_by(status='Active')
    if team_id:
        query = query.filter_by(team_id=team_id)

    candidates = query.all()
    if not candidates and team_id:
        # Fallback to org-wide active employees if team is empty
        candidates = Employee.query.filter_by(status='Active').all()

    if isinstance(due_date, str):
        due_date = datetime.strptime(due_date, '%Y-%m-%d').date()

    req_skill = db.session.get(Skill, required_skill_id) if required_skill_id else None
    results = []

    for emp in candidates:
        workload_data = calculate_employee_workload(emp.id)
        current_workload = workload_data['workload_pct']
        pending_count = workload_data['active_tasks_count']

        # 1. Skill Match (0 to 40 pts)
        skill_score = 0.0
        has_skill = False
        proficiency = None

        if req_skill:
            emp_skill = EmployeeSkill.query.filter_by(employee_id=emp.id, skill_id=req_skill.id).first()
            if emp_skill:
                has_skill = True
                proficiency = emp_skill.proficiency
                mult = PROFICIENCY_SCORES.get(emp_skill.proficiency, 0.70)
                skill_score = 40.0 * mult
            else:
                skill_score = 5.0 # baseline adaptability score
        else:
            skill_score = 30.0 # No specific skill required

        # 2. Capacity Score (0 to 35 pts)
        # Lower workload gives higher capacity points
        capacity_score = max(0.0, 35.0 * ((100.0 - current_workload) / 100.0))

        # 3. Pending Tasks Score (0 to 15 pts)
        # Having fewer than 5 pending tasks is optimal
        pending_penalty = min(pending_count * 3.0, 15.0)
        tasks_score = max(0.0, 15.0 - pending_penalty)

        # 4. Availability / Deadline Fit (0 to 10 pts)
        conflict_tasks = Task.query.filter(
            Task.assigned_to == emp.id,
            Task.status.notin_(['Completed']),
            Task.due_date == due_date
        ).count()
        availability_score = 10.0 if conflict_tasks == 0 else 3.0

        total_score = round(skill_score + capacity_score + tasks_score + availability_score, 1)

        # Transparent explanation generator
        reasons = []
        if req_skill:
            if has_skill:
                reasons.append(f"{req_skill.name} ({proficiency}) verified")
            else:
                reasons.append(f"Missing primary skill {req_skill.name}")
        
        reasons.append(f"Workload {current_workload}% ({workload_data['category']})")
        reasons.append(f"{pending_count} active task(s)")
        
        if conflict_tasks > 0:
            reasons.append("Has another task due on same date")
        else:
            reasons.append("No deadline clash")

        explanation = " • ".join(reasons)

        results.append({
            'employee': emp,
            'score': total_score,
            'has_skill': has_skill,
            'proficiency': proficiency,
            'workload': workload_data,
            'pending_tasks': pending_count,
            'explanation': explanation,
            'is_recommended': False
        })

    # Sort descending by match score
    results.sort(key=lambda x: x['score'], reverse=True)
    if results:
        results[0]['is_recommended'] = True

    return results


def detect_deadline_risks(team_id=None, employee_id=None):
    """
    Identifies tasks approaching deadline that have incomplete progress.
    Rule: Status != 'Completed' AND 0 <= Days Left <= 2 AND Progress < 60%
    (Also detects overdue tasks).
    """
    today = date.today()
    query = Task.query.filter(Task.status.notin_(['Completed']))

    if team_id:
        query = query.filter(Task.team_id == team_id)
    if employee_id:
        query = query.filter(Task.assigned_to == employee_id)

    tasks = query.all()
    at_risk_tasks = []

    for t in tasks:
        days_left = (t.due_date - today).days if t.due_date else 99
        is_overdue = days_left < 0
        is_approaching = (0 <= days_left <= 2) and (t.progress or 0) < 60

        if is_overdue or is_approaching:
            risk_level = 'Critical' if (is_overdue or (days_left <= 1 and t.priority in ['High', 'Critical'])) else 'High'
            at_risk_tasks.append({
                'task': t,
                'days_left': days_left,
                'is_overdue': is_overdue,
                'risk_level': risk_level,
                'reason': f"Due {'yesterday or earlier' if is_overdue else ('in ' + str(days_left) + ' day(s)')} with only {t.progress or 0}% completed."
            })

    return at_risk_tasks


def analyze_skill_gaps(team_id=None):
    """
    Compares organization or team-level skill demand vs skilled employee supply.
    Demand = count of active tasks requiring skill X
    Supply = count of active employees possessing skill X
    """
    skills = Skill.query.all()
    gap_data = []

    for s in skills:
        task_query = Task.query.filter(
            Task.required_skill_id == s.id,
            Task.status.notin_(['Completed'])
        )
        if team_id:
            task_query = task_query.filter(Task.team_id == team_id)
        demand_count = task_query.count()

        emp_query = Employee.query.join(EmployeeSkill).filter(
            EmployeeSkill.skill_id == s.id,
            Employee.status == 'Active'
        )
        if team_id:
            emp_query = emp_query.filter(Employee.team_id == team_id)
        supply_count = emp_query.count()

        # Deficit calculation
        deficit = demand_count - supply_count
        has_gap = (demand_count > 0 and supply_count == 0) or (demand_count > supply_count)

        if demand_count > 0 or supply_count > 0:
            status = 'Critical Gap' if (demand_count > 0 and supply_count == 0) else ('Skill Gap' if has_gap else 'Adequate')
            badge_class = 'badge-danger' if status == 'Critical Gap' else ('badge-warning' if status == 'Skill Gap' else 'badge-success')

            gap_data.append({
                'skill': s,
                'demand': demand_count,
                'supply': supply_count,
                'deficit': deficit,
                'has_gap': has_gap,
                'status': status,
                'badge_class': badge_class
            })

    gap_data.sort(key=lambda x: (x['has_gap'], x['deficit']), reverse=True)
    return gap_data
