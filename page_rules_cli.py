#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path
from typing import Any

import httpx


API_BASE = "https://api.cloudflare.com/client/v4"
REDIRECT_STATUS_LABELS = {
    301: "301 - Permanent Redirect",
    302: "302 - Temporary Redirect",
}
HELP_EPILOG = """Exemplos:
  python3 page_rules_cli.py zones
  python3 page_rules_cli.py zones --name-contains movida
  python3 page_rules_cli.py rules --zone-name example.com
  python3 page_rules_cli.py enable --zone-name example.com --position 1
  python3 page_rules_cli.py disable --zone-name example.com --position 1,3
  python3 page_rules_cli.py enable --zone-name example.com --rule-id <RULE_ID>
  python3 page_rules_cli.py disable --zone-name example.com --all

Credenciais:
  - o script aceita --api-token e --account-id
  - também aceita CLOUDFLARE_API_TOKEN e CLOUDFLARE_ACCOUNT_ID
  - também carrega um arquivo .env automaticamente
"""
ZONES_EPILOG = """Exemplos:
  python3 page_rules_cli.py zones
  python3 page_rules_cli.py zones --name-contains razor
  python3 page_rules_cli.py zones --account-id <ACCOUNT_ID>
"""
RULES_EPILOG = """Exemplos:
  python3 page_rules_cli.py rules --zone-name example.com
  python3 page_rules_cli.py rules --zone-id <ZONE_ID>
"""
ENABLE_DISABLE_EPILOG = """Seleção de regras:
  Informe exatamente uma opção entre --rule-id, --position ou --all.

Exemplos:
  python3 page_rules_cli.py enable --zone-name example.com --position 1
  python3 page_rules_cli.py disable --zone-name example.com --position 1,3
  python3 page_rules_cli.py enable --zone-name example.com --position 1 --position 3
  python3 page_rules_cli.py disable --zone-name example.com --rule-id <RULE_ID_1>,<RULE_ID_2>
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
        description="Gerencia Page Rules da Cloudflare por conta e zona.",
        epilog=HELP_EPILOG,
        formatter_class=HelpFormatter,
    )
    parser.add_argument(
        "--api-token",
        default=os.getenv("CLOUDFLARE_API_TOKEN", "").strip(),
        help="API token da Cloudflare. Também aceita CLOUDFLARE_API_TOKEN.",
    )
    parser.add_argument(
        "--account-id",
        default=os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip(),
        help="Account ID da Cloudflare para filtrar zonas. Também aceita CLOUDFLARE_ACCOUNT_ID.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    zones_parser = subparsers.add_parser(
        "zones",
        help="Lista zonas acessíveis ao token.",
        description="Lista as zonas acessíveis ao token atual.",
        epilog=ZONES_EPILOG,
        formatter_class=HelpFormatter,
    )
    zones_parser.add_argument(
        "--name-contains",
        default="",
        help="Filtra zonas que contenham este texto.",
    )

    rules_parser = subparsers.add_parser(
        "rules",
        help="Lista as Page Rules de uma zona.",
        description="Lista as Page Rules de uma zona usando --zone-name ou --zone-id.",
        epilog=RULES_EPILOG,
        formatter_class=HelpFormatter,
    )
    add_zone_arguments(rules_parser)

    enable_parser = subparsers.add_parser(
        "enable",
        help="Ativa uma ou mais Page Rules.",
        description="Ativa Page Rules de uma zona por Rule ID, Position ou --all.",
        epilog=ENABLE_DISABLE_EPILOG,
        formatter_class=HelpFormatter,
    )
    add_zone_arguments(enable_parser)
    add_rule_selector_arguments(enable_parser)

    disable_parser = subparsers.add_parser(
        "disable",
        help="Desativa uma ou mais Page Rules.",
        description="Desativa Page Rules de uma zona por Rule ID, Position ou --all.",
        epilog=ENABLE_DISABLE_EPILOG,
        formatter_class=HelpFormatter,
    )
    add_zone_arguments(disable_parser)
    add_rule_selector_arguments(disable_parser)

    return parser


def add_zone_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--zone-id", default="", help="Zone ID. Use quando você já souber o identificador da zona.")
    parser.add_argument("--zone-name", default="", help="Nome da zona. Exemplo: example.com")


def add_rule_selector_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--rule-id",
        action="append",
        default=[],
        help="ID da Page Rule. Aceita múltiplos valores via vírgula ou repetindo a flag.",
    )
    parser.add_argument(
        "--position",
        action="append",
        default=[],
        help="Position exibida na listagem. Aceita múltiplos valores via vírgula ou repetindo a flag.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all_rules",
        help="Aplica a alteração a todas as Page Rules da zona.",
    )


def require_value(value: str, message: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise SystemExit(message)
    return normalized


def make_client(api_token: str) -> httpx.Client:
    return httpx.Client(
        base_url=API_BASE,
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )


def api_request(client: httpx.Client, method: str, path: str, **kwargs: Any) -> Any:
    response = client.request(method, path, **kwargs)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        errors = payload.get("errors") or []
        details = "; ".join(
            f"{item.get('code', 'erro')}: {item.get('message', 'sem mensagem')}"
            for item in errors
        ) or "Resposta sem sucesso da Cloudflare."
        raise CloudflareAPIError(details)
    return payload.get("result")


def list_zones(client: httpx.Client, account_id: str = "", name_contains: str = "") -> list[dict[str, Any]]:
    zones: list[dict[str, Any]] = []
    page = 1
    while True:
        params: dict[str, Any] = {
            "page": page,
            "per_page": 50,
            "order": "name",
            "direction": "asc",
        }
        if account_id.strip():
            params["account.id"] = account_id.strip()
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

    if name_contains:
        term = name_contains.strip().lower()
        zones = [zone for zone in zones if term in (zone.get("name") or "").lower()]
    return zones


def resolve_zone(client: httpx.Client, account_id: str, zone_id: str, zone_name: str) -> dict[str, Any]:
    if zone_id.strip():
        result = api_request(client, "GET", f"/zones/{zone_id.strip()}")
        return {"id": result["id"], "name": result["name"]}

    name = require_value(zone_name, "Informe --zone-id ou --zone-name.")
    zones = list_zones(client, account_id)
    matches = [zone for zone in zones if (zone.get("name") or "").strip().lower() == name.lower()]
    if not matches:
        if account_id.strip():
            raise SystemExit(f"Zona '{name}' não encontrada na conta {account_id}.")
        raise SystemExit(f"Zona '{name}' não encontrada entre as zonas acessíveis ao token.")
    if len(matches) > 1:
        raise SystemExit(f"Mais de uma zona com nome '{name}' foi encontrada. Use --zone-id ou informe --account-id.")
    zone = matches[0]
    return {"id": zone["id"], "name": zone["name"]}


def list_page_rules(client: httpx.Client, zone_id: str) -> list[dict[str, Any]]:
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


def parse_position_arguments(values: list[str]) -> list[int]:
    positions: list[int] = []
    for item in parse_csv_arguments(values):
        try:
            positions.append(int(item))
        except ValueError as exc:
            raise SystemExit(f"Position inválida: '{item}'. Use números inteiros.") from exc
    return positions


def resolve_rule_selection(
    rules: list[dict[str, Any]],
    rule_ids: list[str],
    positions: list[int],
    all_rules: bool,
) -> list[dict[str, Any]]:
    normalized_rule_ids = parse_csv_arguments(rule_ids)
    normalized_positions = parse_position_arguments([str(position) for position in positions])
    selectors = sum([bool(normalized_rule_ids), bool(normalized_positions), bool(all_rules)])
    if selectors != 1:
        raise SystemExit("Informe exatamente uma opção entre --rule-id, --position ou --all.")

    if not rules:
        raise SystemExit("Nenhuma Page Rule encontrada na zona.")

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

    if normalized_rule_ids:
        unique_rule_ids = list(dict.fromkeys(normalized_rule_ids))
        rules_by_id = {
            (rule.get("id") or "").strip(): rule
            for rule in rules
        }
        missing_rule_ids = [rule_id for rule_id in unique_rule_ids if rule_id not in rules_by_id]
        if missing_rule_ids:
            raise SystemExit(f"Page Rule(s) não encontrada(s) na zona: {', '.join(missing_rule_ids)}.")
        selected_rules = [with_position(rules_by_id[rule_id]) for rule_id in unique_rule_ids]
        return order_rules_for_display(selected_rules)

    unique_positions = list(dict.fromkeys(normalized_positions))
    invalid_positions = [str(position) for position in unique_positions if position <= 0 or position > len(ordered_rules)]
    if invalid_positions:
        raise SystemExit(
            f"Position(s) inválida(s): {', '.join(invalid_positions)}. "
            f"Total de regras na listagem: {len(ordered_rules)}."
        )
    selected_rules = [with_position(ordered_rules[position - 1]) for position in unique_positions]
    return order_rules_for_display(selected_rules)


def set_page_rule_status(client: httpx.Client, zone_id: str, rule_id: str, status: str) -> dict[str, Any]:
    return api_request(
        client,
        "PATCH",
        f"/zones/{zone_id}/pagerules/{rule_id}",
        json={"status": status},
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
        print("Nenhuma zona encontrada.")
        return
    print(f"{'ZONE ID':<36} {'STATUS':<10} NOME")
    for zone in zones:
        print(f"{zone.get('id', ''):<36} {zone.get('status', ''):<10} {zone.get('name', '')}")


def print_rules(rules: list[dict[str, Any]]) -> None:
    if not rules:
        print("Nenhuma Page Rule encontrada.")
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

    api_token = require_value(args.api_token, "Informe --api-token ou defina CLOUDFLARE_API_TOKEN.")
    account_id = args.account_id.strip()

    try:
        with make_client(api_token) as client:
            if args.command == "zones":
                print_zones(list_zones(client, account_id, args.name_contains))
                return 0

            zone = resolve_zone(client, account_id, args.zone_id, args.zone_name)

            if args.command == "rules":
                print(f"Zona: {zone['name']} ({zone['id']})")
                print_rules(list_page_rules(client, zone["id"]))
                return 0

            target_status = "active" if args.command == "enable" else "disabled"
            rules = list_page_rules(client, zone["id"])
            selected_rules = resolve_rule_selection(
                rules,
                args.rule_id,
                args.position,
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

            print(f"Zona: {zone['name']} ({zone['id']})")
            if len(updated_rules) == 1:
                print("Page Rule atualizada com sucesso:")
            else:
                print(f"Page Rules atualizadas com sucesso: {len(updated_rules)}")
            print_rules(updated_rules)
            return 0
    except httpx.HTTPStatusError as exc:
        print(f"Erro HTTP da Cloudflare: {exc.response.status_code} {exc.response.text}", file=sys.stderr)
        return 1
    except CloudflareAPIError as exc:
        print(f"Erro da API Cloudflare: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
