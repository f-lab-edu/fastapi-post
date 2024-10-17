from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domains.post import Post
from src.domains.user import User
from src.servicies.post import PostService


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.exec = AsyncMock()

    @asynccontextmanager
    async def session_factory(key=None):
        yield session

    return session_factory


@pytest.fixture
def post_service(mock_session):
    return PostService(session_factory=mock_session)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_post(mocker, post_service: PostService) -> None:
    # Given
    mocker.patch("src.domains.comment.Comment")
    user_id = 1
    title = "테스트 제목"
    content = "테스트 내용"

    # When
    result = await post_service.create_post(user_id, title, content)

    # Then
    assert isinstance(result, Post)
    assert result.author_id == 1
    assert result.title == "테스트 제목"
    assert result.content == "테스트 내용"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_posts(mock_session: AsyncMock, post_service: PostService) -> None:
    # Given
    mock_posts = [
        Post(
            id=1,
            title="테스트 제목 1",
            content="테스트 내용 1",
            user=User(id=1, nickname="테스트 닉네임1"),
        ),
        Post(
            id=2,
            title="테스트 제목 2",
            content="테스트 내용 2",
            user=User(id=1, nickname="테스트 닉네임1"),
        ),
        Post(
            id=3,
            title="테스트 제목 3",
            content="테스트 내용 3",
            user=User(id=1, nickname="테스트 닉네임1"),
        ),
    ]
    mock_result = MagicMock()
    mock_result.all.return_value = mock_posts

    async with mock_session() as session:
        session.exec.return_value = mock_result

        # When
        result = await post_service.get_posts(page=1)

    # Then
    assert isinstance(result[0], Post)
    assert len(result) == 3
    assert result[0].title == "테스트 제목 1"
    assert result[0].content == "테스트 내용 1"
    assert isinstance(result[0].user, User)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_post(mock_session: AsyncMock, post_service: PostService) -> None:
    # Given
    mock_post = Post(
        id=1,
        title="테스트 제목 1",
        content="테스트 내용 1",
        user=User(id=1, nickname="테스트 닉네임1"),
    )

    mock_result = MagicMock()
    mock_result.first.return_value = mock_post

    async with mock_session() as session:
        session.exec.return_value = mock_result

        # When
        result = await post_service.get_post(post_id=1)

    # Then
    assert isinstance(result, Post)
    assert result.title == "테스트 제목 1"
    assert result.content == "테스트 내용 1"
    assert isinstance(result.user, User)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_edit_post(mock_session: AsyncMock, post_service: PostService) -> None:
    # Given
    mock_post = Post(id=1, title="테스트 제목 1", content="테스트 내용 1")

    # When
    result = await post_service.edit_post(  # type: ignore
        post=mock_post, title="edit_title", content="edit_content"
    )

    # Then
    assert result is None
    assert mock_post.title == "edit_title"
    assert mock_post.content == "edit_content"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_delete_post(mock_session: AsyncMock, post_service: PostService) -> None:
    # Given
    mock_post = Post(id=1, title="테스트 제목 1", content="테스트 내용 1")

    # When
    result = await post_service.delete_post(post=mock_post)  # type: ignore

    # Then
    assert result is None
