import asyncio
import signal
from concurrent.futures import Executor
from typing import List

import time
import uvloop
from uvloop.loop import UDPTransport, Loop, Server

from executors import process_executor, thread_executor
from models.block import BlockType, BlockParser
from models.messages import Message, MessageParser, KeepAliveMessage, \
    FrontierReqMessage, BulkPullMessage
from type_definitions import Address

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

EXPAND_PEERS = False


async def handle_msg(data: bytes, addr: Address, transport: UDPTransport):
    message: Message = MessageParser.parse(data)
    print(message.header.message_type)

    if not await message.verify():
        print('INVALID MESSAGE!!')
        print(message.message_type)
        raise Exception('INVALID MESSAGE')
    else:
        print('Message valid')

    if isinstance(message, KeepAliveMessage):
        print('peers..')
        print(message.peers)

        keepalive_response = KeepAliveMessage().to_bytes()
        transport.sendto(keepalive_response, addr)

        if EXPAND_PEERS and len(message.peers):
            print(f'constructing keepalive for first peer {message.peers[0]}')
            transport.sendto(keepalive_response, message.peers[0].to_tuple())
        else:
            print('found no valid peers')

    print('done')


class UDPServerProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport: UDPTransport):
        self.transport = transport

    def datagram_received(self, data: bytes, addr: Address):
        print(f'## Received {len(data)} bytes from {addr}')
        asyncio.ensure_future(handle_msg(data, addr, transport))


# This server needs to respond to frontier_req and bulk_pull
class TCPServerProtocol(asyncio.Protocol):
    def __init__(self):
        print('init')
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        print('connection made')

    def data_received(self, data):
        print('tcp data received', data)


async def get_frontiers(host, port=7075):
    s = time.time()

    reader, writer = await asyncio.open_connection(host, port)

    # Fetch all frontiers - max age and count - I don't know how lowering these values would affect
    # the result.
    message = FrontierReqMessage(age=bytes([255,255,255,255]), count=bytes([255,255,255,255]))
    writer.write(message.to_bytes())
    await writer.drain()

    # Note: frontiers is only 25MB atm (391k frontiers). Investigate pulling frontiers from more
    # than one host if we have the bandwidth for it, since knowing all frontiers and having up to
    # date blocks is important.
    frontiers = await read_frontiers(reader)
    print(len(frontiers))

    # TODO: Do this for every frontier. Do many of these in parallel to multiple peers
    # TODO: Need to filter frontiers. If we already have frontiers newest block, don't fetch.
    # TODO: If we have a newer block than the peer, we need to send them the update (bulk_push?)
    start, end = frontiers[0]
    print(start.hex())
    print(end.hex())
    message2 = BulkPullMessage(start=start, end=bytes(32))
    writer.write(message2.to_bytes())
    await writer.drain()
    await read_bulk_pull(reader)

    writer.close()

    print(f'get_frontiers from {host} {port} done in {(time.time()-s)*1000}ms')


async def read_frontiers(reader: asyncio.StreamReader):
    c = 0
    frontiers = []
    # Note: frontiers arrive ordered by ascending account value
    while True:
        # Each frontier is 2x32 bytes
        line = await reader.read(64)
        if not line:
            break
        account = line[0:32]
        # The account 0000...0 signals the end of the frontiers message
        if account == bytes(32):
            break
        block_hash = line[32:64]
        frontiers.append((account, block_hash))
        c += 1

    print(f'done pulling {c} frontiers!')
    return frontiers


async def read_bulk_pull(reader: asyncio.StreamReader):
    while True:
        block_type_byte = await reader.read(1)
        if not block_type_byte:
            print('unexpected end of stream')
            break

        block_type = BlockType(block_type_byte[0])
        # Block type 0x01 (NOT_A_BLOCK) signals that there are no more blocks
        if block_type == BlockType.NOT_A_BLOCK:
            print('end of blocks')
            break

        length = BlockParser.length(block_type)
        # Need to read the right amount of bytes so that we start at the right place when reading
        # the next block
        block_data = await reader.read(length)
        block = BlockParser.parse(block_type, block_data)
        print(block)


async def startup():
    import socket
    ipv4 = socket.gethostbyname(socket.gethostname())
    ipv6 = f'::ffff:{ipv4}'
    # print(f'sending keepalive to {ipv6}')
    # # Send keepalive to local rai_node in order to start receiving updates from it.
    # transport.sendto(KeepAliveMessage().to_bytes(), (ipv6, 7075, 0, 0))

    # Fetch frontiers and blocks from the local rai_node instance (separate service).
    # This should only be done on bootstrap in the future.
    await get_frontiers(ipv6, 7075)


loop = asyncio.get_event_loop()

tcp_coro = loop.create_server(TCPServerProtocol, '::', 8888)

udp_coro = loop.create_datagram_endpoint(
    UDPServerProtocol, local_addr=('::', 8888)
)

print('starting TCP server')
server = loop.run_until_complete(tcp_coro)
print('starting UDP server')
transport, protocol = loop.run_until_complete(udp_coro)

asyncio.ensure_future(startup(), loop=loop)


def shutdown(_loop: Loop, _transport: asyncio.Transport, _server: Server, executors: List[Executor]):
    print('shutting down sockets, processes, threads and abort tasks')
    for task in asyncio.Task.all_tasks():
        task.cancel()
    for executor in executors:
        executor.shutdown()
    _transport.close()
    _server.close()
    _loop.stop()


loop.add_signal_handler(signal.SIGINT,
                        shutdown,
                        loop,
                        transport,
                        server,
                        [thread_executor, process_executor])
loop.run_forever()
print('closing loop')
loop.close()
