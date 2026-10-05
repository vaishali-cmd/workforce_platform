from datetime import date
from flask import Blueprint, render_template, request, session, redirect, url_for
from models import db, Employee, Department, Team, Task, Skill, EmployeeSkill, Attendance
from routes.auth import login_required, role_required
from services.analytics_service import get_manager_team_comparison
from services.intelligence import analyze_skill_gaps, detect_deadline_risks

manager_bp = Blueprint('manager', __name__, url_prefix='/manager')


@manager_bp.before_request
@login_required
@role_required(['manager', 'admin'])
def before_request():
    pass


@manager_bp.route('/', strict_slashes=False)
def index():
    return redirect(url_for('manager.dashboard'))


@manager_bp.route('/dashboard')
def dashboard():
    emp_id = session.get('employee_id')
    
    teams_comparison = get_manager_team_comparison()
    total_teams = len(teams_comparison)
    total_employees = sum(t['member_count'] for t in teams_comparison)
    total_active_tasks = sum(t['active_tasks'] for t in teams_comparison)
    total_delayed_tasks = sum(t['delayed_tasks'] for t in teams_comparison)
    total_completed_tasks = sum(t['completed_tasks'] for t in teams_comparison)
    
    # Average assigned capacity
    avg_capacity = round(sum(t['assigned_pct'] for t in teams_comparison) / max(1, total_teams), 1)
    
    # Skill gaps
    skill_gaps = analyze_skill_gaps()
    critical_gaps_count = sum(1 for g in skill_gaps if g['has_gap'])

    # Delayed tasks list
    delayed_tasks = Task.query.filter(
        Task.status.notin_(['Completed']),
        Task.due_date < date.today()
    ).order_by(Task.due_date.asc()).limit(6).all()

    # Chart data for team comparison
    team_labels = [t['team'].name for t in teams_comparison]
    team_workloads = [t['assigned_pct'] for t in teams_comparison]
    team_completions = [t['completion_rate'] for t in teams_comparison]

    return render_template(
        'manager/dashboard.html',
        total_teams=total_teams,
        total_employees=total_employees,
        total_active_tasks=total_active_tasks,
        total_delayed_tasks=total_delayed_tasks,
        total_completed_tasks=total_completed_tasks,
        avg_capacity=avg_capacity,
        critical_gaps_count=critical_gaps_count,
        teams_comparison=teams_comparison,
        delayed_tasks=delayed_tasks,
        team_labels=team_labels,
        team_workloads=team_workloads,
        team_completions=team_completions,
        skill_gaps=skill_gaps[:5]
    )


@manager_bp.route('/teams')
def teams():
    teams_comparison = get_manager_team_comparison()
    return render_template('manager/teams.html', teams_comparison=teams_comparison)


@manager_bp.route('/workload')
def workload():
    teams_comparison = get_manager_team_comparison()
    return render_template('manager/workload.html', teams_comparison=teams_comparison)


@manager_bp.route('/skill-gaps')
def skill_gaps():
    gaps = analyze_skill_gaps()
    return render_template('manager/skill_gaps.html', skill_gaps=gaps)
