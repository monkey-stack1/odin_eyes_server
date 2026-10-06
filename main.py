import os
import sys

from collector import collect
from validator import validate_configs
from encryptor import encrypt_configs, save_encrypted
from uploader import upload_with_rotation
from gist_updater import update_gist


MAX_CONFIGS = int(os.environ.get("MAX_CONFIGS", "5000"))
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "configs.json")
ENCRYPTED_FILE = os.environ.get("ENCRYPTED_FILE", "configs.enc")


def main() -> int:
    print("=== Odin Eyes Update Pipeline ===")

    print(f"Collecting configs (max={MAX_CONFIGS})...")

    configs = collect(
        max_configs=MAX_CONFIGS,
        output=OUTPUT_FILE,
    )

    if not configs:
        print("No configs collected. Aborting.")
        return 1

    print(f"Collected: {len(configs)}")

    valid_configs = validate_configs(configs)

    if not valid_configs:
        print("No valid configs after validation. Aborting.")
        return 1

    print(f"Valid: {len(valid_configs)}")

    encrypted = encrypt_configs(valid_configs)

    save_encrypted(
        encrypted,
        ENCRYPTED_FILE,
    )

    print(
        f"Encrypted {len(valid_configs)} "
        f"configs to {ENCRYPTED_FILE}."
    )

    result = upload_with_rotation(ENCRYPTED_FILE)

    if not result:
        print("Upload failed. Aborting.")
        return 1

    url, name = result

    print(f"Uploaded to {name}: {url}")

    success = update_gist(url, name)

    if not success:
        print("Gist update FAILED.")
        return 1

    print("Gist update: OK")
    print("=== Pipeline finished successfully ===")

    return 0


if __name__ == "__main__":
    sys.exit(main())
