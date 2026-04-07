# Page Rules CLI

Script isolado para listar e alterar `Page Rules` da Cloudflare por conta e zona.

`account_id` é opcional. Quando informado, ele é usado para filtrar a listagem de zonas.

## O que ele faz

- lista zonas acessíveis ao token
- lista `Page Rules` de uma zona
- ativa regras específicas
- desativa regras específicas
- permite selecionar regras por `Rule ID`, `Position` ou `--all`
- aceita múltiplas regras no mesmo comando

## Sintaxe geral

O script usa subcomandos:

```bash
python3 page_rules_cli.py <zones|rules|enable|disable> [opções]
```

Exemplos válidos:

```bash
python3 page_rules_cli.py rules --zone-name example.com
python3 page_rules_cli.py enable --zone-name example.com --position 1
python3 page_rules_cli.py disable --zone-name example.com --all
```

Exemplo inválido:

```bash
python3 page_rules_cli.py --zone-name example.com --enable --all
```

`enable` e `disable` são subcomandos, não flags.

## Requisitos

- Python 3
- biblioteca `httpx`
- arquivo `.env` opcional para guardar credenciais localmente

## Instalação

Em muitos sistemas Linux, basta instalar a dependência com:

```bash
python3 -m pip install httpx
```

Em Debian/Ubuntu mais recentes, esse comando pode falhar com erro `externally-managed-environment`. Nesse caso, use um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install httpx
```

Se a criação do `venv` falhar, instale o suporte necessário:

```bash
sudo apt update
sudo apt install python3-venv
```

## Permissões recomendadas do API Token

- `Zone Read`
- `Page Rules Read`
- `Page Rules Edit`

Escopo:

- restrinja o token às zonas da conta que você pretende administrar

Observação:

- dependendo da tela da Cloudflare, a permissão pode aparecer com nome ligeiramente diferente, como `Page Rules Write`

## Configuração

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

`CLOUDFLARE_ACCOUNT_ID` é opcional.

Crie um arquivo `.env` na raiz do projeto para armazenar suas credenciais. O script busca esse arquivo automaticamente.

Exemplo:

```dotenv
# .env
CLOUDFLARE_API_TOKEN="seu_api_token_aqui"
CLOUDFLARE_ACCOUNT_ID=""
```

Se preferir, também é possível definir as credenciais como variáveis de ambiente no terminal ou no container:

```bash
export CLOUDFLARE_API_TOKEN="seu_api_token_aqui"
export CLOUDFLARE_ACCOUNT_ID=""
```

Observação:

- o script usa `CLOUDFLARE_API_TOKEN`, não `CLOUDFLARE_API_KEY`
- `CLOUDFLARE_ACCOUNT_ID` é opcional
- o `.env` pode ficar no diretório atual ou ao lado de `page_rules_cli.py`

Ordem de precedência:

1. argumentos de linha de comando, como `--api-token` e `--account-id`
2. variáveis de ambiente já definidas no shell ou no container
3. valores encontrados no arquivo `.env`

## Exemplos

Com `.env` preenchido, basta rodar os comandos normalmente:

Listar zonas:

```bash
python3 page_rules_cli.py zones
```

Listar zonas filtrando por nome:

```bash
python3 page_rules_cli.py zones --name-contains example
```

Listar zonas filtrando por conta:

```bash
python3 page_rules_cli.py zones --account-id <ACCOUNT_ID>
```

Listar `Page Rules` de uma zona:

```bash
python3 page_rules_cli.py rules --zone-name example.com
```

Também é possível usar `--zone-id` no lugar de `--zone-name`:

```bash
python3 page_rules_cli.py rules --zone-id <ZONE_ID>
```

## Seleção de regras

Nos comandos `enable` e `disable`, informe exatamente uma opção entre:

- `--rule-id`
- `--position`
- `--all`

As opções `--rule-id` e `--position` aceitam um ou vários valores.

### Por `Rule ID`

Ativar uma regra:

```bash
python3 page_rules_cli.py enable --zone-name example.com --rule-id <RULE_ID>
```

Desativar uma regra:

```bash
python3 page_rules_cli.py disable --zone-name example.com --rule-id <RULE_ID>
```

Desativar múltiplas regras:

```bash
python3 page_rules_cli.py disable --zone-name example.com --rule-id <RULE_ID_1>,<RULE_ID_2>
python3 page_rules_cli.py disable --zone-name example.com --rule-id <RULE_ID_1> --rule-id <RULE_ID_2>
```

### Por `Position`

Ativar ou desativar uma regra pela posição exibida na listagem:

```bash
python3 page_rules_cli.py enable --zone-name example.com --position 1
python3 page_rules_cli.py disable --zone-name example.com --position 1
```

Ativar ou desativar múltiplas posições:

```bash
python3 page_rules_cli.py enable --zone-name example.com --position 1,3
python3 page_rules_cli.py disable --zone-name example.com --position 1 --position 3
```

### Todas as regras da zona

Aplicar a alteração a todas as `Page Rules` da zona:

```bash
python3 page_rules_cli.py enable --zone-name example.com --all
python3 page_rules_cli.py disable --zone-name example.com --all
```

## Formato da saída

Na listagem de regras, o script mostra:

- `Position`
- `Rule ID`
- `URL`
- `Description`
- `Action`

Exemplo:

```bash
python3 page_rules_cli.py rules --zone-name example.com
```

```text
Zona: example.com (ZONE_ID)
Position: 1
Rule ID: abc123
URL: app.example.com/*
Description: Forwarding URL (Status Code: 302 - Temporary Redirect, Url: https://destino.example.com/)
Action: Enabled
```

## Observações

- `Position` é conveniente para operação manual, mas não é um identificador estável como `Rule ID`
- para automação, prefira `--rule-id`
- em seleções múltiplas, o script aplica as alterações e imprime as regras atualizadas no final
- em container, você pode usar tanto variáveis de ambiente do runtime quanto um `.env` montado no diretório da aplicação
