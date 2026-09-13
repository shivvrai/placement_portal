# 🧑‍💻 Yash's Task Sheet — DB Seeding + Auth + Architecture + Team Lead

> **Role:** Team lead. Build the foundations EVERYONE depends on: database with real data, working auth, Docker setup.
> **Priority:** 🔴 P0 (EVERYONE IS BLOCKED WITHOUT THIS)

---

## 📋 Why This Is P0

Every single team member needs:
1. A **running database with real test data** — without students, companies, jobs, and skills in the DB, every API call returns empty/errors
2. A **working auth flow** — without login, nobody can test their pages
3. A **running backend** — Docker or manual, everyone needs to hit API endpoints

**Do these first, before anything else. Your team is blocked until this is done.**

---

## TASK 1: Create the Database Seed Script

### What's needed
Create `d:\Projects\p1\backend\scripts\seed.py` — a script that populates the database with realistic test data.

### What to seed (minimum quantities)

```
├── 5 Departments (CS, IT, ECE, ME, EEE)
├── 50+ Students across all departments
│   ├── Each with: name, email, roll_number, CGPA (6.0-9.5), semester
│   ├── 20+ students with skills assigned (5-10 skills each)
│   └── 10+ students with academic records (semester grades)
├── 100+ Skills in taxonomy
│   ├── Categories: language, tools, web, ml_ai, cs_fundamentals, data, soft_skills
│   └── Examples: Python, JavaScript, SQL, Docker, React, TensorFlow, etc.
├── 10+ Companies
│   ├── Mix: Google, Amazon, Infosys, TCS, Wipro, Microsoft, Deloitte, etc.
│   └── Each with: name, industry, location
├── 20+ Jobs (linked to companies)
│   ├── Each with: title, role_category, min_cgpa, salary_min, salary_max
│   ├── Each with 5-8 required skills (via JobSkill join table)
│   └── Mix: SDE, Data Analyst, DevOps, ML Engineer roles
├── 8+ Placement Drives (linked to companies)
│   ├── Mix of statuses: upcoming, open, in_progress, completed
│   ├── Each with: drive_date, registration_deadline, min_cgpa, eligible_departments
│   └── Some with salary_ctc set
├── 30+ Applications (students applied to drives)
│   ├── Mix of statuses: applied, shortlisted, in_progress, selected, rejected
│   └── Some with interview stages
├── 10+ Placement Outcomes (for completed drives)
│   └── Each with: student_id, drive_id, salary_ctc (for analytics)
├── 15+ Subjects per department (semester 5-8)
│   └── Each with: code, name, credits, semester_number
├── Curriculum Skills (mapping subjects → skills)
│   └── Each subject mapped to 3-6 skills from taxonomy
└── 1 TPO user + 1 Faculty user (for login testing)
```

### Script structure

```python
# d:\Projects\p1\backend\scripts\seed.py

import asyncio
import uuid
import random
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_factory, engine
from app.core.security import hash_password
from app.models.user import User, Student, Department, Faculty
from app.models.skill import Skill, StudentSkill, CurriculumSkill
from app.models.industry import Company, Job, JobSkill
from app.models.placement import PlacementDrive, Application, PlacementOutcome
from app.models.academic import Subject, AcademicRecord
from app.models.system import CopilotConversation
# Import all models so tables are created

async def seed():
    # Create all tables
    async with engine.begin() as conn:
        from app.models import user, skill, industry, placement, academic, system, assessment, roadmap
        from app.core.database import Base
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        # 1. Departments
        departments = {}
        for code, name in [("CS", "Computer Science"), ("IT", "Information Technology"), 
                           ("ECE", "Electronics & Communication"), ("ME", "Mechanical Engineering"),
                           ("EEE", "Electrical Engineering")]:
            dept = Department(code=code, name=name)
            db.add(dept)
            departments[code] = dept
        await db.flush()

        # 2. Skills Taxonomy (100+)
        skills = {}
        skill_data = [
            # Languages
            ("Python", "language"), ("JavaScript", "language"), ("Java", "language"),
            ("C++", "language"), ("SQL", "language"), ("TypeScript", "language"),
            ("Go", "language"), ("Rust", "language"), ("R", "language"),
            # Web
            ("React", "web"), ("Angular", "web"), ("Vue.js", "web"), ("Node.js", "web"),
            ("Django", "web"), ("Flask", "web"), ("FastAPI", "web"), ("HTML/CSS", "web"),
            ("REST API", "web"), ("GraphQL", "web"),
            # Tools
            ("Docker", "tools"), ("Kubernetes", "tools"), ("Git", "tools"), ("Linux", "tools"),
            ("AWS", "tools"), ("GCP", "tools"), ("CI/CD", "tools"), ("Terraform", "tools"),
            ("Jenkins", "tools"), ("Nginx", "tools"),
            # ML/AI
            ("Machine Learning", "ml_ai"), ("Deep Learning", "ml_ai"), ("TensorFlow", "ml_ai"),
            ("PyTorch", "ml_ai"), ("scikit-learn", "ml_ai"), ("NLP", "ml_ai"),
            ("Computer Vision", "ml_ai"), ("Statistics", "ml_ai"),
            # CS Fundamentals
            ("Data Structures", "cs_fundamentals"), ("Algorithms", "cs_fundamentals"),
            ("System Design", "cs_fundamentals"), ("OOP", "cs_fundamentals"),
            ("Computer Networks", "cs_fundamentals"), ("Operating Systems", "cs_fundamentals"),
            ("Design Patterns", "cs_fundamentals"), ("DBMS", "cs_fundamentals"),
            # Data
            ("pandas", "data"), ("numpy", "data"), ("Spark", "data"), ("Kafka", "data"),
            ("Tableau", "data"), ("Power BI", "data"), ("Excel", "data"),
            ("Data Analysis", "data"), ("Data Engineering", "data"),
            # Soft Skills
            ("Communication", "soft_skills"), ("Teamwork", "soft_skills"),
            ("Problem Solving", "soft_skills"), ("Leadership", "soft_skills"),
        ]
        for name, category in skill_data:
            skill = Skill(name=name, normalized_name=name.lower(), category=category)
            db.add(skill)
            skills[name] = skill
        await db.flush()

        # 3. TPO User
        tpo_user = User(
            email="tpo@ccip.edu", password_hash=hash_password("tpo123"),
            role="tpo", first_name="Admin", last_name="TPO", is_active=True
        )
        db.add(tpo_user)

        # 4. Faculty User
        faculty_user = User(
            email="faculty@ccip.edu", password_hash=hash_password("faculty123"),
            role="faculty", first_name="Dr. Sharma", last_name="HOD", is_active=True
        )
        db.add(faculty_user)
        await db.flush()
        
        faculty = Faculty(id=faculty_user.id, department_id=departments["CS"].id, is_hod=True)
        db.add(faculty)

        # 5. Students (50+)
        student_names = [
            "Priya Agarwal", "Arjun Sharma", "Sneha Reddy", "Rahul Nair", "Divya Iyer",
            "Mohammed Ali", "Kavya Menon", "Aditya Verma", "Pooja Gupta", "Karan Joshi",
            # ... add 40+ more names
            "Shreya Das", "Vishal Kumar", "Ananya Singh", "Rohit Patil", "Neha Kapoor",
            "Siddharth Rao", "Meera Desai", "Varun Choudhury", "Ishita Bose", "Pranav Kulkarni",
            # ... etc (you need 50+ total)
        ]
        dept_codes = ["CS", "CS", "IT", "CS", "ECE", "IT", "CS", "ME", "CS", "IT",
                      "ECE", "CS", "CS", "IT", "CS", "ECE", "IT", "ME", "CS", "EEE"]
        
        students = []
        for i, name in enumerate(student_names):
            parts = name.split()
            dept_code = dept_codes[i % len(dept_codes)]
            roll = f"{dept_code}21B{str(i+1).zfill(3)}"
            
            user = User(
                email=f"{parts[0].lower()}.{parts[1].lower()}@ccip.edu",
                password_hash=hash_password("student123"),
                role="student", first_name=parts[0], last_name=parts[1], is_active=True
            )
            db.add(user)
            await db.flush()

            student = Student(
                id=user.id,
                roll_number=roll,
                department_id=departments[dept_code].id,
                current_semester=random.choice([7, 8]),
                admission_year=2021,
                cgpa=Decimal(str(round(random.uniform(6.0, 9.5), 1))),
            )
            db.add(student)
            students.append(student)
        await db.flush()

        # 6. Assign skills to students (5-10 per student)
        skill_list = list(skills.values())
        for student in students:
            num_skills = random.randint(5, 10)
            chosen = random.sample(skill_list, num_skills)
            for skill in chosen:
                ss = StudentSkill(
                    student_id=student.id,
                    skill_id=skill.id,
                    confidence=Decimal(str(round(random.uniform(0.3, 0.95), 2))),
                    source=random.choice(["self_reported", "assessment", "resume"]),
                )
                db.add(ss)

        # 7. Companies
        companies = {}
        for name, industry, location in [
            ("Google", "Technology", "Bangalore"), ("Amazon", "E-Commerce", "Hyderabad"),
            ("Microsoft", "Technology", "Bangalore"), ("Infosys", "IT Services", "Pune"),
            ("TCS", "IT Services", "Mumbai"), ("Wipro", "IT Services", "Bangalore"),
            ("Deloitte", "Consulting", "Gurgaon"), ("Goldman Sachs", "Finance", "Bangalore"),
            ("Adobe", "Technology", "Noida"), ("Flipkart", "E-Commerce", "Bangalore"),
            ("Razorpay", "Fintech", "Bangalore"), ("PhonePe", "Fintech", "Bangalore"),
        ]:
            company = Company(name=name, industry=industry, location=location)
            db.add(company)
            companies[name] = company
        await db.flush()

        # 8. Jobs (20+) — linked to companies with required skills
        # ... create Job objects with JobSkill requirements

        # 9. Placement Drives (8+)
        # ... create PlacementDrive objects with various statuses

        # 10. Applications + Outcomes
        # ... create Application objects and PlacementOutcome for completed drives

        # 11. Subjects + Academic Records
        # ... create Subject objects per department, AcademicRecord per student

        await db.commit()
        print("✅ Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
```

### ⚠️ CRITICAL: Check model imports
Before running the seed script, verify all model classes exist:
- `d:\Projects\p1\backend\app\models\user.py` — User, Student, Department, Faculty
- `d:\Projects\p1\backend\app\models\skill.py` — Skill, StudentSkill, CurriculumSkill
- `d:\Projects\p1\backend\app\models\industry.py` — Company, Job, JobSkill
- `d:\Projects\p1\backend\app\models\placement.py` — PlacementDrive, Application, PlacementOutcome
- `d:\Projects\p1\backend\app\models\academic.py` — Subject, AcademicRecord
- `d:\Projects\p1\backend\app\models\assessment.py` — AssessmentQuestionBank, AssessmentSession
- `d:\Projects\p1\backend\app\models\roadmap.py` — Roadmap, RoadmapTask

Check each model's fields match what the seed script expects. Fix any mismatches.

### How to run
```bash
cd d:\Projects\p1\backend
python -m scripts.seed
```

---

## TASK 2: Verify Auth Flow End-to-End

### Test this exact flow:

1. **Register a student:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@ccip.edu","password":"test123","role":"student","first_name":"Test","last_name":"Student","roll_number":"CS21B099","department_code":"CS"}'
```

2. **Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@ccip.edu","password":"test123"}'
```
Should return: `{ "access_token": "...", "refresh_token": "..." }`

3. **Get profile:**
```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer {access_token}"
```

4. **Refresh token:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"..."}'
```

5. **Test frontend login:**
- Go to `http://localhost:5173/login`
- Login with `test@ccip.edu` / `test123`
- Should redirect to `/student/dashboard`

### Fix common issues:
- If database connection fails: check `DATABASE_URL` in `.env`
- If JWT decode fails: check `SECRET_KEY` in `.env`
- If CORS errors: check CORS middleware in `main.py`

---

## TASK 3: Environment Setup

### Backend `.env` (create if missing)
File: `d:\Projects\p1\backend\.env`
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ccip
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
GEMINI_API_KEY=
UPLOAD_DIR=./uploads
MAX_RESUME_SIZE_MB=5
```

### Frontend `.env`
File: `d:\Projects\p1\frontend\.env`
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_USE_MOCKS=false
```

**IMPORTANT:** Set `VITE_USE_MOCKS=false` so the team tests against real APIs.

---

## TASK 4: Docker Setup

### Verify `docker-compose.yml` works
File: `d:\Projects\p1\docker-compose.yml`

It should have:
1. **postgres** service — PostgreSQL database
2. **backend** service — FastAPI app
3. **frontend** service — Vite dev server (optional, can run locally)

Test: `docker-compose up -d` → all services running → API accessible at `http://localhost:8000`

If Docker isn't set up, at minimum provide instructions for team:
```bash
# Option 1: Docker
docker-compose up -d

# Option 2: Manual
# Terminal 1: PostgreSQL (install locally or use Docker just for DB)
docker run -d --name ccip-db -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=ccip postgres:15

# Terminal 2: Backend
cd d:\Projects\p1\backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# Terminal 3: Frontend
cd d:\Projects\p1\frontend
npm install
npm run dev
```

---

## TASK 5: Code Review + Integration Support

### Your ongoing responsibilities:
1. **Review all PRs** before merge — ensure code quality and consistency
2. **Resolve conflicts** when team members edit shared files (especially `endpoints.js`, `AppRouter.jsx`)
3. **Test integration** — after each member finishes, verify their feature works with the seeded data
4. **Fix blockers** — if a team member is stuck, help them debug

### Key shared files that might conflict:
- `frontend/src/api/endpoints.js` — Sakshi, Sachin, Anjula all add/modify endpoints
- `frontend/src/router/AppRouter.jsx` — if new pages/routes are added
- `backend/app/main.py` — if new routers are registered
- `backend/requirements.txt` — if new packages are added

---

## ✅ Checklist — What "Done" Looks Like
- [ ] Database has 50+ students, 10+ companies, 20+ jobs, 100+ skills, 8+ drives seeded
- [ ] `python -m scripts.seed` runs without errors
- [ ] Auth register → login → JWT → /me flow works perfectly
- [ ] TPO login works (tpo@ccip.edu / tpo123)
- [ ] Faculty login works (faculty@ccip.edu / faculty123)
- [ ] Student login works (any seeded student email / student123)
- [ ] Frontend connects to backend with `VITE_USE_MOCKS=false`
- [ ] No CORS errors in browser console
- [ ] Docker or manual setup instructions documented for team
- [ ] All seeded data produces meaningful results when other features are tested
