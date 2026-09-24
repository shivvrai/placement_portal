-- CCIP Platform Database Fix Script
-- Resolves all missing columns and missing tables in PostgreSQL (Supabase)

-- 1. Add missing columns to existing tables
ALTER TABLE student_skills ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE;
ALTER TABLE certifications ADD COLUMN IF NOT EXISTS credential_id VARCHAR(200);
ALTER TABLE internships ADD COLUMN IF NOT EXISTS location VARCHAR(200);
ALTER TABLE internships ADD COLUMN IF NOT EXISTS employment_type VARCHAR(50) DEFAULT 'Internship';
ALTER TABLE internships ADD COLUMN IF NOT EXISTS is_current BOOLEAN DEFAULT FALSE;

-- 2. Curriculum Proposals
CREATE TABLE IF NOT EXISTS curriculum_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(300) NOT NULL,
    department_code VARCHAR(10) NOT NULL,
    description TEXT NOT NULL,
    rationale TEXT NOT NULL,
    proposed_changes JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'draft',
    submitted_by UUID REFERENCES users(id),
    reviewed_by UUID REFERENCES users(id),
    hod_comments TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    reviewed_at TIMESTAMP WITHOUT TIME ZONE
);

-- 3. Mock Interview Sessions
CREATE TABLE IF NOT EXISTS mock_interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id),
    role_target VARCHAR(200) NOT NULL,
    company_style VARCHAR(50) NOT NULL DEFAULT 'Product',
    difficulty VARCHAR(30) NOT NULL DEFAULT 'campus',
    status VARCHAR(20) NOT NULL DEFAULT 'setup',
    current_round INTEGER DEFAULT 0,
    transcript JSONB DEFAULT '[]',
    questions_asked TEXT[],
    performance_scores JSONB,
    final_report JSONB,
    duration_seconds INTEGER,
    word_count INTEGER,
    filler_word_count INTEGER DEFAULT 0,
    started_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    completed_at TIMESTAMP WITHOUT TIME ZONE
);

-- 4. In-App Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'info',
    link VARCHAR(500),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- 5. Student Talent Cohorts
CREATE TABLE IF NOT EXISTS student_cohorts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    criteria JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- 6. Interview Experiences & Questions
CREATE TABLE IF NOT EXISTS interview_experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id),
    company_name VARCHAR(200) NOT NULL,
    role VARCHAR(200) NOT NULL,
    placement_drive_id UUID REFERENCES placement_drives(id),
    difficulty VARCHAR(20) NOT NULL,
    verdict VARCHAR(30) NOT NULL,
    overall_experience TEXT NOT NULL,
    questions_asked JSONB DEFAULT '[]',
    tips_for_juniors TEXT,
    upvotes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- 7. Drive Announcements
CREATE TABLE IF NOT EXISTS drive_announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drive_id UUID NOT NULL REFERENCES placement_drives(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(300) NOT NULL,
    message TEXT NOT NULL,
    urgency VARCHAR(20) DEFAULT 'normal',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
