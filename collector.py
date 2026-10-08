import argparse
import base64
import json
import os
import re
from typing import List, Tuple

import requests


SOURCES: List[Tuple[str, str]] = [
    # TCP aggregators
    (
        "matin_super",
        "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/super-sub.txt",
    ),
    (
        "matin_all",
        "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/all_sub.txt",
    ),
    (
        "miladtahanian",
        "https://raw.githubusercontent.com/miladtahanian/Config-Collector/main/mixed_iran.txt",
    ),
    (
        "mohammadaz2_validated",
        "https://raw.githubusercontent.com/mohammadaz2/v2rayConfigsForYou/main/configs.txt",
    ),
    (
        "vlesscollector",
        "https://raw.githubusercontent.com/vlesscollector/vlesscollector/refs/heads/main/vless_configs.txt",
    ),
    (
        "mahdibland",
        "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    ),
    (
        "epodonios_all",
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
    ),
    # Per-protocol (SoliSpirit: Protocols/)
    (
        "solispirit_vless",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Protocols/vless.txt",
    ),
    (
        "solispirit_trojan",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Protocols/trojan.txt",
    ),
    (
        "solispirit_ss",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Protocols/ss.txt",
    ),
    # Mixed / all
    (
        "dukemehdi_all",
        "https://raw.githubusercontent.com/DukeMehdi/FreeList-V2ray-Configs/main/Configs/All-DukeMehdi-Configs.txt",
    ),
    (
        "argh94_all",
        "https://raw.githubusercontent.com/Argh94/Proxy-List/main/All_Config.txt",
    ),
    # New TCP aggregators (vless+reality, ss, xhttp)
    (
        "aliilapro",
        "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server.txt",
    ),
    (
        "barryfar",
        "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/All_Configs_Sub.txt",
    ),
    (
        "epodonios_spl_vless",
        "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/vless.txt",
    ),
    # Near-Iran countries (low latency, gaming)
    (
        "country_turkiye",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Countries/T%C3%BCrkiye.txt",
    ),
    (
        "country_uae",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Countries/United_Arab_Emirates.txt",
    ),
    (
        "country_armenia",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Countries/Armenia.txt",
    ),
    (
        "country_azerbaijan",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Countries/Azerbaijan.txt",
    ),
    (
        "country_saudi",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Countries/Saudi_Arabia.txt",
    ),
    (
        "country_bahrain",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Countries/Bahrain.txt",
    ),
    (
        "country_iraq",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Countries/Iraq.txt",
    ),
    (
        "country_cyprus",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Countries/Cyprus.txt",
    ),
    (
        "country_kazakhstan",
        "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/Countries/Kazakhstan.txt",
    ),
]


# WireGuard is published as INI configs ([Interface]/[Peer]), not as URIs.
# Each entry is (owner/repo, directory) whose *.conf files are merged.
WIREGUARD_DIRS: List[Tuple[str, str]] = [
    ("rtwo2/FastNodes", "sub/wireguard"),
]


SUPPORTED_PREFIXES = (
    "vmess://",
    "vless://",
    "trojan://",
    "ss://",
)


FAMILY_ORDER = (
    "vmess://",
    "vless://",
    "trojan://",
    "ss://",
)


URI_PATTERN = re.compile(
    r"(?:vmess|vless|trojan|ss)://\S+",
    flags=re.IGNORECASE,
)


def _is_wireguard_block(text: str) -> bool:
    lower = text.lower()

    return "[interface]" in lower and "[peer]" in lower


def _extract_wireguard_blocks(text: str) -> List[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    blocks: List[str] = []
    current: List[str] = []

    for line in normalized.split("\n"):
        stripped = line.strip()

        if stripped.lower().startswith("[interface]"):
            if current:
                blocks.append("\n".join(current).strip())

            current = [stripped]
            continue

        if current:
            current.append(line.rstrip())

    if current:
        blocks.append("\n".join(current).strip())

    return [block for block in blocks if _is_wireguard_block(block)]


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


def _gh_headers() -> dict:
    headers = {
        "User-Agent": "OdinEyes-Collector/2.0",
        "Accept": "application/vnd.github+json",
    }

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def _fetch_wireguard_configs() -> List[str]:
    blocks: List[str] = []

    for repo, path in WIREGUARD_DIRS:
        try:
            listing = requests.get(
                f"https://api.github.com/repos/{repo}/contents/{path}",
                headers=_gh_headers(),
                timeout=20,
            )

            listing.raise_for_status()

            files = [
                item
                for item in listing.json()
                if item.get("type") == "file"
                and item.get("name", "").lower().endswith(".conf")
                and item.get("download_url")
            ]

            fetched = 0

            for item in files:
                raw = requests.get(
                    item["download_url"],
                    headers=_gh_headers(),
                    timeout=20,
                )

                raw.raise_for_status()

                parsed = _extract_wireguard_blocks(raw.text)
                blocks.extend(parsed)
                fetched += len(parsed)

            print(
                f"Source wireguard:{repo}/{path}: "
                f"files={len(files)} configs={fetched}"
            )

        except Exception as exc:
            print(f"Source wireguard:{repo}/{path}: ERROR {exc}")

    return blocks


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

    all_configs.extend(_fetch_wireguard_configs())

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

        if _is_wireguard_block(config):
            if len(config) >= 20:
                valid.append(config)

            continue

        if not lower.startswith(SUPPORTED_PREFIXES):
            continue

        if len(config) < 20:
            continue

        valid.append(config)

    return valid


def protocol_of(config: str) -> str:
    if _is_wireguard_block(config):
        return "wireguard"

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

    category_counts = {"vless_reality": 0, "vless_xhttp": 0, "ss2022": 0}

    for config in valid:
        lower = config.lower()

        if lower.startswith("vless://"):
            if "security=reality" in lower:
                category_counts["vless_reality"] += 1

            if "type=xhttp" in lower:
                category_counts["vless_xhttp"] += 1

        if lower.startswith("ss://") and "2022-blake3" in lower:
            category_counts["ss2022"] += 1

    print("Category counts:")

    for key, count in category_counts.items():
        print(f"  {key}: {count}")

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
