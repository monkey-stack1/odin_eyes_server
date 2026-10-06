# Odin Eyes Server

Collects, validates, encrypts, and publishes configuration lists, then records
the published URL in a GitHub Gist.

## Pipeline

`main.py` runs the whole pipeline in order:

1. `collector.py`    - collect raw configs (`collect`)
2. `validator.py`    - validate them (`validate_configs`)
3. `encryptor.py`    - encrypt (`encrypt_configs`, `save_encrypted`)
4. `uploader.py`     - upload with rotation across hosts (`upload_with_rotation`)
5. `gist_updater.py` - publish `current_url` to the gist (`update_gist`)

## Requirements

```
requests
pycryptodome
viking-file
```

## Configuration (environment / GitHub secrets)

| Name | Purpose |
|---|---|
| `GH_TOKEN` | GitHub token used to update the gist |
| `GIST_ID`  | Target gist id |
| `AES_KEY`  | Encryption key (**required**) |
| `AES_IV`   | Encryption IV (**required**) |
| `MAX_CONFIGS` / `OUTPUT_FILE` / `ENCRYPTED_FILE` | Optional pipeline knobs |

## Automation

`.github/workflows/update.yml` runs hourly, on push to `main`, and manually.
The run **fails fast** if `AES_KEY`/`AES_IV` are not set, so the pipeline never
encrypts with insecure defaults.

## Security notes

- Set `AES_KEY` and `AES_IV` as repository secrets before running.
- The workflow intentionally does **not** upload build artifacts, so collected
  or encrypted data is not exposed.
- Upload URLs are not printed, because workflow logs on a public repository are
  world-readable.
