"""API endpoints for enhanced name data (ethnicity, nicknames, etc.)"""
from fastapi import APIRouter, Depends, HTTPException, Query
import asyncpg
from typing import Optional

from core.models.v1.name_enhancement import (
    EthnicityProbability,
    NicknameInfo,
    NameWithEnhancements,
    CulturalFitScore,
    FeatureDescription
)
from db.base import get_names_db_raw

router = APIRouter()


@router.get("/ethnicity/{name_id}", response_model=EthnicityProbability | None)
async def get_ethnicity_data(
    name_id: int,
    conn: asyncpg.Connection = Depends(get_names_db_raw),
):
    """Get ethnicity probability distribution for a name"""
    result = await conn.fetchrow(
        "SELECT * FROM name_ethnicity_probabilities WHERE name_id = $1",
        name_id
    )

    if not result:
        return None

    return dict(result)


@router.get("/nicknames/{name_id}", response_model=list[NicknameInfo])
async def get_nicknames(
    name_id: int,
    conn: asyncpg.Connection = Depends(get_names_db_raw),
):
    """Get all nicknames for a name"""
    results = await conn.fetch(
        """
        SELECT nickname, is_diminutive, popularity_rank
        FROM name_nicknames
        WHERE name_id = $1
        ORDER BY popularity_rank NULLS LAST
        """,
        name_id
    )

    return [dict(row) for row in results]


@router.get("/enhanced/{name_id}", response_model=NameWithEnhancements)
async def get_enhanced_name(
    name_id: int,
    conn: asyncpg.Connection = Depends(get_names_db_raw),
):
    """Get name with all enhancements (ethnicity, nicknames, etc.)"""
    # Get base name data
    name_result = await conn.fetchrow(
        """
        SELECT id, name, gender, origin_country, meaning,
               has_ethnicity_data, has_nicknames, has_perception_data, nickname_count
        FROM names
        WHERE id = $1
        """,
        name_id
    )

    if not name_result:
        raise HTTPException(status_code=404, detail="Name not found")

    name_data = dict(name_result)

    # Get ethnicity data if available
    ethnicity_data = None
    if name_data['has_ethnicity_data']:
        eth_result = await conn.fetchrow(
            "SELECT * FROM name_ethnicity_probabilities WHERE name_id = $1",
            name_id
        )
        if eth_result:
            ethnicity_data = dict(eth_result)

    # Get nicknames if available
    nicknames = []
    if name_data['has_nicknames']:
        nick_results = await conn.fetch(
            """
            SELECT nickname, is_diminutive, popularity_rank
            FROM name_nicknames
            WHERE name_id = $1
            ORDER BY popularity_rank NULLS LAST
            """,
            name_id
        )
        nicknames = [dict(row) for row in nick_results]

    return {
        **name_data,
        'ethnicity_data': ethnicity_data,
        'nicknames': nicknames,
    }


@router.get("/cultural-fit/{name_id}")
async def get_cultural_fit(
    name_id: int,
    user_ethnicity: str = Query(..., description="User's ethnicity: white, black, hispanic, asian, or other"),
    conn: asyncpg.Connection = Depends(get_names_db_raw),
):
    """Calculate cultural fit score for a name given user's ethnicity"""
    # Get name and ethnicity data
    result = await conn.fetchrow(
        """
        SELECT n.name, e.*
        FROM names n
        LEFT JOIN name_ethnicity_probabilities e ON n.id = e.name_id
        WHERE n.id = $1
        """,
        name_id
    )

    if not result:
        raise HTTPException(status_code=404, detail="Name not found")

    if not result['white_probability']:
        # No ethnicity data available
        return {
            "name_id": name_id,
            "name": result['name'],
            "user_ethnicity": user_ethnicity,
            "fit_score": None,
            "match_probability": None,
            "error": "No ethnicity data available for this name"
        }

    # Map user ethnicity to database column
    ethnicity_map = {
        'white': float(result['white_probability']),
        'black': float(result['black_probability']),
        'hispanic': float(result['hispanic_probability']),
        'asian': float(result['asian_probability']),
        'other': float(result['other_probability']),
    }

    user_eth_lower = user_ethnicity.lower()
    if user_eth_lower not in ethnicity_map:
        raise HTTPException(
            status_code=400,
            detail="Invalid ethnicity. Must be one of: white, black, hispanic, asian, other"
        )

    match_probability = ethnicity_map[user_eth_lower]
    fit_score = match_probability * 100  # Convert to percentage

    return {
        "name_id": name_id,
        "name": result['name'],
        "user_ethnicity": user_ethnicity,
        "fit_score": round(fit_score, 1),
        "match_probability": match_probability,
        "white_probability": ethnicity_map['white'],
        "black_probability": ethnicity_map['black'],
        "hispanic_probability": ethnicity_map['hispanic'],
        "asian_probability": ethnicity_map['asian'],
        "other_probability": ethnicity_map['other'],
    }


@router.get("/features", response_model=list[FeatureDescription])
async def get_feature_descriptions(
    conn: asyncpg.Connection = Depends(get_names_db_raw),
):
    """Get all feature descriptions for tooltips and help text"""
    results = await conn.fetch(
        """
        SELECT feature_key, display_name, short_description, detailed_explanation,
               data_source, display_order
        FROM feature_descriptions
        ORDER BY display_order
        """
    )

    return [dict(row) for row in results]


@router.get("/features/{feature_key}", response_model=FeatureDescription)
async def get_feature_description(
    feature_key: str,
    conn: asyncpg.Connection = Depends(get_names_db_raw),
):
    """Get a specific feature description"""
    result = await conn.fetchrow(
        """
        SELECT feature_key, display_name, short_description, detailed_explanation,
               data_source, display_order
        FROM feature_descriptions
        WHERE feature_key = $1
        """,
        feature_key
    )

    if not result:
        raise HTTPException(status_code=404, detail="Feature description not found")

    return dict(result)
