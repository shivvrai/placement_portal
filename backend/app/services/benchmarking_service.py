import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import numpy as np

from app.models.user import Student, User
from app.models.skill import StudentSkill
from app.models.portfolio import Project, Resume
from app.models.placement import Application

class BenchmarkingService:
    async def get_cohort_stats(self, db: AsyncSession, student_id: uuid.UUID, scope: str = "department") -> dict:
        student = await db.get(Student, student_id, options=[selectinload(Student.department)])
        query = select(Student)
        if scope == "department" and student.department_id:
            query = query.where(Student.department_id == student.department_id)
        
        peers = (await db.execute(query)).scalars().all()
        peer_ids = [p.id for p in peers]
        
        cgpas = [float(p.cgpa) for p in peers if p.cgpa is not None]
        student_cgpa = float(student.cgpa) if student.cgpa else 0.0
        
        cgpa_stats = {
            "value": student_cgpa,
            "mean": round(np.mean(cgpas), 2) if cgpas else 0.0,
            "median": round(np.median(cgpas), 2) if cgpas else 0.0,
            "p25": round(np.percentile(cgpas, 25), 2) if cgpas else 0.0,
            "p75": round(np.percentile(cgpas, 75), 2) if cgpas else 0.0,
            "percentile": round(sum(c < student_cgpa for c in cgpas) / len(cgpas) * 100) if cgpas else 0
        }
        
        skill_counts = {}
        for pid in peer_ids:
            cnt = (await db.execute(select(func.count(StudentSkill.id)).where(StudentSkill.student_id == pid))).scalar() or 0
            skill_counts[pid] = cnt
            
        sk_vals = list(skill_counts.values())
        student_sk = skill_counts.get(student_id, 0)
        
        skill_stats = {
            "value": student_sk,
            "mean": round(np.mean(sk_vals), 2) if sk_vals else 0.0,
            "median": round(np.median(sk_vals), 2) if sk_vals else 0.0,
            "p25": round(np.percentile(sk_vals, 25), 2) if sk_vals else 0.0,
            "p75": round(np.percentile(sk_vals, 75), 2) if sk_vals else 0.0,
            "percentile": round(sum(c < student_sk for c in sk_vals) / len(sk_vals) * 100) if sk_vals else 0
        }
        
        app_counts = {}
        for pid in peer_ids:
            cnt = (await db.execute(select(func.count(Application.id)).where(Application.student_id == pid))).scalar() or 0
            app_counts[pid] = cnt
            
        app_vals = list(app_counts.values())
        student_app = app_counts.get(student_id, 0)
        
        app_stats = {
            "value": student_app,
            "mean": round(np.mean(app_vals), 2) if app_vals else 0.0,
            "median": round(np.median(app_vals), 2) if app_vals else 0.0,
            "p25": round(np.percentile(app_vals, 25), 2) if app_vals else 0.0,
            "p75": round(np.percentile(app_vals, 75), 2) if app_vals else 0.0,
            "percentile": round(sum(c < student_app for c in app_vals) / len(app_vals) * 100) if app_vals else 0
        }
        
        return {
            "cgpa": cgpa_stats,
            "skills": skill_stats,
            "applications": app_stats,
            "assessments": {}
        }

    async def get_department_leaderboard(self, db: AsyncSession, dept_code: str, metric: str, current_student_id: uuid.UUID) -> list[dict]:
        from app.models.user import Department
        dept = (await db.execute(select(Department).where(Department.code == dept_code))).scalar_one_or_none()
        if not dept: return []
        
        peers = (await db.execute(select(Student).where(Student.department_id == dept.id))).scalars().all()
        
        data = []
        for p in peers:
            val = float(p.cgpa) if p.cgpa else 0.0
            if metric == "skill_count":
                val = (await db.execute(select(func.count(StudentSkill.id)).where(StudentSkill.student_id == p.id))).scalar() or 0
            elif metric == "applications_filed":
                val = (await db.execute(select(func.count(Application.id)).where(Application.student_id == p.id))).scalar() or 0
                
            data.append({"id": p.id, "value": val, "user_id": p.id})
            
        data.sort(key=lambda x: x["value"], reverse=True)
        top = data[:10]
        
        res = []
        for i, d in enumerate(top):
            res.append({
                "rank": i + 1,
                "label": f"Student #{i+1}",
                "value": d["value"],
                "is_me": d["id"] == current_student_id
            })
            
        if current_student_id not in [d["id"] for d in top]:
            my_d = next((d for d in data if d["id"] == current_student_id), None)
            if my_d:
                rank = data.index(my_d) + 1
                res.append({
                    "rank": rank,
                    "label": f"Student #{rank}",
                    "value": my_d["value"],
                    "is_me": True
                })
        
        return res

    async def get_readiness_score(self, db: AsyncSession, student_id: uuid.UUID) -> dict:
        student = await db.get(Student, student_id, options=[selectinload(Student.department)])
        if not student:
            return {}
            
        components = []
        total_score = 0
        
        user = await db.get(User, student_id)
        prof_score = 10 if (user and user.phone) else 5
        res_cnt = (await db.execute(select(func.count(Resume.id)).where(Resume.student_id == student_id))).scalar() or 0
        if res_cnt > 0: prof_score += 10
        components.append({"name": "Profile", "score": prof_score, "max_score": 20})
        total_score += prof_score
        
        cgpa_score = min(20, (float(student.cgpa) / 10.0) * 20) if student.cgpa else 0
        components.append({"name": "CGPA", "score": round(cgpa_score), "max_score": 20})
        total_score += cgpa_score
        
        sk_cnt = (await db.execute(select(func.count(StudentSkill.id)).where(StudentSkill.student_id == student_id))).scalar() or 0
        sk_score = min(30, (sk_cnt / 10) * 30)
        components.append({"name": "Skills", "score": round(sk_score), "max_score": 30})
        total_score += sk_score
        
        components.append({"name": "Assessment", "score": 10, "max_score": 15})
        total_score += 10
        
        app_cnt = (await db.execute(select(func.count(Application.id)).where(Application.student_id == student_id))).scalar() or 0
        proj_cnt = (await db.execute(select(func.count(Project.id)).where(Project.student_id == student_id))).scalar() or 0
        act_score = min(15, (app_cnt * 2 + proj_cnt * 5))
        components.append({"name": "Activity", "score": act_score, "max_score": 15})
        total_score += act_score
        
        total_score = round(total_score)
        
        if total_score >= 80: label = "Placement Ready"
        elif total_score >= 60: label = "Almost There"
        else: label = "Needs Work"
        
        return {
            "total_score": total_score,
            "components": components,
            "percentile_in_dept": 75,
            "label": label
        }

benchmarking_service = BenchmarkingService()
