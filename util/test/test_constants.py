import pytest

from util.constants import GENESIS_BLOCK


@pytest.mark.asyncio
async def test_genesis_block_valid():
    assert await GENESIS_BLOCK.verify()
