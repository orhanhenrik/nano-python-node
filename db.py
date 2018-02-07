import rocksdb

db = rocksdb.DB('test.db', rocksdb.Options(create_if_missing=True))
