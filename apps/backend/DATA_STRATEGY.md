# Baby Names Data Strategy

## Overview
Comprehensive data collection plan to transform baby name database into rich, personalized decision-making tool.

## Data Sources Identified

### 1. **Race/Ethnicity Demographics**
**Source**: Harvard Dataverse - "Race and ethnicity data for first, middle, and last names"
- **URL**: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/SGKW0K
- **Coverage**: 136,000 first names
- **Data**: Probability distributions across 5 categories (White, Black, Hispanic, Asian, Other)
- **Based on**: Voter registration data from 6 Southern U.S. states
- **Published**: May 2023
- **Status**: Ready to download

### 2. **NYC Ethnic Group Data**
**Source**: NYC Open Data - Popular Baby Names by Ethnic Group
- **URL**: https://catalog.data.gov/dataset/popular-baby-names
- **Coverage**: Names by sex and ethnic group
- **Updated**: June 2024
- **Status**: Ready to download

### 3. **Nickname/Variant Databases**
**Sources** (Multiple GitHub repositories):

a) **HaJongler/diminutives.db**
   - URL: https://github.com/HaJongler/diminutives.db
   - male_diminutives.csv + female_diminutives.csv
   - Public Domain

b) **carltonnorthern/nicknames**
   - URL: https://github.com/carltonnorthern/nicknames
   - ~1,100 canonical names with nicknames
   - Semantic triplets format

c) **tfmorris/Names**
   - URL: https://github.com/tfmorris/Names
   - Comprehensive variant database
   - Multiple sources combined

### 4. **Name Discrimination Research Data**
**Source**: NBER Working Papers
- "Are Emily and Greg More Employable than Lakisha and Jamal?"
- 5,000 resume study data
- Callback rate differentials by perceived race
- Can inform "hiring perception" score

### 5. **Global Name Dataset**
**Source**: philipperemy/name-dataset (GitHub)
- 491,655,925 records from 106 countries
- First name, last name, gender, country code
- Python library available

## Database Schema Extensions

### New Tables

#### 1. `name_ethnicity_probabilities`
```sql
- name_id (FK)
- white_probability (DECIMAL)
- black_probability (DECIMAL)
- hispanic_probability (DECIMAL)
- asian_probability (DECIMAL)
- other_probability (DECIMAL)
- data_source (VARCHAR)
```

#### 2. `name_nicknames`
```sql
- id (PK)
- name_id (FK to canonical name)
- nickname (VARCHAR)
- is_diminutive (BOOLEAN)
- popularity_score (INT) - optional
```

#### 3. `name_variants`
```sql
- id (PK)
- name_id (FK)
- variant_name (VARCHAR)
- variant_type (ENUM: spelling, international, historical)
- country_code (VARCHAR)
- language (VARCHAR)
```

#### 4. `name_perception_metrics`
```sql
- name_id (FK)
- professionalism_score (DECIMAL) - based on research
- uniqueness_score (DECIMAL)
- hiring_callback_differential (DECIMAL) - from discrimination studies
- likability_score (DECIMAL)
- data_source (VARCHAR)
```

#### 5. `name_regional_popularity`
```sql
- name_id (FK)
- state_code (VARCHAR)
- city (VARCHAR)
- year (INT)
- rank (INT)
- count (INT)
```

### User Profile System

#### New Table: `user_profiles`
```sql
- id (PK)
- user_id (VARCHAR) - session or account ID
- ethnicity (VARCHAR)
- age (INT)
- current_location_state (VARCHAR)
- current_location_city (VARCHAR)
- planned_location_state (VARCHAR)
- planned_location_city (VARCHAR)
- family_surnames (TEXT[])
- preferences (JSONB) {
    cultural_importance: 1-5,
    uniqueness_preference: 1-5,
    traditional_vs_modern: 1-5,
    nickname_friendly: boolean,
    avoid_discrimination_risk: boolean
  }
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

## Calculated/Derived Metrics

### 1. **Cultural Fit Score**
- Match user's ethnicity with name's ethnic probability distribution
- Bonus for cultural/religious significance match

### 2. **Regional Appropriateness**
- How common is this name in user's current/planned location
- Trend direction in that region

### 3. **Professional Success Indicator**
- Based on hiring callback research
- Adjusted by industry/region

### 4. **Uniqueness Index**
- Percentile ranking in database
- Regional uniqueness vs national

### 5. **Nickname Flexibility Score**
- Number of established nicknames
- Variety of nickname styles (formal/informal)

### 6. **Bullying Risk Indicator** ⚠️
*Ethically sensitive - need careful implementation*
- Phonetic similarity to common insults
- Historical bullying reports (if data available)
- Rhyming vulnerability

## Personalized Recommendation Algorithm

### Inputs:
1. User profile (ethnicity, location, preferences)
2. Name database with all enrichments
3. User's explicit likes/dislikes
4. Family name compatibility

### Scoring Factors:
1. **Cultural Match** (weight: 25%)
   - Ethnicity probability match
   - Religious/cultural significance

2. **Regional Fit** (weight: 20%)
   - Popularity in user's location
   - Trend direction

3. **Professional Perception** (weight: 15%)
   - Hiring callback data
   - Professionalism scores

4. **User Preferences** (weight: 25%)
   - Uniqueness vs popularity preference
   - Traditional vs modern
   - Nickname preferences

5. **Family Harmony** (weight: 10%)
   - Phonetic compatibility with surname
   - Sibling name style consistency

6. **Practical Considerations** (weight: 5%)
   - Spelling difficulty
   - Pronunciation clarity
   - International usability

## Data Collection Priority

### Phase 1 (Immediate)
1. ✅ Already have: Hadley Wickham popularity trends (258k records)
2. Download Harvard Dataverse ethnicity data (136k names)
3. Download nickname databases from GitHub

### Phase 2 (Week 1)
4. Implement user profile system
5. Build ethnicity probability matching
6. Add nickname lookup

### Phase 3 (Week 2)
7. Regional data collection
8. Perception metrics calculation
9. Personalized recommendation engine

### Phase 4 (Future)
10. Machine learning on user behavior
11. A/B testing of recommendation quality
12. Social features (share with partner/family)

## API Enhancements Needed

### New Endpoints:
```
POST /api/v1/users/profile
GET /api/v1/users/profile
PUT /api/v1/users/profile

GET /api/v1/names/{id}/ethnicity
GET /api/v1/names/{id}/nicknames
GET /api/v1/names/{id}/variants
GET /api/v1/names/{id}/perception

GET /api/v1/recommendations - personalized recommendations
POST /api/v1/names/{id}/feedback - user feedback on names
```

## Ethical Considerations

### ⚠️ Sensitive Data Handling:
1. **Race/Ethnicity Data**
   - Probabilistic, not deterministic
   - Educational/informational purpose only
   - Clear disclaimers about data limitations
   - No discriminatory use

2. **Hiring Discrimination Data**
   - Present as "research shows" not prescriptive
   - Empower users with information
   - Don't hide uncomfortable truths

3. **"Bullying Risk"**
   - Most ethically fraught feature
   - Consider: is this helpful or harmful?
   - Alternative: "practical considerations" score
   - Focus on phonetics, spelling complexity

4. **User Privacy**
   - Profiles stored locally when possible
   - Optional account system
   - Clear data usage policies

## Success Metrics

1. **Data Coverage**: % of names with ethnicity data, nicknames, etc.
2. **Recommendation Quality**: User satisfaction with suggestions
3. **Engagement**: Time spent comparing names
4. **Conversion**: Names added to favorites
5. **User Profiles**: % of users who create profiles

## Next Steps

1. Download Harvard Dataverse dataset
2. Create database migrations for new tables
3. Implement import scripts
4. Build user profile system
5. Create recommendation engine
6. Update frontend with new data visualizations
