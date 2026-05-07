#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional


API_BASE = "https://api.cloudflare.com/client/v4"
REDIRECT_STATUS_LABELS = {
    301: "301 - Permanent Redirect",
    302: "302 - Temporary Redirect",
}
HELP_EPILOG = """Examples:
  python3 page_rules_cli.py zones
  python3 page_rules_cli.py rules --zone-name example.com
  python3 page_rules_cli.py enable --zone-name example.com --position 1
  python3 page_rules_cli.py enable --zone-name example.com --rule-id RULE_ID
  python3 page_rules_cli.py disable --zone-name example.com --position 1,3
  python3 page_rules_cli.py disable --zone-name example.com --rule-id RULE_ID_1,RULE_ID_2
  python3 page_rules_cli.py disable --zone-name example.com --all

Credentials:
  - the script accepts --api-token
  - it also accepts CLOUDFLARE_API_TOKEN
  - it also loads a .env file automatically
"""
ZONES_EPILOG = """Examples:
  python3 page_rules_cli.py zones
"""
RULES_EPILOG = """Examples:
  python3 page_rules_cli.py rules --zone-name example.com
"""
ENABLE_DISABLE_EPILOG = """Rule selection:
  Provide exactly one of --position, --rule-id, or --all.

Examples:
  python3 page_rules_cli.py enable --zone-name example.com --position 1
  python3 page_rules_cli.py disable --zone-name example.com --position 1,3
  python3 page_rules_cli.py enable --zone-name example.com --rule-id RULE_ID
  python3 page_rules_cli.py disable --zone-name example.com --rule-id RULE_ID_1,RULE_ID_2
  python3 page_rules_cli.py enable --zone-name example.com --all
"""


class HelpFormatter(argparse.RawTextHelpFormatter):
    pass


class CloudflareAPIError(RuntimeError):
    pass


def load_dotenv() -> None:
    candidate_paths = [Path.cwd() / ".env", Path(__file__).resolve().with_name(".env")]
    seen_paths: set[Path] = set()

    for env_path in candidate_paths:
        if env_path in seen_paths or not env_path.is_file():
            continue
        seen_paths.add(env_path)

        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            if not key or key in os.environ:
                continue

            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]

            os.environ[key] = value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage Cloudflare Page Rules for zones accessible to an API token.",
        epilog=HELP_EPILOG,
        formatter_class=HelpFormatter,
    )
    parser.add_argument(
        "--api-token",
        default=os.getenv("CLOUDFLARE_API_TOKEN", "").strip(),
        help="Cloudflare API token. Also accepts CLOUDFLARE_API_TOKEN.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    zones_parser = subparsers.add_parser(
        "zones",
        help="List zones accessible to the token.",
        description="List the zones accessible to the current token.",
        epilog=ZONES_EPILOG,
        formatter_class=HelpFormatter,
    )

    rules_parser = subparsers.add_parser(
        "rules",
        help="List Page Rules for a zone.",
        description="List Page Rules for a zone using --zone-name.",
        epilog=RULES_EPILOG,
        formatter_class=HelpFormatter,
    )
    add_zone_arguments(rules_parser)

    enable_parser = subparsers.add_parser(
        "enable",
        help="Enable one or more Page Rules.",
        description="Enable Page Rules in a zone by Position, Rule ID, or --all.",
        epilog=ENABLE_DISABLE_EPILOG,
        formatter_class=HelpFormatter,
    )
    add_zone_arguments(enable_parser)
    add_rule_selector_arguments(enable_parser)

    disable_parser = subparsers.add_parser(
        "disable",
        help="Disable one or more Page Rules.",
        description="Disable Page Rules in a zone by Position, Rule ID, or --all.",
        epilog=ENABLE_DISABLE_EPILOG,
        formatter_class=HelpFormatter,
    )
    add_zone_arguments(disable_parser)
    add_rule_selector_arguments(disable_parser)

    return parser


def add_zone_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--zone-name", required=True, help="Zone name. Example: example.com")


def add_rule_selector_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--position",
        default="",
        help="Position shown in the rules listing. Use comma-separated values for multiple positions.",
    )
    parser.add_argument(
        "--rule-id",
        default="",
        help="Page Rule ID. Use comma-separated values for multiple rule IDs.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all_rules",
        help="Apply the change to all Page Rules in the zone.",
    )


def require_value(value: str, message: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise SystemExit(message)
    return normalized


class CloudflareClient:
    def __init__(self, api_token: str) -> None:
        self.api_token = api_token


def api_request(
    client: CloudflareClient,
    method: str,
    path: str,
    params: Optional[dict[str, Any]] = None,
    body: Optional[dict[str, Any]] = None,
) -> Any:
    url = f"{API_BASE}{path}"
    if params:
        filtered = {key: value for key, value in params.items() if value not in (None, "")}
        if filtered:
            url = f"{url}?{urllib.parse.urlencode(filtered, doseq=True)}"

    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {client.api_token}",
            "Content-Type": "application/json",
        },
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=30.0) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        response_text = exc.read().decode("utf-8", errors="replace")
        raise CloudflareAPIError(f"HTTP error: {exc.code} {response_text}") from exc
    except urllib.error.URLError as exc:
        raise CloudflareAPIError(f"Request error: {exc.reason}") from exc

    if not payload.get("success"):
        errors = payload.get("errors") or []
        details = "; ".join(
            f"{item.get('code', 'error')}: {item.get('message', 'no message')}"
            for item in errors
        ) or "Cloudflare returned an unsuccessful response."
        raise CloudflareAPIError(details)
    return payload.get("result")


def list_zones(client: CloudflareClient) -> list[dict[str, Any]]:
    zones: list[dict[str, Any]] = []
    page = 1
    while True:
        params: dict[str, Any] = {
            "page": page,
            "per_page": 50,
            "order": "name",
            "direction": "asc",
        }
        result = api_request(
            client,
            "GET",
            "/zones",
            params=params,
        )
        if not result:
            break
        zones.extend(result)
        if len(result) < 50:
            break
        page += 1
    return zones


def resolve_zone(client: CloudflareClient, zone_name: str) -> dict[str, Any]:
    name = require_value(zone_name, "Provide --zone-name.")
    zones = list_zones(client)
    matches = [zone for zone in zones if (zone.get("name") or "").strip().lower() == name.lower()]
    if not matches:
        raise SystemExit(f"Zone '{name}' was not found among the zones accessible to the token.")
    if len(matches) > 1:
        raise SystemExit(f"More than one zone named '{name}' was found.")
    zone = matches[0]
    return {"id": zone["id"], "name": zone["name"]}


def list_page_rules(client: CloudflareClient, zone_id: str) -> list[dict[str, Any]]:
    return api_request(
        client,
        "GET",
        f"/zones/{zone_id}/pagerules",
        params={"order": "priority", "direction": "asc"},
    ) or []


def order_rules_for_display(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if rules and all(rule.get("_display_position") is not None for rule in rules):
        return sorted(rules, key=lambda rule: int(rule.get("_display_position") or 0))
    return sorted(
        rules,
        key=lambda rule: int(rule.get("priority") or -1),
        reverse=True,
    )


def parse_csv_arguments(values: list[str]) -> list[str]:
    parsed_values: list[str] = []
    for raw_value in values:
        for item in str(raw_value).split(","):
            normalized = item.strip()
            if normalized:
                parsed_values.append(normalized)
    return parsed_values


def parse_position_arguments(value: str) -> list[int]:
    positions: list[int] = []
    for item in parse_csv_arguments([value]):
        try:
            positions.append(int(item))
        except ValueError as exc:
            raise SystemExit(f"Invalid position: '{item}'. Use integers.") from exc
    return positions


def parse_rule_id_arguments(value: str) -> list[str]:
    return parse_csv_arguments([value])


def resolve_rule_selection(
    rules: list[dict[str, Any]],
    positions: str,
    rule_ids: str,
    all_rules: bool,
) -> list[dict[str, Any]]:
    normalized_positions = parse_position_arguments(positions)
    normalized_rule_ids = parse_rule_id_arguments(rule_ids)
    selectors = sum([bool(normalized_positions), bool(normalized_rule_ids), bool(all_rules)])
    if selectors != 1:
        raise SystemExit("Provide exactly one of --position, --rule-id, or --all.")

    if not rules:
        raise SystemExit("No Page Rules were found in the zone.")

    ordered_rules = order_rules_for_display(rules)
    positions_by_id = {
        (rule.get("id") or "").strip(): index
        for index, rule in enumerate(ordered_rules, start=1)
    }

    def with_position(rule: dict[str, Any]) -> dict[str, Any]:
        selected_rule = dict(rule)
        selected_rule["_display_position"] = positions_by_id.get((rule.get("id") or "").strip())
        return selected_rule

    if all_rules:
        return [with_position(rule) for rule in ordered_rules]

    rules_by_id = {
        (rule.get("id") or "").strip(): rule
        for rule in ordered_rules
        if (rule.get("id") or "").strip()
    }

    if normalized_rule_ids:
        unique_rule_ids = list(dict.fromkeys(normalized_rule_ids))
        invalid_rule_ids = [rule_id for rule_id in unique_rule_ids if rule_id not in rules_by_id]
        if invalid_rule_ids:
            raise SystemExit(
                f"Invalid rule ID(s): {', '.join(invalid_rule_ids)}. "
                "Use the Rule ID shown in the rules output."
            )
        selected_rules = [with_position(rules_by_id[rule_id]) for rule_id in unique_rule_ids]
        return order_rules_for_display(selected_rules)

    unique_positions = list(dict.fromkeys(normalized_positions))
    invalid_positions = [str(position) for position in unique_positions if position <= 0 or position > len(ordered_rules)]
    if invalid_positions:
        raise SystemExit(
            f"Invalid position(s): {', '.join(invalid_positions)}. "
            f"Total rules in the listing: {len(ordered_rules)}."
        )
    selected_rules = [with_position(ordered_rules[position - 1]) for position in unique_positions]
    return order_rules_for_display(selected_rules)


def set_page_rule_status(client: CloudflareClient, zone_id: str, rule_id: str, status: str) -> dict[str, Any]:
    return api_request(
        client,
        "PATCH",
        f"/zones/{zone_id}/pagerules/{rule_id}",
        body={"status": status},
    )


def format_target(rule: dict[str, Any]) -> str:
    targets = rule.get("targets") or []
    if not targets:
        return "-"
    first = targets[0]
    constraint = first.get("constraint") or {}
    return str(constraint.get("value") or "-")


def format_status(rule_status: str) -> str:
    normalized = (rule_status or "").strip().lower()
    if normalized == "active":
        return "Enabled"
    if normalized == "disabled":
        return "Disabled"
    return normalized.title() if normalized else "-"


def format_action_value(value: Any) -> str:
    if isinstance(value, bool):
        return "On" if value else "Off"
    if isinstance(value, dict):
        return ", ".join(f"{key}: {item}" for key, item in value.items()) or "-"
    if value is None:
        return "-"
    normalized = str(value).strip()
    if normalized.lower() in {"on", "off"}:
        return normalized.capitalize()
    return normalized


def format_rule_descriptions(rule: dict[str, Any]) -> list[str]:
    actions = rule.get("actions") or []
    if not actions:
        return ["-"]

    descriptions: list[str] = []
    for action in actions:
        action_id = (action.get("id") or "").strip()
        value = action.get("value")

        if action_id == "forwarding_url" and isinstance(value, dict):
            status_code = value.get("status_code")
            status_code_label = REDIRECT_STATUS_LABELS.get(status_code, str(status_code or "-"))
            url = value.get("url") or "-"
            descriptions.append(
                f"Forwarding URL (Status Code: {status_code_label}, Url: {url})"
            )
            continue

        if action_id == "automatic_https_rewrites":
            descriptions.append(f"Automatic HTTPS Rewrites: {format_action_value(value)}")
            continue

        action_name = action_id.replace("_", " ").title() if action_id else "Action"
        descriptions.append(f"{action_name}: {format_action_value(value)}")

    return descriptions


def print_zones(zones: list[dict[str, Any]]) -> None:
    if not zones:
        print("No zones found.")
        return
    print(f"{'ZONE ID':<36} {'STATUS':<10} NAME")
    for zone in zones:
        print(f"{zone.get('id', ''):<36} {zone.get('status', ''):<10} {zone.get('name', '')}")


def print_rules(rules: list[dict[str, Any]]) -> None:
    if not rules:
        print("No Page Rules found.")
        return
    ordered_rules = order_rules_for_display(rules)
    for fallback_position, rule in enumerate(ordered_rules, start=1):
        position = int(rule.get("_display_position") or fallback_position)
        descriptions = format_rule_descriptions(rule)
        print(f"Position: {position}")
        print(f"Rule ID: {rule.get('id', '')}")
        print(f"URL: {format_target(rule)}")
        for description in descriptions:
            print(f"Description: {description}")
        print(f"Action: {format_status(rule.get('status', ''))}")
        print()


def main() -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()

    api_token = require_value(args.api_token, "Provide --api-token or set CLOUDFLARE_API_TOKEN.")

    try:
        client = CloudflareClient(api_token)
        if args.command == "zones":
            print_zones(list_zones(client))
            return 0

        zone = resolve_zone(client, args.zone_name)

        if args.command == "rules":
            print(f"Zone: {zone['name']} ({zone['id']})")
            print_rules(list_page_rules(client, zone["id"]))
            return 0

        target_status = "active" if args.command == "enable" else "disabled"
        rules = list_page_rules(client, zone["id"])
        selected_rules = resolve_rule_selection(
            rules,
            args.position,
            args.rule_id,
            args.all_rules,
        )

        updated_rules = [
            set_page_rule_status(client, zone["id"], (rule.get("id") or "").strip(), target_status)
            for rule in selected_rules
        ]
        selected_positions = {
            (rule.get("id") or "").strip(): rule.get("_display_position")
            for rule in selected_rules
        }
        for updated_rule in updated_rules:
            updated_rule["_display_position"] = selected_positions.get((updated_rule.get("id") or "").strip())

        print(f"Zone: {zone['name']} ({zone['id']})")
        if len(updated_rules) == 1:
            print("Page Rule updated successfully:")
        else:
            print(f"Page Rules updated successfully: {len(updated_rules)}")
        print_rules(updated_rules)
        return 0
    except CloudflareAPIError as exc:
        print(f"Cloudflare API error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
