from collector import collect
from validator import validate_configs
from encryptor import encrypt_configs, save_encrypted
from uploader import upload_with_rotation
from gist_updater import update_gist


def main():
    print("=== Odin Eyes Update Pipeline ===")

    # Step 1: Collect configs from GitHub
    configs = collect()
    if not configs:
        print("No configs collected. Aborting.")
        return

    # Step 2: Validate (remove dead and insecure)
    valid_configs = validate_configs(configs)
    if not valid_configs:
        print("No valid configs after validation. Aborting.")
        return

    # Step 3: Encrypt
    encrypted = encrypt_configs(valid_configs)
    save_encrypted(encrypted)
    print(f"Encrypted {len(valid_configs)} configs.")

    # Step 4: Upload with rotation
    result = upload_with_rotation('configs.enc')
    if not result:
        print("Upload failed. Aborting.")
        return

    url, name = result
    print(f"Uploaded to {name}: {url}")

    # Step 5: Update Gist
    success = update_gist(url, name)
    print(f"Gist update: {'OK' if success else 'FAILED'}")


if __name__ == '__main__':
    main()
