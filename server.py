import asyncio
import signal
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Executor
from typing import List

import time
import uvloop
from uvloop.loop import UDPTransport, Loop, Server

from blake2 import try_hash
from executors import process_executor, thread_executor
from models.messages import Message, MessageType, MessageParser, KeepAliveMessage
from type_definitions import Address
from util.crypto import blake2b_async

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def handle_msg(data: bytes, addr: Address, transport: UDPTransport):

    message: Message = MessageParser.parse(data)
    print(message.header.message_type)

    if message.block:
        if not await message.block.verify():
            print('INVALID BLOCK!!')
            raise Exception('INVALID BLOCK')
        else:
            print('Block valid')

    if isinstance(message, KeepAliveMessage):
        print('peers..')
        print(message.peers)

        keepalive_response = KeepAliveMessage().to_bytes()
        transport.sendto(keepalive_response, addr)

        EXPAND_PEERS = False
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


class TCPServerProtocol(asyncio.Protocol):
    def __init__(self):
        print('init')
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        print('connection made')

    def data_received(self, data):
        print('tcp data received', data)


loop = asyncio.get_event_loop()

tcp_coro = loop.create_server(TCPServerProtocol, '::', 8888)

udp_coro = loop.create_datagram_endpoint(
    UDPServerProtocol, local_addr=('::', 8888)
)

print('starting TCP server')
server = loop.run_until_complete(tcp_coro)
print(server)
print('starting UDP server')
transport, protocol = loop.run_until_complete(udp_coro)




async def boot():
    import socket
    ipv4 = socket.gethostbyname(socket.gethostname())
    ipv6 = f'::ffff:{ipv4}'
    print(f'sending keepalive to {ipv6}')
    transport.sendto(KeepAliveMessage().to_bytes(), (ipv6, 7075, 0, 0))

    # await multi_hash()
    # await counter_in_threads()

    # await asyncio.gather(
    #     blake2b_async(b't1'),
    #     blake2b_async(b't2')
    # )
    # print('done')


def waiter(n):
    print(n, 'start')
    time.sleep(1)
    print(n, 'done')
    return n*2


async def multi_hash():
    _loop = asyncio.get_event_loop()
    found = False
    s0 = time.time()
    while not found:
        s = time.time()
        tasks = [
            _loop.run_in_executor(process_executor, try_hash, i, 256*256)
            for i in range(8)
        ]
        await asyncio.wait(tasks)
        print((time.time() - s)*1000)
        for t in tasks:
            print(t.result())
            if t.result():
                found = True
                print('FOUND', t.result())
                print((time.time() - s0)*1000)


async def counter_in_threads():
    _loop = asyncio.get_event_loop()
    print('making tasks')
    tasks = [
        _loop.run_in_executor(thread_executor, waiter, i)
        for i in range(10)
    ]
    print('waiting')
    await asyncio.wait(tasks)
    print('finished')
    print([t.result() for t in tasks])


asyncio.ensure_future(boot(), loop=loop)


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
