import asyncio
import time
import os

from executors import process_executor
from util.crypto import blake2b_hash


def try_hash(task_num, n, hash=b"718CC2121C3E641059BC1C2CFC456111"):
    r0 = os.urandom(6)
    for i in range(n):
        # r = os.urandom(8)
        r = r0 + bytes([i & 0xFF, i & 0xFF00 >> 8])
        digest = blake2b_hash(r + hash, digest_size=8)[::-1]

        # digest = blake2b(r+hash, digest_size=8).digest()[::-1]

        if digest >= bytes.fromhex("ffffffc000000000"):
            print(f"task {task_num}: found it {digest.hex()}")
            return digest
    # print(f'task {task_num}: done')
    return None


async def multi_hash():
    _loop = asyncio.get_event_loop()
    found = False
    s0 = time.time()
    while not found:
        s = time.time()
        tasks = [
            _loop.run_in_executor(process_executor, try_hash, i, 256 * 256)
            for i in range(8)
        ]
        await asyncio.wait(tasks)
        print((time.time() - s) * 1000)
        for t in tasks:
            print(t.result())
            if t.result():
                found = True
                print("FOUND", t.result())
                print((time.time() - s0) * 1000)


if __name__ == "__main__":
    s = time.process_time()
    for i in range(100000000):
        # h = blake2b()
        # h.update(b'718CC2121C3E641059BC1C2CFC456111')
        # h.update(r)
        # h.hexdigest()

        s2 = time.process_time()
        r = os.urandom(8)
        # print((time.process_time() - s2)*1000)
        digest = blake2b_hash(r, b"718CC2121C3E641059BC1C2CFC456111", digest_size=8)[
            ::-1
        ]
        # print((time.process_time() - s2)*1000)
        # print("#")
        if digest >= bytes.fromhex("ffffffc000000000"):
            print("found it")
            print(digest)
            break

    print((time.process_time() - s) * 1000)
