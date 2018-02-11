from util.crypto import blake2b_hash

account_loopup = "13456789abcdefghijkmnopqrstuwxyz"
account_reverse = "~0~1234567~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~89:;<=>?@AB~CDEFGHIJK~LMNO~~~~~"


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
        r = num & 0x1f
        num = num >> 5
        output += account_encode(r)

    output += "_brx"
    return output[::-1]


def account_to_public_key(account: str) -> bytes:
    assert account.startswith('xrb_')
    num = 0
    for c in account[4:]:
        # c = ord(c)
        # assert c >= 0x30
        # assert c < 0x80
        byte = account_decode(c)
        num = num << 5
        num += byte

    public_key = (num >> 40).to_bytes(32, byteorder="big")
    sent_hash = (num & 0xffffffffff).to_bytes(5, byteorder="little")
    pk_hash = blake2b_hash(public_key, digest_size=5)
    assert sent_hash == pk_hash, "checksum incorrect"

    return public_key


if __name__ == '__main__':
    public_key = bytes.fromhex('00002C972CAB7164C44E237AD0AA4A54D110006CA22715D2DB26ED180365E4CB')
    account = 'xrb_11117kdkscujem46wautt4o6no8j4118saj94qbfpbqf513pds8dqm4e4cfn'

    print(public_key_to_account(public_key))
    print(account)
    assert public_key_to_account(public_key) == account

    print(account_to_public_key(account).hex())
    print(public_key.hex())
    assert account_to_public_key(account) == public_key

