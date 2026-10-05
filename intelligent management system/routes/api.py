from flask import Blueprint, jsonify, request, session
from models import db, Notification, Employee, Task, Skill, LeaveRequest
from services.intelligence import (
    recommend_employees_for_task,
    evaluate_leave_impact,
    calculate_employee_workload,
    analyze_skill_gaps,
    detect_deadline_risks
)
from services.analytics_service import get_hr_workforce_analytics, get_manager_team_comparison

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/notifications/unread-count')
def unread_notifications_count():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'count': 0})
    count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    return jsonify({'count': count})


@api_bp.route('/notifications/list')
def notifications_list():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'notifications': []})
    notifs = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(15).all()
    results = [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.type,
        'link': n.link,
        'is_read': n.is_read,
        'time_ago': n.time_ago,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M')
    } for n in notifs]
    return jsonify({'notifications': results})


@api_bp.route('/notifications/<int:notif_id>/mark-read', methods=['POST'])
def mark_notification_read(notif_id):
    user_id = session.get('user_id')
    notif = db.session.get(Notification, notif_id)
    if notif and notif.user_id == user_id:
        notif.is_read = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404


@api_bp.route('/notifications/mark-all-read', methods=['POST'])
def mark_all_notifications_read():
    user_id = session.get('user_id')
    if user_id:
        Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 401


@api_bp.route('/task-recommendations')
def task_recommendations():
    """Returns candidate recommendations based on skill, priority, and deadline."""
    skill_id = request.args.get('skill_id')
    priority = request.args.get('priority', 'Medium')
    due_date = request.args.get('due_date')
    team_id = request.args.get('team_id')

    if not due_date:
        return jsonify({'candidates': []})

    s_id = int(skill_id) if skill_id and skill_id.isdigit() else None
    t_id = int(team_id) if team_id and team_id.isdigit() else None

    recs = recommend_employees_for_task(s_id, priority, due_date, team_id=t_id)
    
    data = [{
        'employee_id': r['employee'].id,
        'full_name': r['employee'].full_name,
        'emp_code': r['employee'].emp_code,
        'score': r['score'],
        'has_skill': r['has_skill'],
        'proficiency': r['proficiency'] or 'N/A',
        'workload_pct': r['workload']['workload_pct'],
        'workload_category': r['workload']['category'],
        'pending_tasks': r['pending_tasks'],
        'explanation': r['explanation'],
        'is_recommended': r['is_recommended']
    } for r in recs]

    return jsonify({'candidates': data})


@api_bp.route('/leave-impact-check')
def leave_impact_check():
    """Checks leave impact conflicts for an employee and date range."""
    emp_id = request.args.get('employee_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not emp_id or not start_date or not end_date:
        return jsonify({'error': 'Missing parameters'}), 400

    impact = evaluate_leave_impact(int(emp_id), start_date, end_date)
    return jsonify({
        'has_impact': impact['has_impact'],
        'severity': impact['severity'],
        'summary': impact['summary'],
        'bullet_points': impact['bullet_points'],
        'workload_pct': impact['workload']['workload_pct']
    })


@api_bp.route('/employee/<int:emp_id>/workload')
def employee_workload(emp_id):
    workload = calculate_employee_workload(emp_id)
    return jsonify(workload)

@api_bp.route('/deadline-risks')
def deadline_risks():
    """Returns at-risk tasks due soon, optionally filtered by team or employee."""
    team_id = request.args.get('team_id')
    employee_id = request.args.get('employee_id')
    try:
        team_id = int(team_id) if team_id and team_id.isdigit() else None
        employee_id = int(employee_id) if employee_id and employee_id.isdigit() else None
    except Exception:
        team_id = employee_id = None
    risks = detect_deadline_risks(team_id=team_id, employee_id=employee_id)
    data = [{
        'task_id': r['task'].id,
        'title': r['task'].title,
        'due_date': r['task'].due_date.strftime('%Y-%m-%d') if r['task'].due_date else None,
        'days_left': r['days_left'],
        'is_overdue': r['is_overdue'],
        'risk_level': r['risk_level'],
        'reason': r['reason']
    } for r in risks]
    return jsonify({'deadline_risks': data})

@api_bp.route('/skill-gaps')
def skill_gaps():
    """Provides organization-wide or team-specific skill gap analysis."""
    team_id = request.args.get('team_id')
    try:
        team_id = int(team_id) if team_id and team_id.isdigit() else None
    except Exception:
        team_id = None
    gaps = analyze_skill_gaps(team_id=team_id)
    data = [{
        'skill_id': g['skill'].id,
        'skill_name': g['skill'].name,
        'demand': g['demand'],
        'supply': g['supply'],
        'deficit': g['deficit'],
        'has_gap': g['has_gap'],
        'status': g['status'],
        'badge_class': g['badge_class']
    } for g in gaps]
    return jsonify({'skill_gaps': data})
