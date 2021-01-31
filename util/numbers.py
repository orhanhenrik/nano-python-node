from pure25519_blake2b.ed25519_oop import SigningKey

from util.crypto import blake2b_hash

account_loopup = "13456789abcdefghijkmnopqrstuwxyz"
account_reverse = (
    "~0~1234567~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~89:;<=>?@AB~CDEFGHIJK~LMNO~~~~~"
)


def account_encode(r):
    assert r < 32
    return account_loopup[r]


def account_decode(c: str) -> int:
    return account_loopup.index(c)
    # return ord(account_reverse[c - 0x30]) - 0x30


def public_key_to_account(public_key: bytes) -> str:
    hash = blake2b_hash(public_key, digest_size=5)

    num = int.from_bytes(public_key, byteorder="big")
    num = num << 40
    num = num | int.from_bytes(hash, byteorder="little")

    output = ""
    for i in range(60):
        r = num & 0x1F
        num = num >> 5
        output += account_encode(r)

    output += "_onan"
    return output[::-1]


def account_to_public_key(account: str) -> bytes:
    assert account.startswith("nano_") or account.startswith("xrb_")

    rest = account[5:] if account.startswith("nano_") else account[4:]
    num = 0
    for c in rest:
        # c = ord(c)
        # assert c >= 0x30
        # assert c < 0x80
        byte = account_decode(c)
        num = num << 5
        num += byte

    public_key = (num >> 40).to_bytes(32, byteorder="big")
    sent_hash = (num & 0xFFFFFFFFFF).to_bytes(5, byteorder="little")
    pk_hash = blake2b_hash(public_key, digest_size=5)
    assert sent_hash == pk_hash, "checksum incorrect"

    return public_key


def deterministic_key(seed: bytes, index: int):
    private_key = blake2b_hash(
        seed + index.to_bytes(4, byteorder="big"), digest_size=32
    )
    public_key = SigningKey(private_key).get_verifying_key().to_bytes()
    return private_key, public_key
