from typing import List

from util.crypto import blake2b_hash, blake2b_async, verify_signature_async
from .block import Block, BlockType


class OpenBlock(Block):
    LENGTH = 168

    @classmethod
    def parse(cls, data: bytes):
        assert (
            len(data) == cls.LENGTH
        ), f"Invalid data length! Expected: {cls.LENGTH}, actual: {len(data)}"
        source = data[0:32]
        representative = data[32:64]
        account = data[64:96]
        signature = data[96:160]
        work = data[160:168]

        return cls(source, representative, account, signature, work)

    def __init__(self, source, representative, account, signature, work):
        super(OpenBlock, self).__init__(BlockType.OPEN)
        self.source = source
        self.representative = representative
        self.account = account
        self.signature = signature
        self.work = work

    @property
    def root(self):
        return self.account

    def hash_sync(self):
        return blake2b_hash(self.source + self.representative + self.account)

    def dependencies(self) -> List[bytes]:
        return [self.source]

    async def verify_signature(self):
        _hash = await self.hash()
        return await verify_signature_async(_hash, self.signature, self.account)

    async def hash(self):
        return await blake2b_async(self.source + self.representative + self.account)

    def to_bytes(self) -> bytes:
        return (
            super(OpenBlock, self).to_bytes()
            + self.source
            + self.representative
            + self.account
            + self.signature
            + self.work
        )