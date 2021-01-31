import pytest

from models.blocks import OpenBlock
from network.block_handler import BlockHandler
from storage.in_memory import InMemoryStorage
from util.crypto import sign
from util.numbers import deterministic_key
from storage.storage import Storage

work = bytes.fromhex("591bcb21af41d3bf")[::-1]
seed = bytes(32)
priv, pub = deterministic_key(seed, 0)
b = OpenBlock(bytes(32), bytes(32), pub, bytes(64), work)
b.signature = bytes(64)


@pytest.fixture
def storage():
    return InMemoryStorage()


@pytest.fixture
def open_block():
    work = bytes.fromhex("591bcb21af41d3bf")[::-1]
    seed = bytes(32)
    priv, pub = deterministic_key(seed, 0)
    b = OpenBlock(bytes(32), bytes(32), pub, bytes(64), work)
    sig = sign(b.hash_sync(), priv)
    b.signature = sig
    return b


@pytest.fixture
def open_block_without_pow(open_block):
    open_block.work = bytes(8)
    return open_block


@pytest.fixture
def open_block_without_sig(open_block):
    open_block.signature = bytes(64)
    return open_block


@pytest.mark.asyncio
async def test_block_handler_rejects_invalid_pow(storage, open_block_without_pow):
    block_handler = BlockHandler(storage)

    await block_handler.start()
    await block_handler.handle_block(open_block_without_pow)
    await block_handler.stop()

    assert block_handler.invalid_pow_count == 1
    assert block_handler.invalid_signature_count == 0


@pytest.mark.asyncio
async def test_block_handler_rejects_invalid_signature(storage, open_block_without_sig):
    block_handler = BlockHandler(storage)
    storage.put(open_block_without_sig.source, b"123")

    await block_handler.start()
    await block_handler.handle_block(open_block_without_sig)
    await block_handler.stop()

    assert block_handler.invalid_pow_count == 0
    assert block_handler.invalid_signature_count == 1


@pytest.mark.asyncio
async def test_block_handler_queues_block_with_missing_dep(storage, open_block):
    block_handler = BlockHandler(storage)

    await block_handler.start()
    await block_handler.handle_block(open_block)
    await block_handler.stop()

    assert block_handler.invalid_pow_count == 0
    assert block_handler.invalid_signature_count == 0
    assert block_handler.storage_queue.qsize() == 0
    # TODO: Check that block is put into "dependency watcher"


@pytest.mark.asyncio
async def test_block_handler_accepts_valid_pow_and_signature(
    storage: Storage, open_block: OpenBlock
):
    block_handler = BlockHandler(storage)

    for dep in open_block.dependencies():
        storage.put(dep, b"")

    await block_handler.start()
    await block_handler.handle_block(open_block)
    await block_handler.stop()

    assert block_handler.invalid_pow_count == 0
    assert block_handler.invalid_signature_count == 0
    assert block_handler.storage_queue.qsize() == 1
