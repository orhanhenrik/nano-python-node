from util.crypto import sign, verify_signature, private_to_public
from util.numbers import deterministic_key


def test_sign_verify():
    priv, pub = deterministic_key(bytes(32), 0)
    msg = b"123"
    sig = sign(msg, priv)
    assert verify_signature(msg, sig, pub)


def test_public_key_derivation():
    # https://github.com/clemahieu/raiblocks/wiki/Design-features#signing-algorithm---ed25519
    priv = bytes.fromhex("0" * 64)
    print(len(priv))
    pub = private_to_public(priv)
    assert pub == bytes.fromhex(
        "19D3D919475DEED4696B5D13018151D1AF88B2BD3BCFF048B45031C1F36D1858"
    )


def test_signature_valid():
    msg = b"U\x00\x95\xad\xd6\xd70\xa9D\x02\xc9\xd2BF\xae\x14\x19\xf5\xd8\n\xa3{8\x99\xfd[\xa5c}\xd0\xc7~"
    signature = b"\xeb\xb5Sv\xee1U\x06X\xab3q.\xd8{\xf5{\xda\x8e\xd1\xa1\xb0\x1a\xeair\x0e\xc6D\x1a\xc5\x08\xb8\xbdk67\xae\x80\xc4s\xd1\\\x91\xabQf\xe3\x18\xd7\xb1??c6\xe4\xa8\x91f^\xc5\x8b\xfe\x07"
    public_key = b"J\xf2\xb8L\xae\xe7\x8c0\xd2\xcaM\xdb\x1fq\xb2E\t\xec[\x06\x19\xe5\xa7\xd7\x90\x9c\x84\x0e\x8d\x84\x9a\x1e"
    assert verify_signature(msg, signature, public_key)
    assert not verify_signature(msg + b"123", signature, public_key)
