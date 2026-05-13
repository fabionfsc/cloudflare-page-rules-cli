# Cloudflare Page Rules CLI

Python CLI for listing, enabling, and disabling Cloudflare `Page Rules` for zones accessible to a given API token.

## Overview

The script can:

- list zones accessible to the token
- list `Page Rules` for a zone
- enable or disable rules by `Position`
- enable or disable rules by `Rule ID`
- apply changes to all rules in a zone with `--all`
- update multiple rules in a single command
- run batch enable/disable from a CSV file

## Requirements

- Python 3

## Installation

No package install is required for runtime if you already have Python 3 available.

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
- `--rule-id`
- `--all`
- `--batch`

#### Select by `Position`

Rules are selected by the `Position` shown in the `rules` output.

```bash
python3 page_rules_cli.py enable --zone-name example.com --position 1
python3 page_rules_cli.py disable --zone-name example.com --position 1
python3 page_rules_cli.py enable --zone-name example.com --position 1,3
python3 page_rules_cli.py disable --zone-name example.com --position 1,3
```

#### Select by `Rule ID`

Rules are selected by the `Rule ID` shown in the `rules` output.

```bash
python3 page_rules_cli.py enable --zone-name example.com --rule-id RULE_ID
python3 page_rules_cli.py disable --zone-name example.com --rule-id RULE_ID
python3 page_rules_cli.py enable --zone-name example.com --rule-id RULE_ID_1,RULE_ID_2
python3 page_rules_cli.py disable --zone-name example.com --rule-id RULE_ID_1,RULE_ID_2
```

#### Select with `--all`

Applies the change to all `Page Rules` in the zone.

```bash
python3 page_rules_cli.py enable --zone-name example.com --all
python3 page_rules_cli.py disable --zone-name example.com --all
```

#### Batch CSV

Batch mode applies `enable` or `disable` to the rule IDs listed in a CSV file.

The public CLI/CSV format uses kebab-case with `-`. Internally, Python variables use snake_case with `_`.

CSV format:

```csv
zone-name,rule-id
example.com,884eeac1759a01ee9434b29f4242a65f
example.net,9c8a1c48d719f5d98680037a0e8bdb55
```

Required headers:

- `zone-name`
- `rule-id`

Dry-run is the default:

```bash
python3 page_rules_cli.py disable --batch rules.csv
python3 page_rules_cli.py enable --batch rules.csv
```

To apply all valid entries in the CSV, add `--all`:

```bash
python3 page_rules_cli.py disable --batch rules.csv --all
python3 page_rules_cli.py enable --batch rules.csv --all
```

In batch mode, `--all` means "apply all valid entries from the CSV". Outside batch mode, `--all` keeps its original meaning: apply the change to all `Page Rules` in one zone.

Batch safety behavior:

- the CSV header must be exactly `zone-name,rule-id`
- `zone-name` is resolved against zones accessible to the token
- `rule-id` must exist inside the matching zone
- duplicate `zone-name,rule-id` rows are rejected
- if any row has an error, nothing is changed
- without `--all`, no changes are made

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
