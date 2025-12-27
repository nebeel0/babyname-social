-- Migration: Add prefix tree for name exploration
-- Supports filtering by gender, origin, popularity and highlighting

-- Prefix tree nodes for efficient name exploration
CREATE TABLE IF NOT EXISTS name_prefix_tree (
    id SERIAL PRIMARY KEY,
    prefix VARCHAR(50) NOT NULL UNIQUE,
    prefix_length INTEGER NOT NULL,
    is_complete_name BOOLEAN DEFAULT FALSE,
    name_id INTEGER REFERENCES names(id) ON DELETE CASCADE,

    -- Tree structure
    parent_id INTEGER REFERENCES name_prefix_tree(id) ON DELETE CASCADE,
    child_count INTEGER DEFAULT 0,
    total_descendants INTEGER DEFAULT 0,

    -- Filtering metadata (aggregated from child names)
    gender_counts JSONB DEFAULT '{"male": 0, "female": 0, "unisex": 0, "neutral": 0}',
    origin_countries TEXT[], -- Array of origin countries in this subtree
    popularity_range JSONB DEFAULT '{"min": 0, "max": 0, "avg": 0}',

    -- Highlighting support
    match_score FLOAT DEFAULT 0.0, -- For search relevance
    is_highlighted BOOLEAN DEFAULT FALSE, -- For UI highlighting
    highlight_reason VARCHAR(100), -- 'favorite', 'recent', 'match', etc.

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_prefix_tree_prefix ON name_prefix_tree(prefix);
CREATE INDEX IF NOT EXISTS idx_prefix_tree_prefix_length ON name_prefix_tree(prefix_length);
CREATE INDEX IF NOT EXISTS idx_prefix_tree_parent_id ON name_prefix_tree(parent_id);
CREATE INDEX IF NOT EXISTS idx_prefix_tree_name_id ON name_prefix_tree(name_id);
CREATE INDEX IF NOT EXISTS idx_prefix_tree_complete ON name_prefix_tree(is_complete_name) WHERE is_complete_name = TRUE;
CREATE INDEX IF NOT EXISTS idx_prefix_tree_highlighted ON name_prefix_tree(is_highlighted) WHERE is_highlighted = TRUE;

-- GIN index for origin countries array queries
CREATE INDEX IF NOT EXISTS idx_prefix_tree_origins ON name_prefix_tree USING GIN(origin_countries);

-- GIN index for gender_counts JSONB queries
CREATE INDEX IF NOT EXISTS idx_prefix_tree_gender_counts ON name_prefix_tree USING GIN(gender_counts);

-- Function to build/rebuild the prefix tree from existing names
CREATE OR REPLACE FUNCTION build_prefix_tree() RETURNS void AS $$
DECLARE
    name_record RECORD;
    current_prefix VARCHAR(50);
    current_length INTEGER;
    parent_node_id INTEGER;
    node_id INTEGER;
BEGIN
    -- Clear existing tree
    TRUNCATE name_prefix_tree CASCADE;

    -- For each name, create all its prefixes
    FOR name_record IN
        SELECT
            id,
            name,
            gender,
            origin_country,
            COALESCE(avg_rating, 0) as popularity
        FROM names
        ORDER BY name
    LOOP
        parent_node_id := NULL;

        -- Generate all prefixes for this name
        FOR current_length IN 1..LENGTH(name_record.name)
        LOOP
            current_prefix := SUBSTRING(name_record.name, 1, current_length);

            -- Insert or get existing node
            INSERT INTO name_prefix_tree (
                prefix,
                prefix_length,
                is_complete_name,
                name_id,
                parent_id,
                gender_counts,
                origin_countries,
                popularity_range
            )
            VALUES (
                current_prefix,
                current_length,
                current_length = LENGTH(name_record.name),
                CASE WHEN current_length = LENGTH(name_record.name) THEN name_record.id ELSE NULL END,
                parent_node_id,
                jsonb_build_object(
                    'male', CASE WHEN name_record.gender = 'male' THEN 1 ELSE 0 END,
                    'female', CASE WHEN name_record.gender = 'female' THEN 1 ELSE 0 END,
                    'unisex', CASE WHEN name_record.gender = 'unisex' THEN 1 ELSE 0 END,
                    'neutral', CASE WHEN name_record.gender = 'neutral' OR name_record.gender IS NULL THEN 1 ELSE 0 END
                ),
                ARRAY[name_record.origin_country]::TEXT[],
                jsonb_build_object(
                    'min', name_record.popularity,
                    'max', name_record.popularity,
                    'avg', name_record.popularity
                )
            )
            ON CONFLICT (prefix)
            DO UPDATE SET
                -- Update gender counts
                gender_counts = jsonb_build_object(
                    'male',
                    (name_prefix_tree.gender_counts->>'male')::int +
                    CASE WHEN name_record.gender = 'male' THEN 1 ELSE 0 END,

                    'female',
                    (name_prefix_tree.gender_counts->>'female')::int +
                    CASE WHEN name_record.gender = 'female' THEN 1 ELSE 0 END,

                    'unisex',
                    (name_prefix_tree.gender_counts->>'unisex')::int +
                    CASE WHEN name_record.gender = 'unisex' THEN 1 ELSE 0 END,

                    'neutral',
                    (name_prefix_tree.gender_counts->>'neutral')::int +
                    CASE WHEN name_record.gender = 'neutral' OR name_record.gender IS NULL THEN 1 ELSE 0 END
                ),
                -- Append origin if not already present
                origin_countries = CASE
                    WHEN name_record.origin_country = ANY(name_prefix_tree.origin_countries) THEN name_prefix_tree.origin_countries
                    ELSE array_append(name_prefix_tree.origin_countries, name_record.origin_country)
                END,
                -- Update popularity range
                popularity_range = jsonb_build_object(
                    'min', LEAST((name_prefix_tree.popularity_range->>'min')::float, name_record.popularity),
                    'max', GREATEST((name_prefix_tree.popularity_range->>'max')::float, name_record.popularity),
                    'avg', ((name_prefix_tree.popularity_range->>'avg')::float + name_record.popularity) / 2.0
                ),
                updated_at = NOW()
            RETURNING id INTO node_id;

            -- Update parent's child count
            IF parent_node_id IS NOT NULL THEN
                UPDATE name_prefix_tree
                SET child_count = child_count + 1,
                    updated_at = NOW()
                WHERE id = parent_node_id;
            END IF;

            -- Current node becomes parent for next iteration
            parent_node_id := node_id;
        END LOOP;
    END LOOP;

    -- Update total_descendants counts (simpler approach)
    -- Count all descendant nodes for each prefix
    UPDATE name_prefix_tree parent
    SET total_descendants = (
        SELECT COUNT(*)
        FROM name_prefix_tree child
        WHERE child.prefix LIKE parent.prefix || '%'
        AND child.id != parent.id
        AND child.is_complete_name = TRUE
    ),
    updated_at = NOW();

    RAISE NOTICE 'Prefix tree built successfully with % nodes', (SELECT COUNT(*) FROM name_prefix_tree);
END;
$$ LANGUAGE plpgsql;

-- Add indexes to names table for better prefix tree performance
CREATE INDEX IF NOT EXISTS idx_names_name_text ON names(name text_pattern_ops);
CREATE INDEX IF NOT EXISTS idx_names_name_lower ON names(LOWER(name));

-- Update names table to track prefix tree membership
ALTER TABLE names
ADD COLUMN IF NOT EXISTS in_prefix_tree BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_names_in_prefix_tree ON names(in_prefix_tree) WHERE in_prefix_tree = TRUE;

-- Build the initial prefix tree
SELECT build_prefix_tree();
