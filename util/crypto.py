import asyncio
import functools
import logging
from concurrent.futures import Executor
from hashlib import blake2b

import time
from pure25519_blake2b.ed25519_oop import VerifyingKey, BadSignatureError, SigningKey

from executors import thread_executor, process_executor


def verify_pow(data: bytes, work: bytes):
    digest = blake2b_hash(work + data, digest_size=8)[::-1]
    return digest >= bytes.fromhex("ffffffc000000000")


async def verify_pow_async(
    data: bytes, work: bytes, executor: Executor = thread_executor
):
    _loop = asyncio.get_event_loop()
    return await _loop.run_in_executor(executor, verify_pow, data, work)


def verify_signature(msg: bytes, signature: bytes, public_key: bytes):
    verifying_key = VerifyingKey(public_key)
    try:
        verifying_key.verify(signature, msg)
        return True
    except BadSignatureError:
        print("bad signature :(")
        return False


def sign(msg: bytes, private_key: bytes):
    sk = SigningKey(private_key)
    return sk.sign(msg)


# This task is quite slow (atm) - so executing it in a new process is good for performance
async def verify_signature_async(
    hash: bytes,
    signature: bytes,
    public_key: bytes,
    executor: Executor = process_executor,
):
    # return verify_signature(hash, signature, public_key)
    _loop = asyncio.get_event_loop()
    logging.warning("sig start")
    res = await _loop.run_in_executor(
        executor, verify_signature, hash, signature, public_key
    )
    logging.warning("sig done " + str(res))
    return res


def blake2b_hash(value: bytes, digest_size: int = 32):
    h = blake2b(value, digest_size=digest_size)
    return h.digest()


# Need this because run_in_executor cannot pass kwargs (digest_size) to a function
def _blake2b_hash(value: bytes, digest_size: int):
    return blake2b_hash(value, digest_size)


async def blake2b_async(
    value: bytes, digest_size: int = 32, executor: Executor = thread_executor
):
    # return blake2b_hash(value, digest_size = digest_size)
    _loop = asyncio.get_event_loop()
    logging.warning("hash start")
    res = await _loop.run_in_executor(
        executor, functools.partial(blake2b_hash, value, digest_size=digest_size)
    )
    logging.warning("hash done " + res.hex())
    return res


def private_to_public(private: bytes) -> bytes:
    return SigningKey(private).get_verifying_key().to_bytes()
