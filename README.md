# mikrotik-ai-automation

Automacao local, segura e read-only para MikroTik RouterOS via SSH. O projeto coleta informacoes operacionais e de configuracao, sanitiza segredos, gera export textual, cria relatorio Markdown, permite diff entre coletas e prepara uma base GitOps para analise futura por IA.

Status:

- Fase 1: producao read-only para coleta, diagnostico, diff e relatorio.
- Fase 2: provisionamento inicial controlado, com render por padrao e aplicacao somente com flags explicitas.

## O que faz

- Valida ambiente local com `doctor`.
- Valida comandos read-only por allowlist e denylist.
- Executa dry-run sem senha e sem conexao SSH.
- Testa porta SSH via TCP sem login.
- Coleta via SSH somente com `--execute`.
- Sanitiza senhas, tokens, chaves, certificados, emails e campos sensiveis antes de salvar.
- Gera exports em `exports/` e relatorios em `reports/`.
- Gera diff Markdown entre duas coletas.
- Registra logs seguros em `logs/YYYY-MM-DD_mikrotik_ai.log`.
- Valida profile YAML de provisionamento.
- Gera bootstrap `.rsc` para RB resetada.
- Gera configuracao completa `.rsc` revisavel.
- Simula provisionamento por padrao.

## O que nao faz

- Nao executa comandos de escrita.
- Nao implementa REST API.
- Nao cria servidor web.
- Nao expoe SSH, API ou REST para internet.
- Nao salva backup binario do RouterOS.
- Nao substitui backup operacional seguro fora do repositorio.
- Nao executa reset automatico.
- Nao configura VPN, IPsec, load balance, VLANs complexas, QoS, WireGuard, BGP/OSPF, Hotspot ou CAPsMAN nesta fase.

## Requisitos

- Windows com PowerShell.
- Python 3.11 ou superior.
- Acesso ao MikroTik por rede local ou VPN.
- SSH habilitado no MikroTik.
- Usuario dedicado, exemplo `ia-automation`, com permissao minima para leitura.

## Instalacao no Windows sem ativar venv

Use o Python da venv diretamente. Isso evita o problema de `Activate.ps1` bloqueado por politica de execucao.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env -Force
notepad .env
```

Configure:

```env
MIKROTIK_HOST=192.168.88.1
MIKROTIK_SSH_PORT=22
MIKROTIK_USER=ia-automation
MIKROTIK_PASSWORD=
MIKROTIK_TIMEOUT=15
MIKROTIK_STRICT_HOST_KEY_CHECKING=false
PROJECT_NAME=mikrotik-ai-automation
```

Se `MIKROTIK_PASSWORD` ficar vazio, a senha sera solicitada apenas em `collect --execute`.

## Dry-run

Nao pede senha, nao abre SSH e nao envia comandos.

```powershell
.\.venv\Scripts\python.exe src\main.py collect
```

Mensagem esperada:

```text
DRY-RUN: nenhuma conexao SSH foi aberta e nenhum comando foi enviado.
```

## Doctor

Valida ambiente local, `.env`, diretorios, venv e dependencias sem imprimir senha.

```powershell
.\.venv\Scripts\python.exe src\main.py doctor
```

## SSH check

Testa somente TCP host/porta, sem senha e sem login.

```powershell
.\.venv\Scripts\python.exe src\main.py ssh-check
```

Se falhar, verifique no MikroTik:

```routeros
/ip service print detail where name=ssh
```

Tambem revise firewall input, `address=` em `/ip service`, IP correto do MikroTik e conectividade por VPN/rede local.

## Validar comandos

```powershell
.\.venv\Scripts\python.exe src\main.py validate-commands
```

## Coleta real read-only

Nao rode antes de revisar `docs/checklist-primeira-coleta.md`.

```powershell
.\.venv\Scripts\python.exe src\main.py collect --execute
```

Saidas:

- `exports/YYYY-MM-DD_HHMMSS_routeros_collect_sanitized.txt`
- `reports/YYYY-MM-DD_HHMMSS_relatorio_mikrotik.md`
- `logs/YYYY-MM-DD_mikrotik_ai.log`

## Comparar coletas

```powershell
.\.venv\Scripts\python.exe src\main.py diff --before "exports\arquivo_antigo.txt" --after "exports\arquivo_novo.txt"
```

## Fase 2: provisionamento inicial controlado

O comando padrao nunca altera o MikroTik. Renderizar bootstrap, renderizar configuracao e validar profile nao conectam no roteador e nao pedem senha SSH.

### Validar profile

```powershell
.\.venv\Scripts\python.exe src\main.py validate-profile --profile profiles\example.branch-reset.yaml
```

### Renderizar bootstrap

```powershell
.\.venv\Scripts\python.exe src\main.py render-bootstrap --profile profiles\example.branch-reset.yaml
```

Use o bootstrap quando a RB estiver resetada e voce acessa por Winbox MAC. O console mostra o script sanitizado e o script sensivel local. Nao commite o arquivo sensivel.

### Renderizar configuracao completa

```powershell
.\.venv\Scripts\python.exe src\main.py render-config --profile profiles\example.branch-reset.yaml
```

### Simular provisionamento

```powershell
.\.venv\Scripts\python.exe src\main.py provision --profile profiles\example.branch-reset.yaml
```

### Aplicar provisionamento via SSH

Use somente depois de revisar o `.rsc`, confirmar conectividade SSH e aceitar alterar o roteador:

```powershell
.\.venv\Scripts\python.exe src\main.py provision --profile profiles\minha-rb.yaml --execute --i-understand-this-changes-router
```

O comando ainda exige confirmacao textual `APLICAR`.

### Reset bloqueado

```powershell
.\.venv\Scripts\python.exe src\main.py reset-router
```

Esse comando sempre falha por seguranca.

## Fluxo recomendado para RB resetada

1. Criar profile:

```powershell
copy profiles\example.branch-reset.yaml profiles\minha-rb.yaml
notepad profiles\minha-rb.yaml
```

2. Validar:

```powershell
.\.venv\Scripts\python.exe src\main.py validate-profile --profile profiles\minha-rb.yaml
```

3. Renderizar bootstrap:

```powershell
.\.venv\Scripts\python.exe src\main.py render-bootstrap --profile profiles\minha-rb.yaml
```

4. Acessar via Winbox MAC.
5. Colar script bootstrap no Terminal.
6. Testar conectividade:

```powershell
.\.venv\Scripts\python.exe src\main.py ssh-check
```

7. Coletar estado:

```powershell
.\.venv\Scripts\python.exe src\main.py collect --execute
```

8. Se necessario, renderizar config completa:

```powershell
.\.venv\Scripts\python.exe src\main.py render-config --profile profiles\minha-rb.yaml
```

9. Aplicar somente se tiver certeza:

```powershell
.\.venv\Scripts\python.exe src\main.py provision --profile profiles\minha-rb.yaml --execute --i-understand-this-changes-router
```

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Scripts auxiliares

Os scripts em `scripts/` sao opcionais. Se o PowerShell bloquear `.ps1`, rode os comandos diretos acima.

- `scripts\run-dry.ps1`
- `scripts\run-doctor.ps1`
- `scripts\run-collect.ps1`
- `scripts\run-tests.ps1`

## Versionamento seguro

Pode versionar:

- `src/`, `tests/`, `docs/`, `README.md`, `.env.example`, `requirements.txt`, `pyproject.toml`.
- Exports sanitizados cujo nome nao contenha `raw` ou `sensitive`.
- Relatorios Markdown em `reports/`.

Nao versionar:

- `.env`
- `.venv/`
- chaves `*.key`, `*.pem`, `*.p12`, `*.pfx`
- arquivos com `raw`, `sensitive`, `.backup` ou `.rsc.sensitive`
- `generated/*sensitive*`
- profiles locais ou secretos

Antes de commit:

```powershell
git status
git diff --cached
```

## Troubleshooting rapido

- `Activate.ps1` bloqueado: use `.\.venv\Scripts\python.exe ...`.
- `TcpTestSucceeded False` ou `ssh-check` falhando: revise SSH habilitado, firewall input, `address=` do servico SSH e VPN/rede local.
- Porta diferente de 22: ajuste `MIKROTIK_SSH_PORT`.
- Credencial invalida: revise usuario dedicado e senha.
- Paramiko/algoritmo SSH incompativel: revise RouterOS, host key e politicas SSH.
- Relatorio vazio: confirme se os comandos retornaram saida e se o usuario tem permissao read-only suficiente.

## Checklist antes da primeira coleta real

1. Confirmar IP do MikroTik.
2. Confirmar SSH habilitado e restrito.
3. Confirmar usuario `ia-automation`, sem usar `admin`.
4. Confirmar `.env` fora do Git.
5. Rodar `doctor`.
6. Rodar `ssh-check`.
7. Rodar dry-run.
8. Rodar `validate-commands`.
9. Executar `collect --execute`.
10. Revisar export sanitizado, relatorio e `git status`.
