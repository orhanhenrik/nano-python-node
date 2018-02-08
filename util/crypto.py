from hashlib import blake2b

from ed25519 import VerifyingKey, BadSignatureError


def verify_pow(data, work):
    # h = blake2b(digest_size=8)
    # h.update(work)
    # h.update(data)
    # digest = h.digest()[::-1]
    digest = blake2b_hash(work, data, digest_size=8)[::-1]
    return digest >= bytes.fromhex('ffffffc000000000')


def verify_signature(hash, signature, public_key):
    print('verifying - not implemented')
    return True
    print('hash', len(hash), hash.hex())
    print('signature', len(signature), signature.hex())
    print('public_key', len(public_key), public_key.hex())
    verifying_key = VerifyingKey(public_key)
    print(verifying_key)
    try:
        verifying_key.verify(signature, hash)
        print("signature is valid!")
    except BadSignatureError:
        print("bad signature :(")
    return True


def blake2b_hash(*values, digest_size=32):
    h = blake2b(digest_size=digest_size)
    for val in values:
        h.update(val)
    return h.digest()


if __name__ == '__main__':
    hash = b'U\x00\x95\xad\xd6\xd70\xa9D\x02\xc9\xd2BF\xae\x14\x19\xf5\xd8\n\xa3{8\x99\xfd[\xa5c}\xd0\xc7~'
    signature = b'\xeb\xb5Sv\xee1U\x06X\xab3q.\xd8{\xf5{\xda\x8e\xd1\xa1\xb0\x1a\xeair\x0e\xc6D\x1a\xc5\x08\xb8\xbdk67\xae\x80\xc4s\xd1\\\x91\xabQf\xe3\x18\xd7\xb1??c6\xe4\xa8\x91f^\xc5\x8b\xfe\x07'
    public_key = b'J\xf2\xb8L\xae\xe7\x8c0\xd2\xcaM\xdb\x1fq\xb2E\t\xec[\x06\x19\xe5\xa7\xd7\x90\x9c\x84\x0e\x8d\x84\x9a\x1e'
    verify_signature(hash, signature, public_key)