import asyncio

import uvloop
from uvloop.loop import UDPTransport

from models.messages import Message, MessageType, MessageParser, KeepAliveMessage
from type_definitions import Address

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def handle_msg(data: bytes, addr: Address, transport: UDPTransport):

    message: Message = MessageParser.parse(data)
    print(message.header.message_type)

    if message.block:
        if not message.block.verify():
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


class EchoServerProtocol(asyncio.DatagramProtocol):

    def connection_made(self, transport: UDPTransport):
        self.transport = transport

    def datagram_received(self, data: bytes, addr: Address):
        print(f'## Received {len(data)} bytes from {addr}')
        asyncio.ensure_future(handle_msg(data, addr, transport))


loop = asyncio.get_event_loop()
print('starting UDP server')

listen = loop.create_datagram_endpoint(
    EchoServerProtocol, local_addr=('::', 8888)
)

transport, protocol = loop.run_until_complete(listen)

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

transport.close()
loop.close()
