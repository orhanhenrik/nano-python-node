import itertools

import marshal
import rocksdb
import time
import lmdb

from models.blocks import BlockParser, BlockType


def get_rocks_db():
    size = 128 * 1024 * 1024
    opts = rocksdb.Options()
    opts.create_if_missing = True
    opts.write_buffer_size = size
    opts.max_write_buffer_number = 2
    opts.target_file_size_base = size
    opts.compression = rocksdb.CompressionType.no_compression
    opts.disable_auto_compactions = True
    opts.table_factory = rocksdb.BlockBasedTableFactory(
        block_size=512,
        filter_policy=rocksdb.BloomFilterPolicy(10),
        block_cache=rocksdb.LRUCache(2 * (1024 ** 3)),
        block_cache_compressed=rocksdb.LRUCache(500 * (1024 ** 2)),
    )
    db = rocksdb.DB("rocks.db", opts)
    return db


def test_rocks_db(tuples, batch_write=True, batch_read=False, read_only=False):
    db = get_rocks_db()
    s = time.time()
    if not read_only:
        if batch_write:
            print("batch inserting db records")
            batch = rocksdb.WriteBatch()
            for hash, block in tuples:
                batch.put(hash, block)
            db.write(batch, disable_wal=True)
            e = time.time()
            print(f"batch inserted in {(e-s)*1000}ms, {(e-s)*1000/len(tuples)}ms per")
            s = e
        else:
            print("serial inserting db records")
            for hash, block in tuples:
                db.put(hash, block, disable_wal=False)
            e = time.time()
            print(f"serial inserted in {(e-s)*1000}ms, {(e-s)*1000/len(tuples)}ms per")
            s = e

    if batch_read:
        keys = [key for key, _ in tuples]
        # res = db.multi_get(keys)
        for hash, block in tuples:
            assert db.get(hash) == block
        e = time.time()
        print(f"read in {(e-s)*1000}ms, {(e-s)*1000/len(tuples)}ms per")
        s = e
    else:
        print("serial reading db records")
        for hash, block in tuples:
            assert db.get(hash) == block
        e = time.time()
        print(f"serial read in {(e-s)*1000}ms, {(e-s)*1000/len(tuples)}ms per")
        s = e


def get_hash(block):
    b = BlockParser.parse(BlockType(block[0]), block[1:])
    return b.hash_sync()


def get_tuples(filename="marshal_chains.dump"):
    s = time.time()
    chains = []
    with open(filename, "rb") as f:
        chains = marshal.load(f)
    e = time.time()
    print(f"loaded chains in {(e-s)*1000}ms")
    s = e

    blocks = list(itertools.chain.from_iterable(chains))
    e = time.time()
    print(f"transformed chains in {(e-s)*1000}ms")
    s = e

    print(f"{len(chains)} chains, {len(blocks)} blocks")

    tuples = [(get_hash(block), block[1:]) for block in blocks]
    e = time.time()
    print(f"calculated hashes in {(e-s)*1000}ms")
    print(f"total size of keys: {sum([len(k) for k,v in tuples])}")
    print(f"total size of values: {sum([len(v) for v in tuples])}")
    s = e

    return tuples


def load_rocks():
    tuples = get_tuples()
    test_rocks_db(tuples, batch_write=True, batch_read=False)


def test_load_chain_rocks():
    db = get_rocks_db()

    limit = 1500000
    times = []
    for i in range(10):
        current = bytes.fromhex(
            "41F8C2A01043703FA7E48E4880632BBCFBC6DA61C0D12355DE174326F29C8485"
        )
        s = time.time()
        blocks = []
        while len(blocks) < limit:
            b = db.get(current)
            if b is None:
                break
            blocks.append(b)
            current = b[0:32]
        e = time.time()
        print(f"fetched {len(blocks)} blocks in {(e-s)*1000}ms")
        times.append((e - s) * 1000)
    print(sum(times) / len(times))


# RESULTS

# Size=128MB
# Block_size=512B
# Avg 145ms

# Size=64MB
# Block_size=512B
# Avg 950ms

# Size=256MB
# Block_size=512B
# Avg 165ms


def get_lmdb():
    map_size = 2 * 1024 * 1024 * 1024  # 2GB
    env = lmdb.Environment(
        "lm.db",
        metasync=False,
        map_async=True,
        writemap=True,
        lock=False,
        map_size=map_size,
    )
    return env


def load_lmdb():
    tuples = get_tuples()
    env = get_lmdb()
    s = time.time()
    with env.begin(write=True) as txn:
        for hash, block in tuples:
            txn.put(hash, block)
    e = time.time()
    print(f"serial inserted in {(e-s)*1000}ms, {(e-s)*1000/len(tuples)}ms per")

    s = time.time()
    with env.begin() as txn:
        for hash, block in tuples:
            assert txn.get(hash) == block
    e = time.time()
    print(f"serial read in {(e-s)*1000}ms, {(e-s)*1000/len(tuples)}ms per")


def test_load_chain_lmdb():
    env = get_lmdb()
    limit = 1500000
    times = []
    for i in range(10):
        current = bytes.fromhex(
            "41F8C2A01043703FA7E48E4880632BBCFBC6DA61C0D12355DE174326F29C8485"
        )
        s = time.time()
        blocks = []
        with env.begin(buffers=True) as txn:
            while len(blocks) < limit:
                b = txn.get(current)
                if b is None or len(b) == 0:
                    break
                blocks.append(b)
                current = b[0:32]
        e = time.time()
        print(f"fetched {len(blocks)} blocks in {(e-s)*1000}ms")
        times.append((e - s) * 1000)
    print(sum(times) / len(times))


def test_load_chain_memory():
    print("loading data dump file")
    tuples = get_tuples()
    block_dict = {}
    for k, v in tuples:
        block_dict[k] = v

    print("finished setup. Starting speed test")
    limit = 1500000
    times = []
    for i in range(10):
        current = bytes.fromhex(
            "41F8C2A01043703FA7E48E4880632BBCFBC6DA61C0D12355DE174326F29C8485"
        )
        s = time.time()
        blocks = []
        while len(blocks) < limit:
            b = block_dict.get(current)
            if b is None or len(b) == 0:
                break
            blocks.append(b)
            current = b[0:32]
        e = time.time()
        print(f"fetched {len(blocks)} blocks in {(e-s)*1000}ms")
        times.append((e - s) * 1000)
    print(sum(times) / len(times))


if __name__ == "__main__":
    print("Doing speed test!!")
    # load_lmdb()
    # test_load_chain_lmdb()
    test_load_chain_rocks()
    # test_load_chain_memory()
