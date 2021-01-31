from typing import List

from util.crypto import (
    blake2b_hash,
    blake2b_async,
)
from .block import Block, BlockType


class ReceiveBlock(Block):
    LENGTH = 136

    @classmethod
    def parse(cls, data: bytes):
        assert (
            len(data) == cls.LENGTH
        ), f"Invalid data length! Expected: {cls.LENGTH}, actual: {len(data)}"
        previous = data[0:32]
        source = data[32:64]
        signature = data[64:128]
        work = data[128:136]
        return cls(previous, source, signature, work)

    def __init__(self, previous, source, signature, work):
        super(ReceiveBlock, self).__init__(BlockType.RECEIVE)
        self.previous = previous
        self.source = source
        self.signature = signature
        self.work = work

    @property
    def root(self):
        return self.previous

    def hash_sync(self):
        return blake2b_hash(self.previous + self.source)

    def dependencies(self) -> List[bytes]:
        return [self.previous, self.source]

    async def hash(self):
        return await blake2b_async(self.previous + self.source)

    def to_bytes(self) -> bytes:
        return (
            super(ReceiveBlock, self).to_bytes()
            + self.previous
            + self.source
            + self.signature
            + self.work
        )
