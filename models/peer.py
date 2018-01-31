import ipaddr
from ipaddr import IPv6Address


class Peer:
    def __init__(self, data):
        self.ipv6 = IPv6Address(ipaddr.Bytes(data[:16]))
        self.ipv4 = self.ipv6.ipv4_mapped
        self.port = int.from_bytes(data[16:], byteorder='little')

    def to_bytes(self):
        pass

    def to_tuple(self):
        return str(self.ipv4), self.port

    def __str__(self):
        return f'<Peer {self.ipv4 or self.ipv6}, port:{self.port}>'

    def __repr__(self):
        return str(self)
