import base64
import json
import re
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple
from urllib.parse import unquote, urlparse
from uuid import UUID


SUPPORTED_PROTOCOLS = (
    "vmess://",
    "vless://",
    "trojan://",
    "ss://",
    "hysteria2://",
    "hy2://",
    "hysteria://",
    "tuic://",
    "anytls://",
)

TCP_PROTOCOLS = (
    "vmess://",
    "vless://",
    "trojan://",
    "ss://",
    "anytls://",
)

UDP_PROTOCOLS = (
    "hysteria2://",
    "hy2://",
    "hysteria://",
    "tuic://",
)

HOST_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")


def _decode_base64_text(value: str) -> Optional[str]:
    try:
        padded = value.strip()
        padded += "=" * (-len(padded) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
        return decoded.decode("utf-8")
    except Exception:
        return None


def _valid_port(value: object) -> bool:
    try:
        port = int(value)
        return 1 <= port <= 65535
    except (TypeError, ValueError):
        return False


def _valid_host(host: object) -> bool:
    if not isinstance(host, str):
        return False

    value = unquote(host).strip()

    if not value or len(value) > 253:
        return False

    if value.lower() in {"localhost", "0.0.0.0"}:
        return False

    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]

    return bool(HOST_PATTERN.fullmatch(value))


def _extract_vmess(config: str) -> Optional[Tuple[str, int]]:
    encoded = config[len("vmess://"):].strip()

    decoded = _decode_base64_text(encoded)
    if not decoded:
        return None

    try:
        data = json.loads(decoded)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(data, dict):
        return None

    host = data.get("add")
    port = data.get("port")

    if not _valid_host(host) or not _valid_port(port):
        return None

    user_id = str(data.get("id", "")).strip()

    try:
        UUID(user_id)
    except (ValueError, AttributeError, TypeError):
        return None

    network = str(data.get("net", "tcp")).strip().lower()
    allowed_networks = {
        "tcp",
        "kcp",
        "ws",
        "http",
        "h2",
        "grpc",
        "quic",
        "splithttp",
        "xhttp",
    }

    if network not in allowed_networks:
        return None

    return str(host), int(port)


def _extract_uri_host_port(config: str) -> Optional[Tuple[str, int]]:
    try:
        parsed = urlparse(config)
    except ValueError:
        return None

    host = parsed.hostname
    port = parsed.port

    if not _valid_host(host) or not _valid_port(port):
        return None

    return str(host), int(port)


def extract_host_port(config: str) -> Tuple[Optional[str], Optional[int]]:
    value = config.strip()
    lower = value.lower()

    if lower.startswith("vmess://"):
        result = _extract_vmess(value)
        if result:
            return result
        return None, None

    if lower.startswith(
        (
            "vless://",
            "trojan://",
            "ss://",
            "anytls://",
            "hysteria2://",
            "hy2://",
            "hysteria://",
            "tuic://",
        )
    ):
        result = _extract_uri_host_port(value)
        if result:
            return result

    return None, None


def _validate_vless(config: str) -> bool:
    try:
        parsed = urlparse(config)
        if parsed.scheme.lower() != "vless":
            return False

        if not parsed.username:
            return False

        try:
            UUID(unquote(parsed.username))
        except (ValueError, AttributeError, TypeError):
            return False

        host = parsed.hostname
        port = parsed.port

        return _valid_host(host) and _valid_port(port)
    except (ValueError, UnicodeError):
        return False


def _validate_trojan(config: str) -> bool:
    try:
        parsed = urlparse(config)
        if parsed.scheme.lower() != "trojan":
            return False

        password = unquote(parsed.username or "")
        host = parsed.hostname
        port = parsed.port

        if not password:
            return False

        return _valid_host(host) and _valid_port(port)
    except (ValueError, UnicodeError):
        return False


def _validate_ss(config: str) -> bool:
    try:
        parsed = urlparse(config)
        if parsed.scheme.lower() != "ss":
            return False

        if not parsed.hostname or not parsed.port:
            return False

        if not _valid_host(parsed.hostname) or not _valid_port(parsed.port):
            return False

        encoded_userinfo = parsed.username
        password = parsed.password

        if encoded_userinfo and password:
            decoded_userinfo = _decode_base64_text(
                unquote(f"{encoded_userinfo}:{password}")
            )
            if not decoded_userinfo:
                return False
            return ":" in decoded_userinfo

        if encoded_userinfo:
            decoded_userinfo = _decode_base64_text(unquote(encoded_userinfo))
            if not decoded_userinfo:
                return False
            return ":" in decoded_userinfo

        return False
    except (ValueError, UnicodeError):
        return False


def _validate_anytls(config: str) -> bool:
    try:
        parsed = urlparse(config)
        if parsed.scheme.lower() != "anytls":
            return False

        host = parsed.hostname
        port = parsed.port

        if not _valid_host(host) or not _valid_port(port):
            return False

        return True
    except (ValueError, UnicodeError):
        return False


def _validate_udp_uri(config: str) -> bool:
    try:
        parsed = urlparse(config)
        scheme = parsed.scheme.lower()

        if scheme not in (
            "hysteria2",
            "hy2",
            "hysteria",
            "tuic",
            "wireguard",
            "wg",
        ):
            return False

        host = parsed.hostname
        port = parsed.port

        if not _valid_host(host) or not _valid_port(port):
            return False

        return True
    except (ValueError, UnicodeError):
        return False


def _is_wireguard_ini(config: str) -> bool:
    lower = config.lower()

    return "[interface]" in lower and "[peer]" in lower


def _valid_wireguard_ini(config: str) -> bool:
    lower = config.lower()

    if "127.0.0.1" in lower or "localhost" in lower:
        return False

    return (
        "privatekey" in lower
        and "publickey" in lower
        and "endpoint" in lower
    )


def is_structurally_valid(config: str) -> bool:
    if not isinstance(config, str):
        return False

    value = config.strip()

    if len(value) < 20 or len(value) > 20000:
        return False

    if _is_wireguard_ini(value):
        return _valid_wireguard_ini(value)

    if not value.lower().startswith(SUPPORTED_PROTOCOLS):
        return False

    if any(
        marker in value.lower()
        for marker in (
            "127.0.0.1",
            "localhost",
            "0.0.0.0",
        )
    ):
        return False

    lower = value.lower()

    if lower.startswith("vmess://"):
        return _extract_vmess(value) is not None

    if lower.startswith("vless://"):
        return _validate_vless(value)

    if lower.startswith("trojan://"):
        return _validate_trojan(value)

    if lower.startswith("ss://"):
        return _validate_ss(value)

    if lower.startswith("anytls://"):
        return _validate_anytls(value)

    if lower.startswith(
        (
            "hysteria2://",
            "hy2://",
            "hysteria://",
            "tuic://",
            "wireguard://",
            "wg://",
        )
    ):
        return _validate_udp_uri(value)

    return False


def is_secure(config: str) -> bool:
    lower = config.lower()

    if _is_wireguard_ini(config):
        return True

    if lower.startswith("ss://"):
        insecure_markers = ("method=none", "method=rc4", "method=des")
        if any(marker in lower for marker in insecure_markers):
            return False

    if any(
        marker in lower
        for marker in (
            "127.0.0.1",
            "localhost",
            "0.0.0.0",
        )
    ):
        return False

    return True


def test_ping(host: str, port: int, timeout: int = 3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ValueError):
        return False


def _is_udp_protocol(config: str) -> bool:
    if _is_wireguard_ini(config):
        return True

    lower = config.lower()
    return lower.startswith(UDP_PROTOCOLS)


def validate_configs(
    configs: List[str],
    max_workers: int = 50,
) -> List[str]:
    print(f"Validating {len(configs)} configs...")

    structural_configs = [
        config
        for config in configs
        if is_structurally_valid(config)
    ]
    print(f"After structural validation: {len(structural_configs)}")

    secure_configs = [
        config
        for config in structural_configs
        if is_secure(config)
    ]
    print(f"After security filter: {len(secure_configs)}")

    valid_configs: List[str] = []

    def check_config(config: str) -> Optional[str]:
        if _is_udp_protocol(config):
            return config

        host, port = extract_host_port(config)

        if not host or not port:
            return None

        if test_ping(host, port):
            return config

        return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(check_config, config): config
            for config in secure_configs
        }

        completed = 0

        for future in as_completed(futures):
            completed += 1

            if completed % 100 == 0:
                print(f"Tested {completed}/{len(secure_configs)}...")

            result = future.result()

            if result:
                valid_configs.append(result)

    print(f"After ping test: {len(valid_configs)}")
    return valid_configs


if __name__ == "__main__":
    with open("configs.json", "r", encoding="utf-8") as file:
        configs = json.load(file)

    valid = validate_configs(configs)

    with open("validated.json", "w", encoding="utf-8") as file:
        json.dump(valid, file, ensure_ascii=False)

    print(f"Saved {len(valid)} validated configs to validated.json")
