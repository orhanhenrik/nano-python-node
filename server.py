import asyncio
import signal
from concurrent.futures import Executor
from typing import List, Tuple

import time

import marshal
import uvloop
import pickle
from uvloop.loop import UDPTransport, Loop, Server

from executors import process_executor, thread_executor
from models.blocks import BlockType, BlockParser, Block
from models.messages import (
    Message,
    MessageParser,
    KeepAliveMessage,
    FrontierReqMessage,
    BulkPullMessage,
)
from type_definitions import Address

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

EXPAND_PEERS = False

peers = [("::ffff:192.168.1.136", 7075)]


async def handle_msg(data: bytes, addr: Address, transport: UDPTransport):
    message: Message = MessageParser.parse(data)
    print(message.header.message_type)

    if not await message.verify():
        print("INVALID MESSAGE!!")
        print(message.header.message_type)
        raise Exception("INVALID MESSAGE")
    else:
        print("Message valid")

    if isinstance(message, KeepAliveMessage):
        print("peers..")
        print(message.peers)

        keepalive_response = KeepAliveMessage().to_bytes()
        transport.sendto(keepalive_response, addr)

        if EXPAND_PEERS and len(message.peers):
            print(f"constructing keepalive for first peer {message.peers[0]}")
            transport.sendto(keepalive_response, message.peers[0].to_tuple())
        else:
            print("found no valid peers")

    print("done")


# This server needs to respond to frontier_req and bulk_pull
class TCPServerProtocol(asyncio.Protocol):
    def __init__(self):
        print("init")
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        print("connection made")

    def data_received(self, data):
        print("tcp data received", data)


# Todo: this needs to fetch from a global queue. If many workers are spawned now they will all pull
# the same frontiers.
async def get_accounts(
    i: int,
    frontiers: List[Tuple[bytes, bytes]],
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
):
    print(f"start worker {i}")
    account_count = 0
    block_count = 0
    failures = 0
    chains = []
    while len(frontiers):
        start, end = frontiers.pop()
        message = BulkPullMessage(start=start, end=bytes(32))
        writer.write(message.to_bytes())
        await writer.drain()

        try:
            blocks = await read_bulk_pull(reader)
        except Exception:
            # If getting blocks failed, retry at a later stage
            frontiers.append((start, end))
            failures += 1
            continue

        account_count += 1
        block_count += len(blocks)
        chains.append(blocks)
        if len(frontiers) != 0 and len(frontiers) % 100 == 0:
            print(f"frontiers left:{len(frontiers)}")

    print(
        f"worker {i} done. Pulled {account_count} accounts, {block_count} blocks."
        f"Failures: {failures}"
    )
    return chains


async def get_all_accounts(frontiers, num_workers=10):
    tasks = []
    for i in range(num_workers):
        peer = peers[0]
        reader, writer = await asyncio.open_connection(peer[0], peer[1])
        tasks.append(get_accounts(i, frontiers, reader, writer))
    return [chain for chains in await asyncio.gather(*tasks) for chain in chains]


async def get_frontiers(host, port=7075):
    s = time.time()

    reader, writer = await asyncio.open_connection(host, port)

    # Fetch all frontiers - max age and count - I don't know how lowering these values would affect
    # the result.
    message = FrontierReqMessage(age=bytes([255] * 4), count=bytes([255] * 4))
    writer.write(message.to_bytes())
    await writer.drain()

    # Note: frontiers is only 25MB atm (391k frontiers). Investigate pulling frontiers from more
    # than one host if we have the bandwidth for it, since knowing all frontiers and having up to
    # date blocks is important.

    print("Getting frontiers")
    frontiers = await read_frontiers(reader)
    print(f"Got {len(frontiers)} frontiers")

    # TODO: Need to filter frontiers. If we already have frontiers newest block, don't fetch.
    # TODO: If we have a newer block than the peer, we need to send them the update (bulk_push?)

    print("Getting accounts")
    chains = await get_all_accounts(frontiers)
    print("Finished getting accounts")
    print(
        f"Got {len(chains)} accounts with total of {sum(len(chain) for chain in chains)} blocks"
    )
    writer.close()

    # Dump all account chains to file
    with open("marshal_chains.dump", "wb") as f:
        chains = list(
            map(lambda chain: list(map(lambda block: block.to_bytes(), chain)), chains)
        )
        marshal.dump(chains, f)

    print(f"get_frontiers from {host} {port} done in {(time.time()-s)*1000}ms")


async def read_frontiers(reader: asyncio.StreamReader):
    c = 0
    frontiers = []
    # Note: frontiers arrive ordered by ascending account value
    while True:
        # Each frontier is 2x32 bytes
        line = bytes()
        while len(line) != 64:
            line += await reader.read(64 - len(line))
        account = line[0:32]
        # The account 0000...0 signals the end of the frontiers message
        if account == bytes(32):
            break
        block_hash = line[32:64]
        frontiers.append((account, block_hash))
        c += 1

    print(f"done pulling {c} frontiers!")
    return frontiers


async def read_multiple_blocks(reader: asyncio.StreamReader, max_count: int = 0):
    blocks: List[Block] = []
    while True:
        block_type_byte = await reader.read(1)
        if not block_type_byte:
            print("unexpected end of stream")
            break

        try:
            block_type = BlockType(block_type_byte[0])
        except ValueError:
            raise Exception(f"{block_type_byte.hex()} is not a valid block type..")

        # Block type 0x01 (NOT_A_BLOCK) signals that there are no more blocks
        if block_type == BlockType.NOT_A_BLOCK:
            break

        # Need to read the right amount of bytes so that we start at the right place when reading
        # the next block
        length = BlockParser.length(block_type)
        block_data = bytes()
        # This is needed because reader.read(n) may return less than n bytes
        while len(block_data) != length:
            block_data += await reader.read(length - len(block_data))

        block = BlockParser.parse(block_type, block_data)
        blocks.append(block)

        if max_count != 0 and len(blocks) == max_count:
            break

    return blocks


async def read_bulk_pull(reader: asyncio.StreamReader):
    blocks: List[Block] = read_multiple_blocks(reader)
    if len(blocks) and blocks[-1].block_type != BlockType.OPEN:
        raise Exception(
            f"Last block should be OPEN, but was {blocks[-1].block_type.name}"
        )

    # TODO: Check that all the blocks point to each other as source - no missing blocks
    return blocks


async def startup():
    # Send keepalive to local rai_node in order to start receiving updates from it.
    # print(f'sending keepalive to {ipv6}')
    # transport.sendto(KeepAliveMessage().to_bytes(), (ipv6, 7075, 0, 0))

    # Fetch frontiers and blocks from the local rai_node instance (separate service).
    # This should only be done on bootstrap in the future.
    peer = peers[0]
    await get_frontiers(peer[0], peer[1])


loop = asyncio.get_event_loop()

tcp_coro = loop.create_server(TCPServerProtocol, "::", 8888)


print("starting TCP server")
server = loop.run_until_complete(tcp_coro)
asyncio.ensure_future(startup(), loop=loop)


def shutdown(
    _loop: Loop,
    _server: Server,
    executors: List[Executor],
):
    print("shutting down sockets, processes, threads and abort tasks")
    for task in asyncio.Task.all_tasks():
        task.cancel()
    for executor in executors:
        executor.shutdown()
    _server.close()
    _loop.stop()


loop.add_signal_handler(
    signal.SIGINT,
    shutdown,
    loop,
    server,
    [thread_executor, process_executor],
)
loop.run_forever()
print("closing loop")
loop.close()
