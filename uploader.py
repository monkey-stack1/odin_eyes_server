import requests

# ============================================================
# 1. CATBOX (Anonymous, Permanent, Direct Link)
# ============================================================
def upload_to_catbox(file_path: str) -> str | None:
    try:
        with open(file_path, 'rb') as f:
            response = requests.post(
                'https://catbox.moe/user/api.php',
                data={'reqtype': 'fileupload'},
                files={'fileToUpload': f},
                timeout=60,
            )
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        print(f"Catbox error: {e}")
    return None


# ============================================================
# 2. 0x0.ST (Anonymous, Direct Link, 30 days)
# ============================================================
def upload_to_0x0(file_path: str) -> str | None:
    try:
        with open(file_path, 'rb') as f:
            response = requests.post(
                'https://0x0.st',
                files={'file': f},
                timeout=60,
            )
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        print(f"0x0 error: {e}")
    return None


# ============================================================
# 3. UGUU (Anonymous, Temporary, Direct Link)
# ============================================================
def upload_to_uguu(file_path: str) -> str | None:
    try:
        with open(file_path, 'rb') as f:
            response = requests.post(
                'https://uguu.se/upload',
                files={'files[]': f},
                timeout=60,
            )
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('files'):
                return data['files'][0].get('url')
    except Exception as e:
        print(f"Uguu error: {e}")
    return None


# ============================================================
# 4. TMPFILES.ORG (Anonymous, Temporary, Direct Link)
# ============================================================
def upload_to_tmpfiles(file_path: str) -> str | None:
    try:
        with open(file_path, 'rb') as f:
            response = requests.post(
                'https://tmpfiles.org/api/v1/upload',
                files={'file': f},
                timeout=60,
            )
        if response.status_code == 200:
            data = response.json()
            # Convert to direct link
            page_url = data.get('data', {}).get('url', '')
            if page_url:
                return page_url.replace('tmpfiles.org/', 'tmpfiles.org/dl/')
    except Exception as e:
        print(f"Tmpfiles error: {e}")
    return None


# ============================================================
# 5. UPLOAD.IR (Iranian, Anonymous, Direct Link)
# ============================================================
def upload_to_uupload(file_path: str) -> str | None:
    try:
        with open(file_path, 'rb') as f:
            response = requests.post(
                'https://uupload.ir/api/v1/upload/',
                files={'file': f},
                timeout=60,
            )
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return data.get('file', {}).get('url')
    except Exception as e:
        print(f"Uupload error: {e}")
    return None


# ============================================================
# ROTATION LOGIC
# ============================================================
def upload_with_rotation(file_path: str) -> tuple[str, str] | None:
    """Tries each uploader in order until one succeeds."""
    uploaders = [
        ('catbox', upload_to_catbox),
        ('0x0', upload_to_0x0),
        ('uguu', upload_to_uguu),
        ('tmpfiles', upload_to_tmpfiles),
        ('uupload', upload_to_uupload),
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
