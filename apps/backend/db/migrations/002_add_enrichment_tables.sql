-- Migration: Add tables for name enrichment data
-- Famous people/characters, popularity trends, related names, and trivia

-- Famous people/characters associated with names
CREATE TABLE IF NOT EXISTS famous_namesakes (
    id SERIAL PRIMARY KEY,
    name_id INTEGER REFERENCES names(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    category VARCHAR(50), -- 'historical', 'celebrity', 'fictional', 'athlete', 'politician', 'artist'
    description TEXT,
    birth_year INTEGER,
    death_year INTEGER,
    profession VARCHAR(100),
    notable_for TEXT,
    image_url VARCHAR(500),
    wikipedia_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_famous_namesakes_name_id ON famous_namesakes(name_id);
CREATE INDEX idx_famous_namesakes_category ON famous_namesakes(category);

-- Popularity trends over time
CREATE TABLE IF NOT EXISTS popularity_trends (
    id SERIAL PRIMARY KEY,
    name_id INTEGER REFERENCES names(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    rank INTEGER,
    count INTEGER,
    gender VARCHAR(20),
    country VARCHAR(2) DEFAULT 'US',
    source VARCHAR(50) DEFAULT 'SSA',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(name_id, year, gender, country, source)
);

CREATE INDEX idx_popularity_trends_name_id ON popularity_trends(name_id);
CREATE INDEX idx_popularity_trends_year ON popularity_trends(year);
CREATE INDEX idx_popularity_trends_rank ON popularity_trends(rank);

-- Related/similar names
CREATE TABLE IF NOT EXISTS related_names (
    id SERIAL PRIMARY KEY,
    name_id INTEGER REFERENCES names(id) ON DELETE CASCADE,
    related_name_id INTEGER REFERENCES names(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50), -- 'variant', 'diminutive', 'similar', 'rhymes', 'anagram'
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(name_id, related_name_id, relationship_type)
);

CREATE INDEX idx_related_names_name_id ON related_names(name_id);
CREATE INDEX idx_related_names_related_name_id ON related_names(related_name_id);

-- Name metadata and trivia
CREATE TABLE IF NOT EXISTS name_trivia (
    id SERIAL PRIMARY KEY,
    name_id INTEGER REFERENCES names(id) ON DELETE CASCADE,
    trivia_type VARCHAR(50), -- 'fact', 'quote', 'tradition', 'superstition', 'literature'
    content TEXT NOT NULL,
    source VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_name_trivia_name_id ON name_trivia(name_id);
CREATE INDEX idx_name_trivia_type ON name_trivia(trivia_type);

-- Update existing names table to track data completeness
ALTER TABLE names
ADD COLUMN IF NOT EXISTS has_trends BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS has_famous_people BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS data_last_enriched TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_names_has_trends ON names(has_trends);
CREATE INDEX IF NOT EXISTS idx_names_has_famous_people ON names(has_famous_people);
