import argparse
import base64
import json
import re
from typing import List, Tuple

import requests


SOURCES: List[Tuple[str, str]] = [
    ("matin_super", "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/super-sub.txt"),
    ("argh94_hysteria2", "https://raw.githubusercontent.com/Argh94/Proxy-List/main/hysteria/Hysteria2.txt"),
    ("matin_all", "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/all_sub.txt"),
    ("argh94_tuic", "https://raw.githubusercontent.com/Argh94/Proxy-List/main/tuic/Tuic.txt"),
    ("miladtahanian", "https://raw.githubusercontent.com/miladtahanian/Config-Collector/main/mixed_iran.txt"),
    ("argh94_wireguard", "https://raw.githubusercontent.com/Argh94/Proxy-List/main/wireguard/WireGuard.txt"),
    ("mohammadaz2_validated", "https://raw.githubusercontent.com/mohammadaz2/v2rayConfigsForYou/main/configs.txt"),
    ("argh94_all", "https://raw.githubusercontent.com/Argh94/Proxy-List/main/All_Config.txt"),
    ("vlesscollector", "https://raw.githubusercontent.com/vlesscollector/vlesscollector/refs/heads/main/vless_configs.txt"),
    ("limilco_hysteria", "https://raw.githubusercontent.com/liMilCo/v2r/main/pro/hysteria.txt"),
    ("solispirit_vless", "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Subscriptions/vless.txt"),
    ("solispirit_trojan", "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Subscriptions/trojan.txt"),
    ("solispirit_ss", "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Subscriptions/ss.txt"),
    ("mahdibland", "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt"),
    ("soroushmirzaei", "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/splitted/mixed"),
    ("dukemehdi_all", "https://raw.githubusercontent.com/DukeMehdi/FreeList-V2ray-Configs/main/All_Config.txt"),
]

FAMILY_ORDER = (
    "vmess",
    "hysteria2",
    "vless",
    "tuic",
    "trojan",
    "anytls",
    "ss",
    "wireguard",
)

SUPPORTED_PREFIXES = tuple(f"{family}://" for family in FAMILY_ORDER) + (
    "hy2://",
    "hysteria://",
    "wg://",
)

URI_PATTERN = re.compile(
    r"(?:vmess|vless|trojan|ss|hysteria2|hy2|hysteria|tuic|anytls|wireguard|wg)://\S+",
    flags=re.IGNORECASE,
)


def protocol_of(config: str) -> str:
    lower = config.lower()
    aliases = {
        "hy2://": "hysteria2",
        "hysteria://": "hysteria2",
        "wg://": "wireguard",
    }
    for prefix, family in aliases.items():
        if lower.startswith(prefix):
            return family
    for family in FAMILY_ORDER:
        if lower.startswith(f"{family}://"):
            return family
    return "unknown"


def extract_uri_lines(text: str) -> List[str]:
    lines: List[str] = []
    for line in text.replace("\r", "\n").splitlines():
        value = line.strip().strip(chr(96)).strip()
        if not value or value.startswith("#"):
            continue
        if value.lower().startswith(SUPPORTED_PREFIXES):
            lines.append(value)
            continue
        matches = URI_PATTERN.findall(value)
        lines.extend(match.strip().rstrip(",") for match in matches)
    return lines


def decode_base64_text(text: str) -> str | None:
    compact = "".join(text.split())
    if not compact or len(compact) < 20:
        return None
    padding = "=" * (-len(compact) % 4)
    for decoder in (base64.b64decode, base64.urlsafe_b64decode):
        try:
            decoded = decoder(compact + padding, validate=False)
            result = decoded.decode("utf-8", errors="ignore").strip()
            if result:
                return result
        except Exception:
            continue
    return None


def parse_source_content(content: str) -> List[str]:
    direct = extract_uri_lines(content)
    if direct:
        return direct
    decoded = decode_base64_text(content)
    return extract_uri_lines(decoded) if decoded else []


def fetch_configs() -> List[str]:
    all_configs: List[str] = []
    for name, source in SOURCES:
        try:
            response = requests.get(
                source,
                timeout=20,
                headers={"User-Agent": "OdinEyes-Collector/3.0"},
            )
            response.raise_for_status()
            configs = parse_source_content(response.text)
            print(f"Source {name}: http={response.status_code} configs={len(configs)}")
            all_configs.extend(configs)
        except Exception as exc:
            print(f"Source {name}: ERROR {exc}")
    return all_configs


def deduplicate(configs: List[str]) -> List[str]:
    seen = set()
    unique: List[str] = []
    for config in configs:
        normalized = config.strip().rstrip(",")
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(normalized)
    return unique


def filter_valid(configs: List[str]) -> List[str]:
    return [
        config
        for config in configs
        if len(config) >= 20 and config.lower().startswith(SUPPORTED_PREFIXES)
    ]


def select_round_robin(configs: List[str], max_configs: int) -> List[str]:
    buckets = {family: [] for family in FAMILY_ORDER}
    for config in configs:
        family = protocol_of(config)
        if family in buckets:
            buckets[family].append(config)

    order = [family for family in FAMILY_ORDER if buckets[family]]
    print(f"Round-robin order: {order}")
    print("Round-robin available: " + ", ".join(
        f"{family}={len(buckets[family])}" for family in order
    ))

    selected: List[str] = []
    index = 0
    while len(selected) < max_configs:
        progress = False
        for family in order:
            bucket = buckets[family]
            if index < len(bucket):
                selected.append(bucket[index])
                progress = True
                if len(selected) >= max_configs:
                    break
        if not progress:
            break
        index += 1
    return selected


def collect(max_configs: int = 0, keep_tcp: bool = False) -> List[str]:
    raw = fetch_configs()
    unique = deduplicate(raw)
    valid = filter_valid(unique)

    print(f"Fetched: {len(raw)}")
    print(f"Unique: {len(unique)}")
    print(f"Valid: {len(valid)}")
    print(f"keep_tcp={keep_tcp}")

    if max_configs > 0:
        valid = select_round_robin(valid, max_configs)

    counts = {family: 0 for family in FAMILY_ORDER}
    for config in valid:
        family = protocol_of(config)
        if family in counts:
            counts[family] += 1

    print("Protocol breakdown:")
    for family in FAMILY_ORDER:
        print(f"  {family}: {counts[family]}")

    return valid


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-configs", type=int, default=0)
    parser.add_argument("--keep-tcp", action="store_true")
    parser.add_argument("--output", default="configs.json")
    args = parser.parse_args()

    configs = collect(args.max_configs, args.keep_tcp)
    with open(args.output, "w", encoding="utf-8") as output:
        json.dump(configs, output, ensure_ascii=False)
    print(f"Saved {len(configs)} configs to {args.output}")


if __name__ == "__main__":
    main()
