from typing import List, Dict


class Storage:
    def __init__(self, config=None):
        pass

    def get(self, key: bytes) -> bytes:
        pass

    def put(self, key: bytes, value: bytes):
        pass

    def delete(self, key: bytes):
        pass

    def bulk_get(self, keys: List[bytes]) -> Dict[bytes, bytes]:
        output: Dict[bytes, bytes] = {}
        for key in keys:
            output[key] = self.get(key)
        return output

    def bulk_put(self, kv: Dict[bytes, bytes]):
        for key, value in kv.items():
            self.put(key, value)

    def bulk_delete(self, keys: List[bytes]):
        for key in keys:
            self.delete(key)
