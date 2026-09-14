import requests
import base64
import re
import json
from typing import List

SOURCES = [
    "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/super-sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/splitted/mixed",
]


def fetch_configs() -> List[str]:
    all_configs = []
    for source in SOURCES:
        try:
            response = requests.get(source, timeout=15)
            if response.status_code != 200:
                continue
            content = response.text.strip()
            if not content.startswith(('vmess://', 'vless://',
                                       'trojan://', 'ss://')):
                try:
                    content = base64.b64decode(content).decode('utf-8')
                except Exception:
                    pass
            configs = [
                line.strip() for line in content.split('\n')
                if line.strip() and not line.startswith('#')
            ]
            all_configs.extend(configs)
        except Exception as e:
            print(f"Error fetching {source}: {e}")
    return all_configs


def extract_key(config: str) -> str:
    match = re.search(r'@([^:]+):(\d+)', config)
    if match:
        return f"{match.group(1)}:{match.group(2)}"
    if config.startswith('vmess://'):
        try:
            decoded = base64.b64decode(config[8:]).decode('utf-8')
            data = json.loads(decoded)
            return f"{data.get('add')}:{data.get('port')}"
        except Exception:
            pass
    return config[:50]


def deduplicate(configs: List[str]) -> List[str]:
    seen = set()
    unique = []
    for config in configs:
        key = extract_key(config)
        if key and key not in seen:
            seen.add(key)
            unique.append(config)
    return unique


def filter_valid(configs: List[str]) -> List[str]:
    valid = []
    for config in configs:
        if not any(config.startswith(p) for p in [
            'vmess://', 'vless://', 'trojan://', 'ss://'
        ]):
            continue
        if len(config) < 20:
            continue
        valid.append(config)
    return valid


def collect() -> List[str]:
    print("Fetching configs...")
    raw = fetch_configs()
    print(f"Fetched: {len(raw)}")
    unique = deduplicate(raw)
    print(f"Unique: {len(unique)}")
    valid = filter_valid(unique)
    print(f"Valid: {len(valid)}")
    return valid


if __name__ == '__main__':
    configs = collect()
    with open('configs.json', 'w', encoding='utf-8') as f:
        json.dump(configs, f, ensure_ascii=False)
    print(f"Saved {len(configs)} configs to configs.json")
