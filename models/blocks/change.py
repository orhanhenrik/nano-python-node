from typing import List

from util.crypto import (
    blake2b_hash,
    blake2b_async,
)
from .block import Block, BlockType


class ChangeBlock(Block):
    LENGTH = 136

    @classmethod
    def parse(cls, data: bytes):
        assert (
            len(data) == cls.LENGTH
        ), f"Invalid data length! Expected: {cls.LENGTH}, actual: {len(data)}"
        previous = data[0:32]
        representative = data[32:64]
        signature = data[64:128]
        work = data[128:136]
        return cls(previous, representative, signature, work)

    def __init__(self, previous, representative, signature, work):
        super(ChangeBlock, self).__init__(BlockType.CHANGE)
        self.previous = previous
        self.representative = representative
        self.signature = signature
        self.work = work

    @property
    def root(self):
        return self.previous

    def hash_sync(self):
        return blake2b_hash(self.previous + self.representative)

    def dependencies(self) -> List[bytes]:
        return [self.previous]

    async def hash(self):
        return await blake2b_async(self.previous + self.representative)

    def to_bytes(self) -> bytes:
        return (
            super(ChangeBlock, self).to_bytes()
            + self.previous
            + self.representative
            + self.signature
            + self.work
        )
