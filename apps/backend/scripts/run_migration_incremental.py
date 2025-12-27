"""Run database migration with intelligent table handling"""
import asyncio
import sys
from pathlib import Path
import asyncpg


async def run_migration():
    """Run migration by checking what exists and updating incrementally"""

    print("="*70)
    print("🚀 RUNNING INCREMENTAL MIGRATION")
    print("="*70)

    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        user='postgres',
        password='postgres',
        database='babynames_db'
    )

    try:
        # Get existing tables
        tables_result = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        existing_tables = {row['table_name'] for row in tables_result}
        print(f"📊 Found {len(existing_tables)} existing tables")

        # 1. Create name_ethnicity_probabilities table
        if 'name_ethnicity_probabilities' not in existing_tables:
            print("\n📦 Creating name_ethnicity_probabilities table...")
            await conn.execute("""
                CREATE TABLE name_ethnicity_probabilities (
                    id SERIAL PRIMARY KEY,
                    name_id INTEGER REFERENCES names(id) ON DELETE CASCADE,
                    white_probability DECIMAL(5,4) DEFAULT 0,
                    black_probability DECIMAL(5,4) DEFAULT 0,
                    hispanic_probability DECIMAL(5,4) DEFAULT 0,
                    asian_probability DECIMAL(5,4) DEFAULT 0,
                    other_probability DECIMAL(5,4) DEFAULT 0,
                    sample_size INTEGER,
                    data_source VARCHAR(100) DEFAULT 'Harvard Dataverse 2023',
                    confidence_level VARCHAR(20),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(name_id, data_source)
                )
            """)
            await conn.execute("CREATE INDEX idx_ethnicity_name_id ON name_ethnicity_probabilities(name_id)")
            await conn.execute("CREATE INDEX idx_ethnicity_confidence ON name_ethnicity_probabilities(confidence_level)")
            print("  ✅ Created name_ethnicity_probabilities")
        else:
            print("  ⏭️  name_ethnicity_probabilities already exists")

        # 2. Add ethnicity flag to names table
        print("\n📦 Adding has_ethnicity_data flag to names...")
        try:
            await conn.execute("ALTER TABLE names ADD COLUMN IF NOT EXISTS has_ethnicity_data BOOLEAN DEFAULT FALSE")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_names_has_ethnicity ON names(has_ethnicity_data)")
            print("  ✅ Added has_ethnicity_data flag")
        except Exception as e:
            print(f"  ⏭️  Column already exists or error: {e}")

        # 3. Create name_nicknames table
        if 'name_nicknames' not in existing_tables:
            print("\n📦 Creating name_nicknames table...")
            await conn.execute("""
                CREATE TABLE name_nicknames (
                    id SERIAL PRIMARY KEY,
                    name_id INTEGER REFERENCES names(id) ON DELETE CASCADE,
                    nickname VARCHAR(100) NOT NULL,
                    is_diminutive BOOLEAN DEFAULT TRUE,
                    popularity_rank INTEGER,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(name_id, nickname)
                )
            """)
            await conn.execute("CREATE INDEX idx_nicknames_name_id ON name_nicknames(name_id)")
            await conn.execute("CREATE INDEX idx_nicknames_popularity ON name_nicknames(popularity_rank)")
            print("  ✅ Created name_nicknames")
        else:
            print("  ⏭️  name_nicknames already exists")

        # 4. Update name_variants table (alter if needed)
        if 'name_variants' in existing_tables:
            print("\n📦 Updating name_variants table...")
            try:
                await conn.execute("ALTER TABLE name_variants ADD COLUMN IF NOT EXISTS country_code VARCHAR(2)")
                await conn.execute("ALTER TABLE name_variants ADD COLUMN IF NOT EXISTS is_common BOOLEAN DEFAULT FALSE")
                print("  ✅ Added missing columns to name_variants")
            except Exception as e:
                print(f"  ⏭️  Columns may already exist: {e}")

        # 5. Add nickname flags to names table
        print("\n📦 Adding nickname flags to names...")
        try:
            await conn.execute("ALTER TABLE names ADD COLUMN IF NOT EXISTS has_nicknames BOOLEAN DEFAULT FALSE")
            await conn.execute("ALTER TABLE names ADD COLUMN IF NOT EXISTS nickname_count INTEGER DEFAULT 0")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_names_has_nicknames ON names(has_nicknames)")
            print("  ✅ Added nickname flags")
        except Exception as e:
            print(f"  ⏭️  Columns already exist: {e}")

        # 6. Create user_profiles table
        if 'user_profiles' not in existing_tables:
            print("\n📦 Creating user_profiles table...")
            await conn.execute("""
                CREATE TABLE user_profiles (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) UNIQUE NOT NULL,
                    ethnicity VARCHAR(50),
                    age INTEGER,
                    current_state VARCHAR(2),
                    current_city VARCHAR(100),
                    planned_state VARCHAR(2),
                    planned_city VARCHAR(100),
                    country VARCHAR(2) DEFAULT 'US',
                    partner_ethnicity VARCHAR(50),
                    existing_children_names TEXT[],
                    family_surnames TEXT[],
                    cultural_importance INTEGER DEFAULT 3 CHECK (cultural_importance BETWEEN 1 AND 5),
                    uniqueness_preference INTEGER DEFAULT 3 CHECK (uniqueness_preference BETWEEN 1 AND 5),
                    traditional_vs_modern INTEGER DEFAULT 3 CHECK (traditional_vs_modern BETWEEN 1 AND 5),
                    nickname_friendly BOOLEAN DEFAULT TRUE,
                    religious_significance BOOLEAN DEFAULT FALSE,
                    avoid_discrimination_risk BOOLEAN DEFAULT TRUE,
                    pronunciation_simplicity INTEGER DEFAULT 3 CHECK (pronunciation_simplicity BETWEEN 1 AND 5),
                    preferred_name_length VARCHAR(20),
                    preferred_origins TEXT[],
                    disliked_sounds TEXT[],
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            await conn.execute("CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id)")
            await conn.execute("CREATE INDEX idx_user_profiles_ethnicity ON user_profiles(ethnicity)")
            await conn.execute("CREATE INDEX idx_user_profiles_location ON user_profiles(current_state, current_city)")
            print("  ✅ Created user_profiles")
        else:
            print("  ⏭️  user_profiles already exists")

        # 7. Create name_perception_metrics table
        if 'name_perception_metrics' not in existing_tables:
            print("\n📦 Creating name_perception_metrics table...")
            await conn.execute("""
                CREATE TABLE name_perception_metrics (
                    id SERIAL PRIMARY KEY,
                    name_id INTEGER REFERENCES names(id) ON DELETE CASCADE,
                    professionalism_score DECIMAL(5,2),
                    likability_score DECIMAL(5,2),
                    uniqueness_percentile DECIMAL(5,2),
                    memorability_score DECIMAL(5,2),
                    pronunciation_difficulty DECIMAL(5,2),
                    spelling_difficulty DECIMAL(5,2),
                    hiring_callback_differential DECIMAL(6,3),
                    callback_research_note TEXT,
                    formality_score DECIMAL(5,2),
                    modern_vs_classic_score DECIMAL(5,2),
                    potential_teasing_risk BOOLEAN DEFAULT FALSE,
                    teasing_explanation TEXT,
                    data_sources TEXT[],
                    confidence_level VARCHAR(20),
                    last_updated TIMESTAMP DEFAULT NOW(),
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(name_id)
                )
            """)
            await conn.execute("CREATE INDEX idx_perception_name_id ON name_perception_metrics(name_id)")
            await conn.execute("CREATE INDEX idx_perception_professionalism ON name_perception_metrics(professionalism_score)")
            await conn.execute("CREATE INDEX idx_perception_uniqueness ON name_perception_metrics(uniqueness_percentile)")
            print("  ✅ Created name_perception_metrics")
        else:
            print("  ⏭️  name_perception_metrics already exists")

        # 8. Add perception flag to names table
        print("\n📦 Adding has_perception_data flag to names...")
        try:
            await conn.execute("ALTER TABLE names ADD COLUMN IF NOT EXISTS has_perception_data BOOLEAN DEFAULT FALSE")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_names_has_perception ON names(has_perception_data)")
            print("  ✅ Added has_perception_data flag")
        except Exception as e:
            print(f"  ⏭️  Column already exists: {e}")

        # 9. Create name_regional_popularity table
        if 'name_regional_popularity' not in existing_tables:
            print("\n📦 Creating name_regional_popularity table...")
            await conn.execute("""
                CREATE TABLE name_regional_popularity (
                    id SERIAL PRIMARY KEY,
                    name_id INTEGER REFERENCES names(id) ON DELETE CASCADE,
                    state_code VARCHAR(2),
                    city VARCHAR(100),
                    year INTEGER NOT NULL,
                    rank INTEGER,
                    count INTEGER,
                    trend_direction VARCHAR(10),
                    year_over_year_change DECIMAL(6,2),
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(name_id, state_code, city, year)
                )
            """)
            await conn.execute("CREATE INDEX idx_regional_name_id ON name_regional_popularity(name_id)")
            await conn.execute("CREATE INDEX idx_regional_location ON name_regional_popularity(state_code, city)")
            await conn.execute("CREATE INDEX idx_regional_year ON name_regional_popularity(year)")
            print("  ✅ Created name_regional_popularity")
        else:
            print("  ⏭️  name_regional_popularity already exists")

        # 10. Create user_name_interactions table
        if 'user_name_interactions' not in existing_tables:
            print("\n📦 Creating user_name_interactions table...")
            await conn.execute("""
                CREATE TABLE user_name_interactions (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    name_id INTEGER REFERENCES names(id) ON DELETE CASCADE,
                    interaction_type VARCHAR(50),
                    interaction_metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            await conn.execute("CREATE INDEX idx_interactions_user_id ON user_name_interactions(user_id)")
            await conn.execute("CREATE INDEX idx_interactions_name_id ON user_name_interactions(name_id)")
            await conn.execute("CREATE INDEX idx_interactions_type ON user_name_interactions(interaction_type)")
            await conn.execute("CREATE INDEX idx_interactions_created_at ON user_name_interactions(created_at)")
            print("  ✅ Created user_name_interactions")
        else:
            print("  ⏭️  user_name_interactions already exists")

        # 11. Create feature_descriptions table and populate
        if 'feature_descriptions' not in existing_tables:
            print("\n📦 Creating feature_descriptions table...")
            await conn.execute("""
                CREATE TABLE feature_descriptions (
                    id SERIAL PRIMARY KEY,
                    feature_key VARCHAR(100) UNIQUE NOT NULL,
                    display_name VARCHAR(200) NOT NULL,
                    short_description TEXT NOT NULL,
                    detailed_explanation TEXT,
                    data_source TEXT,
                    research_citations TEXT[],
                    display_order INTEGER,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Populate with initial feature descriptions
            features = [
                ('cultural_fit', 'Cultural Fit Score', 'How well this name matches your cultural background',
                 'Based on demographic data from 136,000 names, this score shows how commonly this name is used within your ethnic/racial community. A higher score means the name is more prevalent in your community.', 1),
                ('ethnicity_distribution', 'Community Usage', 'Which communities commonly use this name',
                 'Shows the probability distribution of this name across different ethnic and racial groups based on voter registration data from six U.S. states.', 2),
                ('nickname_flexibility', 'Nickname Options', 'Informal name variations',
                 'Lists established nicknames and diminutives for this name. More options means more flexibility in how your child can choose to be called.', 3),
                ('professional_perception', 'Professional Perception', 'How this name may be perceived in professional settings',
                 'Based on academic research including resume callback studies. This indicator shows whether research has found any bias (positive or negative) associated with this name in hiring contexts.', 4),
                ('regional_popularity', 'Local Popularity', 'How popular this name is in your area',
                 'Shows the ranking and trends for this name in your current or planned location. Helps you understand if the name will be common or unique in your community.', 5),
                ('uniqueness_score', 'Uniqueness Score', 'How rare or common this name is',
                 'Percentile ranking from 0 (very common) to 100 (very rare). Based on national popularity data.', 6),
                ('pronunciation_ease', 'Pronunciation Simplicity', 'How easy this name is to pronounce',
                 'Indicates whether this name has straightforward pronunciation or may require frequent correction.', 7),
                ('hiring_research', 'Hiring Research Indicator', 'Research findings on name-based hiring bias',
                 'Academic studies have found that some names receive different callback rates on resumes. We provide this information so you can make an informed decision.', 8),
                ('surname_compatibility', 'Surname Compatibility', 'How well this name sounds with your family name',
                 'Analyzes phonetic flow, rhythm, and potential awkward combinations between the first and last name.', 9),
                ('sibling_harmony', 'Sibling Name Harmony', 'Style consistency with existing children',
                 'Compares naming style, length, origin, and popularity with names of existing children to maintain a cohesive family naming pattern.', 10)
            ]

            for feature_key, display_name, short_desc, detailed_exp, order in features:
                await conn.execute("""
                    INSERT INTO feature_descriptions (feature_key, display_name, short_description, detailed_explanation, display_order)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (feature_key) DO NOTHING
                """, feature_key, display_name, short_desc, detailed_exp, order)

            print(f"  ✅ Created and populated feature_descriptions ({len(features)} features)")
        else:
            print("  ⏭️  feature_descriptions already exists")

        print("\n" + "="*70)
        print("✅ MIGRATION COMPLETE!")
        print("="*70)

        # Show updated table count
        tables_result = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        print(f"\n📊 Total tables: {len(tables_result)}")
        for row in tables_result:
            print(f"  - {row['table_name']}")

        return True

    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await conn.close()


if __name__ == "__main__":
    success = asyncio.run(run_migration())
    sys.exit(0 if success else 1)
