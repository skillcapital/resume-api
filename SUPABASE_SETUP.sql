-- AI Resume Builder - Supabase Database Setup
-- Run this SQL in your Supabase SQL Editor

-- ============================================
-- 1. Create resumes table
-- ============================================
CREATE TABLE IF NOT EXISTS resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- 2. Create resume_versions table
-- ============================================
CREATE TABLE IF NOT EXISTS resume_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    content JSONB NOT NULL,
    version_type TEXT DEFAULT 'improved' CHECK (version_type IN ('improved', 'tailored', 'original')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- 3. Create indexes for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_resume_versions_resume_id 
    ON resume_versions(resume_id);

CREATE INDEX IF NOT EXISTS idx_resume_versions_created_at 
    ON resume_versions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_resume_versions_type 
    ON resume_versions(version_type);

CREATE INDEX IF NOT EXISTS idx_resumes_created_at 
    ON resumes(created_at DESC);

-- ============================================
-- 4. Enable Row Level Security (RLS)
-- ============================================
ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE resume_versions ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 5. Create RLS Policies
-- ============================================
-- Allow service role to do everything (for backend API)
CREATE POLICY "Service role can do everything on resumes"
    ON resumes FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role can do everything on resume_versions"
    ON resume_versions FOR ALL
    USING (true)
    WITH CHECK (true);

-- ============================================
-- 6. Create function to update updated_at timestamp
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_resumes_updated_at 
    BEFORE UPDATE ON resumes 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 7. Storage Buckets Setup
-- ============================================
-- Note: These need to be created in Supabase Dashboard > Storage
-- 
-- Bucket 1: "uploads"
--   - Public: Yes
--   - File size limit: 10MB
--   - Allowed MIME types: application/pdf
--
-- Bucket 2: "exports"
--   - Public: Yes
--   - File size limit: 5MB
--   - Allowed MIME types: application/pdf

-- ============================================
-- 8. Optional: Create view for latest resume versions
-- ============================================
CREATE OR REPLACE VIEW latest_resume_versions AS
SELECT DISTINCT ON (resume_id)
    rv.*,
    r.raw_text,
    r.created_at as resume_created_at
FROM resume_versions rv
JOIN resumes r ON r.id = rv.resume_id
ORDER BY rv.resume_id, rv.created_at DESC;

-- ============================================
-- Setup Complete!
-- ============================================
-- Next steps:
-- 1. Create storage buckets in Dashboard > Storage
-- 2. Update your .env file with Supabase credentials
-- 3. Run the FastAPI application

