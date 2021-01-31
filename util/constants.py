import asyncio

from models.blocks import OpenBlock
from util.numbers import account_to_public_key

GENESIS_JSON = {
    "type": "open",
    "source": "E89208DD038FBB269987689621D52292AE9C35941A7484756ECCED92A65093BA",
    "representative": "nano_3t6k35gi95xu6tergt6p69ck76ogmitsa8mnijtpxm9fkcm736xtoncuohr3",
    "account": "nano_3t6k35gi95xu6tergt6p69ck76ogmitsa8mnijtpxm9fkcm736xtoncuohr3",
    "work": "62f05417dd3fb691",
    "signature": "9F0C933C8ADE004D808EA1985FA746A7E95BA2A38F867640F53EC8F180BDFE9E2C1268DEAD7C2664F356E37ABA362BC58E46DBA03E523A7B5A19E4B6EB12BB02",
}

# TODO: Use JSON deserializer instead when that is done
GENESIS_BLOCK = OpenBlock(
    source=bytes.fromhex(
        "E89208DD038FBB269987689621D52292AE9C35941A7484756ECCED92A65093BA"
    ),
    representative=account_to_public_key(
        "nano_3t6k35gi95xu6tergt6p69ck76ogmitsa8mnijtpxm9fkcm736xtoncuohr3"
    ),
    account=account_to_public_key(
        "nano_3t6k35gi95xu6tergt6p69ck76ogmitsa8mnijtpxm9fkcm736xtoncuohr3"
    ),
    work=bytes.fromhex("62f05417dd3fb691")[::-1],
    signature=bytes.fromhex(
        "9F0C933C8ADE004D808EA1985FA746A7E95BA2A38F867640F53EC8F180BDFE9E2C1268DEAD7C2664F356E37ABA362BC58E46DBA03E523A7B5A19E4B6EB12BB02"
    ),
)
