from enum import IntEnum


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

    def __init__(self, block_type):
        self.block_type = block_type

    def to_bytes(self):
        return bytes([self.block_type.value])

    def __str__(self):
        return f'<Block {self.block_type.name}>'

    def __repr__(self):
        return str(self)


class SendBlock(Block):
    @classmethod
    def parse(cls, data: bytes):
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


class ReceiveBlock(Block):
    @classmethod
    def parse(cls, data: bytes):
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


class OpenBlock(Block):
    @classmethod
    def parse(cls, data: bytes):
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


class ChangeBlock(Block):
    @classmethod
    def parse(cls, data: bytes):
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


class BlockParser:
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
