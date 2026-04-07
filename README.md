# Page Rules CLI

CLI em Python para listar, ativar e desativar `Page Rules` da Cloudflare por zona.

## Visão geral

O script permite:

- listar zonas acessíveis ao token
- listar `Page Rules` de uma zona
- ativar ou desativar regras por `Rule ID`
- ativar ou desativar regras por `Position`
- aplicar a alteração a todas as regras da zona com `--all`
- alterar múltiplas regras no mesmo comando

## Requisitos

- Python 3
- biblioteca `httpx`

## Instalação

Em ambientes onde `pip` pode instalar normalmente:

```bash
python3 -m pip install httpx
```

Em Debian/Ubuntu com `externally-managed-environment`, use `venv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install httpx
```

Se necessário:

```bash
sudo apt update
sudo apt install python3-venv
```

## Permissões do token

Permissões recomendadas:

- `Zone Read`
- `Page Rules Read`
- `Page Rules Edit`

Observação:

- em algumas telas da Cloudflare, `Page Rules Edit` pode aparecer como `Page Rules Write`
- restrinja o token apenas às zonas que serão administradas

## Configuração

O script aceita credenciais por:

1. argumentos de linha de comando
2. variáveis de ambiente
3. arquivo `.env`

Variáveis suportadas:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

`CLOUDFLARE_ACCOUNT_ID` é opcional.

### Arquivo `.env`

Crie um arquivo `.env` na raiz do projeto:

```dotenv
CLOUDFLARE_API_TOKEN="seu_api_token_aqui"
CLOUDFLARE_ACCOUNT_ID=""
```

### Variáveis de ambiente

Ou defina as variáveis no shell ou no container:

```bash
export CLOUDFLARE_API_TOKEN="seu_api_token_aqui"
export CLOUDFLARE_ACCOUNT_ID=""
```

Observação:

- o script usa `CLOUDFLARE_API_TOKEN`, não `CLOUDFLARE_API_KEY`
- o arquivo `.env` é carregado automaticamente

## Uso

Sintaxe geral:

```bash
python3 page_rules_cli.py <zones|rules|enable|disable> [opções]
```

Ajuda no terminal:

```bash
python3 page_rules_cli.py --help
python3 page_rules_cli.py enable --help
python3 page_rules_cli.py disable --help
```

## Comandos

### `zones`

Lista as zonas acessíveis ao token. Pode ser usado com filtro de nome e, opcionalmente, com `account_id`.

Exemplos:

```bash
python3 page_rules_cli.py zones
python3 page_rules_cli.py zones --name-contains example
python3 page_rules_cli.py zones --account-id <ACCOUNT_ID>
```

### `rules`

Lista as `Page Rules` de uma zona usando `--zone-name` ou `--zone-id`.

Exemplos:

```bash
python3 page_rules_cli.py rules --zone-name example.com
python3 page_rules_cli.py rules --zone-id <ZONE_ID>
```

### `enable` e `disable`

Ativam ou desativam `Page Rules` de uma zona.

Para esses comandos, informe exatamente uma forma de seleção:

- `--rule-id`
- `--position`
- `--all`

#### Seleção por `Rule ID`

Mais adequada para automação e uso estável.

```bash
python3 page_rules_cli.py enable --zone-name example.com --rule-id <RULE_ID>
python3 page_rules_cli.py disable --zone-name example.com --rule-id <RULE_ID>
python3 page_rules_cli.py disable --zone-name example.com --rule-id <RULE_ID_1>,<RULE_ID_2>
python3 page_rules_cli.py disable --zone-name example.com --rule-id <RULE_ID_1> --rule-id <RULE_ID_2>
```

#### Seleção por `Position`

Mais adequada para operação manual com base na listagem exibida pelo comando `rules`.

```bash
python3 page_rules_cli.py enable --zone-name example.com --position 1
python3 page_rules_cli.py disable --zone-name example.com --position 1
python3 page_rules_cli.py enable --zone-name example.com --position 1,3
python3 page_rules_cli.py disable --zone-name example.com --position 1 --position 3
```

#### Seleção com `--all`

Aplica a alteração a todas as `Page Rules` da zona.

```bash
python3 page_rules_cli.py enable --zone-name example.com --all
python3 page_rules_cli.py disable --zone-name example.com --all
```

## Saída

Na listagem de regras, o script exibe:

- `Position`
- `Rule ID`
- `URL`
- `Description`
- `Action`

Exemplo:

```text
Zona: example.com (ZONE_ID)
Position: 1
Rule ID: abc123
URL: app.example.com/*
Description: Forwarding URL (Status Code: 302 - Temporary Redirect, Url: https://destino.example.com/)
Action: Enabled
```

## Observações

- `Position` é conveniente para uso manual, mas não é um identificador estável como `Rule ID`
- para automação, prefira `--rule-id`
- em operações com múltiplas regras, o script imprime as regras atualizadas ao final
- em container, você pode usar variáveis de ambiente do runtime ou montar um arquivo `.env`
