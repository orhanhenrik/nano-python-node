import asyncio
from enum import IntEnum
from typing import List

from util.crypto import (
    verify_pow_async,
    verify_signature_async,
)


class BlockType(IntEnum):
    INVALID = 0
    NOT_A_BLOCK = 1
    SEND = 2
    RECEIVE = 3
    OPEN = 4
    CHANGE = 5


class Block:
    @classmethod
    def parse(cls, data: bytes):
        pass

    def __init__(self, block_type: BlockType):
        self.work: bytes = bytes()
        self.signature: bytes = bytes()
        self.block_type: BlockType = block_type

    @property
    def root(self) -> bytes:
        return bytes()

    def hash_sync(self):
        return bytes()

    def dependencies(self) -> List[bytes]:
        return []

    async def hash(self):
        return bytes()

    async def verify(self):
        results = await asyncio.gather(
            self.verify_signature(), self.verify_pow(), self.verify_consistency()
        )
        return all(results)

    async def verify_pow(self):
        return await verify_pow_async(self.root, self.work)

    async def verify_signature(self):
        raise NotImplementedError()
        _hash = await self.hash()
        if hash and isinstance(self, OpenBlock):
            return await verify_signature_async(_hash, self.signature, self.account)
        return True

    async def verify_consistency(self):
        # Check that hashes it references exist.
        # Check that there is no conflicting transactions (branches)
        # Check that account has sufficient funds if type=send
        # And more?
        return True

    def to_bytes(self) -> bytes:
        return bytes([self.block_type.value])

    def __str__(self) -> str:
        return f"<Block {self.block_type.name}>"

    def __repr__(self) -> str:
        return str(self)
