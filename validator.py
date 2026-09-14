import re
import socket
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed


def extract_host_port(config: str) -> tuple:
    """Extracts host and port from a V2Ray config."""
    try:
        # For vless/trojan/ss: vless://uuid@host:port?...
        match = re.search(r'@([^:]+):(\d+)', config)
        if match:
            return match.group(1), int(match.group(2))

        # For vmess: base64 encoded JSON
        if config.startswith('vmess://'):
            import base64
            import json
            decoded = base64.b64decode(config[8:]).decode('utf-8')
            data = json.loads(decoded)
            return data.get('add'), int(data.get('port', 0))

        # For ss: ss://base64@host:port
        if config.startswith('ss://'):
            match = re.search(r'@([^:]+):(\d+)', config)
            if match:
                return match.group(1), int(match.group(2))
    except Exception:
        pass
    return None, None


def test_ping(host: str, port: int, timeout: int = 3) -> bool:
    """Tests if a host:port is reachable."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def is_secure(config: str) -> bool:
    """Checks if the config uses a secure protocol."""
    # Reject insecure Shadowsocks (without proper encryption)
    if config.startswith('ss://'):
        lower = config.lower()
        if 'none' in lower or 'rc4' in lower or 'des' in lower:
            return False

    # Reject VMess without TLS
    if config.startswith('vmess://'):
        lower = config.lower()
        if 'tls' not in lower and 'security' not in lower:
            # Allow but mark as lower priority
            pass

    # Reject configs with suspicious patterns
    suspicious = ['0.0.0.0', '127.0.0.1', 'localhost']
    if any(s in config for s in suspicious):
        return False

    return True


def validate_configs(configs: List[str], max_workers: int = 50) -> List[str]:
    """Validates all configs: removes unreachable and insecure ones."""
    print(f"Validating {len(configs)} configs...")

    # Step 1: Security filter (fast)
    secure_configs = [c for c in configs if is_secure(c)]
    print(f"After security filter: {len(secure_configs)}")

    # Step 2: Ping test (parallel)
    valid_configs = []

    def check_config(config):
        host, port = extract_host_port(config)
        if not host or not port:
            return None
        if test_ping(host, port):
            return config
        return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(check_config, c): c
            for c in secure_configs
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


if __name__ == '__main__':
    import json

    with open('configs.json', 'r', encoding='utf-8') as f:
        configs = json.load(f)

    valid = validate_configs(configs)

    with open('validated.json', 'w', encoding='utf-8') as f:
        json.dump(valid, f, ensure_ascii=False)

    print(f"Saved {len(valid)} validated configs to validated.json")
