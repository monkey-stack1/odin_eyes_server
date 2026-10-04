import argparse
import base64
import json
import re
from typing import List, Tuple

import requests


SOURCES: List[Tuple[str, str]] = [
    (
        "matin_super",
        "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/"
        "main/subscriptions/v2ray/super-sub.txt",
    ),
    (
        "matin_all",
        "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/"
        "main/subscriptions/v2ray/all_sub.txt",
    ),
    (
        "miladtahanian",
        "https://raw.githubusercontent.com/miladtahanian/"
        "Config-Collector/main/mixed_iran.txt",
    ),
    (
        "mohammadaz2_validated",
        "https://raw.githubusercontent.com/mohammadaz2/"
        "v2rayConfigsForYou/main/configs.txt",
    ),
    (
        "vlesscollector",
        "https://raw.githubusercontent.com/vlesscollector/"
        "vlesscollector/refs/heads/main/vless_configs.txt",
    ),
    (
        "solispirit_vless",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/"
        "main/Subscriptions/vless.txt",
    ),
    (
        "solispirit_trojan",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/"
        "main/Subscriptions/trojan.txt",
    ),
    (
        "solispirit_ss",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/"
        "main/Subscriptions/ss.txt",
    ),
    (
        "mahdibland",
        "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/"
        "master/sub/sub_merge.txt",
    ),
    (
        "soroushmirzaei",
        "https://raw.githubusercontent.com/soroushmirzaei/"
        "telegram-configs-collector/main/splitted/mixed",
    ),
    (
        "argh94_hysteria2",
        "https://raw.githubusercontent.com/Argh94/Proxy-List/"
        "main/hysteria/Hysteria2.txt",
    ),
    (
        "argh94_tuic",
        "https://raw.githubusercontent.com/Argh94/Proxy-List/"
        "main/tuic/Tuic.txt",
    ),
    (
        "argh94_all",
        "https://raw.githubusercontent.com/Argh94/Proxy-List/"
        "main/All_Config.txt",
    ),
    (
        "limilco_hysteria",
        "https://raw.githubusercontent.com/liMilCo/v2r/"
        "main/pro/hysteria.txt",
    ),
    (
        "dukemehdi_all",
        "https://raw.githubusercontent.com/DukeMehdi/"
        "FreeList-V2ray-Configs/main/All_Config.txt",
    ),
    (
        "argh94_wireguard",
        "https://raw.githubusercontent.com/Argh94/Proxy-List/"
        "main/wireguard/WireGuard.txt",
    ),
]

SUPPORTED_PREFIXES = (
    "vmess://",
    "vless://",
    "trojan://",
    "ss://",
    "hysteria2://",
    "hy2://",
    "hysteria://",
    "tuic://",
    "wireguard://",
    "wg://",
)

# TCP first, UDP second (TCP is proven; UDP is experimental)
FAMILY_ORDER = (
    "vmess://",
    "vless://",
    "trojan://",
    "ss://",
    "hysteria2://",
    "hy2://",
    "tuic://",
    "wireguard://",
    "wg://",
)

URI_PATTERN = re.compile(
    r"(?:vmess|vless|trojan|ss|hysteria2|hy2|hysteria|tuic|wireguard|wg)://\S+",
    flags=re.IGNORECASE,
)


def _extract_uri_lines(text: str) -> List[str]:
    lines = []
    for line in text.replace("\\r", "\\n").splitlines():
        value = line.strip().strip("`").strip()
        if not value or value.startswith("#"):
            continue

        if value.lower().startswith(SUPPORTED_PREFIXES):
            lines.append(value)
            continue

        matches = URI_PATTERN.findall(value)
        lines.extend(match.strip().rstrip(",") for match in matches)

    return lines


def _decode_base64_text(text: str) -> str | None:
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


def _parse_source_content(content: str) -> List[str]:
    direct = _extract_uri_lines(content)

    if direct:
        return direct

    decoded = _decode_base64_text(content)

    if decoded:
        parsed = _extract_uri_lines(decoded)
        if parsed:
            return parsed

    return []


def fetch_configs() -> List[str]:
    all_configs: List[str] = []

    for name, source in SOURCES:
        try:
            response = requests.get(
                source,
                timeout=20,
                headers={"User-Agent": "OdinEyes-Collector/2.0"},
            )
            response.raise_for_status()

            configs = _parse_source_content(response.text)

            print(
                f"Source {name}: "
                f"http={response.status_code} "
                f"configs={len(configs)}"
            )

            all_configs.extend(configs)
        except Exception as exc:
            print(f"Source {name}: ERROR {exc}")

    return all_configs


def _canonicalize(config: str) -> str:
    return config.strip().rstrip(",")


def deduplicate(configs: List[str]) -> List[str]:
    seen = set()
    unique: List[str] = []

    for config in configs:
        normalized = _canonicalize(config)

        if not normalized:
            continue

        key = normalized.lower()

        if key in seen:
            continue

        seen.add(key)
        unique.append(normalized)

    return unique


def filter_valid(configs: List[str]) -> List[str]:
    valid: List[str] = []

    for config in configs:
        lower = config.lower()

        if not lower.startswith(SUPPORTED_PREFIXES):
            continue

        if len(config) < 20:
            continue

        valid.append(config)

    return valid


def protocol_of(config: str) -> str:
    lower = config.lower()
    for prefix in FAMILY_ORDER:
        if lower.startswith(prefix):
            return prefix.replace("://", "")
    return "unknown"


def select_round_robin(
    configs: List[str],
    max_configs: int,
) -> List[str]:
    buckets: dict = {}
    for config in configs:
        proto = protocol_of(config)
        buckets.setdefault(proto, []).append(config)

    order = [p.replace("://", "") for p in FAMILY_ORDER]
    order.append("unknown")
    for proto in buckets:
        if proto not in order:
            order.append(proto)

    selected: List[str] = []
    index = 0
    while len(selected) < max_configs:
        progress = False
        for proto in order:
            bucket = buckets.get(proto, [])
            if index < len(bucket):
                selected.append(bucket[index])
                progress = True
                if len(selected) >= max_configs:
                    break
        if not progress:
            break
        index += 1

    return selected


def collect(max_configs: int = 0) -> List[str]:
    print("Fetching configs from configured sources...")

    raw = fetch_configs()
    print(f"Fetched: {len(raw)}")

    unique = deduplicate(raw)
    print(f"Unique: {len(unique)}")

    valid = filter_valid(unique)
    print(f"Valid: {len(valid)}")

    if max_configs > 0 and len(valid) > max_configs:
        valid = select_round_robin(valid, max_configs)
        print(f"Selected (round-robin, max={max_configs}): {len(valid)}")

    protocol_counts: dict = {}
    for config in valid:
        proto = protocol_of(config)
        protocol_counts[proto] = protocol_counts.get(proto, 0) + 1

    print("Protocol breakdown:")
    for protocol, count in sorted(
        protocol_counts.items(), key=lambda x: -x[1]
    ):
        print(f"  {protocol}: {count}")

    return valid


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max-configs",
        type=int,
        default=0,
        help="Maximum configs to keep (0 = no limit). TCP first, round-robin.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="configs.json",
        help="Output JSON file.",
    )
    args = parser.parse_args()

    configs = collect(max_configs=args.max_configs)

    with open(args.output, "w", encoding="utf-8") as output:
        json.dump(configs, output, ensure_ascii=False)

    print(f"Saved {len(configs)} configs to {args.output}")


if __name__ == "__main__":
    main()
