from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, case
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.v1.name import NameCreate, NameRead, NameUpdate
from db.base import get_names_db
from db.models.name import Name

router = APIRouter()


@router.get("/", response_model=list[NameRead])
async def get_names(
    skip: int = 0,
    limit: int = 10000,
    session: AsyncSession = Depends(get_names_db),
):
    """Get list of names with pagination."""
    # Filter out names with null or empty name values
    result = await session.execute(
        select(Name)
        .where(Name.name.isnot(None))
        .where(Name.name != '')
        .offset(skip)
        .limit(limit)
    )
    names = result.scalars().all()
    return names


@router.get("/{name_id}", response_model=NameRead)
async def get_name(
    name_id: int,
    session: AsyncSession = Depends(get_names_db),
):
    """Get a specific name by ID."""
    result = await session.execute(select(Name).where(Name.id == name_id))
    name = result.scalar_one_or_none()

    if not name:
        raise HTTPException(status_code=404, detail="Name not found")

    return name


@router.post("/", response_model=NameRead, status_code=201)
async def create_name(
    name_data: NameCreate,
    session: AsyncSession = Depends(get_names_db),
):
    """Create a new name entry."""
    # Check if name already exists
    result = await session.execute(select(Name).where(Name.name == name_data.name))
    existing_name = result.scalar_one_or_none()

    if existing_name:
        raise HTTPException(status_code=400, detail="Name already exists")

    # Create new name
    name = Name(**name_data.model_dump())
    session.add(name)
    await session.commit()
    await session.refresh(name)

    return name


@router.get("/search/{query}", response_model=list[NameRead])
async def search_names(
    query: str,
    limit: int = 20,
    session: AsyncSession = Depends(get_names_db),
):
    """Search names by partial match with relevance ordering."""
    # Create case statement for ordering:
    # 1 = exact match (highest priority)
    # 2 = starts with query
    # 3 = contains query
    relevance_order = case(
        (Name.name.ilike(query), 1),
        (Name.name.ilike(f"{query}%"), 2),
        else_=3
    )

    result = await session.execute(
        select(Name)
        .where(Name.name.ilike(f"%{query}%"))
        .order_by(relevance_order, Name.name)
        .limit(limit)
    )
    names = result.scalars().all()
    return names


@router.put("/{name_id}", response_model=NameRead)
async def update_name(
    name_id: int,
    name_data: NameUpdate,
    session: AsyncSession = Depends(get_names_db),
):
    """Update an existing name."""
    result = await session.execute(select(Name).where(Name.id == name_id))
    name = result.scalar_one_or_none()

    if not name:
        raise HTTPException(status_code=404, detail="Name not found")

    # Update fields
    update_data = name_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(name, field, value)

    await session.commit()
    await session.refresh(name)

    return name


@router.delete("/{name_id}", status_code=204)
async def delete_name(
    name_id: int,
    session: AsyncSession = Depends(get_names_db),
):
    """Delete a name."""
    result = await session.execute(select(Name).where(Name.id == name_id))
    name = result.scalar_one_or_none()

    if not name:
        raise HTTPException(status_code=404, detail="Name not found")

    await session.delete(name)
    await session.commit()

    return None
