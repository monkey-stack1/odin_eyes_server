import base64
import json
from datetime import datetime, timezone

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


SECRET_KEY = b"OdinEyes2026Key!"
IV = b"OdinEyesIV2026!!"


def encrypt_configs(configs: list) -> str:
    data = json.dumps(
        {
            "version": 1,
            "updated": datetime.now(timezone.utc).isoformat(),
            "configs": configs,
        },
        ensure_ascii=False,
    )

    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    padded = pad(data.encode("utf-8"), AES.block_size)
    encrypted = cipher.encrypt(padded)

    return base64.b64encode(encrypted).decode("utf-8")


def save_encrypted(encrypted: str, path: str = "configs.enc") -> str:
    with open(path, "w") as f:
        f.write(encrypted)
    return path


if __name__ == "__main__":
    with open("validated.json", "r", encoding="utf-8") as f:
        configs = json.load(f)

    encrypted = encrypt_configs(configs)
    save_encrypted(encrypted)
    print(f"Encrypted {len(configs)} configs to configs.enc")
