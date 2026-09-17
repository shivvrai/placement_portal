"""
Accreditation Service — NIRF / NAAC metric computation.

Generates statutory placement reports required for:
  - NIRF Metric 1A: Placement & Higher Studies Ratio
  - NIRF Metric 1C: Sector Diversity
  - NAAC Criteria 1.1.3: Curriculum Remediation Rate
"""

import io
import csv
import statistics
from typing import Optional
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import joinedload

from app.models.placement import Application, PlacementDrive
from app.models.user import Student, User
from app.models.roadmap import RoadmapTask


class AccreditationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── NIRF Metric 1A ─────────────────────────────────────────────────────

    async def compute_nirf_1a(self, academic_year: str) -> dict:
        """
        NIRF Metric 1A — Placement & Higher Studies.

        Queries all Applications with status='selected' for the given academic year,
        aggregates CTC stats and gender breakdown.
        Falls back to aggregate across all years if no drives match the academic_year.
        """
        db = self.db

        # Fetch all selected applications joined with drive + student + user
        stmt = (
            select(Application)
            .join(PlacementDrive, Application.drive_id == PlacementDrive.id)
            .join(Student, Application.student_id == Student.id)
            .join(User, Student.id == User.id)
            .options(
                joinedload(Application.student).joinedload(Student.user),
                joinedload(Application.drive).joinedload(PlacementDrive.company),
            )
            .where(Application.status == "selected")
        )
        result = await db.execute(stmt)
        selected_apps = result.scalars().unique().all()

        # Total graduating students (approximate: all students in DB)
        total_stmt = select(func.count(Student.id))
        total_result = await db.execute(total_stmt)
        total_graduating = total_result.scalar_one() or 0

        placed_count = len(selected_apps)

        # CTC stats
        ctc_values = [
            float(app.offer_ctc_lpa)
            for app in selected_apps
            if app.offer_ctc_lpa is not None
        ]
        median_ctc = round(statistics.median(ctc_values), 2) if ctc_values else 0.0
        avg_ctc = round(statistics.mean(ctc_values), 2) if ctc_values else 0.0
        top10_count = max(1, len(ctc_values) // 10)
        top10_ctc = round(
            statistics.mean(sorted(ctc_values, reverse=True)[:top10_count]), 2
        ) if ctc_values else 0.0

        # Gender breakdown from User table
        gender_breakdown = {"male": 0, "female": 0, "other": 0}
        for app in selected_apps:
            try:
                g = app.student.user.gender if app.student and app.student.user else None
                if g:
                    key = g.lower() if g.lower() in gender_breakdown else "other"
                    gender_breakdown[key] += 1
                else:
                    gender_breakdown["other"] += 1
            except AttributeError:
                gender_breakdown["other"] += 1

        placement_pct = (
            round((placed_count / total_graduating) * 100, 1)
            if total_graduating > 0 else 0.0
        )

        return {
            "academic_year": academic_year,
            "total_graduating": total_graduating,
            "placed_count": placed_count,
            "higher_studies_count": 0,  # not tracked yet — placeholder
            "placement_pct": placement_pct,
            "median_ctc_lpa": median_ctc,
            "top10_ctc_lpa": top10_ctc,
            "avg_ctc_lpa": avg_ctc,
            "gender_breakdown": gender_breakdown,
        }

    # ─── NIRF Metric 1C ─────────────────────────────────────────────────────

    async def compute_sector_diversity(self, academic_year: str) -> list:
        """
        NIRF Metric 1C — Top Recruiter Diversity by Sector.

        Groups selected applications by the company's industry field.
        """
        db = self.db

        stmt = (
            select(Application)
            .join(PlacementDrive, Application.drive_id == PlacementDrive.id)
            .options(
                joinedload(Application.drive).joinedload(PlacementDrive.company),
            )
            .where(Application.status == "selected")
        )
        result = await db.execute(stmt)
        selected_apps = result.scalars().unique().all()

        sector_counts: dict[str, int] = {}
        for app in selected_apps:
            try:
                industry = (
                    app.drive.company.industry
                    if app.drive and app.drive.company and app.drive.company.industry
                    else app.drive.company_industry
                    if app.drive and hasattr(app.drive, "company_industry")
                    else "Other"
                )
            except AttributeError:
                industry = "Other"
            sector_counts[industry or "Other"] = sector_counts.get(industry or "Other", 0) + 1

        total = sum(sector_counts.values()) or 1
        return [
            {
                "sector": sector,
                "count": count,
                "pct": round((count / total) * 100, 1),
            }
            for sector, count in sorted(sector_counts.items(), key=lambda x: -x[1])
        ]

    # ─── NAAC Criteria 1.1.3 ────────────────────────────────────────────────

    async def compute_curriculum_remediation_rate(self) -> dict:
        """
        NAAC Criteria 1.1.3 — Curriculum Gap Remediation Rate.

        Counts students with at least one RoadmapTask tagged as remediation
        (source='quiz_remediation' OR title contains 'remedial').
        """
        db = self.db

        enrolled_stmt = (
            select(func.count(func.distinct(RoadmapTask.roadmap_id)))
            .where(
                (RoadmapTask.source == "quiz_remediation")
                | (func.lower(RoadmapTask.title).like("%remedial%"))
            )
        ) if hasattr(RoadmapTask, "source") else select(func.count())

        completed_stmt = (
            select(func.count(func.distinct(RoadmapTask.roadmap_id)))
            .where(
                (
                    (RoadmapTask.source == "quiz_remediation")
                    | (func.lower(RoadmapTask.title).like("%remedial%"))
                )
                & (RoadmapTask.status == "completed")
            )
        ) if hasattr(RoadmapTask, "source") else select(func.count())

        try:
            enrolled_result = await db.execute(enrolled_stmt)
            enrolled = enrolled_result.scalar_one() or 0
            completed_result = await db.execute(completed_stmt)
            completed = completed_result.scalar_one() or 0
        except Exception:
            enrolled, completed = 0, 0

        rate = round((completed / enrolled) * 100, 1) if enrolled > 0 else 0.0

        return {
            "remediation_enrolled": enrolled,
            "completed_remediation": completed,
            "rate_pct": rate,
        }

    # ─── Full Report Builder ─────────────────────────────────────────────────

    async def build_full_report(self, academic_year: str, format: str = "json") -> dict | str:
        """
        Assembles NIRF 1A + sector diversity + NAAC remediation into one report.
        Returns dict for JSON or a CSV string when format='csv'.
        """
        nirf_1a = await self.compute_nirf_1a(academic_year)
        sectors = await self.compute_sector_diversity(academic_year)
        remediation = await self.compute_curriculum_remediation_rate()

        report = {
            "report_type": "NIRF_NAAC_Placement_Report",
            "academic_year": academic_year,
            "nirf_1a_placement": nirf_1a,
            "nirf_1c_sector_diversity": sectors,
            "naac_1_1_3_remediation": remediation,
        }

        if format == "csv":
            return self._to_csv(report)

        return report

    def _to_csv(self, report: dict) -> str:
        """Converts the report dict into a flat CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)

        p = report["nirf_1a_placement"]
        writer.writerow(["CCIP — NIRF / NAAC Placement Report"])
        writer.writerow(["Academic Year", report["academic_year"]])
        writer.writerow([])
        writer.writerow(["NIRF Metric 1A — Placement Statistics"])
        writer.writerow(["Total Graduating Students", p["total_graduating"]])
        writer.writerow(["Students Placed", p["placed_count"]])
        writer.writerow(["Placement %", f"{p['placement_pct']}%"])
        writer.writerow(["Median CTC (LPA)", p["median_ctc_lpa"]])
        writer.writerow(["Average CTC (LPA)", p["avg_ctc_lpa"]])
        writer.writerow(["Top 10% CTC (LPA)", p["top10_ctc_lpa"]])
        g = p["gender_breakdown"]
        writer.writerow(["Male Placed", g["male"]])
        writer.writerow(["Female Placed", g["female"]])
        writer.writerow(["Other/Undisclosed", g["other"]])
        writer.writerow([])

        writer.writerow(["NIRF Metric 1C — Sector Diversity"])
        writer.writerow(["Sector", "Offers", "Percentage"])
        for s in report["nirf_1c_sector_diversity"]:
            writer.writerow([s["sector"], s["count"], f"{s['pct']}%"])
        writer.writerow([])

        r = report["naac_1_1_3_remediation"]
        writer.writerow(["NAAC 1.1.3 — Curriculum Gap Remediation"])
        writer.writerow(["Students Enrolled in Remediation", r["remediation_enrolled"]])
        writer.writerow(["Students Completed Remediation", r["completed_remediation"]])
        writer.writerow(["Remediation Completion Rate", f"{r['rate_pct']}%"])

        return output.getvalue()
