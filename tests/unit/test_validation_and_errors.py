import pytest

from core.exceptions import InvalidUsernameError, ScanTimeoutError
from modules.username_search.scanner import scan_username


@pytest.mark.asyncio
async def test_invalid_username_raises_exception():
    with pytest.raises(InvalidUsernameError):
        await scan_username("user with spaces!")

    with pytest.raises(InvalidUsernameError):
        await scan_username("")

    with pytest.raises(InvalidUsernameError):
        await scan_username("a" * 65)


@pytest.mark.asyncio
async def test_invalid_concurrency_raises_value_error():
    with pytest.raises(ValueError):
        await scan_username("valid_user", concurrency=0)

    with pytest.raises(ValueError):
        await scan_username("valid_user", concurrency=25)
