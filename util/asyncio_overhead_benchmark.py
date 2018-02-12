import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

import time

from util.crypto import blake2b_async, blake2b_hash, verify_signature, verify_signature_async

hash = b'U\x00\x95\xad\xd6\xd70\xa9D\x02\xc9\xd2BF\xae\x14\x19\xf5\xd8\n\xa3{8\x99\xfd[\xa5c}\xd0\xc7~'
signature = b'\xeb\xb5Sv\xee1U\x06X\xab3q.\xd8{\xf5{\xda\x8e\xd1\xa1\xb0\x1a\xeair\x0e\xc6D\x1a\xc5\x08\xb8\xbdk67\xae\x80\xc4s\xd1\\\x91\xabQf\xe3\x18\xd7\xb1??c6\xe4\xa8\x91f^\xc5\x8b\xfe\x07'
public_key = b'J\xf2\xb8L\xae\xe7\x8c0\xd2\xcaM\xdb\x1fq\xb2E\t\xec[\x06\x19\xe5\xa7\xd7\x90\x9c\x84\x0e\x8d\x84\x9a\x1e'

hashable = b'abc123'


def sync_benchmark_blake2b(n):
    for i in range(n):
        blake2b_hash(hashable)


async def benchmark_blake2b(n, executor):
    for i in range(n):
        await blake2b_async(hashable, executor=executor)


def sync_benchmark_signature_validation(n):
    for i in range(n):
        verify_signature(hash, signature, public_key)


async def benchmark_signature_validation(n, executor):
    for i in range(n):
        await verify_signature_async(hash, signature, public_key, executor=executor)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    te = ThreadPoolExecutor(max_workers=1)
    pe = ProcessPoolExecutor(max_workers=1)

    n = 10
    # Blake2b
    start = time.time()
    sync_benchmark_blake2b(n)
    print(f'blake2b, n={n} sync done in {(time.time()-start)*1000} ms')

    start = time.time()
    fut: asyncio.Future = asyncio.ensure_future(benchmark_blake2b(n, te))
    loop.run_until_complete(fut)
    print(f'blake2b, n={n} thread done in {(time.time()-start)*1000} ms')

    start = time.time()
    fut: asyncio.Future = asyncio.ensure_future(benchmark_blake2b(n, pe))
    loop.run_until_complete(fut)
    print(f'blake2b, n={n} process done in {(time.time()-start)*1000} ms')

    # Signature
    start = time.time()
    sync_benchmark_signature_validation(n)
    print(f'signature, n={n} sync done in {(time.time()-start)*1000} ms')

    start = time.time()
    fut: asyncio.Future = asyncio.ensure_future(benchmark_signature_validation(n, te))
    loop.run_until_complete(fut)
    print(f'signature, n={n} thread done in {(time.time()-start)*1000} ms')

    start = time.time()
    fut: asyncio.Future = asyncio.ensure_future(benchmark_signature_validation(n, pe))
    loop.run_until_complete(fut)
    print(f'signature, n={n} process done in {(time.time()-start)*1000} ms')

    loop.close()
