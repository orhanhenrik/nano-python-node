import lmdb

env = lmdb.Environment("data.ldb", map_size=1024 ** 4, subdir=False, max_dbs=128)


send_db = env.open_db(b"send")
receive_db = env.open_db(b"receive")
open_db = env.open_db(b"open")
change_db = env.open_db(b"change")
blocks_info_db = env.open_db(b"blocks_info")

with env.begin(db=blocks_info_db) as txn:
    cursor = txn.cursor()
    c = 0
    for k, v in cursor:
        c += 1
    print(f"blocks_info had {c} keys")


def iterate_db(txn):
    cursor = txn.cursor()
    c = 0
    for hash, v in cursor:
        block_bytes = v[:-32]
        next_block = v[-32:]
        c += 1
    return c


with env.begin(db=send_db) as txn:
    send_count = iterate_db(txn)
    print(f"got {send_count} send blocks")

with env.begin(db=receive_db) as txn:
    receive_count = iterate_db(txn)
    print(f"got {receive_count} receive blocks")

with env.begin(db=open_db) as txn:
    open_count = iterate_db(txn)
    print(f"got {open_count} open blocks")

with env.begin(db=change_db) as txn:
    change_count = iterate_db(txn)
    print(f"got {change_count} change blocks")
