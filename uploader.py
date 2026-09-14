from viking_file import VikingClient
from pathlib import Path


def upload_to_vikingfile(file_path: str) -> str | None:
    """Uploads a file to VikingFile anonymously (sync)."""
    try:
        client = VikingClient()  # user_hash خالی = آپلود ناشناس
        uploaded = client.upload_file(filepath=Path(file_path))
        print(f"Uploaded: {uploaded.name}")
        print(f"URL: {uploaded.url}")
        return uploaded.url
    except Exception as e:
        print(f"VikingFile error: {e}")
        return None


def upload_with_rotation(file_path: str) -> tuple[str, str] | None:
    uploaders = [
        ('vikingfile', upload_to_vikingfile),
    ]

    for name, func in uploaders:
        print(f"Trying {name}...")
        url = func(file_path)
        if url:
            print(f"Success via {name}: {url}")
            return url, name

    return None


if __name__ == '__main__':
    result = upload_with_rotation('configs.enc')
    if result:
        url, name = result
        print(f"Uploaded: {url}")
        print(f"Uploader: {name}")
    else:
        print("All uploaders failed.")
