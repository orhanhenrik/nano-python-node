import asyncio
from concurrent.futures import Executor
from hashlib import blake2b

import time
from pure25519_blake2b.ed25519_oop import VerifyingKey, BadSignatureError, SigningKey

from executors import thread_executor, process_executor


def verify_pow(data: bytes, work: bytes):
    digest = blake2b_hash(work + data, digest_size=8)[::-1]
    return digest >= bytes.fromhex('ffffffc000000000')


async def verify_pow_async(data: bytes, work: bytes, executor: Executor = thread_executor):
    _loop = asyncio.get_event_loop()
    return await _loop.run_in_executor(executor, verify_pow, data, work)


def verify_signature(hash: bytes, signature: bytes, public_key: bytes):
    verifying_key = VerifyingKey(public_key)
    try:
        verifying_key.verify(signature, hash)
        return True
    except BadSignatureError:
        print("bad signature :(")
        return False


# This task is quite slow (atm) - so executing it in a new process is good for performance
async def verify_signature_async(hash: bytes, signature: bytes, public_key: bytes, executor: Executor = process_executor):
    _loop = asyncio.get_event_loop()
    return await _loop.run_in_executor(executor, verify_signature, hash, signature, public_key)


def blake2b_hash(value: bytes, digest_size: int = 32):
    h = blake2b(value, digest_size=digest_size)
    return h.digest()


# Need this because run_in_executor cannot pass kwargs (digest_size) to a function
def _blake2b_hash(value: bytes, digest_size: int):
    return blake2b_hash(value, digest_size)


async def blake2b_async(value: bytes, digest_size: int = 32, executor: Executor = thread_executor):
    _loop = asyncio.get_event_loop()
    return await _loop.run_in_executor(executor, _blake2b_hash, value, digest_size)


if __name__ == '__main__':
    # https://github.com/clemahieu/raiblocks/wiki/Design-features#signing-algorithm---ed25519
    pub = SigningKey(bytes.fromhex(
        '0000000000000000000000000000000000000000000000000000000000000000')).get_verifying_key().to_bytes().hex().upper()
    print('correct public key derivation:', pub == '19D3D919475DEED4696B5D13018151D1AF88B2BD3BCFF048B45031C1F36D1858')

    # Just an example block from the ledger
    hash = b'U\x00\x95\xad\xd6\xd70\xa9D\x02\xc9\xd2BF\xae\x14\x19\xf5\xd8\n\xa3{8\x99\xfd[\xa5c}\xd0\xc7~'
    signature = b'\xeb\xb5Sv\xee1U\x06X\xab3q.\xd8{\xf5{\xda\x8e\xd1\xa1\xb0\x1a\xeair\x0e\xc6D\x1a\xc5\x08\xb8\xbdk67\xae\x80\xc4s\xd1\\\x91\xabQf\xe3\x18\xd7\xb1??c6\xe4\xa8\x91f^\xc5\x8b\xfe\x07'
    public_key = b'J\xf2\xb8L\xae\xe7\x8c0\xd2\xcaM\xdb\x1fq\xb2E\t\xec[\x06\x19\xe5\xa7\xd7\x90\x9c\x84\x0e\x8d\x84\x9a\x1e'
    t = time.process_time()
    valid = verify_signature(hash, signature, public_key)
    print(f'signature validation took {(time.process_time()-t)*1000}ms')
    print("signature valid:", valid)
    assert valid, "Valid signature failed"
    assert not verify_signature(hash+b'x', signature, public_key), "Invalid signature was not caught.."
