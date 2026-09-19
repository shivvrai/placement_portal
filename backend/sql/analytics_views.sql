-- ============================================================================
-- CCIP Analytics Views — Advanced SQL for BI Integration
-- These views power both Apache Superset (direct SQL) and Power BI (OData feed).
-- Demonstrates: CTEs, window functions, conditional aggregation, percentiles.
-- ============================================================================

-- ─── View 1: Placement Summary with Year-over-Year Growth ───────────────────
-- Uses: CTE, LAG(), PERCENTILE_CONT(), ROUND()
-- Purpose: KPI dashboard — placement rate, avg/median/max CTC per academic year

CREATE OR REPLACE VIEW v_placement_summary AS
WITH total_students AS (
    SELECT COUNT(*) AS total FROM students
),
yearly_outcomes AS (
    SELECT
        po.academic_year,
        COUNT(*)                                                        AS placed_count,
        ROUND(AVG(po.salary_ctc)::numeric, 2)                          AS avg_ctc_lpa,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY po.salary_ctc)     AS median_ctc_lpa,
        PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY po.salary_ctc)     AS p90_ctc_lpa,
        MAX(po.salary_ctc)                                              AS max_ctc_lpa,
        MIN(po.salary_ctc)                                              AS min_ctc_lpa,
        COUNT(DISTINCT po.company_name)                                 AS unique_companies
    FROM placement_outcomes po
    WHERE po.academic_year IS NOT NULL
    GROUP BY po.academic_year
),
with_yoy AS (
    SELECT
        yo.*,
        ts.total                                                        AS total_students,
        ROUND((yo.placed_count::numeric / NULLIF(ts.total, 0)) * 100, 1) AS placement_rate_pct,
        LAG(yo.placed_count) OVER (ORDER BY yo.academic_year)           AS prev_year_placed,
        LAG(yo.avg_ctc_lpa)  OVER (ORDER BY yo.academic_year)           AS prev_year_avg_ctc,
        ROUND(
            (yo.placed_count - LAG(yo.placed_count) OVER (ORDER BY yo.academic_year))::numeric
            / NULLIF(LAG(yo.placed_count) OVER (ORDER BY yo.academic_year), 0) * 100, 1
        )                                                               AS yoy_placed_growth_pct,
        ROUND(
            (yo.avg_ctc_lpa - LAG(yo.avg_ctc_lpa) OVER (ORDER BY yo.academic_year))::numeric
            / NULLIF(LAG(yo.avg_ctc_lpa) OVER (ORDER BY yo.academic_year), 0) * 100, 1
        )                                                               AS yoy_ctc_growth_pct
    FROM yearly_outcomes yo
    CROSS JOIN total_students ts
)
SELECT * FROM with_yoy
ORDER BY academic_year;


-- ─── View 2: Department Performance Ranking ─────────────────────────────────
-- Uses: RANK(), PERCENT_RANK(), DENSE_RANK(), COUNT FILTER
-- Purpose: Compare departments on placement rate, avg CTC, skill readiness

CREATE OR REPLACE VIEW v_dept_performance AS
WITH dept_stats AS (
    SELECT
        d.code                                                         AS department_code,
        d.name                                                         AS department_name,
        COUNT(DISTINCT s.id)                                           AS total_students,
        COUNT(DISTINCT po.id)                                          AS placed_students,
        ROUND(
            COUNT(DISTINCT po.id)::numeric
            / NULLIF(COUNT(DISTINCT s.id), 0) * 100, 1
        )                                                              AS placement_rate_pct,
        ROUND(AVG(po.salary_ctc)::numeric, 2)                         AS avg_ctc_lpa,
        MAX(po.salary_ctc)                                             AS max_ctc_lpa,
        COUNT(DISTINCT po.company_name)                                AS unique_recruiters,
        -- Conditional aggregation: count by placement type
        COUNT(DISTINCT po.id) FILTER (WHERE po.placement_type = 'on_campus')
                                                                       AS on_campus_placed,
        COUNT(DISTINCT po.id) FILTER (WHERE po.placement_type != 'on_campus')
                                                                       AS off_campus_placed
    FROM departments d
    LEFT JOIN students s ON s.department_id = d.id
    LEFT JOIN placement_outcomes po ON po.student_id = s.id
    GROUP BY d.id, d.code, d.name
    HAVING COUNT(DISTINCT s.id) > 0
)
SELECT
    ds.*,
    RANK()         OVER (ORDER BY ds.placement_rate_pct DESC NULLS LAST) AS placement_rank,
    DENSE_RANK()   OVER (ORDER BY ds.avg_ctc_lpa DESC NULLS LAST)       AS ctc_rank,
    ROUND(
        PERCENT_RANK() OVER (ORDER BY ds.placement_rate_pct ASC NULLS FIRST)::numeric * 100, 1
    )                                                                    AS percentile_rank
FROM dept_stats ds
ORDER BY placement_rank;


-- ─── View 3: Skill Demand vs Supply Matrix ──────────────────────────────────
-- Uses: CASE WHEN bucketing, LEFT JOINs, conditional COUNT, subquery
-- Purpose: Heatmap of industry demand vs campus supply with gap classification

CREATE OR REPLACE VIEW v_skill_demand_matrix AS
WITH demand AS (
    SELECT
        sk.id                                                          AS skill_id,
        sk.name                                                        AS skill_name,
        sk.category,
        COUNT(DISTINCT js.job_id)                                      AS jobs_requiring,
        ROUND(
            COUNT(DISTINCT js.job_id)::numeric
            / NULLIF((SELECT COUNT(*) FROM jobs WHERE is_active = true), 0) * 100, 1
        )                                                              AS demand_pct
    FROM skills sk
    INNER JOIN job_skills js ON js.skill_id = sk.id
    INNER JOIN jobs j ON j.id = js.job_id AND j.is_active = true
    GROUP BY sk.id, sk.name, sk.category
),
supply AS (
    SELECT
        ss.skill_id,
        COUNT(DISTINCT ss.student_id)                                  AS students_with_skill,
        ROUND(AVG(ss.confidence)::numeric * 100, 1)                    AS avg_confidence_pct,
        ROUND(
            COUNT(DISTINCT ss.student_id)::numeric
            / NULLIF((SELECT COUNT(*) FROM students), 0) * 100, 1
        )                                                              AS supply_pct
    FROM student_skills ss
    GROUP BY ss.skill_id
)
SELECT
    d.skill_name,
    d.category,
    COALESCE(d.demand_pct, 0)                                          AS demand_pct,
    COALESCE(s.supply_pct, 0)                                          AS supply_pct,
    ROUND(COALESCE(d.demand_pct, 0) - COALESCE(s.supply_pct, 0), 1)   AS gap_score,
    COALESCE(d.jobs_requiring, 0)                                      AS jobs_requiring,
    COALESCE(s.students_with_skill, 0)                                 AS students_with_skill,
    COALESCE(s.avg_confidence_pct, 0)                                  AS avg_confidence_pct,
    CASE
        WHEN COALESCE(d.demand_pct, 0) - COALESCE(s.supply_pct, 0) > 30 THEN 'critical_gap'
        WHEN COALESCE(d.demand_pct, 0) - COALESCE(s.supply_pct, 0) > 15 THEN 'moderate_gap'
        WHEN COALESCE(d.demand_pct, 0) - COALESCE(s.supply_pct, 0) > 0  THEN 'slight_gap'
        ELSE 'surplus'
    END                                                                AS gap_classification
FROM demand d
LEFT JOIN supply s ON s.skill_id = d.skill_id
ORDER BY gap_score DESC;


-- ─── View 4: Student Risk Score (Composite) ─────────────────────────────────
-- Uses: NTILE(), weighted scoring CTE, COALESCE, multi-factor risk model
-- Purpose: Identify at-risk students for proactive TPO intervention

CREATE OR REPLACE VIEW v_student_risk_score AS
WITH student_metrics AS (
    SELECT
        s.id                                                           AS student_id,
        s.roll_number,
        u.first_name || ' ' || u.last_name                            AS full_name,
        u.email,
        d.code                                                         AS department_code,
        d.name                                                         AS department_name,
        s.current_semester,
        s.admission_year,
        COALESCE(s.cgpa::numeric, 0)                                   AS cgpa,
        -- Skill readiness: average confidence across all skills
        COALESCE(
            (SELECT ROUND(AVG(ss.confidence)::numeric * 100, 1)
             FROM student_skills ss WHERE ss.student_id = s.id),
            0
        )                                                              AS avg_skill_confidence,
        -- Skill count
        (SELECT COUNT(*) FROM student_skills ss WHERE ss.student_id = s.id)
                                                                       AS skill_count,
        -- Has placement outcome?
        EXISTS (
            SELECT 1 FROM placement_outcomes po WHERE po.student_id = s.id
        )                                                              AS is_placed,
        -- Application count
        (SELECT COUNT(*) FROM applications a WHERE a.student_id = s.id)
                                                                       AS applications_count,
        -- Resume uploaded?
        CASE WHEN s.resume_url IS NOT NULL THEN true ELSE false END    AS has_resume
    FROM students s
    INNER JOIN users u ON u.id = s.id
    INNER JOIN departments d ON d.id = s.department_id
),
scored AS (
    SELECT
        sm.*,
        -- Composite risk score: 0-100 (higher = more at-risk)
        ROUND(
            GREATEST(0, LEAST(100,
                -- CGPA factor (40% weight): low CGPA increases risk
                (CASE
                    WHEN sm.cgpa >= 8.0 THEN 0
                    WHEN sm.cgpa >= 7.0 THEN 15
                    WHEN sm.cgpa >= 6.0 THEN 35
                    WHEN sm.cgpa >= 5.0 THEN 60
                    ELSE 80
                END) * 0.40
                +
                -- Skill readiness factor (35% weight)
                (CASE
                    WHEN sm.avg_skill_confidence >= 70 THEN 0
                    WHEN sm.avg_skill_confidence >= 50 THEN 20
                    WHEN sm.avg_skill_confidence >= 30 THEN 50
                    ELSE 75
                END) * 0.35
                +
                -- Engagement factor (25% weight): resume + applications
                (CASE
                    WHEN sm.has_resume AND sm.applications_count >= 3 THEN 0
                    WHEN sm.has_resume AND sm.applications_count >= 1 THEN 15
                    WHEN sm.has_resume THEN 35
                    ELSE 65
                END) * 0.25
            ))::numeric, 1
        )                                                              AS risk_score
    FROM student_metrics sm
    WHERE sm.is_placed = false   -- Only un-placed students
)
SELECT
    sc.*,
    NTILE(4) OVER (ORDER BY sc.risk_score ASC)                         AS risk_quartile,
    CASE
        WHEN sc.risk_score >= 60 THEN 'high'
        WHEN sc.risk_score >= 35 THEN 'medium'
        WHEN sc.risk_score >= 15 THEN 'low'
        ELSE 'minimal'
    END                                                                AS risk_tier,
    RANK() OVER (
        PARTITION BY sc.department_code ORDER BY sc.risk_score DESC
    )                                                                  AS dept_risk_rank
FROM scored sc
ORDER BY risk_score DESC;
