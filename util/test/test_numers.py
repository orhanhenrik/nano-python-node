from util.numbers import public_key_to_account, account_to_public_key, deterministic_key


def test_pubkey_account_conversion():
    public_key = bytes.fromhex(
        "00002C972CAB7164C44E237AD0AA4A54D110006CA22715D2DB26ED180365E4CB"
    )
    account = "xrb_11117kdkscujem46wautt4o6no8j4118saj94qbfpbqf513pds8dqm4e4cfn"

    assert public_key_to_account(public_key) == account
    assert account_to_public_key(account) == public_key


def test_deterministic_key():
    seed = bytes.fromhex(
        "91C6120B51D2244F912A9F94BF60588712F10151FC57D7F33697D064C91290A8"
    )

    keys0 = (
        bytes.fromhex(
            "74E988A492618A05463233D92A975DBD697FD9EC9C584FACC280C82AB5B8A8D8"
        ),
        bytes.fromhex(
            "6B012D2E8D389D52DAF89FFC38D23279D754B65C700DB0DB20133C8314A84686"
        ),
    )
    assert keys0 == deterministic_key(seed, 0)

    keys9 = (
        bytes.fromhex(
            "16923523074D88994D97F30858E626FA80587B71A10099A0FBC899240F526D5C"
        ),
        bytes.fromhex(
            "A6A1CE1BCE9D5910FD68533431E3B3FA89855ACDB6E8DFA55622C32963CBD4FD"
        ),
    )
    assert keys9 == deterministic_key(seed, 9)
