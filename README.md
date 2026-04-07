# Page Rules CLI

Python CLI for listing, enabling, and disabling Cloudflare `Page Rules` by zone.

## Overview

The script can:

- list zones accessible to the token
- list `Page Rules` for a zone
- enable or disable rules by `Rule ID`
- enable or disable rules by `Position`
- apply changes to all rules in a zone with `--all`
- update multiple rules in a single command

## Requirements

- Python 3
- `httpx`

## Installation

On systems where `pip` can install packages normally:

```bash
python3 -m pip install httpx
```

On Debian/Ubuntu systems with `externally-managed-environment`, use a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install httpx
```

If needed:

```bash
sudo apt update
sudo apt install python3-venv
```

## Token Permissions

Recommended permissions:

- `Zone - Zone: Read`
- `Zone - Page Rules: Read`
- `Zone - Page Rules: Edit`

Recommended token scope:

- `Zone Resources - Include: All zones from an account`
- or restrict the token to specific zones when appropriate

Notes:

- in some API references, `Page Rules Edit` may appear as `Page Rules Write`
- prefer the smallest scope that matches your operational need

## Configuration

The script accepts credentials from:

1. command-line arguments
2. environment variables
3. a `.env` file

Supported variables:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

`CLOUDFLARE_ACCOUNT_ID` is optional.

### `.env` file

Create a `.env` file in the project root:

```dotenv
CLOUDFLARE_API_TOKEN="your_api_token_here"
CLOUDFLARE_ACCOUNT_ID=""
```

### Environment variables

Or define the variables in your shell or container:

```bash
export CLOUDFLARE_API_TOKEN="your_api_token_here"
export CLOUDFLARE_ACCOUNT_ID=""
```

Notes:

- the script uses `CLOUDFLARE_API_TOKEN`, not `CLOUDFLARE_API_KEY`
- the `.env` file is loaded automatically

## Usage

General syntax:

```bash
python3 page_rules_cli.py <zones|rules|enable|disable> [options]
```

Terminal help:

```bash
python3 page_rules_cli.py --help
python3 page_rules_cli.py enable --help
python3 page_rules_cli.py disable --help
```

## Commands

### `zones`

Lists the zones accessible to the token. Supports optional name filtering and optional `account_id` filtering.

Examples:

```bash
python3 page_rules_cli.py zones
python3 page_rules_cli.py zones --name-contains example
python3 page_rules_cli.py zones --account-id <ACCOUNT_ID>
```

### `rules`

Lists the `Page Rules` for a zone using either `--zone-name` or `--zone-id`.

Examples:

```bash
python3 page_rules_cli.py rules --zone-name example.com
python3 page_rules_cli.py rules --zone-id <ZONE_ID>
```

### `enable` and `disable`

Enable or disable `Page Rules` for a zone.

For these commands, provide exactly one selection mode:

- `--rule-id`
- `--position`
- `--all`

#### Select by `Rule ID`

Best option for automation and stable targeting.

```bash
python3 page_rules_cli.py enable --zone-name example.com --rule-id <RULE_ID>
python3 page_rules_cli.py disable --zone-name example.com --rule-id <RULE_ID>
python3 page_rules_cli.py disable --zone-name example.com --rule-id <RULE_ID_1>,<RULE_ID_2>
python3 page_rules_cli.py disable --zone-name example.com --rule-id <RULE_ID_1> --rule-id <RULE_ID_2>
```

#### Select by `Position`

Best option for manual operation based on the order shown by the `rules` command.

```bash
python3 page_rules_cli.py enable --zone-name example.com --position 1
python3 page_rules_cli.py disable --zone-name example.com --position 1
python3 page_rules_cli.py enable --zone-name example.com --position 1,3
python3 page_rules_cli.py disable --zone-name example.com --position 1 --position 3
```

#### Select with `--all`

Applies the change to all `Page Rules` in the zone.

```bash
python3 page_rules_cli.py enable --zone-name example.com --all
python3 page_rules_cli.py disable --zone-name example.com --all
```

## Output

When listing rules, the script shows:

- `Position`
- `Rule ID`
- `URL`
- `Description`
- `Action`

Example:

```text
Zone: example.com (ZONE_ID)
Position: 1
Rule ID: abc123
URL: app.example.com/*
Description: Forwarding URL (Status Code: 302 - Temporary Redirect, Url: https://destination.example.com/)
Action: Enabled
```

## Notes

- `Position` is convenient for manual use, but it is not as stable as `Rule ID`
- for automation, prefer `--rule-id`
- for multi-rule operations, the script prints the updated rules at the end
- in containers, you can use runtime environment variables or mount a `.env` file
