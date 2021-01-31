from typing import List

from util.crypto import (
    blake2b_hash,
    blake2b_async,
)
from .block import Block, BlockType


class SendBlock(Block):
    LENGTH = 152

    @classmethod
    def parse(cls, data: bytes):
        assert (
            len(data) == cls.LENGTH
        ), f"Invalid data length! Expected: {cls.LENGTH}, actual: {len(data)}"
        previous = data[0:32]
        destination = data[32:64]
        balance = data[64:80]
        signature = data[80:144]
        work = data[144:152]
        return cls(previous, destination, balance, signature, work)

    def __init__(self, previous, destination, balance, signature, work):
        super(SendBlock, self).__init__(BlockType.SEND)
        self.previous = previous
        self.destination = destination
        self.balance = balance
        self.signature = signature
        self.work = work

    @property
    def root(self):
        return self.previous

    def hash_sync(self):
        return blake2b_hash(self.previous + self.destination + self.balance)

    def dependencies(self) -> List[bytes]:
        return [self.previous]

    async def hash(self):
        return await blake2b_async(self.previous + self.destination + self.balance)

    def to_bytes(self) -> bytes:
        return (
            super(SendBlock, self).to_bytes()
            + self.previous
            + self.destination
            + self.balance
            + self.signature
            + self.work
        )
