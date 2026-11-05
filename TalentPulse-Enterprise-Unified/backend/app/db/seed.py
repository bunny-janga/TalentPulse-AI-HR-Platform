import os
import random
import json
from datetime import datetime, date, timedelta
from app.db.session import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.department import Department
from app.models.user import User
from app.models.employee import Employee
from app.models.leave import LeaveRequest
from app.models.review import PerformanceReview
from app.models.policy import PolicyDocument
from app.models.survey import EngagementSurvey, SurveyResponse
from app.models.onboarding import OnboardingTask
from app.models.attrition import AttritionScore
from app.models.communication import Notification

def seed_database():
    print("=" * 60)
    print("TalentPulse AI: Initializing Database & Seeding Data...")
    print("=" * 60)

    # Create tables if not exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded (prevent duplicate insertion if employees exist)
        existing_users = db.query(User).count()
        if existing_users >= 5:
            print(f"Database already contains {existing_users} users. Skipping seed.")
            return

        print("1. Creating Departments...")
        departments_data = [
            {"name": "Software Engineering", "code": "SWE", "description": "Full-stack, backend, mobile and platform software development."},
            {"name": "Quality Assurance & Testing", "code": "QA", "description": "Manual testing, automated regression, and performance validation."},
            {"name": "Cloud & DevOps Infrastructure", "code": "INFRA", "description": "Cloud architecture, Kubernetes, CI/CD pipelines, and SRE operations."},
            {"name": "Data Science & AI Solutions", "code": "AI", "description": "Predictive analytics, GenAI solutions, machine learning, and data pipelines."},
            {"name": "Product & UI/UX Design", "code": "DES", "description": "User experience research, wireframing, design systems and product management."},
            {"name": "HR & People Operations", "code": "OPS", "description": "Talent acquisition, employee engagement, payroll, benefits and retention."},
        ]

        departments = {}
        for d in departments_data:
            dept = db.query(Department).filter(Department.code == d["code"]).first()
            if not dept:
                dept = Department(**d)
                db.add(dept)
                db.flush()
            departments[d["code"]] = dept

        print("2. Creating Core Demo Accounts...")
        # 0. Super Admin (Higher Authority Category: Assigning Authority & Admin Access Control)
        superadmin_user = db.query(User).filter(User.email == "superadmin@talentpulse.local").first()
        if not superadmin_user:
            superadmin_user = User(
                email="superadmin@talentpulse.local",
                hashed_password=get_password_hash("super123!"),
                initial_password="super123!",
                full_name="Dr. APJ Executive (Super Admin)",
                role="superadmin",
                department_id=departments["EXEC"].id if "EXEC" in departments else departments["OPS"].id,
                is_active=True
            )
            db.add(superadmin_user)
            db.flush()

        # 1. Admin
        admin_user = db.query(User).filter(User.email == "admin@talentpulse.local").first()
        if not admin_user:
            admin_user = User(
                email="admin@talentpulse.local",
                hashed_password=get_password_hash("Admin123!"),
                initial_password="Admin123!",
                full_name="Vikramaditya Sharma",
                role="admin",
                department_id=departments["OPS"].id,
                is_active=True
            )
            db.add(admin_user)
            db.flush()

        # 2. HR Lead
        hr_user = db.query(User).filter(User.email == "hr@talentpulse.local").first()
        if not hr_user:
            hr_user = User(
                email="hr@talentpulse.local",
                hashed_password=get_password_hash("Hr123!"),
                initial_password="Hr123!",
                full_name="Sneha Kulkarni",
                role="hr",
                department_id=departments["OPS"].id,
                manager_id=admin_user.id,
                is_active=True
            )
            db.add(hr_user)
            db.flush()

        # 3. Primary Engineering Manager (Rajesh Varma)
        mgr1_user = db.query(User).filter(User.email == "manager@talentpulse.local").first()
        if not mgr1_user:
            mgr1_user = User(
                email="manager@talentpulse.local",
                hashed_password=get_password_hash("Manager123!"),
                initial_password="Manager123!",
                full_name="Rajesh Varma",
                role="manager",
                department_id=departments["SWE"].id,
                manager_id=admin_user.id,
                is_active=True
            )
            db.add(mgr1_user)
            db.flush()

        # 4. Unrelated QA Manager (Anand Rao - for testing access control boundaries)
        mgr2_user = db.query(User).filter(User.email == "manager2@talentpulse.local").first()
        if not mgr2_user:
            mgr2_user = User(
                email="manager2@talentpulse.local",
                hashed_password=get_password_hash("Manager123!"),
                initial_password="Manager123!",
                full_name="Anand Rao",
                role="manager",
                department_id=departments["QA"].id,
                manager_id=admin_user.id,
                is_active=True
            )
            db.add(mgr2_user)
            db.flush()

        # Additional managers for other depts
        mgr_infra = User(
            email="infra.lead@talentpulse.local",
            hashed_password=get_password_hash("Manager123!"),
            initial_password="Manager123!",
            full_name="Manoj Nambiar",
            role="manager",
            department_id=departments["INFRA"].id,
            manager_id=admin_user.id,
            is_active=True
        )
        db.add(mgr_infra)

        mgr_ai = User(
            email="ai.lead@talentpulse.local",
            hashed_password=get_password_hash("Manager123!"),
            initial_password="Manager123!",
            full_name="Dr. Haritha Sundaram",
            role="manager",
            department_id=departments["AI"].id,
            manager_id=admin_user.id,
            is_active=True
        )
        db.add(mgr_ai)

        mgr_des = User(
            email="design.lead@talentpulse.local",
            hashed_password=get_password_hash("Manager123!"),
            initial_password="Manager123!",
            full_name="Divya Chandran",
            role="manager",
            department_id=departments["DES"].id,
            manager_id=admin_user.id,
            is_active=True
        )
        db.add(mgr_des)
        db.flush()

        # 5. Core Demo Employee (reports directly to Rajesh Varma)
        emp_user = db.query(User).filter(User.email == "employee@talentpulse.local").first()
        if not emp_user:
            emp_user = User(
                email="employee@talentpulse.local",
                hashed_password=get_password_hash("Employee123!"),
                initial_password="Employee123!",
                full_name="Kavya Reddy",
                role="employee",
                department_id=departments["SWE"].id,
                manager_id=mgr1_user.id,
                is_active=True
            )
            db.add(emp_user)
            db.flush()

        # Create employee record for Kavya
        emp_kavya = Employee(
            user_id=emp_user.id,
            employee_code="EMP-1001",
            job_title="Senior Software Engineer",
            hire_date=date.today() - timedelta(days=780),
            salary=1250000.0,
            salary_band="Medium",
            overtime_status=True,
            performance_rating=3.2,
            last_promotion_date=date.today() - timedelta(days=600),
            total_experience_years=5.5,
            years_at_company=2.1,
            location="Visakhapatnam"
        )
        db.add(emp_kavya)
        db.flush()

        # Also create employee profiles for managers and HR
        mgr1_emp = Employee(
            user_id=mgr1_user.id,
            employee_code="EMP-1002",
            job_title="Engineering Manager",
            hire_date=date.today() - timedelta(days=1800),
            salary=2400000.0,
            salary_band="High",
            overtime_status=False,
            performance_rating=4.5,
            last_promotion_date=date.today() - timedelta(days=365),
            total_experience_years=11.0,
            years_at_company=5.0,
            location="Visakhapatnam"
        )
        db.add(mgr1_emp)

        mgr2_emp = Employee(
            user_id=mgr2_user.id,
            employee_code="EMP-1003",
            job_title="QA Manager",
            hire_date=date.today() - timedelta(days=1500),
            salary=2100000.0,
            salary_band="High",
            overtime_status=False,
            performance_rating=4.2,
            last_promotion_date=date.today() - timedelta(days=400),
            total_experience_years=10.0,
            years_at_company=4.2,
            location="Visakhapatnam"
        )
        db.add(mgr2_emp)

        hr_emp = Employee(
            user_id=hr_user.id,
            employee_code="EMP-1004",
            job_title="HR Operations Lead",
            hire_date=date.today() - timedelta(days=1200),
            salary=1500000.0,
            salary_band="Medium",
            overtime_status=False,
            performance_rating=4.0,
            last_promotion_date=date.today() - timedelta(days=450),
            total_experience_years=7.5,
            years_at_company=3.3,
            location="Visakhapatnam"
        )
        db.add(hr_emp)

        superadmin_emp = Employee(
            user_id=superadmin_user.id,
            employee_code="EMP-SA-0001",
            job_title="Chief Executive Officer",
            hire_date=date.today() - timedelta(days=2200),
            salary=3500000.0,
            salary_band="High",
            overtime_status=False,
            performance_rating=5.0,
            last_promotion_date=date.today() - timedelta(days=365),
            total_experience_years=16.0,
            years_at_company=6.0,
            location="Visakhapatnam"
        )
        db.add(superadmin_emp)

        admin_emp = Employee(
            user_id=admin_user.id,
            employee_code="EMP-ADM-0002",
            job_title="Head of People Operations",
            hire_date=date.today() - timedelta(days=2000),
            salary=2800000.0,
            salary_band="High",
            overtime_status=False,
            performance_rating=4.8,
            last_promotion_date=date.today() - timedelta(days=365),
            total_experience_years=13.0,
            years_at_company=5.5,
            location="Visakhapatnam"
        )
        db.add(admin_emp)
        db.flush()

        print("3. Generating 60 Synthetic Employees across 6 Departments...")
        first_names = [
            "Sai", "Praneeth", "Divya", "Suresh", "Swathi", "Ramesh", "Ananya", "Karthik",
            "Pooja", "Arvind", "Keerthi", "Naveen", "Bhavani", "Tarun", "Deepika", "Sandeep",
            "Harish", "Aishwarya", "Mahesh", "Sravani", "Santosh", "Vandana", "Ganesh", "Madhuri",
            "Venkatesh", "Lavanya", "Kishore", "Roopa", "Pradeep", "Meghana", "Charan", "Sireesha",
            "Bhargav", "Preethi", "Ashok", "Sujatha", "Vinay", "Padmaja", "Ravi", "Geetha",
            "Sunil", "Aparna", "Raghav", "Suma", "Chaitanya", "Radhika", "Praveen", "Swapna",
            "Naresh", "Jhansi", "Gopi", "Pavani", "Mohan", "Gayathri", "Shiva", "Pallavi",
            "Kiran", "Sandhya", "Srikanth", "Anitha"
        ]
        last_names = [
            "Varma", "Reddy", "Rao", "Prasad", "Patnaik", "Chowdary", "Naidu", "Sharma",
            "Murthy", "Raju", "Gupta", "Nair", "Pillai", "Das", "Sen", "Joshi", "Babu",
            "Kulkarni", "Mishra", "Venkatesan"
        ]

        dept_managers = {
            "SWE": mgr1_user,
            "QA": mgr2_user,
            "INFRA": mgr_infra,
            "AI": mgr_ai,
            "DES": mgr_des,
            "OPS": hr_user,
        }

        dept_titles = {
            "SWE": ["Software Engineer", "Senior Software Engineer", "Backend Developer", "Frontend Developer", "Full Stack Engineer"],
            "QA": ["QA Automation Engineer", "Manual Test Analyst", "SDET", "Performance Test Engineer"],
            "INFRA": ["DevOps Engineer", "Cloud Infrastructure Engineer", "Site Reliability Engineer", "Systems Admin"],
            "AI": ["Machine Learning Engineer", "Data Scientist", "NLP Specialist", "AI Research Analyst"],
            "DES": ["UI/UX Designer", "Product Designer", "User Researcher", "Visual Designer"],
            "OPS": ["HR Specialist", "Talent Acquisition Associate", "HR Business Partner", "Operations Coordinator"]
        }

        all_employees = [emp_kavya]
        all_employee_users = [emp_user]

        random.seed(42)  # Deterministic seed for reproducible testing

        # Let's flag a few specific employees for AI 2 (consecutive declining reviews)
        declining_review_indices = {4, 12, 19, 28, 41}
        # High attrition risk candidates
        high_risk_indices = {4, 7, 12, 18, 28, 35, 45, 52}

        dept_keys = list(departments.keys())

        for i in range(len(first_names)):
            fn = first_names[i]
            ln = random.choice(last_names)
            full_name = f"{fn} {ln}"
            email = f"{fn.lower()}.{ln.lower()}{i+10}@talentpulse.local"
            emp_code = f"EMP-{1005 + i}"
            dept_key = dept_keys[i % len(dept_keys)]
            dept = departments[dept_key]
            mgr = dept_managers[dept_key]
            job_title = random.choice(dept_titles[dept_key])

            # Experience & tenure
            tenure_months = random.randint(4, 84)
            hire_d = date.today() - timedelta(days=tenure_months * 30)
            exp_years = round((tenure_months / 12.0) + random.uniform(0.5, 6.0), 1)
            tenure_years = round(tenure_months / 12.0, 1)

            # Salary band
            if exp_years < 3.0:
                salary_band = "Low"
                salary = random.randint(450000, 750000)
            elif exp_years < 7.0:
                salary_band = "Medium"
                salary = random.randint(800000, 1500000)
            else:
                salary_band = "High"
                salary = random.randint(1550000, 2600000)

            # High risk or overtime attributes
            if i in high_risk_indices:
                overtime = True
                perf_rating = random.choice([2.5, 2.8, 3.0])
                last_promo_months = random.randint(36, 60)
            else:
                overtime = random.random() < 0.28
                perf_rating = round(random.uniform(3.2, 4.8), 1)
                last_promo_months = random.randint(8, 28)

            last_promo_d = date.today() - timedelta(days=last_promo_months * 30)
            if last_promo_d < hire_d:
                last_promo_d = hire_d

            u = User(
                email=email,
                hashed_password=get_password_hash("Password123!"),
                initial_password="Password123!",
                full_name=full_name,
                role="employee",
                department_id=dept.id,
                manager_id=mgr.id,
                is_active=True
            )
            db.add(u)
            db.flush()

            emp = Employee(
                user_id=u.id,
                employee_code=emp_code,
                job_title=job_title,
                hire_date=hire_d,
                salary=float(salary),
                salary_band=salary_band,
                overtime_status=overtime,
                performance_rating=perf_rating,
                last_promotion_date=last_promo_d,
                total_experience_years=exp_years,
                years_at_company=tenure_years,
                location="Visakhapatnam"
            )
            db.add(emp)
            db.flush()

            all_employees.append(emp)
            all_employee_users.append(u)

        print(f"Total employees seeded: {len(all_employees)}")

        print("4. Generating Historical Performance Reviews...")
        # Review cycles: 2024-H1, 2024-H2, 2025-H1
        cycles = ["2024-H1", "2024-H2", "2025-H1"]
        for idx, emp in enumerate(all_employees):
            mgr_user_id = emp.user.manager_id or mgr1_user.id
            if idx in declining_review_indices:
                # Deliberately failing/declining review ratings (e.g., 4 -> 3 -> 2)
                ratings = [4, 3, 2]
                comments_list = [
                    ("Met expectations in early deliverables.", "Strong coding foundation.", "Need better test coverage.", "Deliver on time"),
                    ("Output dropped, missed 2 sprint commitments.", "Good domain knowledge.", "Requires frequent follow-up.", "Improve punctuality and ownership"),
                    ("Significant performance slump. Low engagement.", "Assists juniors when asked.", "Chronic delays and unresponsiveness.", "Action plan required")
                ]
            else:
                # Normal or strong ratings
                base_r = int(emp.performance_rating)
                ratings = [
                    max(1, min(5, base_r + random.choice([-1, 0]))),
                    max(1, min(5, base_r + random.choice([0, 1]))),
                    max(1, min(5, base_r + random.choice([0, 1])))
                ]
                comments_list = [
                    ("Consistently dependable sprint performer.", "Solid technical execution.", "Can mentor newer engineers.", "Lead tech spike"),
                    ("Exceeded team targets during release.", "Cross-functional communication.", "Deepen cloud architecture knowledge.", "Drive system refactoring"),
                    ("Outstanding contribution to production stability.", "Proactive problem solver.", "Public speaking and tech blogging.", "Architect next microservice")
                ]

            for c_idx, cycle in enumerate(cycles):
                r_rating = ratings[c_idx]
                fback, strn, grw, gls = comments_list[c_idx]
                rev = PerformanceReview(
                    employee_id=emp.id,
                    reviewer_id=mgr_user_id,
                    review_cycle=cycle,
                    rating=r_rating,
                    feedback=fback,
                    strengths=strn,
                    growth_areas=grw,
                    goals=gls,
                    status="COMPLETED",
                    created_at=datetime.utcnow() - timedelta(days=(3 - c_idx) * 120)
                )
                db.add(rev)

        print("5. Generating Sample Leave History...")
        leave_types = ["Sick Leave", "Casual Leave", "Earned Leave", "Unpaid Leave"]
        reasons = [
            "Fever and medical consultation in Vizag Hospital.",
            "Family wedding ceremony in hometown.",
            "Personal domestic work and bank errands.",
            "Annual family vacation and recharge.",
            "Minor surgical procedure recovery.",
            "Home shifting and parental assistance."
        ]

        for idx, emp in enumerate(all_employees):
            # Generate 2 to 4 leave records
            num_leaves = random.randint(2, 4)
            for _ in range(num_leaves):
                days = random.randint(1, 5)
                start_offset = random.randint(15, 300)
                st_d = date.today() - timedelta(days=start_offset)
                en_d = st_d + timedelta(days=days - 1)
                
                # Status: recent ones might be pending
                if start_offset < 30 and random.random() < 0.4:
                    status = "PENDING"
                    approver_id = None
                    approver_comment = None
                else:
                    status = random.choice(["APPROVED", "APPROVED", "APPROVED", "REJECTED"])
                    approver_id = emp.user.manager_id or mgr1_user.id
                    approver_comment = "Approved as per leave policy quota." if status == "APPROVED" else "Rejected due to critical release freeze."

                lr = LeaveRequest(
                    employee_id=emp.id,
                    leave_type=random.choice(leave_types),
                    start_date=st_d,
                    end_date=en_d,
                    days_count=days,
                    reason=random.choice(reasons),
                    status=status,
                    approver_id=approver_id,
                    approver_comment=approver_comment,
                    created_at=datetime.utcnow() - timedelta(days=start_offset + 3)
                )
                db.add(lr)

        print("6. Creating Engagement Surveys & Responses...")
        survey1 = EngagementSurvey(
            title="Q1 2025 Workplace Happiness & Pulse Survey",
            description="Quarterly pulse check covering work-life balance, compensation satisfaction, manager support and career growth in Visakhapatnam center.",
            is_active=True,
            created_by=hr_user.id
        )
        survey2 = EngagementSurvey(
            title="2024 Annual Engineering & Operations Satisfaction Check",
            description="Detailed annual feedback on company policies, hybrid work expectations, and professional development programs.",
            is_active=False,
            created_by=hr_user.id
        )
        db.add(survey1)
        db.add(survey2)
        db.flush()

        positive_comments = [
            "Great supportive team culture and collaborative colleagues in Vizag center.",
            "Leadership communicates town hall updates transparently. Enjoying my project.",
            "Good learning curve on cloud and GenAI tools, manager provides clear feedback.",
            "Work-life balance is respected and flexible working hours help a lot."
        ]
        neutral_comments = [
            "Work is okay, but promotion process could be more data-driven and objective.",
            "Average salary increment compared to Tier-1 metro IT standards, but manageable.",
            "Tools and hardware setup could be upgraded for faster compilation speeds.",
            "Leave approvals are sometimes delayed because everything is scattered."
        ]
        negative_comments = [
            "Excessive overtime hours and constant weekend deployments without comp-off.",
            "Haven't had a salary review or promotion in over 3 years. Feeling undervalued.",
            "Micromanagement and unclear roadmap from client leads causing severe burnout.",
            "Lack of growth opportunities. Thinking about exploring external offers soon."
        ]

        for idx, emp in enumerate(all_employees):
            if random.random() < 0.85:  # 85% response rate
                if idx in high_risk_indices:
                    score = random.choice([1, 2])
                    comm = random.choice(negative_comments)
                    sent_score = round(random.uniform(-0.85, -0.4), 2)
                    sent_label = "Negative"
                elif random.random() < 0.6:
                    score = random.choice([4, 5])
                    comm = random.choice(positive_comments)
                    sent_score = round(random.uniform(0.45, 0.9), 2)
                    sent_label = "Positive"
                else:
                    score = 3
                    comm = random.choice(neutral_comments)
                    sent_score = round(random.uniform(-0.15, 0.2), 2)
                    sent_label = "Neutral"

                resp = SurveyResponse(
                    survey_id=survey1.id,
                    employee_id=emp.id,
                    score=score,
                    comments=comm,
                    sentiment_score=sent_score,
                    sentiment_label=sent_label,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(5, 45))
                )
                db.add(resp)

        print("7. Seeding Onboarding Checklist Tasks...")
        standard_tasks = [
            ("Visakhapatnam IT ID Badge & Biometric Registration", "Collect physical badge from security desk at Block B, ground floor.", "IT Setup"),
            ("Sign Non-Disclosure Agreement (NDA) & Code of Conduct", "Submit digitally signed copies of company ethics guidelines to HR.", "HR Paperwork"),
            ("Developer Workstation Provisioning & GitHub Access", "Configure standard Docker, Python, Node.js and AWS sandbox credentials.", "IT Setup"),
            ("Mandatory POSH & Information Security Compliance Training", "Complete self-paced e-learning modules and pass the 80% test.", "Training"),
            ("1-on-1 Welcome & OKR Alignment Session with Manager", "Meet reporting manager to establish 90-day objectives and project roadmap.", "Team Intro"),
            ("Enroll in Group Medical & Health Insurance Scheme", "Add family dependents to policy portal for medical claim coverage.", "HR Paperwork")
        ]

        # Assign onboarding tasks to recent hires (tenure <= 6 months)
        for emp in all_employees:
            if emp.years_at_company <= 0.6 or emp.id == emp_kavya.id:
                for t_title, t_desc, t_cat in standard_tasks:
                    is_done = random.random() < 0.7
                    task = OnboardingTask(
                        employee_id=emp.id,
                        title=t_title,
                        description=t_desc,
                        category=t_cat,
                        due_date=date.today() + timedelta(days=random.randint(5, 20)),
                        is_completed=is_done,
                        completed_at=datetime.utcnow() - timedelta(days=random.randint(1, 10)) if is_done else None
                    )
                    db.add(task)

        print("8. Seeding Standard HR Policy Documents...")
        # Seed realistic HR policies so RAG / Helpdesk works out of the box!
        policies_data = [
            {
                "title": "Comprehensive Leave Policy 2025",
                "category": "Leave",
                "text": """TALENTPULSE TECHNOLOGIES - LEAVE POLICY 2025
1. Casual Leave (CL): All full-time employees are entitled to 12 days of Casual Leave per calendar year, credited pro-rata at 1 day per month. Casual leaves can be availed up to 3 consecutive days with prior manager approval. Unavailed CL lapses at year-end.
2. Sick Leave (SL): Employees are granted 10 days of Sick Leave per calendar year. For sick leave exceeding 2 continuous days, a registered medical practitioner certificate is mandatory. Sick leave can be accumulated up to a maximum of 30 days.
3. Earned Leave / Privilege Leave (EL): Employees earn 15 days of Earned Leave annually (1.25 days per month of service). EL requires manager approval at least 14 days in advance. A maximum of 45 days can be accumulated or encashed at separation.
4. Maternity Leave: Female employees who have worked for at least 80 days in the preceding 12 months are eligible for 26 weeks (182 days) of fully paid Maternity Leave for up to two surviving children. Additional 30 days of leave is available in case of medical complications.
5. Paternity Leave: New fathers are entitled to 10 consecutive working days of paid Paternity Leave, to be availed within 6 months of childbirth or legal adoption.
6. Bereavement Leave: 5 days of paid leave is granted in the unfortunate event of the demise of an immediate family member (parents, spouse, siblings, children).
7. Compensatory Off (Comp-off): Employees who work on declared company holidays or weekends under direct manager sign-off may claim a compensatory day off within 60 days of the occurrence."""
            },
            {
                "title": "Health Benefits, Insurance and Wellness Policy",
                "category": "Benefits",
                "text": """TALENTPULSE TECHNOLOGIES - MEDICAL INSURANCE & EMPLOYEE WELL-BEING POLICY
1. Group Medical Insurance (GMC): Every employee is covered under a corporate group health insurance policy of INR 5,00,000 (5 Lakhs) sum insured covering self, spouse, and up to two dependent children. Dependent parents can be co-opted with an optional subsidized payroll deduction.
2. Cashless Hospitalization: Network hospitals across Visakhapatnam, Hyderabad, Chennai and Bengaluru support cashless claims with TPA MediAssist. Planned admissions require 48 hours pre-authorization. Emergency admissions require notification within 24 hours.
3. Annual Preventive Health Check-Up: Employees above 30 years are entitled to an annual comprehensive health screening package fully reimbursed up to INR 3,500 at partnered diagnostic centers.
4. Mental Health & Counseling Support: Free, 100% confidential 24/7 counseling sessions are provided via our Employee Assistance Program (EAP) hotline for work stress, personal anxiety, or family well-being.
5. Gym & Fitness Allowance: A monthly wellness subsidy of INR 1,500 is reimbursable upon submission of gym membership or sports facility invoices through the HR portal."""
            },
            {
                "title": "Hybrid Work, Travel and Overtime Compensation Policy",
                "category": "Operations",
                "text": """TALENTPULSE TECHNOLOGIES - HYBRID WORKPLACE & TRAVEL EXPENSE GUIDELINES
1. Hybrid Schedule: Employees are expected to work 3 days from the Visakhapatnam development center (Block B, Tech Park) and up to 2 days remotely per week, aligned with team client commitments and manager approval.
2. Internet & Home Office Allowance: Remote work setup reimbursement of a one-time INR 10,000 is permitted for monitor/chair purchases. A recurring internet allowance of INR 1,200 per month is paid automatically with salary.
3. Domestic Business Travel: Domestic travel by air (economy class) or AC 2-Tier train is covered for client meetings. Per diem food and local transport allowance is INR 2,000 per day in Tier-1 cities and INR 1,500 in Tier-2 cities.
4. Overtime and On-Call Policy: Software Engineers required for planned production deployments outside standard working hours (8:00 PM to 6:00 AM) or weekend shifts receive an on-call allowance of INR 1,800 per shift plus dinner reimbursement up to INR 600, in addition to comp-off eligibility."""
            }
        ]

        for p in policies_data:
            # Simple chunking by paragraph / sections (300-500 words)
            paragraphs = [para.strip() for para in p["text"].split("\n") if len(para.strip()) > 30]
            chunks = []
            for c_id, para in enumerate(paragraphs):
                chunks.append({
                    "chunk_id": c_id + 1,
                    "title": p["title"],
                    "category": p["category"],
                    "text": para
                })

            policy_doc = PolicyDocument(
                title=p["title"],
                category=p["category"],
                extracted_text=p["text"],
                chunks_json=json.dumps(chunks),
                uploaded_by=hr_user.id
            )
            db.add(policy_doc)

        print("9. Generating Initial Baseline Attrition Risk Scores...")
        for idx, emp in enumerate(all_employees):
            if idx in high_risk_indices:
                risk_score = round(random.uniform(0.72, 0.94), 2)
                risk_band = "HIGH"
                top_factors = json.dumps([
                    "Frequent overtime without role progression",
                    "Declining survey sentiment and low engagement score",
                    "Promotion gap exceeding 36 months"
                ])
            elif emp.overtime_status or emp.performance_rating < 3.2:
                risk_score = round(random.uniform(0.38, 0.65), 2)
                risk_band = "MEDIUM"
                top_factors = json.dumps([
                    "Moderate compensation gap relative to experience",
                    "Elevated leave frequency over past two quarters",
                    "Recent performance rating plateau"
                ])
            else:
                risk_score = round(random.uniform(0.08, 0.32), 2)
                risk_band = "LOW"
                top_factors = json.dumps([
                    "Consistent positive performance appraisal",
                    "High engagement survey feedback",
                    "Competitive salary band alignment"
                ])

            att = AttritionScore(
                employee_id=emp.id,
                risk_score=risk_score,
                risk_band=risk_band,
                top_factors=top_factors,
                computed_at=datetime.utcnow()
            )
            db.add(att)

        print("10. Seeding Sample Notifications...")
        welcome_notifications = [
            (admin_user.id, "Welcome to TalentPulse AI", "System initialized with 6 departments, demo hierarchy, and IBM HR attrition baseline."),
            (hr_user.id, "Attrition Alert", "Quarterly attrition risk model flagged high-risk employees in Engineering. Review recommended."),
            (mgr1_user.id, "Pending Leave Requests", "You have pending leave requests awaiting approval from your direct reports."),
            (emp_user.id, "Review Cycle 2025-H1 Completed", "Your performance review has been published by your manager Rajesh Varma.")
        ]
        for u_id, title, msg in welcome_notifications:
            notif = Notification(
                user_id=u_id,
                title=title,
                message=msg,
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.add(notif)

        db.commit()
        print("=" * 60)
        print("TalentPulse AI: Seeding Completed Successfully!")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
