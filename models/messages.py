import asyncio
from enum import IntEnum
from typing import List

from models.block import Block, BlockType, BlockParser
from models.peer import Peer
from util.crypto import verify_signature_async, blake2b_async


class MessageType(IntEnum):
    INVALID = 0
    NOT_A_TYPE = 1
    KEEPALIVE = 2
    PUBLISH = 3
    CONFIRM_REQ = 4
    CONFIRM_ACK = 5
    BULK_PULL = 6
    BULK_PUSH = 7
    FRONTIER_REQ = 8
    # BULK_PULL_BLOCKS = 9
    NODE_ID_HANDSHAKE = 10
    BULK_PULL_ACCOUNT = 11
    TELEMETRY_REQ = 12
    TELEMETRY_ACK = 13


class BulkPullAccountFlags(IntEnum):
    PENDING_HASH_AND_AMOUNT = 0
    PENDING_ADDRESS_ONLY = 1
    PENDING_HASH_AMOUNT_AND_ADDRESS = 2


class Header:
    @classmethod
    def parse(cls, data: bytes):
        magic = data[0:2]
        version_max = data[2]
        version_current = data[3]
        version_min = data[4]
        message_type = MessageType(data[5])
        extensions = data[6]
        return cls(
            magic, version_max, version_current, version_min, message_type, extensions
        )

    def __init__(
        self, magic, version_max, version_current, version_min, message_type, extensions
    ):
        self.magic = magic
        self.version_max = version_max
        self.version_current = version_current
        self.version_min = version_min
        self.message_type = message_type
        self.extensions = extensions

    def verify(self):
        return True

    @classmethod
    def default_header(cls, message_type: MessageType):
        return cls(b"RC", 5, 5, 1, message_type, 0)

    def to_bytes(self):
        return self.magic + bytes(
            [
                self.version_max,
                self.version_current,
                self.version_min,
                self.message_type.value,
                self.extensions,
            ]
        )


class Message:
    @classmethod
    def parse(cls, header: Header, block_type: BlockType, data: bytes):
        pass

    def __init__(self, header: Header, block_type: BlockType):
        self.header = header
        self.block_type = block_type
        self.block = None

    async def verify(self):
        return self.header.verify()

    def to_bytes(self):
        return self.header.to_bytes() + bytes([self.block_type.value])


class KeepAliveMessage(Message):
    @classmethod
    def parse(cls, header: Header, block_type: BlockType, data: bytes):
        peers: List[Peer] = []
        for i in range(0, len(data), 18):
            ip = data[i : i + 18]
            peers.append(Peer(ip))
        # print(peers)
        return cls(header, block_type, peers)

    def __init__(
        self,
        header: Header = None,
        block_type: BlockType = BlockType.INVALID,
        peers: List[Peer] = None,
    ):
        if header is None:
            header = Header.default_header(MessageType.KEEPALIVE)
        if peers is None:
            peers = []

        super(KeepAliveMessage, self).__init__(header, block_type)

        self.peers = peers

    def to_bytes(self):
        # TODO: Add peers
        return super(KeepAliveMessage, self).to_bytes()


class PublishMessage(Message):
    @classmethod
    def parse(cls, header: Header, block_type: BlockType, data: bytes):
        block: Block = BlockParser.parse(block_type, data)
        return cls(header, block_type, block)

    def __init__(
        self,
        header: Header = None,
        block_type: BlockType = BlockType.INVALID,
        block: Block = None,
    ):
        if header is None:
            header = Header.default_header(MessageType.PUBLISH)
        super(PublishMessage, self).__init__(header, block_type)
        self.block = block

    async def verify(self):
        result = asyncio.gather(
            super(PublishMessage, self).verify(), self.block.verify()
        )
        return all(result)

    def to_bytes(self):
        return super(PublishMessage, self).to_bytes() + self.block.to_bytes()


class ReqMessage(Message):
    @classmethod
    def parse(cls, header: Header, block_type: BlockType, data: bytes):
        block: Block = BlockParser.parse(block_type, data)
        return cls(header, block_type, block)

    def __init__(
        self,
        header: Header = None,
        block_type: BlockType = BlockType.INVALID,
        block: Block = None,
    ):
        if header is None:
            header = Header.default_header(MessageType.CONFIRM_REQ)
        super(ReqMessage, self).__init__(header, block_type)
        self.block = block

    async def verify(self):
        result = asyncio.gather(super(ReqMessage, self).verify(), self.block.verify())
        return all(result)

    def to_bytes(self):
        return super(ReqMessage, self).to_bytes() + self.block.to_bytes()


class AckMessage(Message):
    @classmethod
    def parse(cls, header: Header, block_type: BlockType, data: bytes):
        # TODO: Create Vote class
        vote = dict(account=data[0:32], signature=data[32:96], sequence=data[96:104])
        block: Block = BlockParser.parse(block_type, data[104:])
        return cls(header, block_type, vote, block)

    def __init__(
        self,
        header: Header = None,
        block_type: BlockType = BlockType.INVALID,
        vote=None,
        block: Block = None,
    ):
        if header is None:
            header = Header.default_header(MessageType.CONFIRM_ACK)
        super(AckMessage, self).__init__(header, block_type)
        self.vote = vote
        self.block = block

    async def verify_signature(self):
        _hash = await blake2b_async(await self.block.hash() + self.vote["sequence"])
        return await verify_signature_async(
            _hash, self.vote["signature"], self.vote["account"]
        )

    async def verify(self):
        results = await asyncio.gather(
            super(AckMessage, self).verify(),
            self.block.verify(),
            self.verify_signature(),
        )
        return all(results)

    def to_bytes(self):
        return super(AckMessage, self).to_bytes() + self.block.to_bytes()


class FrontierReqMessage(Message):
    @classmethod
    def parse(cls, header: Header, block_type: BlockType, data: bytes):
        account = data[0:32]
        age = data[32:36]
        count = data[36:40]
        return cls(header, block_type, account, age, count)

    def __init__(
        self,
        header: Header = None,
        block_type: BlockType = BlockType.INVALID,
        account: bytes = bytes(32),
        age: bytes = bytes(4),
        count: bytes = bytes(4),
    ):
        if header is None:
            header = Header.default_header(MessageType.FRONTIER_REQ)
        super(FrontierReqMessage, self).__init__(header, block_type)
        self.account = account
        self.age = age
        self.count = count

    def to_bytes(self):
        return (
            super(FrontierReqMessage, self).to_bytes()
            + self.account
            + self.age
            + self.count
        )


class BulkPullMessage(Message):
    @classmethod
    def parse(cls, header: Header, block_type: BlockType, data: bytes):
        start = data[0:32]
        end = data[32:64]
        return cls(header, block_type, start, end)

    def __init__(
        self,
        header: Header = None,
        block_type: BlockType = BlockType.INVALID,
        start: bytes = bytes(32),
        end: bytes = bytes(32),
    ):
        if header is None:
            header = Header.default_header(MessageType.BULK_PULL)
        super(BulkPullMessage, self).__init__(header, block_type)
        self.start = start
        self.end = end

    def to_bytes(self):
        return super(BulkPullMessage, self).to_bytes() + self.start + self.end


class MessageParser:
    @staticmethod
    def parse(data: bytes) -> Message:
        # print('parsing message..')
        if len(data) < 8:
            pass  # raise

        header: Header = Header.parse(data[:7])
        block_type: BlockType = BlockType(data[7])

        if header.message_type == MessageType.KEEPALIVE:
            return KeepAliveMessage.parse(header, block_type, data[8:])
        elif header.message_type == MessageType.PUBLISH:
            return PublishMessage.parse(header, block_type, data[8:])
        elif header.message_type == MessageType.CONFIRM_REQ:
            return ReqMessage.parse(header, block_type, data[8:])
        elif header.message_type == MessageType.CONFIRM_ACK:
            return AckMessage.parse(header, block_type, data[8:])

        return Message(header, block_type)
