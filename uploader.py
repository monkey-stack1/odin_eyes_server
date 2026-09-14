from viking_file import VikingClient
from pathlib import Path


def upload_to_vikingfile(file_path: str) -> str | None:
    """Uploads a file to VikingFile and returns the DIRECT download URL."""
    try:
        client = VikingClient()

        # Upload the file
        uploaded = client.upload_file(filepath=Path(file_path))
        print(f"Uploaded hash: {uploaded.hash}")
        print(f"Uploaded name: {uploaded.name}")
        print(f"Page URL: {uploaded.url}")

        # Get file info to find the direct download URL
        file_info = client.get_file(uploaded.hash)
        
        # Try different attributes that might contain the direct URL
        direct_url = None
        if hasattr(file_info, 'download_url') and file_info.download_url:
            direct_url = file_info.download_url
        elif hasattr(file_info, 'url') and file_info.url:
            direct_url = file_info.url
        elif hasattr(file_info, 'direct_url') and file_info.direct_url:
            direct_url = file_info.direct_url
        
        print(f"Direct URL: {direct_url}")
        return direct_url

    except Exception as e:
        print(f"VikingFile error: {e}")
        return None


def upload_with_rotation(file_path: str) -> tuple[str, str] | None:
    """Tries each uploader in order until one succeeds."""
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
