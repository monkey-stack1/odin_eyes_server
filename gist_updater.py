import json
import os
import sys
from datetime import datetime, timezone

import requests


def update_gist(
    upload_url: str,
    uploader_name: str,
    extra: dict = None,
) -> bool:
    gist_id = os.environ.get("GIST_ID")
    github_token = os.environ.get("GH_TOKEN")

    if not gist_id or not github_token:
        print("Missing GIST_ID or GH_TOKEN environment variables.")
        return False

    content = {
        "current_url": upload_url,
        "uploader": uploader_name,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "version": 1,
    }

    if extra:
        content.update(extra)

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    data = {
        "files": {
            "odin_eyes.json": {
                "content": json.dumps(content, indent=2),
            }
        }
    }

    try:
        response = requests.patch(
            f"https://api.github.com/gists/{gist_id}",
            headers=headers,
            json=data,
            timeout=30,
        )
    except requests.RequestException as exc:
        print(f"Gist update request failed: {exc}")
        return False

    if response.status_code == 200:
        # Do not print the URL: workflow logs on a public repo are world-readable.
        print("Gist update: OK")
        return True

    print(
        f"Gist update FAILED: "
        f"http={response.status_code} "
        f"body={response.text[:300]}"
    )
    return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python gist_updater.py <upload_url> <uploader_name>")
        sys.exit(1)

    url = sys.argv[1]
    name = sys.argv[2]
    success = update_gist(url, name)
    print(f"Gist update: {'OK' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
