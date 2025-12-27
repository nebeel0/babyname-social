"""Unit tests for prefix tree helper functions."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.api.v1.endpoints.prefix_tree import build_tree_hierarchy
from core.models.v1.prefix_tree import PrefixNodeRead
from db.models.name_prefix_tree import NamePrefixTree


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = AsyncMock()
    return session


@pytest.fixture
def sample_nodes():
    """Create sample prefix tree nodes for testing."""
    # Create a simple tree: A -> AB -> ABC
    #                           -> ABD
    node_a = NamePrefixTree(
        id=1,
        prefix="A",
        prefix_length=1,
        is_complete_name=False,
        name_id=None,
        parent_id=None,
        child_count=1,
        total_descendants=3,
        gender_counts={"male": 2, "female": 1},
        origin_countries=["USA", "UK"],
        popularity_range={"min": 0.5, "max": 0.9, "avg": 0.7},
        match_score=0.0,
        is_highlighted=False,
        highlight_reason=None,
    )

    node_ab = NamePrefixTree(
        id=2,
        prefix="AB",
        prefix_length=2,
        is_complete_name=False,
        name_id=None,
        parent_id=1,
        child_count=2,
        total_descendants=2,
        gender_counts={"male": 1, "female": 1},
        origin_countries=["USA"],
        popularity_range={"min": 0.6, "max": 0.8, "avg": 0.7},
        match_score=0.0,
        is_highlighted=False,
        highlight_reason=None,
    )

    node_abc = NamePrefixTree(
        id=3,
        prefix="ABC",
        prefix_length=3,
        is_complete_name=True,
        name_id=101,
        parent_id=2,
        child_count=0,
        total_descendants=0,
        gender_counts={"male": 1},
        origin_countries=["USA"],
        popularity_range={"min": 0.6, "max": 0.6, "avg": 0.6},
        match_score=0.0,
        is_highlighted=False,
        highlight_reason=None,
    )

    node_abd = NamePrefixTree(
        id=4,
        prefix="ABD",
        prefix_length=3,
        is_complete_name=True,
        name_id=102,
        parent_id=2,
        child_count=0,
        total_descendants=0,
        gender_counts={"female": 1},
        origin_countries=["UK"],
        popularity_range={"min": 0.8, "max": 0.8, "avg": 0.8},
        match_score=0.0,
        is_highlighted=False,
        highlight_reason=None,
    )

    return [node_a, node_ab, node_abc, node_abd]


@pytest.mark.asyncio
async def test_build_tree_hierarchy_basic(mock_session, sample_nodes):
    """Test basic tree building with valid nodes."""
    result = await build_tree_hierarchy(
        nodes=sample_nodes,
        parent_id=None,
        max_depth=3,
        current_depth=0,
        include_names=False,
        session=mock_session,
    )

    # Should return root node (A)
    assert len(result) == 1
    assert result[0].prefix == "A"
    assert result[0].child_count == 1

    # Check that children are loaded
    assert len(result[0].children) == 1
    assert result[0].children[0].prefix == "AB"

    # Check grandchildren
    assert len(result[0].children[0].children) == 2
    grandchild_prefixes = {child.prefix for child in result[0].children[0].children}
    assert grandchild_prefixes == {"ABC", "ABD"}


@pytest.mark.asyncio
async def test_build_tree_hierarchy_max_depth_limit(mock_session, sample_nodes):
    """Test that max_depth parameter limits tree depth."""
    result = await build_tree_hierarchy(
        nodes=sample_nodes,
        parent_id=None,
        max_depth=2,
        current_depth=0,
        include_names=False,
        session=mock_session,
    )

    # Should return root node
    assert len(result) == 1
    assert result[0].prefix == "A"

    # Should have one child (AB)
    assert len(result[0].children) == 1
    assert result[0].children[0].prefix == "AB"

    # AB should have NO children due to max_depth=2
    # When max_depth is reached, children field is not set (None or empty list)
    assert result[0].children[0].children is None or len(result[0].children[0].children) == 0


@pytest.mark.asyncio
async def test_build_tree_hierarchy_filters_null_origins(mock_session):
    """Test that null values are filtered from origin_countries."""
    node = NamePrefixTree(
        id=1,
        prefix="A",
        prefix_length=1,
        is_complete_name=False,
        name_id=None,
        parent_id=None,
        child_count=0,
        total_descendants=0,
        gender_counts={},
        origin_countries=["USA", None, "UK", None],  # Has nulls
        popularity_range={},
        match_score=0.0,
        is_highlighted=False,
        highlight_reason=None,
    )

    result = await build_tree_hierarchy(
        nodes=[node],
        parent_id=None,
        max_depth=1,
        current_depth=0,
        include_names=False,
        session=mock_session,
    )

    assert len(result) == 1
    assert result[0].origin_countries == ["USA", "UK"]
    assert None not in result[0].origin_countries


@pytest.mark.asyncio
async def test_build_tree_hierarchy_empty_nodes(mock_session):
    """Test building tree with empty node list."""
    result = await build_tree_hierarchy(
        nodes=[],
        parent_id=None,
        max_depth=3,
        current_depth=0,
        include_names=False,
        session=mock_session,
    )

    assert result == []


@pytest.mark.asyncio
async def test_build_tree_hierarchy_no_matching_parent(mock_session, sample_nodes):
    """Test building tree with non-matching parent_id."""
    result = await build_tree_hierarchy(
        nodes=sample_nodes,
        parent_id=999,  # Non-existent parent
        max_depth=3,
        current_depth=0,
        include_names=False,
        session=mock_session,
    )

    assert result == []


@pytest.mark.asyncio
async def test_build_tree_hierarchy_with_names(mock_session):
    """Test that complete names are loaded when include_names=True."""
    from db.models.name import Name

    node = NamePrefixTree(
        id=1,
        prefix="Alice",
        prefix_length=5,
        is_complete_name=True,
        name_id=101,
        parent_id=None,
        child_count=0,
        total_descendants=0,
        gender_counts={"female": 1},
        origin_countries=["UK"],
        popularity_range={"min": 0.9, "max": 0.9, "avg": 0.9},
        match_score=0.0,
        is_highlighted=False,
        highlight_reason=None,
    )

    # Mock the name query
    from datetime import datetime
    mock_name = Name(
        id=101,
        name="Alice",
        gender="female",
        origin_country="UK",
        avg_rating=4.5,
        rating_count=10,
        created_at=datetime.now(),
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_name
    mock_session.execute.return_value = mock_result

    result = await build_tree_hierarchy(
        nodes=[node],
        parent_id=None,
        max_depth=1,
        current_depth=0,
        include_names=True,
        session=mock_session,
    )

    assert len(result) == 1
    assert result[0].name is not None
    assert result[0].name.name == "Alice"
    assert result[0].name.gender == "female"
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_build_tree_hierarchy_at_max_depth(mock_session, sample_nodes):
    """Test that no nodes are returned when starting at max_depth."""
    result = await build_tree_hierarchy(
        nodes=sample_nodes,
        parent_id=None,
        max_depth=3,
        current_depth=3,  # Already at max depth
        include_names=False,
        session=mock_session,
    )

    assert result == []


@pytest.mark.asyncio
async def test_build_tree_hierarchy_preserves_all_fields(mock_session):
    """Test that all node fields are correctly preserved in the result."""
    node = NamePrefixTree(
        id=42,
        prefix="Test",
        prefix_length=4,
        is_complete_name=True,
        name_id=123,
        parent_id=None,
        child_count=5,
        total_descendants=10,
        gender_counts={"male": 3, "female": 7},
        origin_countries=["France", "Germany"],
        popularity_range={"min": 0.2, "max": 0.8, "avg": 0.5},
        match_score=0.95,
        is_highlighted=True,
        highlight_reason="test_reason",
    )

    result = await build_tree_hierarchy(
        nodes=[node],
        parent_id=None,
        max_depth=1,
        current_depth=0,
        include_names=False,
        session=mock_session,
    )

    assert len(result) == 1
    r = result[0]
    assert r.id == 42
    assert r.prefix == "Test"
    assert r.prefix_length == 4
    assert r.is_complete_name is True
    assert r.name_id == 123
    assert r.parent_id is None
    assert r.child_count == 5
    assert r.total_descendants == 10
    assert r.gender_counts == {"male": 3, "female": 7}
    assert r.origin_countries == ["France", "Germany"]
    assert r.popularity_range == {"min": 0.2, "max": 0.8, "avg": 0.5}
    assert r.match_score == 0.95
    assert r.is_highlighted is True
    assert r.highlight_reason == "test_reason"
