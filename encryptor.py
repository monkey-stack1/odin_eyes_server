import base64
import json
import os
from datetime import datetime, timezone
from typing import List

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


DEFAULT_KEY = b"OdinEyes2026Key!"
DEFAULT_IV = b"OdinEyesIV2026!!"


def _load_key(name: str, default: bytes) -> bytes:
    value = os.environ.get(name)

    if not value:
        print(
            f"Warning: {name} not set, "
            f"using default (insecure)."
        )
        return default

    encoded = value.encode("utf-8")

    if len(encoded) != 16:
        raise ValueError(
            f"{name} must be exactly 16 bytes, "
            f"got {len(encoded)}"
        )

    return encoded


def _get_key() -> bytes:
    return _load_key("AES_KEY", DEFAULT_KEY)


def _get_iv() -> bytes:
    return _load_key("AES_IV", DEFAULT_IV)


def encrypt_configs(configs: List[str]) -> str:
    data = json.dumps(
        {
            "version": 1,
            "updated": datetime.now(timezone.utc).isoformat(),
            "configs": configs,
        },
        ensure_ascii=False,
    )

    cipher = AES.new(
        _get_key(),
        AES.MODE_CBC,
        _get_iv(),
    )

    padded = pad(
        data.encode("utf-8"),
        AES.block_size,
    )

    encrypted = cipher.encrypt(padded)

    return base64.b64encode(encrypted).decode("utf-8")


def save_encrypted(
    encrypted: str,
    path: str = "configs.enc",
) -> str:
    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:
        f.write(encrypted)

    return path


if __name__ == "__main__":
    with open(
        "validated.json",
        "r",
        encoding="utf-8",
    ) as f:
        configs = json.load(f)

    encrypted = encrypt_configs(configs)

    save_encrypted(encrypted)

    print(
        f"Encrypted {len(configs)} "
        f"configs to configs.enc"
    )
