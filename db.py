import pickle

import itertools
import rocksdb
import time

def get_rocks_db():
    size = 128*1024*1024
    opts = rocksdb.Options()
    opts.create_if_missing = True
    opts.write_buffer_size = size
    opts.max_write_buffer_number = 3
    opts.target_file_size_base = size
    opts.compression = rocksdb.CompressionType.no_compression
    opts.disable_auto_compactions = True
    opts.table_factory = rocksdb.BlockBasedTableFactory(
        filter_policy=rocksdb.BloomFilterPolicy(10))
    db = rocksdb.DB('rocks.db', opts)
    return db


def test_rocks_db(tuples, batch_write=True, batch_read=False, read_only=False):
    db = get_rocks_db()
    s = time.time()
    if not read_only:
        if batch_write:
            print('batch inserting db records')
            batch = rocksdb.WriteBatch()
            for hash, block in tuples:
                batch.put(hash, block)
            db.write(batch, disable_wal=True)
            e = time.time()
            print(f'batch inserted in {(e-s)*1000}ms')
            s = e
        else:
            print('serial inserting db records')
            for hash, block in tuples:
                db.put(hash, block, disable_wal=False)
            e = time.time()
            print(f'serial inserted in {(e-s)*1000}ms')
            s = e

    if batch_read:
        keys = [key for key,_ in tuples]
        #res = db.multi_get(keys)
        for hash,block in tuples:
            assert db.get(hash) == block
        e = time.time()
        print(f'read in {(e-s)*1000}ms, {(e-s)*1000/len(tuples)}ms per')
        s = e
    else:
        print('serial reading db records')
        for hash,block in tuples:
            assert db.get(hash) == block
        e = time.time()
        print(f'serial read in {(e-s)*1000}ms, {(e-s)*1000/len(tuples)}ms per')
        s = e


def get_tuples(filename='all_chains.dump'):
    s = time.time()
    chains = []
    with open(filename, 'rb') as f:
        chains = pickle.load(f)
    e = time.time()
    print(f'loaded chains in {(e-s)*1000}ms')
    s = e

    blocks = list(itertools.chain.from_iterable(chains))
    e = time.time()
    print(f'transformed chains in {(e-s)*1000}ms')
    s = e

    print(f'{len(chains)} chains, {len(blocks)} blocks')

    tuples = [(block.hash_sync(), block.to_bytes()) for block in blocks]
    e = time.time()
    print(f'calculated hashes in {(e-s)*1000}ms')
    print(f'total size of keys: {sum([len(k) for k,v in tuples])}')
    print(f'total size of values: {sum([len(v) for v in tuples])}')
    s = e

    return tuples

if __name__ == '__main__':

    print('Doing speed test!!')
    #tuples = get_tuples()
    #test_rocks_db(tuples, batch_write=True, batch_read=False)

    db = get_rocks_db()

    limit = 15000
    current = bytes.fromhex('41F8C2A01043703FA7E48E4880632BBCFBC6DA61C0D12355DE174326F29C8485')
    blocks = []
    s = time.time()
    while len(blocks) < limit:
        b = db.get(current)
        blocks.append(b)
        current = b[0:32]
    e = time.time()
    print(f'fetched {limit} blocks in {(e-s)*1000}ms')


