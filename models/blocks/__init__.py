from .block import Block, BlockType
from .send import SendBlock
from .change import ChangeBlock
from .receive import ReceiveBlock
from .open import OpenBlock


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
