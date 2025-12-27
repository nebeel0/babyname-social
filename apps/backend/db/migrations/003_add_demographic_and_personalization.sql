-- Migration: Add demographic, cultural, and personalization data
-- PURPOSE: Transform app into data-driven decision tool with personalized recommendations
--
-- DATA PURPOSE EXPLANATIONS:
-- 1. Ethnicity/Race Data: Help users find names that match their cultural background
-- 2. Nicknames: Show flexibility and informal options for each name
-- 3. User Profiles: Enable personalized recommendations based on demographics & preferences
-- 4. Perception Metrics: Inform users about research-backed societal perceptions

-- ==========================================
-- ETHNICITY/RACE PROBABILITY DATA
-- ==========================================
-- PURPOSE: Match names to user's cultural/ethnic background
-- USE CASE: "Show me names commonly used in my community"
-- DATA SOURCE: Harvard Dataverse (136k names, voter registration data)
--
-- DISPLAYED AS:
-- - Cultural fit score in comparisons
-- - Ethnicity distribution charts
-- - "Popular in [Your Community]" badges

CREATE TABLE IF NOT EXISTS name_ethnicity_probabilities (
    id SERIAL PRIMARY KEY,
    name_id INTEGER REFERENCES names(id) ON DELETE CASCADE,

    -- Probability distributions (0.0 to 1.0)
    white_probability DECIMAL(5,4) DEFAULT 0,
    black_probability DECIMAL(5,4) DEFAULT 0,
    hispanic_probability DECIMAL(5,4) DEFAULT 0,
    asian_probability DECIMAL(5,4) DEFAULT 0,
    other_probability DECIMAL(5,4) DEFAULT 0,

    -- Metadata
    sample_size INTEGER, -- How many people this is based on
    data_source VARCHAR(100) DEFAULT 'Harvard Dataverse 2023',
    confidence_level VARCHAR(20), -- 'high', 'medium', 'low' based on sample size

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(name_id, data_source)
);

CREATE INDEX idx_ethnicity_name_id ON name_ethnicity_probabilities(name_id);
CREATE INDEX idx_ethnicity_confidence ON name_ethnicity_probabilities(confidence_level);

-- Add ethnicity data availability flag to names table
ALTER TABLE names
ADD COLUMN IF NOT EXISTS has_ethnicity_data BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_names_has_ethnicity ON names(has_ethnicity_data);


-- ==========================================
-- NICKNAMES AND VARIANTS
-- ==========================================
-- PURPOSE: Show naming flexibility and informal options
-- USE CASE: "I want a formal name with cute nickname options"
-- DATA SOURCE: GitHub nickname databases (HaJongler, carltonnorthern)
--
-- DISPLAYED AS:
-- - "Nickname options" list in name details
-- - "Nickname flexibility score" (count of established nicknames)
-- - Filter: "Show only names with nicknames"

CREATE TABLE IF NOT EXISTS name_nicknames (
    id SERIAL PRIMARY KEY,
    name_id INTEGER REFERENCES names(id) ON DELETE CASCADE,
    nickname VARCHAR(100) NOT NULL,
    is_diminutive BOOLEAN DEFAULT TRUE, -- true if shorter/cuter form
    popularity_rank INTEGER, -- 1 = most common nickname for this name

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(name_id, nickname)
);

CREATE INDEX idx_nicknames_name_id ON name_nicknames(name_id);
CREATE INDEX idx_nicknames_popularity ON name_nicknames(popularity_rank);

-- International and spelling variants
-- PURPOSE: Show global variations and alternative spellings
-- USE CASE: "What's this name called in other countries?"
CREATE TABLE IF NOT EXISTS name_variants (
    id SERIAL PRIMARY KEY,
    name_id INTEGER REFERENCES names(id) ON DELETE CASCADE,
    variant_name VARCHAR(100) NOT NULL,
    variant_type VARCHAR(50), -- 'spelling', 'international', 'historical', 'transliteration'
    country_code VARCHAR(2), -- ISO country code
    language VARCHAR(50),
    is_common BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(name_id, variant_name, variant_type)
);

CREATE INDEX idx_variants_name_id ON name_variants(name_id);
CREATE INDEX idx_variants_country ON name_variants(country_code) WHERE country_code IS NOT NULL;

-- Add nickname availability flag to names table
ALTER TABLE names
ADD COLUMN IF NOT EXISTS has_nicknames BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS nickname_count INTEGER DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_names_has_nicknames ON names(has_nicknames);


-- ==========================================
-- USER PROFILES
-- ==========================================
-- PURPOSE: Enable personalized recommendations
-- USE CASE: "Recommend names that fit MY situation"
--
-- PERSONALIZATION FACTORS:
-- - Cultural/ethnic match
-- - Regional popularity (where user lives)
-- - Family surname compatibility
-- - Personal style preferences (unique vs popular, modern vs traditional)
-- - Risk tolerance (discrimination awareness)

CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL, -- Session or account ID

    -- Demographics (optional, for personalization)
    ethnicity VARCHAR(50), -- 'white', 'black', 'hispanic', 'asian', 'multiracial', 'other', 'prefer_not_to_say'
    age INTEGER,

    -- Location (for regional popularity matching)
    current_state VARCHAR(2), -- US state code
    current_city VARCHAR(100),
    planned_state VARCHAR(2), -- Where they plan to live
    planned_city VARCHAR(100),
    country VARCHAR(2) DEFAULT 'US',

    -- Family context
    partner_ethnicity VARCHAR(50),
    existing_children_names TEXT[], -- Names of existing children for style consistency
    family_surnames TEXT[], -- For surname compatibility checking

    -- Preferences (1-5 scale or boolean)
    cultural_importance INTEGER DEFAULT 3 CHECK (cultural_importance BETWEEN 1 AND 5),
    uniqueness_preference INTEGER DEFAULT 3 CHECK (uniqueness_preference BETWEEN 1 AND 5),
    traditional_vs_modern INTEGER DEFAULT 3 CHECK (traditional_vs_modern BETWEEN 1 AND 5),
    nickname_friendly BOOLEAN DEFAULT TRUE,
    religious_significance BOOLEAN DEFAULT FALSE,
    avoid_discrimination_risk BOOLEAN DEFAULT TRUE,
    pronunciation_simplicity INTEGER DEFAULT 3 CHECK (pronunciation_simplicity BETWEEN 1 AND 5),

    -- Additional preferences
    preferred_name_length VARCHAR(20), -- 'short' (<5 letters), 'medium' (5-7), 'long' (8+), 'any'
    preferred_origins TEXT[], -- Array of preferred countries/regions
    disliked_sounds TEXT[], -- Phonetic patterns to avoid

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_ethnicity ON user_profiles(ethnicity);
CREATE INDEX idx_user_profiles_location ON user_profiles(current_state, current_city);


-- ==========================================
-- NAME PERCEPTION METRICS
-- ==========================================
-- PURPOSE: Inform users about societal perceptions (research-based)
-- USE CASE: "How will this name be perceived professionally?"
-- DATA SOURCES: Academic research on name discrimination, likability studies
--
-- DISPLAYED AS:
-- - "Professional perception" score
-- - "Hiring callback research" indicator
-- - "Uniqueness vs commonality" percentile
-- - Educational tooltips explaining research findings

CREATE TABLE IF NOT EXISTS name_perception_metrics (
    id SERIAL PRIMARY KEY,
    name_id INTEGER REFERENCES names(id) ON DELETE CASCADE,

    -- Research-backed metrics (0-100 scale)
    professionalism_score DECIMAL(5,2), -- Based on hiring research
    likability_score DECIMAL(5,2), -- Based on perception studies
    uniqueness_percentile DECIMAL(5,2), -- 0=very common, 100=very rare
    memorability_score DECIMAL(5,2), -- Easy to remember
    pronunciation_difficulty DECIMAL(5,2), -- 0=easy, 100=difficult
    spelling_difficulty DECIMAL(5,2), -- How often misspelled

    -- Hiring discrimination research
    -- Based on NBER studies (Bertrand & Mullainathan, etc.)
    hiring_callback_differential DECIMAL(6,3), -- Relative callback rate vs baseline
    callback_research_note TEXT, -- Explanation of research

    -- Calculated metrics
    formality_score DECIMAL(5,2), -- 0=very informal, 100=very formal
    modern_vs_classic_score DECIMAL(5,2), -- 0=classic, 100=modern

    -- Risk factors (boolean flags with explanations)
    potential_teasing_risk BOOLEAN DEFAULT FALSE,
    teasing_explanation TEXT,

    -- Data provenance
    data_sources TEXT[], -- Array of research papers/studies
    confidence_level VARCHAR(20), -- 'high', 'medium', 'low'
    last_updated TIMESTAMP DEFAULT NOW(),

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(name_id)
);

CREATE INDEX idx_perception_name_id ON name_perception_metrics(name_id);
CREATE INDEX idx_perception_professionalism ON name_perception_metrics(professionalism_score);
CREATE INDEX idx_perception_uniqueness ON name_perception_metrics(uniqueness_percentile);

-- Add perception data flag to names table
ALTER TABLE names
ADD COLUMN IF NOT EXISTS has_perception_data BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_names_has_perception ON names(has_perception_data);


-- ==========================================
-- REGIONAL POPULARITY
-- ==========================================
-- PURPOSE: Show where names are popular geographically
-- USE CASE: "Is this name popular in the city I'm moving to?"
-- DATA SOURCE: State/city level popularity data (future enhancement)

CREATE TABLE IF NOT EXISTS name_regional_popularity (
    id SERIAL PRIMARY KEY,
    name_id INTEGER REFERENCES names(id) ON DELETE CASCADE,

    state_code VARCHAR(2),
    city VARCHAR(100),
    year INTEGER NOT NULL,
    rank INTEGER,
    count INTEGER,

    -- Trend indicators
    trend_direction VARCHAR(10), -- 'rising', 'falling', 'stable'
    year_over_year_change DECIMAL(6,2), -- Percentage change from previous year

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(name_id, state_code, city, year)
);

CREATE INDEX idx_regional_name_id ON name_regional_popularity(name_id);
CREATE INDEX idx_regional_location ON name_regional_popularity(state_code, city);
CREATE INDEX idx_regional_year ON name_regional_popularity(year);


-- ==========================================
-- USER NAME INTERACTIONS
-- ==========================================
-- PURPOSE: Track user behavior for improving recommendations
-- USE CASE: Machine learning on user preferences

CREATE TABLE IF NOT EXISTS user_name_interactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    name_id INTEGER REFERENCES names(id) ON DELETE CASCADE,

    interaction_type VARCHAR(50), -- 'view', 'favorite', 'unfavorite', 'compare', 'share'
    interaction_metadata JSONB, -- Additional context

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_interactions_user_id ON user_name_interactions(user_id);
CREATE INDEX idx_interactions_name_id ON user_name_interactions(name_id);
CREATE INDEX idx_interactions_type ON user_name_interactions(interaction_type);
CREATE INDEX idx_interactions_created_at ON user_name_interactions(created_at);


-- ==========================================
-- FEATURE PURPOSE DOCUMENTATION
-- ==========================================
-- This table stores user-facing explanations of what each data point means
-- Used for tooltips and help text in the UI

CREATE TABLE IF NOT EXISTS feature_descriptions (
    id SERIAL PRIMARY KEY,
    feature_key VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    short_description TEXT NOT NULL,
    detailed_explanation TEXT,
    data_source TEXT,
    research_citations TEXT[],
    display_order INTEGER,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Populate with initial feature descriptions
INSERT INTO feature_descriptions (feature_key, display_name, short_description, detailed_explanation, display_order) VALUES
('cultural_fit', 'Cultural Fit Score', 'How well this name matches your cultural background', 'Based on demographic data from 136,000 names, this score shows how commonly this name is used within your ethnic/racial community. A higher score means the name is more prevalent in your community.', 1),
('ethnicity_distribution', 'Community Usage', 'Which communities commonly use this name', 'Shows the probability distribution of this name across different ethnic and racial groups based on voter registration data from six U.S. states.', 2),
('nickname_flexibility', 'Nickname Options', 'Informal name variations', 'Lists established nicknames and diminutives for this name. More options means more flexibility in how your child can choose to be called.', 3),
('professional_perception', 'Professional Perception', 'How this name may be perceived in professional settings', 'Based on academic research including resume callback studies. This indicator shows whether research has found any bias (positive or negative) associated with this name in hiring contexts.', 4),
('regional_popularity', 'Local Popularity', 'How popular this name is in your area', 'Shows the ranking and trends for this name in your current or planned location. Helps you understand if the name will be common or unique in your community.', 5),
('uniqueness_score', 'Uniqueness Score', 'How rare or common this name is', 'Percentile ranking from 0 (very common) to 100 (very rare). Based on national popularity data.', 6),
('pronunciation_ease', 'Pronunciation Simplicity', 'How easy this name is to pronounce', 'Indicates whether this name has straightforward pronunciation or may require frequent correction.', 7),
('hiring_research', 'Hiring Research Indicator', 'Research findings on name-based hiring bias', 'Academic studies have found that some names receive different callback rates on resumes. We provide this information so you can make an informed decision.', 8),
('surname_compatibility', 'Surname Compatibility', 'How well this name sounds with your family name', 'Analyzes phonetic flow, rhythm, and potential awkward combinations between the first and last name.', 9),
('sibling_harmony', 'Sibling Name Harmony', 'Style consistency with existing children', 'Compares naming style, length, origin, and popularity with names of existing children to maintain a cohesive family naming pattern.', 10)
ON CONFLICT (feature_key) DO NOTHING;
