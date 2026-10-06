import re

import requests


def upload_to_catbox(file_path: str) -> str | None:
    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": f},
                timeout=60,
            )

        if response.status_code == 200:
            url = response.text.strip()

            if url.startswith("http"):
                return url

            print(f"Catbox: invalid URL {url[:200]}")
            return None

        print(
            f"Catbox: http={response.status_code} "
            f"body={response.text[:200]}"
        )

    except Exception as e:
        print(f"Catbox error: {e}")

    return None


def upload_to_0x0(file_path: str) -> str | None:
    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                "https://0x0.st",
                files={"file": f},
                timeout=60,
            )

        if response.status_code == 200:
            url = response.text.strip()

            if url.startswith("http"):
                return url

            print(f"0x0: invalid URL {url[:200]}")
            return None

        print(
            f"0x0: http={response.status_code} "
            f"body={response.text[:200]}"
        )

    except Exception as e:
        print(f"0x0 error: {e}")

    return None


def upload_to_tmpfiles(file_path: str) -> str | None:
    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files={"file": f},
                timeout=60,
            )

        if response.status_code != 200:
            print(
                f"Tmpfiles: http={response.status_code} "
                f"body={response.text[:200]}"
            )
            return None

        data = response.json()
        page_url = data.get("data", {}).get("url", "")

        if not page_url:
            print(f"Tmpfiles: empty page_url in {data}")
            return None

        if not page_url.startswith("http"):
            print(f"Tmpfiles: invalid page_url {page_url[:200]}")
            return None

        direct = _tmpfiles_direct_url(page_url)

        if not direct:
            print(f"Tmpfiles: could not resolve direct URL from {page_url}")
            return None

        return direct

    except Exception as e:
        print(f"Tmpfiles error: {e}")

    return None


def _tmpfiles_direct_url(page_url: str) -> str | None:
    """Resolve the real direct-download link from the tmpfiles page.

    https://tmpfiles.org/<id>/<name> redirects /dl/ back to the HTML page, so
    the usable link is the one embedded in the page markup.
    """
    try:
        page = requests.get(page_url, timeout=30)

        match = re.search(
            r'href="(https://tmpfiles\.org/dl/[^"]+)"',
            page.text,
        )

        if match:
            return match.group(1)

        matches = re.findall(
            r"https://tmpfiles\.org/dl/[^\s\"'<>]+",
            page.text,
        )

        if matches:
            return matches[0]

    except Exception as e:
        print(f"Tmpfiles resolve error: {e}")

    return None


def upload_to_uupload(file_path: str) -> str | None:
    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                "https://uupload.ir/api/v1/upload/",
                files={"file": f},
                timeout=60,
            )

        if response.status_code != 200:
            print(
                f"Uupload: http={response.status_code} "
                f"body={response.text[:200]}"
            )
            return None

        data = response.json()

        if data.get("status") != "success":
            print(f"Uupload: status={data.get('status')} body={data}")
            return None

        url = data.get("file", {}).get("url", "")

        if not url:
            print(f"Uupload: empty url in {data}")
            return None

        if not url.startswith("http"):
            print(f"Uupload: invalid url {url[:200]}")
            return None

        return url

    except Exception as e:
        print(f"Uupload error: {e}")

    return None


UPLOADERS = [
    ("catbox", upload_to_catbox),
    ("0x0", upload_to_0x0),
    ("tmpfiles", upload_to_tmpfiles),
    ("uupload", upload_to_uupload),
]


def upload_with_rotation(
    file_path: str,
) -> tuple[str, str] | None:
    for name, func in UPLOADERS:
        print(f"Trying {name}...")

        url = func(file_path)

        if url:
            # Do not print the URL: workflow logs on a public repo are world-readable.
            print(f"Success via {name}")
            return url, name

        print(f"Failed via {name}")

    print("All uploaders failed.")
    return None


if __name__ == "__main__":
    result = upload_with_rotation("configs.enc")

    if result:
        url, name = result
        print("Uploaded")
        print(f"Uploader: {name}")
    else:
        print("All uploaders failed.")
