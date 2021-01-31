import asyncio
import logging
from asyncio import Queue
from typing import List

from models.block import Block
from storage.storage import Storage


class BlockHandler:
    def __init__(self, storage: Storage):
        self.pow_queue: Queue = Queue()
        self.dep_queue: Queue = Queue()
        self.signature_queue: Queue = Queue()
        self.storage_queue: Queue = Queue()
        self.unresolved_queue: Queue = Queue()

        self.pow_consumer = None
        self.dep_consumer = None
        self.signature_consumer = None

        self.invalid_pow_count = 0
        self.invalid_signature_count = 0

        self.storage = storage

    async def start(self):
        self.pow_consumer: asyncio.Future = asyncio.ensure_future(
            self.consume_pow_queue()
        )
        self.dep_consumer: asyncio.Future = asyncio.ensure_future(
            self.consume_dep_queue()
        )
        self.signature_consumer: asyncio.Future = asyncio.ensure_future(
            self.consume_signature_queue()
        )

    async def stop(self):
        await asyncio.gather(
            self.pow_queue.join(),
            self.storage_queue.join(),
            self.signature_queue.join(),
            # self.storage_queue.join()
        )
        self.pow_consumer.cancel()
        self.dep_consumer.cancel()
        self.signature_consumer.cancel()

    async def handle_block(self, block: Block):
        return await self.pow_queue.put(block)

    async def consume_pow_queue(self):
        while True:
            block: Block = await self.pow_queue.get()
            logging.warning("pow start")
            valid = await block.verify_pow()
            if valid:
                await self.dep_queue.put(block)
            else:
                self.invalid_pow_count += 1
            logging.warning("pow done")
            self.pow_queue.task_done()

    async def consume_dep_queue(self):
        while True:
            block: Block = await self.dep_queue.get()
            logging.warning("dep start")
            deps: List[bytes] = block.dependencies()

            all_exist = all(self.storage.bulk_get(deps).values())

            if all_exist:
                await self.signature_queue.put(block)
            else:
                pass
                # Need to add block to a dependency registry so that it can be processed later
            logging.warning("dep done")
            self.dep_queue.task_done()

    async def consume_signature_queue(self):
        while True:
            block: Block = await self.signature_queue.get()
            logging.warning("sig start")
            valid = await block.verify_signature()
            logging.warning(f"sig valid {valid}")
            if valid:
                await self.storage_queue.put(block)
            else:
                self.invalid_signature_count += 1
            logging.warning("sig done")
            self.signature_queue.task_done()
