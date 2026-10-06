import argparse
import base64
import json
import re
from typing import List, Tuple

import requests


SOURCES: List[Tuple[str, str]] = [
    # TCP
    (
        "matin_super",
        "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/super-sub.txt",
    ),
    # UDP - Hysteria2
    (
        "argh94_hysteria2",
        "https://raw.githubusercontent.com/Argh94/Proxy-List/main/hysteria/Hysteria2.txt",
    ),
    # TCP
    (
        "matin_all",
        "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/all_sub.txt",
    ),
    # UDP - TUIC
    (
        "argh94_tuic",
        "https://raw.githubusercontent.com/Argh94/Proxy-List/main/tuic/Tuic.txt",
    ),
    # TCP
    (
        "miladtahanian",
        "https://raw.githubusercontent.com/miladtahanian/Config-Collector/main/mixed_iran.txt",
    ),
    # UDP - WireGuard 
    (
        "gfpcom_wireguard",
        "https://raw.githubusercontent.com/wiki/gfpcom/free-proxy-list/lists/wireguard.txt",
    ),
    # TCP
    (
        "mohammadaz2_validated",
        "https://raw.githubusercontent.com/mohammadaz2/v2rayConfigsForYou/main/configs.txt",
    ),
    # UDP - Hysteria
    (
        "limilco_hysteria",
        "https://raw.githubusercontent.com/liMilCo/v2r/main/pro/hysteria.txt",
    ),
    # TCP
    (
        "vlesscollector",
        "https://raw.githubusercontent.com/vlesscollector/vlesscollector/refs/heads/main/vless_configs.txt",
    ),
    # UDP - All
    (
        "argh94_all",
        "https://raw.githubusercontent.com/Argh94/Proxy-List/main/All_Config.txt",
    ),
    # TCP
    (
        "solispirit_vless",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Subscriptions/vless.txt",
    ),
    # UDP - Mixed 
    (
        "soroushmirzaei",
        "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/splitted/mixed",
    ),
    # TCP
    (
        "solispirit_trojan",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Subscriptions/trojan.txt",
    ),
    # UDP - All 
    (
        "dukemehdi_all",
        "https://raw.githubusercontent.com/DukeMehdi/FreeList-V2ray-Configs/main/All_Config.txt",
    ),
    # TCP
    (
        "solispirit_ss",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Subscriptions/ss.txt",
    ),
    # TCP
    (
        "mahdibland",
        "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    ),
    # UDP - AnyTLS 
    (
        "itlaohui_anytls",
        "https://raw.githubusercontent.com/itlaohui/aggregator/main/subscribe/anytls.txt",
    ),
    # UDP - WireGuard 
    (
        "rtwo2_wireguard",
        "https://raw.githubusercontent.com/rtwo2/FastNodes/main/wireguard.txt",
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
    "anytls://",
    "wireguard://",
    "wg://",
)


FAMILY_ORDER = (
    "vmess://",
    "hysteria2://",
    "vless://",
    "tuic://",
    "trojan://",
    "anytls://",
    "ss://",
    "wireguard://",
    "hy2://",
    "wg://",
)


URI_PATTERN = re.compile(
    r"(?:vmess|vless|trojan|ss|hysteria2|hy2|hysteria|tuic|anytls|wireguard|wg)://\S+",
    flags=re.IGNORECASE,
)


def _extract_uri_lines(text: str) -> List[str]:
    lines = []

    for line in text.replace("\r", "\n").splitlines():
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

    for prefix in SUPPORTED_PREFIXES:
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

    order = []

    for prefix in FAMILY_ORDER:
        proto = prefix.replace("://", "")

        if proto in buckets and proto not in order:
            order.append(proto)

    for proto in buckets:
        if proto not in order:
            order.append(proto)

    print(f"Round-robin order: {order}")

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


def collect(
    max_configs: int = 0,
    output: str = "",
) -> List[str]:
    print("Fetching configs from configured sources...")

    raw = fetch_configs()
    print(f"Fetched: {len(raw)}")

    unique = deduplicate(raw)
    print(f"Unique: {len(unique)}")

    valid = filter_valid(unique)
    print(f"Valid: {len(valid)}")

    if max_configs > 0 and len(valid) > max_configs:
        valid = select_round_robin(valid, max_configs)
        print(
            f"Selected (round-robin, max={max_configs}): "
            f"{len(valid)}"
        )

    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(
                valid,
                f,
                ensure_ascii=False,
            )

        print(f"Saved {len(valid)} configs to {output}")

    protocol_counts: dict = {}

    for config in valid:
        proto = protocol_of(config)
        protocol_counts[proto] = protocol_counts.get(proto, 0) + 1

    print("Protocol breakdown:")

    for protocol, count in sorted(
        protocol_counts.items(),
        key=lambda x: -x[1],
    ):
        print(f"  {protocol}: {count}")

    return valid


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--max-configs",
        type=int,
        default=0,
        help="Maximum configs to keep (0 = no limit).",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="configs.json",
        help="Output JSON file.",
    )

    args = parser.parse_args()

    collect(
        max_configs=args.max_configs,
        output=args.output,
    )


if __name__ == "__main__":
    main()
