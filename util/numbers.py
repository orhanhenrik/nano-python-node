from pure25519_blake2b.ed25519_oop import SigningKey

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


def deterministic_key(seed: bytes, index: int):
    private_key = blake2b_hash(seed+index.to_bytes(4, byteorder="big"), digest_size=32)
    public_key = SigningKey(private_key).get_verifying_key().to_bytes()
    return private_key, public_key


if __name__ == '__main__':
    public_key = bytes.fromhex('00002C972CAB7164C44E237AD0AA4A54D110006CA22715D2DB26ED180365E4CB')
    account = 'xrb_11117kdkscujem46wautt4o6no8j4118saj94qbfpbqf513pds8dqm4e4cfn'

    print(public_key_to_account(public_key))
    print(account)
    assert public_key_to_account(public_key) == account

    print(account_to_public_key(account).hex())
    print(public_key.hex())
    assert account_to_public_key(account) == public_key

    seed = bytes.fromhex('91C6120B51D2244F912A9F94BF60588712F10151FC57D7F33697D064C91290A8')

    keys0 = (bytes.fromhex('74E988A492618A05463233D92A975DBD697FD9EC9C584FACC280C82AB5B8A8D8'), bytes.fromhex('6B012D2E8D389D52DAF89FFC38D23279D754B65C700DB0DB20133C8314A84686'))
    assert keys0 == deterministic_key(seed, 0)

    keys9 = (bytes.fromhex('16923523074D88994D97F30858E626FA80587B71A10099A0FBC899240F526D5C'), bytes.fromhex('A6A1CE1BCE9D5910FD68533431E3B3FA89855ACDB6E8DFA55622C32963CBD4FD'))
    assert keys9 == deterministic_key(seed, 9)
