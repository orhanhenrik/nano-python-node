import pytest

from storage.in_memory import InMemoryStorage


@pytest.fixture
def storage():
    return InMemoryStorage()


def test_put_then_get(storage):
    storage.put(b"1", b"a")
    assert storage.get(b"1") == b"a"


def test_bulk_put_get(storage):
    values = {b"a": b"1", b"b": b"2"}
    storage.bulk_put(values)
    for k, v in values.items():
        assert storage.get(k) == v


def test_bulk_put_bulk_get(storage):
    values = {b"a": b"1", b"b": b"2"}
    storage.bulk_put(values)
    res = storage.bulk_get(values.keys())
    assert set(values.items()) == set(res.items())


def test_get_empty(storage):
    assert storage.get(b"1") is None


def test_delete(storage):
    storage.put(b"a", b"1")
    assert storage.get(b"a") == b"1"
    storage.delete(b"a")
    assert storage.get(b"a") is None


def test_delete_nonexistent(storage):
    assert storage.get(b"a") is None
    storage.delete(b"a")
    assert storage.get(b"a") is None


def test_bulk_delete_nonexistent(storage):
    assert storage.get(b"a") is None
    assert storage.get(b"b") is None
    storage.bulk_delete([b"a", b"b"])
    assert storage.get(b"a") is None
    assert storage.get(b"b") is None


def test_bulk_delete(storage):
    storage.put(b"a", b"a")
    storage.put(b"b", b"b")
    assert storage.get(b"a") == b"a"
    assert storage.get(b"b") == b"b"
    storage.bulk_delete([b"a", b"b"])
    assert storage.get(b"a") is None
    assert storage.get(b"b") is None
