"""API endpoints for name enrichment data (trends, famous people, trivia)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel

from db.base import get_names_db

router = APIRouter()


# Pydantic models for responses
class PopularityTrend(BaseModel):
    year: int
    rank: int | None
    count: int | None
    gender: str

    class Config:
        from_attributes = True


class FamousNamesake(BaseModel):
    id: int
    full_name: str
    category: str | None
    description: str | None
    profession: str | None
    birth_year: int | None
    death_year: int | None
    notable_for: str | None
    image_url: str | None
    wikipedia_url: str | None

    class Config:
        from_attributes = True


class NameTrivia(BaseModel):
    id: int
    trivia_type: str | None
    content: str
    source: str | None

    class Config:
        from_attributes = True


class RelatedName(BaseModel):
    id: int
    name: str
    relationship_type: str
    gender: str | None
    meaning: str | None

    class Config:
        from_attributes = True


@router.get("/{name_id}/trends", response_model=List[PopularityTrend])
async def get_popularity_trends(
    name_id: int,
    session: AsyncSession = Depends(get_names_db),
):
    """Get popularity trends for a specific name."""
    result = await session.execute(
        text("""
            SELECT year, rank, count, gender
            FROM popularity_trends
            WHERE name_id = :name_id
            ORDER BY year ASC
        """),
        {"name_id": name_id}
    )

    trends = []
    for row in result:
        trends.append({
            "year": row.year,
            "rank": row.rank,
            "count": row.count,
            "gender": row.gender,
        })

    return trends


@router.get("/{name_id}/famous-people", response_model=List[FamousNamesake])
async def get_famous_people(
    name_id: int,
    limit: int = 10,
    session: AsyncSession = Depends(get_names_db),
):
    """Get famous people with this name."""
    result = await session.execute(
        text("""
            SELECT id, full_name, category, description, profession,
                   birth_year, death_year, notable_for, image_url, wikipedia_url
            FROM famous_namesakes
            WHERE name_id = :name_id
            ORDER BY birth_year DESC NULLS LAST
            LIMIT :limit
        """),
        {"name_id": name_id, "limit": limit}
    )

    people = []
    for row in result:
        people.append({
            "id": row.id,
            "full_name": row.full_name,
            "category": row.category,
            "description": row.description,
            "profession": row.profession,
            "birth_year": row.birth_year,
            "death_year": row.death_year,
            "notable_for": row.notable_for,
            "image_url": row.image_url,
            "wikipedia_url": row.wikipedia_url,
        })

    return people


@router.get("/{name_id}/trivia", response_model=List[NameTrivia])
async def get_name_trivia(
    name_id: int,
    session: AsyncSession = Depends(get_names_db),
):
    """Get trivia/fun facts about a name."""
    result = await session.execute(
        text("""
            SELECT id, trivia_type, content, source
            FROM name_trivia
            WHERE name_id = :name_id
            ORDER BY id DESC
        """),
        {"name_id": name_id}
    )

    trivia_list = []
    for row in result:
        trivia_list.append({
            "id": row.id,
            "trivia_type": row.trivia_type,
            "content": row.content,
            "source": row.source,
        })

    return trivia_list


@router.get("/{name_id}/related", response_model=List[RelatedName])
async def get_related_names(
    name_id: int,
    session: AsyncSession = Depends(get_names_db),
):
    """Get related/similar names (variants, diminutives, etc.)."""
    result = await session.execute(
        text("""
            SELECT n.id, n.name, rn.relationship_type, n.gender, n.meaning
            FROM related_names rn
            JOIN names n ON n.id = rn.related_name_id
            WHERE rn.name_id = :name_id
            ORDER BY rn.relationship_type, n.name
        """),
        {"name_id": name_id}
    )

    related_list = []
    for row in result:
        related_list.append({
            "id": row.id,
            "name": row.name,
            "relationship_type": row.relationship_type,
            "gender": row.gender,
            "meaning": row.meaning,
        })

    return related_list


@router.get("/stats/overview")
async def get_enrichment_stats(
    session: AsyncSession = Depends(get_names_db),
):
    """Get overall enrichment statistics."""
    result = await session.execute(text("""
        SELECT
            COUNT(DISTINCT name_id) FILTER (WHERE has_trends = TRUE) as names_with_trends,
            COUNT(DISTINCT name_id) FILTER (WHERE has_famous_people = TRUE) as names_with_famous,
            (SELECT COUNT(*) FROM popularity_trends) as total_trends,
            (SELECT COUNT(*) FROM famous_namesakes) as total_famous_people,
            (SELECT COUNT(*) FROM name_trivia) as total_trivia
        FROM names
    """))

    row = result.first()
    return {
        "names_with_trends": row.names_with_trends or 0,
        "names_with_famous_people": row.names_with_famous or 0,
        "total_trend_records": row.total_trends or 0,
        "total_famous_people": row.total_famous_people or 0,
        "total_trivia": row.total_trivia or 0,
    }
