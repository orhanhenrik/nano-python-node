import asyncio
import logging
from enum import IntEnum
from typing import List

from util.crypto import (
    blake2b_hash,
    blake2b_async,
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


class BlockParser:
    @staticmethod
    def length(block_type: BlockType) -> int:
        if block_type == BlockType.SEND:
            return SendBlock.LENGTH
        elif block_type == BlockType.RECEIVE:
            return ReceiveBlock.LENGTH
        elif block_type == BlockType.OPEN:
            return OpenBlock.LENGTH
        elif block_type == BlockType.CHANGE:
            return ChangeBlock.LENGTH
        else:
            return 0

    @staticmethod
    def parse(block_type: BlockType, data: bytes) -> Block:
        if block_type == BlockType.SEND:
            return SendBlock.parse(data)
        elif block_type == BlockType.RECEIVE:
            return ReceiveBlock.parse(data)
        elif block_type == BlockType.OPEN:
            return OpenBlock.parse(data)
        elif block_type == BlockType.CHANGE:
            return ChangeBlock.parse(data)
        else:
            pass

        return Block(block_type)
