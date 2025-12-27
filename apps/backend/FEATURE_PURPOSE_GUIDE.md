# Baby Names App - Feature Purpose Guide

## 🎯 What Each Data Point Does & Why It Matters

This document explains every feature, what data it uses, and how it helps users make better naming decisions.

---

## 1. Cultural Fit Score
**What it shows**: How commonly this name is used in your ethnic/racial community
**Data source**: Harvard Dataverse (136,000 names, voter registration data)
**Use case**: "I want a name that's familiar in my cultural community"

### How it works:
- User selects their ethnicity in profile
- System shows probability distribution: White 45%, Black 35%, Hispanic 15%, Asian 3%, Other 2%
- Cultural Fit Score = alignment between user's ethnicity and name's distribution
- **Display**: Percentage match + distribution chart

**Example**:
- Name: "Aaliyah"
- Distribution: 3% White, 89% Black, 5% Hispanic, 1% Asian, 2% Other
- User ethnicity: Black
- **Cultural Fit: 89%** → "Very common in your community"

---

## 2. Ethnicity Distribution Visualization
**What it shows**: Which communities use this name and how often
**Data source**: Same Harvard dataset
**Use case**: "I want to understand the cultural associations of this name"

### Display format:
```
█████████████████████ White 65%
██████ Black 15%
████ Hispanic 10%
███ Asian 7%
█ Other 3%
```

**Educational purpose**: Helps users make informed decisions about cultural associations

---

## 3. Nickname Flexibility
**What it shows**: All established nicknames/diminutives for a name
**Data source**: GitHub nickname databases (1,100+ canonical names)
**Use case**: "I want a formal name with cute nickname options"

### How it works:
- Shows list of common nicknames
- Calculates "Nickname Flexibility Score" = number of established nicknames
- **Higher score = more options for your child**

**Example**:
- Name: "Alexander"
- Nicknames: Al, Alec, Aleck, Alex, Lex, Sander, Sandy, Xan, Zander
- **Flexibility Score: 9/10** → "Many nickname options"

**Why it matters**: Gives children choices in how they want to be called

---

## 4. Professional Perception Score
**What it shows**: Research-based likelihood of professional bias
**Data source**: Academic hiring callback studies (NBER, Bertrand & Mullainathan)
**Use case**: "How will this name affect my child's job prospects?"

### How it works:
- Based on resume callback research
- Names tested in identical resumes showed different callback rates
- **Not prescriptive** - educational and empowering

**Research findings**:
- "Emily" & "Greg": 50% more callbacks than "Lakisha" & "Jamal" (same resumes)
- Technology industry: No significant bias found
- Other industries: Varying levels of bias

**Display**:
- Research Summary card
- Citation to academic papers
- **Clear disclaimer**: "This is research data, not destiny. Your child's achievements matter most."

**Why we show this**: Controversial but important. Parents deserve to know research findings.

---

## 5. Regional Popularity
**What it shows**: How popular this name is in user's city/state
**Data source**: State-level SSA data + city breakdowns
**Use case**: "Will this name be common or unique where I live?"

### How it works:
- User enters current city + planned future location
- Shows popularity rank in both locations
- Trend indicator: ↗️ Rising, ↘️ Falling, → Stable

**Example**:
- Name: "Liam"
- Your location: Austin, TX
- Rank: #3 (Very common)
- Trend: ↗️ Rising +15% year-over-year
- **Uniqueness in your area: Low**

**Why it matters**: Same name can be unique in rural Montana but common in Brooklyn

---

## 6. Uniqueness Percentile
**What it shows**: How rare or common this name is nationally
**Calculation**: Based on total births with this name
**Use case**: "I want a unique name" or "I want a popular name"

### Scale:
- 0-20%: Very common (top 1,000 names)
- 21-40%: Common
- 41-60%: Moderate
- 61-80%: Uncommon
- 81-100%: Very rare

**Example**:
- "Emma": Uniqueness 5% → "One of the most popular names"
- "Zephyr": Uniqueness 95% → "Very rare and distinctive"

**User preference matching**:
- User sets "Uniqueness Preference: 4/5" (wants unique)
- System recommends names with 70-95% uniqueness

---

## 7. Pronunciation & Spelling Difficulty
**What it shows**: How often this name is mispronounced or misspelled
**Data source**: Phonetic analysis + user reports
**Use case**: "I don't want my child constantly correcting people"

### Metrics:
- **Pronunciation Difficulty**: 1-5 scale
  - 1: "John" - obvious pronunciation
  - 5: "Saoirse" - frequently mispronounced

- **Spelling Difficulty**: Based on common misspellings
  - Examples: "Catherine" vs "Katherine" vs "Kathryn"

**Display**:
- ⚠️ "Commonly mispronounced - may require frequent correction"
- ✓ "Straightforward pronunciation"

---

## 8. Hiring Callback Research Indicator
**What it shows**: Whether research found bias for/against this name
**Data source**: Multiple academic studies on hiring discrimination
**Use case**: Transparency about potential workplace bias

### Research-backed data:
- Resume callback differential percentage
- Industry-specific findings
- Citations to peer-reviewed research

**Example**:
- Name: "Lakisha"
- Research finding: -33% callback rate vs "Emily" (identical resumes)
- Industries studied: Sales, Admin, Clerical, Customer Service
- Technology: No significant bias found

**Why this is important**:
1. **Controversial but necessary**: Hiding this data doesn't make bias disappear
2. **Empowering**: Parents make informed choices
3. **Evidence-based**: Uses peer-reviewed academic research
4. **Not deterministic**: Explained as context, not destiny

---

## 9. Surname Compatibility
**What it shows**: How well first name flows with family surname
**Analysis**: Phonetic rhythm, rhyming issues, awkward combinations
**Use case**: "Does this sound good with our last name?"

### Checks for:
- Rhyming issues: "Ray Bay" ❌
- Repetitive sounds: "Barry Berry" ❌
- Flow/rhythm: Number of syllables, stress patterns
- Awkward combinations: "Richard Head" ❌
- Initial combinations: "A.S.S." ❌

**Example**:
- First: "Emma"
- Last: "Smith"
- Analysis: ✓ Good flow (2 syllables + 1 syllable)
- **Compatibility: 9/10** → "Excellent match"

---

## 10. Sibling Name Harmony
**What it shows**: Style consistency with existing children's names
**Data**: User enters existing children's names
**Use case**: "I want all my kids' names to sound cohesive"

### Analyzes:
- **Length similarity**: All short vs mixing short and long
- **Origin consistency**: All Irish vs mixing origins
- **Popularity alignment**: All popular vs all unique
- **Style matching**: All classic vs all modern

**Example**:
- Existing: "Olivia" and "Sophia"
- Considering: "Ava" ✓ (similar style, popularity, length)
- Considering: "Bartholomew" ❌ (different style and length)

**Display**:
- ✓ "Matches your existing children's name style"
- ⚠️ "Different style than existing names - consider if intentional"

---

## 11. Personalized Recommendations
**What it shows**: Names ranked specifically for your situation
**Combines ALL factors above**
**Use case**: "Just show me the best options for MY family"

### Scoring Algorithm:
```
Total Score =
  Cultural Fit (25%) +
  Regional Appropriateness (20%) +
  Professional Perception (15%) +
  User Style Preferences (25%) +
  Family Harmony (10%) +
  Practical Factors (5%)
```

### User Profile Inputs:
1. **Demographics** (optional):
   - Ethnicity
   - Age

2. **Location**:
   - Current city/state
   - Planned future location

3. **Family Context**:
   - Partner's ethnicity
   - Existing children's names
   - Family surnames

4. **Preferences** (1-5 sliders):
   - Cultural importance: 1 (not important) → 5 (very important)
   - Uniqueness preference: 1 (want popular) → 5 (want unique)
   - Traditional vs Modern: 1 (traditional) → 5 (modern)
   - Pronunciation simplicity: 1 (simple) → 5 (complex ok)

5. **Risk Tolerance**:
   - ☑️ Avoid discrimination risk (uses hiring research)
   - ☑️ Religious significance important
   - ☑️ Must have nickname options

### Example Recommendation:
**User Profile**:
- Ethnicity: Hispanic
- Location: Miami, FL
- Existing child: "Sofia"
- Preferences: Unique (4/5), Traditional (2/5)
- Avoid discrimination: Yes

**Top Recommendation**: "Isla"
- Cultural Fit: 75% (moderately common in Hispanic community)
- Regional: #45 in Miami (unique but not weird)
- Professional: No research bias
- Sibling Harmony: 95% (similar style to "Sofia")
- Uniqueness: 72% (moderately unique)
- **Overall Score: 87/100**

---

## Ethical Considerations

### ⚠️ Sensitive Data - How We Handle It:

1. **Race/Ethnicity Data**:
   - Probabilistic only (never deterministic)
   - Clearly sourced and explained
   - Optional user input
   - Never used for exclusion
   - **Purpose**: Cultural matching, not categorization

2. **Hiring Discrimination Research**:
   - Fully attributed to academic sources
   - Presented as research findings, not predictions
   - Accompanied by context about industries, time periods
   - **Purpose**: Empowerment through information
   - **Not**: Prescriptive or limiting

3. **User Privacy**:
   - Profiles stored locally when possible
   - Optional account creation
   - Clear data usage policies
   - No selling of demographic data

4. **Disclaimers Throughout UI**:
   - "Data is informational, not deterministic"
   - "Your child's character and achievements matter most"
   - "Research shows trends, not individual outcomes"

---

## Feature Priority Implementation

### ✅ Phase 1 (COMPLETED):
- Database migrations with purpose documentation
- Data collection (ethnicity, nicknames)
- Feature descriptions table

### 🚧 Phase 2 (IN PROGRESS):
- Import scripts for ethnicity data
- Import scripts for nickname data
- User profile system

### 📋 Phase 3 (NEXT):
- UI for user profiles
- Enhanced comparison screen
- Personalized recommendations

### 🔮 Phase 4 (FUTURE):
- Machine learning on user preferences
- A/B testing recommendation quality
- Social features (share with partner)

---

## How Users Interact With Features

### Main Flow:
1. **Optional Onboarding**:
   - "Let's personalize your experience"
   - Fill out profile (5 minutes)
   - Can skip and browse without personalization

2. **Browse Names**:
   - See all basic info (meaning, origin)
   - + Ethnicity distribution
   - + Nickname options
   - + Uniqueness score

3. **Compare Names**:
   - Select 2-4 names
   - See side-by-side comparison
   - **NEW**: Cultural fit scores
   - **NEW**: Professional perception indicators
   - **NEW**: Feature comparison table (who "wins" each category)

4. **Get Recommendations**:
   - "Show me personalized suggestions"
   - Ranked list based on profile
   - Explanation of why each name was recommended

5. **Share & Decide**:
   - Share favorites with partner
   - Each person can have their own profile
   - Find names that score high for both

---

## Success Metrics

1. **Data Coverage**:
   - % of names with ethnicity data
   - % of names with nicknames
   - Avg features per name

2. **User Engagement**:
   - % users who create profiles
   - Time spent in compare mode
   - Names favorited per user

3. **Recommendation Quality**:
   - User satisfaction scores
   - Names chosen from recommendations
   - Feedback on accuracy

4. **Ethical Measures**:
   - Clear documentation understood
   - No misuse of sensitive data
   - User trust maintained

---

## Questions & Answers

**Q: Why show potentially uncomfortable data like hiring discrimination?**
A: Hiding bias doesn't eliminate it. Parents deserve research-based information to make informed decisions.

**Q: Isn't ethnicity data stereotyping?**
A: It's probabilistic population data showing naming patterns, not individual characteristics. Purpose is cultural matching for users who want it.

**Q: What if users game the system to avoid discrimination?**
A: That's their choice and right as parents. The app empowers; it doesn't judge.

**Q: How do you ensure data quality?**
A: All data is sourced from academic research or government datasets, with citations and confidence levels.

**Q: Can users opt out of sensitive features?**
A: Yes. Profile is optional, and all features have clear explanations and can be ignored.

---

This guide will be integrated into the UI as tooltips, help text, and an expanded help section.
