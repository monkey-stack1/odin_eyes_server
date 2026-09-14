import json
import os
import requests
from datetime import datetime


def update_gist(upload_url: str, uploader_name: str) -> bool:
    """Updates the Gist with the new upload URL."""
    gist_id = os.environ.get('GIST_ID')
    github_token = os.environ.get('GH_TOKEN')

    if not gist_id or not github_token:
        print("Missing GIST_ID or GH_TOKEN environment variables.")
        return False

    content = {
        'current_url': upload_url,
        'uploader': uploader_name,
        'updated_at': datetime.utcnow().isoformat(),
        'version': 1,
    }

    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json',
    }

    data = {
        'files': {
            'odin_eyes.json': {
                'content': json.dumps(content, indent=2),
            }
        }
    }

    response = requests.patch(
        f'https://api.github.com/gists/{gist_id}',
        headers=headers,
        json=data,
        timeout=30,
    )

    return response.status_code == 200


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("Usage: python gist_updater.py <upload_url> <uploader_name>")
        sys.exit(1)

    url = sys.argv[1]
    name = sys.argv[2]
    success = update_gist(url, name)
    print(f"Gist update: {'OK' if success else 'FAILED'}")
