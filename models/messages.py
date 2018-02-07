from enum import IntEnum
from typing import List

from models.block import Block, BlockType
from models.peer import Peer


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
    FRONTIER = 10000
    BULK = 10001


class Header:
    @classmethod
    def parse(cls, data: bytes):
        greeting = data[0:2]
        version_max = data[2]
        version_current = data[3]
        version_min = data[4]
        message_type = MessageType(data[5])
        extensions = data[6]
        return cls(greeting, version_max, version_current, version_min, message_type, extensions)

    def __init__(self, greeting, version_max, version_current, version_min, message_type, extensions):
        self.greeting = greeting
        self.version_max = version_max
        self.version_current = version_current
        self.version_min = version_min
        self.message_type = message_type
        self.extensions = extensions

    @classmethod
    def default_header(cls):
        return cls(b'RC', 5, 5, 1, MessageType.KEEPALIVE, 0)

    def to_bytes(self):
        return self.greeting + bytes([self.version_max, self.version_current, self.version_min, self.message_type.value, self.extensions])


class Message:
    @classmethod
    def parse(cls, header: Header, block_type: BlockType, data: bytes):
        pass

    def __init__(self, header: Header, block_type: BlockType, message_type: MessageType):
        self.header = header
        self.block_type = block_type
        self.message_type = message_type

    def to_bytes(self):
        return self.header.to_bytes() + bytes([self.block_type.value])


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
            pass
        elif header.message_type == MessageType.CONFIRM_REQ:
            pass
        elif header.message_type == MessageType.CONFIRM_ACK:
            pass

        return Message(header, block_type, header.message_type)


class KeepAliveMessage(Message):
    @classmethod
    def parse(cls, header: Header, block_type: BlockType, data: bytes):
        peers: List[Peer] = []
        for i in range(0, len(data), 18):
            ip = data[i:i+18]
            peers.append(Peer(ip))
        # print(peers)
        return cls(header, block_type, peers)

    def __init__(self, header: Header = None, block_type: BlockType = BlockType.INVALID, peers: List[Peer] = None):
        if header is None:
            header = Header.default_header()
        if peers is None:
            peers = []

        super(KeepAliveMessage, self).__init__(header, block_type, MessageType.KEEPALIVE)

        self.peers = peers

    def to_bytes(self):
        # TODO: Add peers
        return super(KeepAliveMessage, self).to_bytes()


class PublishMessage(Message):
    @classmethod
    def parse(cls, header: Header, block_type: BlockType, data: bytes):
        block: Block = BlockParser.parse()
        peers: List[Peer] = []
        for i in range(0, len(data), 18):
            ip = data[i:i+18]
            peers.append(Peer(ip))
        # print(peers)
        return cls(header, block_type, peers)

    def __init__(self, header: Header = None, block_type: BlockType = BlockType.INVALID, block: Block = None):
        if header is None:
            header = Header.default_header()
        super(PublishMessage, self).__init__(header, block_type, MessageType.PUBLISH)
        self.block = block


    def to_bytes(self):
        # TODO: Add peers
        return super(PublishMessage, self).to_bytes() + self.block.to_bytes()
