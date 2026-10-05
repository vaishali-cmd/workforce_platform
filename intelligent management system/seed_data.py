"""
Seed Data Script
Populates the Workforce Intelligence & Management Platform with realistic,
consistent demo data across all 4 roles, departments, teams, skills,
tasks, attendance logs, and leave requests.
"""

from datetime import date, datetime, timedelta, time
from app import create_app
from models import (
    db, Role, User, Department, Team, Employee, Skill, EmployeeSkill,
    Task, TaskReassignment, Attendance, LeaveRequest, Notification
)

def seed_database():
    app = create_app()
    with app.app_context():
        print("[SEED] Resetting database tables...")
        db.drop_all()
        db.create_all()

        print("[SEED] Creating Roles...")
        roles = {
            'admin': Role(name='admin', description='Human Resources & System Administration'),
            'manager': Role(name='manager', description='Department & Multi-team Operations Manager'),
            'team_lead': Role(name='team_lead', description='Technical Team Lead & Task Dispatcher'),
            'employee': Role(name='employee', description='Individual Contributor / Workforce Member')
        }
        for r in roles.values():
            db.session.add(r)
        db.session.flush()

        print("[SEED] Creating Departments...")
        depts = {
            'ENG': Department(name='Engineering', code='ENG', description='Software Architecture, Cloud Infrastructure, & Systems'),
            'PRD': Department(name='Product & Design', code='PRD', description='Product Strategy, UI/UX Systems, & User Experience'),
            'OPS': Department(name='Operations & Analytics', code='OPS', description='Business Intelligence, Data Operations, & Analytics'),
            'HR': Department(name='People Operations', code='HR', description='Human Capital, Talent Acquisition, & Culture')
        }
        for d in depts.values():
            db.session.add(d)
        db.session.flush()

        print("[SEED] Creating Skills...")
        skills_data = [
            ('Python', 'Technical', 'Core Python programming and scripting'),
            ('SQL', 'Technical', 'Relational database schema design and query optimization'),
            ('Flask', 'Technical', 'Microservices and web application development'),
            ('HTML/CSS', 'Technical', 'Modern responsive layouts, CSS3 animations, and 3D visual tokens'),
            ('Vanilla JS', 'Technical', 'DOM manipulation, async client-side architecture'),
            ('Database Optimization', 'Technical', 'Query profiling, index strategies, and caching'),
            ('Testing & QA', 'Technical', 'Automated unit, integration, and performance testing'),
            ('UI/UX Design', 'Product', 'Figma workflows, 3D glassmorphism, design systems'),
            ('Project Management', 'Soft Skill', 'Agile sprint dispatch, workload balancing, backlog grooming'),
            ('Cloud Architecture', 'Technical', 'Docker, containerization, and cloud deployment')
        ]
        skills = {}
        for name, category, desc in skills_data:
            s = Skill(name=name, category=category, description=desc)
            db.session.add(s)
            skills[name] = s
        db.session.flush()

        print("[SEED] Creating User Accounts & Employees...")

        def create_user_and_emp(username, email, password, role_name, emp_code, full_name, phone, designation, dept_code, joining_days_ago=120):
            u = User(username=username, email=email, role_id=roles[role_name].id, is_active=True)
            u.set_password(password)
            db.session.add(u)
            db.session.flush()

            emp = Employee(
                user_id=u.id,
                emp_code=emp_code,
                full_name=full_name,
                phone=phone,
                designation=designation,
                department_id=depts[dept_code].id if dept_code else None,
                joining_date=date.today() - timedelta(days=joining_days_ago),
                status='Active'
            )
            db.session.add(emp)
            db.session.flush()
            return u, emp

        # 1. HR Admin
        _, emp_admin = create_user_and_emp('admin', 'admin@workforce.com', 'admin123', 'admin', 'EMP-001', 'Sarah Jenkins', '+1 (555) 101-2001', 'Chief People Officer', 'HR', 400)

        # 2. Manager
        _, emp_manager = create_user_and_emp('manager', 'manager@workforce.com', 'manager123', 'manager', 'EMP-002', 'Priya Sharma', '+1 (555) 101-2002', 'Engineering Operations Manager', 'ENG', 350)

        # 3. Team Lead
        _, emp_lead = create_user_and_emp('teamlead', 'teamlead@workforce.com', 'lead123', 'team_lead', 'EMP-003', 'Rajesh Kumar', '+1 (555) 101-2003', 'Lead Systems Architect & Tech Lead', 'ENG', 300)

        # 4. Employees
        _, emp_vaishali = create_user_and_emp('employee', 'employee@workforce.com', 'emp123', 'employee', 'EMP-004', 'Vaishali Nair', '+1 (555) 101-2004', 'Senior Backend Engineer', 'ENG', 200)
        _, emp_rahul = create_user_and_emp('rahul', 'rahul@workforce.com', 'emp123', 'employee', 'EMP-005', 'Rahul Verma', '+1 (555) 101-2005', 'Database Specialist', 'ENG', 180)
        _, emp_ananya = create_user_and_emp('ananya', 'ananya@workforce.com', 'emp123', 'employee', 'EMP-006', 'Ananya Patel', '+1 (555) 101-2006', 'Frontend UI Engineer', 'PRD', 150)
        _, emp_vikram = create_user_and_emp('vikram', 'vikram@workforce.com', 'emp123', 'employee', 'EMP-007', 'Vikram Singh', '+1 (555) 101-2007', 'QA Automation Engineer', 'ENG', 120)

        print("[SEED] Creating Teams & Hierarchies...")
        team_core = Team(
            name='Core Backend Platform',
            department_id=depts['ENG'].id,
            manager_id=emp_manager.id,
            team_lead_id=emp_lead.id,
            capacity=100,
            status='Active'
        )
        team_frontend = Team(
            name='UI/UX Experience Team',
            department_id=depts['PRD'].id,
            manager_id=emp_manager.id,
            team_lead_id=emp_lead.id,
            capacity=100,
            status='Active'
        )
        db.session.add(team_core)
        db.session.add(team_frontend)
        db.session.flush()

        # Link team affiliations and managers
        for e in [emp_lead, emp_vaishali, emp_rahul, emp_vikram]:
            e.team_id = team_core.id
            e.manager_id = emp_manager.id
            e.team_lead_id = emp_lead.id

        emp_ananya.team_id = team_frontend.id
        emp_ananya.manager_id = emp_manager.id
        emp_ananya.team_lead_id = emp_lead.id
        db.session.flush()

        print("[SEED] Assigning Employee Skills...")
        emp_skill_map = [
            (emp_vaishali, [('Python', 'Expert'), ('Flask', 'Expert'), ('SQL', 'Advanced'), ('Testing & QA', 'Intermediate')]),
            (emp_rahul, [('SQL', 'Expert'), ('Database Optimization', 'Expert'), ('Python', 'Intermediate')]),
            (emp_ananya, [('HTML/CSS', 'Expert'), ('Vanilla JS', 'Advanced'), ('UI/UX Design', 'Advanced')]),
            (emp_vikram, [('Testing & QA', 'Expert'), ('Python', 'Intermediate'), ('SQL', 'Intermediate')]),
            (emp_lead, [('Python', 'Expert'), ('Cloud Architecture', 'Expert'), ('Project Management', 'Advanced'), ('SQL', 'Advanced')]),
            (emp_manager, [('Project Management', 'Expert'), ('Cloud Architecture', 'Intermediate')])
        ]
        for emp, skill_list in emp_skill_map:
            for s_name, prof in skill_list:
                es = EmployeeSkill(employee_id=emp.id, skill_id=skills[s_name].id, proficiency=prof)
                db.session.add(es)
        db.session.flush()

        print("[SEED] Creating Tasks & Workloads...")
        today = date.today()

        # Vaishali's tasks: high priority and close deadline to set up the Leave Impact scenario!
        t1 = Task(
            task_code='TSK-0001',
            title='Database Query Performance Optimization',
            description='Analyze slow ORM queries, add composite indexes, and optimize connection pooling under high throughput.',
            required_skill_id=skills['Database Optimization'].id,
            priority='Critical',
            status='In Progress',
            progress=35,
            assigned_to=emp_vaishali.id,
            team_id=team_core.id,
            created_by=emp_lead.id,
            start_date=today - timedelta(days=2),
            due_date=today + timedelta(days=1), # Due tomorrow!
            remarks='Approaching critical milestone deadline.'
        )

        t2 = Task(
            task_code='TSK-0002',
            title='JWT & Session Security Layer Audit',
            description='Enforce server-side role validation, secure cookie policies, and protection against unauthorized URL access.',
            required_skill_id=skills['Python'].id,
            priority='High',
            status='In Progress',
            progress=40,
            assigned_to=emp_vaishali.id,
            team_id=team_core.id,
            created_by=emp_lead.id,
            start_date=today - timedelta(days=3),
            due_date=today + timedelta(days=2),
            remarks='High priority security gate.'
        )

        # Rahul's tasks: light workload, ready for smart task assignment
        t3 = Task(
            task_code='TSK-0003',
            title='Audit Read Replica Latency',
            description='Inspect replication lag across secondary database nodes and log metrics to monitoring dashboard.',
            required_skill_id=skills['SQL'].id,
            priority='Medium',
            status='In Progress',
            progress=65,
            assigned_to=emp_rahul.id,
            team_id=team_core.id,
            created_by=emp_lead.id,
            start_date=today - timedelta(days=4),
            due_date=today + timedelta(days=6)
        )

        # Ananya's tasks
        t4 = Task(
            task_code='TSK-0004',
            title='3D SaaS Glassmorphic Component Tokens',
            description='Implement custom responsive sidebar, layered cards, and vibrant gradient themes using vanilla CSS.',
            required_skill_id=skills['HTML/CSS'].id,
            priority='Medium',
            status='In Progress',
            progress=85,
            assigned_to=emp_ananya.id,
            team_id=team_frontend.id,
            created_by=emp_lead.id,
            start_date=today - timedelta(days=5),
            due_date=today + timedelta(days=3)
        )

        # Vikram's completed task
        t5 = Task(
            task_code='TSK-0005',
            title='Regression Test Suite Pipeline',
            description='Automate end-to-end smoke test execution on pull request merges.',
            required_skill_id=skills['Testing & QA'].id,
            priority='Low',
            status='Completed',
            progress=100,
            assigned_to=emp_vikram.id,
            team_id=team_core.id,
            created_by=emp_lead.id,
            start_date=today - timedelta(days=10),
            due_date=today - timedelta(days=1),
            completed_at=datetime.utcnow() - timedelta(days=1)
        )

        for t in [t1, t2, t3, t4, t5]:
            db.session.add(t)
        db.session.flush()

        print("[SEED] Creating Attendance Records...")
        # Past 7 days attendance for attendance trend charts
        for day_offset in range(6, -1, -1):
            att_date = today - timedelta(days=day_offset)
            # Skip weekend days for realism
            if att_date.weekday() >= 5:
                continue

            for emp in [emp_lead, emp_vaishali, emp_rahul, emp_ananya, emp_vikram]:
                is_today = (day_offset == 0)
                cin = time(9, 15, 0)
                cout = time(17, 45, 0) if not is_today else None
                hrs = 8.5 if cout else 0.0
                status = 'Present'

                att = Attendance(
                    employee_id=emp.id,
                    date=att_date,
                    check_in=cin,
                    check_out=cout,
                    working_hours=hrs,
                    status=status
                )
                db.session.add(att)

        print("[SEED] Creating Leave Requests...")
        # Vaishali's pending leave request covering tomorrow -> conflicts with TSK-0001 deadline!
        leave_vaishali = LeaveRequest(
            employee_id=emp_vaishali.id,
            leave_type='Casual Leave',
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=3),
            days_count=3,
            reason='Family commitment and travel outside the city.',
            status='Pending',
            impact_warning='⚠ Leave Impact Detected: Employee has 2 active High/Critical priority tasks and 1 deadline due during requested leave period.'
        )
        db.session.add(leave_vaishali)

        # Past approved leave for Rahul
        leave_rahul = LeaveRequest(
            employee_id=emp_rahul.id,
            leave_type='Sick Leave',
            start_date=today - timedelta(days=14),
            end_date=today - timedelta(days=13),
            days_count=2,
            reason='Viral fever and doctor consultation.',
            status='Approved',
            reviewed_by=emp_lead.id
        )
        db.session.add(leave_rahul)

        # Past rejected leave for Vikram
        leave_vikram = LeaveRequest(
            employee_id=emp_vikram.id,
            leave_type='Casual Leave',
            start_date=today - timedelta(days=20),
            end_date=today - timedelta(days=18),
            days_count=3,
            reason='Personal vacation.',
            status='Rejected',
            reviewed_by=emp_lead.id,
            rejection_reason='Critical sprint delivery phase.'
        )
        db.session.add(leave_vikram)

        print("[SEED] Creating Notifications...")
        notifs = [
            (emp_vaishali.user_id, 'Leave Request Submitted', 'Your Casual Leave request for 3 days has been sent to Team Lead for review.', 'info', '/employee/leaves'),
            (emp_vaishali.user_id, 'Task Deadline Approaching', 'Task TSK-0001 (Critical) is due tomorrow. Please review progress.', 'warning', '/employee/tasks'),
            (emp_lead.user_id, 'Pending Leave Request', f'Vaishali Nair applied for Casual Leave ({today + timedelta(days=1)} to {today + timedelta(days=3)}). Impact warning detected.', 'warning', '/team-lead/leaves'),
            (emp_lead.user_id, 'Deadline Risk Alert', 'Task TSK-0001 is approaching deadline with only 35% completed.', 'danger', '/team-lead/tasks'),
            (emp_manager.user_id, 'Weekly Workforce Briefing', 'Core Backend Platform is operating at 86% capacity with 2 critical milestones.', 'info', '/manager/dashboard'),
            (emp_admin.user_id, 'System Initialization', 'Workforce Intelligence & Management Platform seeded and operational.', 'success', '/admin/dashboard')
        ]
        for uid, title, msg, ntype, link in notifs:
            n = Notification(user_id=uid, title=title, message=msg, type=ntype, link=link, is_read=False)
            db.session.add(n)

        db.session.commit()
        print("[SEED SUCCESS] Database successfully initialized with realistic workforce data!")
        print("Demo accounts:")
        print("  HR / Admin : admin@workforce.com     | Password: admin123")
        print("  Manager    : manager@workforce.com   | Password: manager123")
        print("  Team Lead  : teamlead@workforce.com  | Password: lead123")
        print("  Employee   : employee@workforce.com  | Password: emp123 (Vaishali Nair)")
        print("  Employee 2 : rahul@workforce.com     | Password: emp123 (Rahul Verma)")

if __name__ == '__main__':
    seed_database()
