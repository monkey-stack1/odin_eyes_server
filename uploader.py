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

        if response.status_code == 200:
            data = response.json()

            page_url = data.get(
                "data",
                {},
            ).get(
                "url",
                "",
            )

            if not page_url:
                return None

            if not page_url.startswith("http"):
                return None

            return page_url.replace(
                "tmpfiles.org/",
                "tmpfiles.org/dl/",
            )

        print(
            f"Tmpfiles: http={response.status_code} "
            f"body={response.text[:200]}"
        )

    except Exception as e:
        print(f"Tmpfiles error: {e}")

    return None


def upload_to_uupload(file_path: str) -> str | None:
    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                "https://uupload.ir/api/v1/upload/",
                files={"file": f},
                timeout=60,
            )

        if response.status_code == 200:
            data = response.json()

            if data.get("status") == "success":
                url = data.get(
                    "file",
                    {},
                ).get(
                    "url",
                    "",
                )

                if not url:
                    return None

                if not url.startswith("http"):
                    return None

                return url

        print(
            f"Uupload: http={response.status_code} "
            f"body={response.text[:200]}"
        )

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
            print(
                f"Success via {name}: {url}"
            )
            return url, name

        print(f"Failed via {name}")

    print("All uploaders failed.")

    return None


if __name__ == "__main__":
    result = upload_with_rotation(
        "configs.enc"
    )

    if result:
        url, name = result

        print(f"Uploaded: {url}")
        print(f"Uploader: {name}")

    else:
        print("All uploaders failed.")
