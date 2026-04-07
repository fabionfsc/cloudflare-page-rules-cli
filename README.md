# Cloudflare Page Rules CLI

Python CLI for listing, enabling, and disabling Cloudflare `Page Rules` for zones accessible to a given API token.

## Overview

The script can:

- list zones accessible to the token
- list `Page Rules` for a zone
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

## Configuration

The script accepts credentials from:

1. command-line arguments
2. environment variables
3. a `.env` file

Supported variables:

- `CLOUDFLARE_API_TOKEN`

### `.env` file

Create a `.env` file in the project root:

```dotenv
CLOUDFLARE_API_TOKEN="your_api_token_here"
```

### Environment variables

Or define the variables in your shell or container:

```bash
export CLOUDFLARE_API_TOKEN="your_api_token_here"
```

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

Lists the zones accessible to the token.

Examples:

```bash
python3 page_rules_cli.py zones
```

### `rules`

Lists the `Page Rules` for a zone using `--zone-name`.

Examples:

```bash
python3 page_rules_cli.py rules --zone-name example.com
```

### `enable` and `disable`

Enable or disable `Page Rules` for a zone.

For these commands, provide exactly one selection mode:

- `--position`
- `--all`

#### Select by `Position`

Rules are selected by the `Position` shown in the `rules` output.

```bash
python3 page_rules_cli.py enable --zone-name example.com --position 1
python3 page_rules_cli.py disable --zone-name example.com --position 1
python3 page_rules_cli.py enable --zone-name example.com --position 1,3
python3 page_rules_cli.py disable --zone-name example.com --position 1,3
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
