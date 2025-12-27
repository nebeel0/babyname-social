from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, or_, func, Integer, Float
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.models.v1.prefix_tree import (
    PrefixTreeResponse,
    PrefixNodeRead,
    PrefixNamesResponse,
    GenderCounts,
    PopularityRange,
)
from core.models.v1.name import NameRead
from db.base import get_names_db
from db.models.name_prefix_tree import NamePrefixTree
from db.models.name import Name

router = APIRouter()


async def build_tree_hierarchy(
    nodes: list[NamePrefixTree],
    parent_id: Optional[int],
    max_depth: int,
    current_depth: int,
    include_names: bool,
    session: AsyncSession,
) -> list[PrefixNodeRead]:
    """Recursively build tree hierarchy from flat list of nodes."""
    if current_depth >= max_depth:
        return []

    result = []
    for node in nodes:
        if node.parent_id == parent_id:
            # Filter out null values from origin_countries before validation
            filtered_origins = None
            if node.origin_countries:
                filtered_origins = [c for c in node.origin_countries if c is not None]

            # Create dict and override origin_countries with filtered version
            node_dict = {
                'id': node.id,
                'prefix': node.prefix,
                'prefix_length': node.prefix_length,
                'is_complete_name': node.is_complete_name,
                'name_id': node.name_id,
                'parent_id': node.parent_id,
                'child_count': node.child_count,
                'total_descendants': node.total_descendants,
                'gender_counts': node.gender_counts,
                'origin_countries': filtered_origins,
                'popularity_range': node.popularity_range,
                'match_score': node.match_score,
                'is_highlighted': node.is_highlighted,
                'highlight_reason': node.highlight_reason,
            }

            node_data = PrefixNodeRead.model_validate(node_dict)

            # Load name if this is a complete name and requested
            if include_names and node.is_complete_name and node.name_id:
                name_result = await session.execute(
                    select(Name).where(Name.id == node.name_id)
                )
                name = name_result.scalar_one_or_none()
                if name:
                    node_data.name = NameRead.model_validate(name)

            # Recursively load children
            if current_depth < max_depth - 1:
                node_data.children = await build_tree_hierarchy(
                    nodes, node.id, max_depth, current_depth + 1, include_names, session
                )

            result.append(node_data)

    return result


@router.get("/tree", response_model=PrefixTreeResponse)
async def get_prefix_tree(
    prefix: str = Query("", description="Prefix to start from"),
    max_depth: int = Query(3, ge=1, le=10, description="Maximum tree depth"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    origin_country: Optional[str] = Query(None, description="Filter by origin"),
    min_popularity: Optional[float] = Query(None, description="Minimum popularity"),
    max_popularity: Optional[float] = Query(None, description="Maximum popularity"),
    highlight_prefixes: str = Query("", description="Comma-separated prefixes to highlight"),
    highlight_name_ids: str = Query("", description="Comma-separated name IDs to highlight"),
    include_names: bool = Query(False, description="Include full name objects"),
    session: AsyncSession = Depends(get_names_db),
):
    """
    Get prefix tree with optional filtering and highlighting.

    Supports:
    - Filtering by gender, origin, and popularity range
    - Highlighting specific prefixes or names
    - Configurable depth
    - Optional name details
    """
    # Parse highlight parameters
    highlight_prefix_list = [p.strip() for p in highlight_prefixes.split(",") if p.strip()]
    highlight_id_list = [int(id.strip()) for id in highlight_name_ids.split(",") if id.strip()]

    # Build query
    query = select(NamePrefixTree).where(
        NamePrefixTree.prefix.like(f"{prefix}%")
    ).where(
        NamePrefixTree.prefix_length <= len(prefix) + max_depth
    )

    # Apply gender filter
    if gender:
        # Filter nodes where ONLY the specified gender exists (all other genders are 0)
        # This ensures we only show prefixes with exclusively male/female/unisex/neutral names
        other_genders = [g for g in ["male", "female", "unisex", "neutral"] if g != gender]

        # The selected gender must have at least one name
        query = query.where(
            func.cast(NamePrefixTree.gender_counts[gender], Integer) > 0
        )

        # All other genders must have zero names
        for other_gender in other_genders:
            query = query.where(
                func.coalesce(func.cast(NamePrefixTree.gender_counts[other_gender], Integer), 0) == 0
            )

    # Apply origin filter
    if origin_country:
        query = query.where(
            NamePrefixTree.origin_countries.contains([origin_country])
        )

    # Apply popularity filters
    if min_popularity is not None:
        query = query.where(
            func.cast(NamePrefixTree.popularity_range["max"], Float) >= min_popularity
        )

    if max_popularity is not None:
        query = query.where(
            func.cast(NamePrefixTree.popularity_range["min"], Float) <= max_popularity
        )

    # Execute query
    result = await session.execute(query.order_by(NamePrefixTree.prefix))
    nodes = list(result.scalars().all())

    if not nodes:
        return PrefixTreeResponse(
            prefix=prefix,
            total_nodes=0,
            total_names=0,
            max_depth=max_depth,
            filters_applied={
                "gender": gender,
                "origin_country": origin_country,
                "min_popularity": min_popularity,
                "max_popularity": max_popularity,
            },
            nodes=[],
        )

    # Apply highlighting
    for node in nodes:
        if node.prefix in highlight_prefix_list:
            node.is_highlighted = True
            node.highlight_reason = "prefix_match"
        elif node.name_id in highlight_id_list:
            node.is_highlighted = True
            node.highlight_reason = "name_selected"

    # Find root nodes (nodes that start with the prefix and have appropriate depth)
    root_nodes = [
        n for n in nodes
        if n.prefix_length == len(prefix) + 1 or (len(prefix) == 0 and n.prefix_length == 1)
    ]

    # Build hierarchy
    tree_nodes = await build_tree_hierarchy(
        nodes, None, max_depth, 0, include_names, session
    )

    # Count complete names
    total_names = sum(1 for n in nodes if n.is_complete_name)

    return PrefixTreeResponse(
        prefix=prefix,
        total_nodes=len(nodes),
        total_names=total_names,
        max_depth=max_depth,
        filters_applied={
            "gender": gender,
            "origin_country": origin_country,
            "min_popularity": min_popularity,
            "max_popularity": max_popularity,
        },
        nodes=tree_nodes,
    )


@router.get("/tree/names/{prefix}", response_model=PrefixNamesResponse)
async def get_prefix_names(
    prefix: str,
    limit: int = Query(100, ge=1, le=1000),
    gender: Optional[str] = Query(None),
    origin_country: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_names_db),
):
    """
    Get all complete names matching a prefix with statistics.

    Returns the full list of names along with:
    - Gender distribution
    - Top origins
    - Popularity statistics
    """
    # Get the prefix node for statistics
    prefix_result = await session.execute(
        select(NamePrefixTree).where(NamePrefixTree.prefix == prefix)
    )
    prefix_node = prefix_result.scalar_one_or_none()

    if not prefix_node:
        raise HTTPException(status_code=404, detail="Prefix not found")

    # Build query for names
    name_query = (
        select(Name)
        .join(NamePrefixTree, NamePrefixTree.name_id == Name.id)
        .where(NamePrefixTree.prefix.like(f"{prefix}%"))
        .where(NamePrefixTree.is_complete_name == True)
    )

    # Apply filters
    if gender:
        name_query = name_query.where(Name.gender == gender)

    if origin_country:
        name_query = name_query.where(Name.origin_country == origin_country)

    name_query = name_query.limit(limit)

    # Execute query
    names_result = await session.execute(name_query)
    names = list(names_result.scalars().all())

    # Calculate statistics
    gender_counts = GenderCounts(
        male=prefix_node.gender_counts.get("male", 0),
        female=prefix_node.gender_counts.get("female", 0),
        unisex=prefix_node.gender_counts.get("unisex", 0),
        neutral=prefix_node.gender_counts.get("neutral", 0),
    )

    popularity_stats = PopularityRange(
        min=prefix_node.popularity_range.get("min", 0.0),
        max=prefix_node.popularity_range.get("max", 0.0),
        avg=prefix_node.popularity_range.get("avg", 0.0),
    )

    # Get top origins (first 5, filter out nulls)
    top_origins = [c for c in (prefix_node.origin_countries or []) if c is not None][:5]

    return PrefixNamesResponse(
        prefix=prefix,
        total_count=prefix_node.total_descendants,
        names=[NameRead.model_validate(name) for name in names],
        gender_distribution=gender_counts,
        top_origins=top_origins,
        popularity_stats=popularity_stats,
    )


@router.post("/tree/rebuild")
async def rebuild_prefix_tree(
    session: AsyncSession = Depends(get_names_db),
):
    """
    Rebuild the entire prefix tree from current names.
    This is an admin operation that should be used when:
    - New names are added in bulk
    - The tree becomes inconsistent
    - Manual maintenance is needed
    """
    try:
        # Call the database function to rebuild the tree
        await session.execute(func.build_prefix_tree())
        await session.commit()

        # Get count of nodes
        count_result = await session.execute(
            select(func.count()).select_from(NamePrefixTree)
        )
        total_nodes = count_result.scalar()

        return {
            "status": "success",
            "message": "Prefix tree rebuilt successfully",
            "total_nodes": total_nodes,
        }
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rebuild prefix tree: {str(e)}"
        )


@router.get("/tree/search")
async def search_prefix_tree(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_names_db),
):
    """
    Search for prefixes and names matching a query.
    Returns both prefix nodes and complete names.
    """
    # Search prefix nodes
    prefix_result = await session.execute(
        select(NamePrefixTree)
        .where(NamePrefixTree.prefix.ilike(f"{query}%"))
        .limit(limit)
        .order_by(NamePrefixTree.prefix_length, NamePrefixTree.prefix)
    )
    prefix_nodes = list(prefix_result.scalars().all())

    # Separate complete names and intermediate nodes
    complete_names = []
    intermediate_nodes = []

    for node in prefix_nodes:
        # Filter out null values from origin_countries before validation
        filtered_origins = None
        if node.origin_countries:
            filtered_origins = [c for c in node.origin_countries if c is not None]

        # Create dict and override origin_countries with filtered version
        node_dict = {
            'id': node.id,
            'prefix': node.prefix,
            'prefix_length': node.prefix_length,
            'is_complete_name': node.is_complete_name,
            'name_id': node.name_id,
            'parent_id': node.parent_id,
            'child_count': node.child_count,
            'total_descendants': node.total_descendants,
            'gender_counts': node.gender_counts,
            'origin_countries': filtered_origins,
            'popularity_range': node.popularity_range,
            'match_score': node.match_score,
            'is_highlighted': node.is_highlighted,
            'highlight_reason': node.highlight_reason,
        }

        node_read = PrefixNodeRead.model_validate(node_dict)

        if node.is_complete_name and node.name_id:
            # Load the name
            name_result = await session.execute(
                select(Name).where(Name.id == node.name_id)
            )
            name = name_result.scalar_one_or_none()
            if name:
                node_read.name = NameRead.model_validate(name)
                complete_names.append(node_read)
        else:
            intermediate_nodes.append(node_read)

    return {
        "query": query,
        "complete_names": complete_names,
        "intermediate_nodes": intermediate_nodes,
        "total_results": len(prefix_nodes),
    }
