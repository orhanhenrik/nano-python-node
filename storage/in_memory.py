from storage.storage import Storage


class InMemoryStorage(Storage):
    def __init__(self, config=None):
        super(InMemoryStorage, self).__init__()
        self.data = {}

    def get(self, key: bytes):
        try:
            return self.data[key]
        except KeyError:
            return None

    def put(self, key: bytes, value: bytes):
        self.data[key] = value

    def delete(self, key: bytes):
        try:
            self.data.pop(key)
        except KeyError:
            pass

