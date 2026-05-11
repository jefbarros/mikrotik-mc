# Producao read-only

## Passo a passo

1. Criar a venv: `python -m venv .venv`.
2. Instalar dependencias: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
3. Criar `.env`: `Copy-Item .env.example .env -Force`.
4. Editar `.env` com host, porta e usuario dedicado.
5. Rodar `.\.venv\Scripts\python.exe src\main.py doctor`.
6. Rodar `.\.venv\Scripts\python.exe src\main.py ssh-check`.
7. Rodar `.\.venv\Scripts\python.exe src\main.py collect`.
8. Revisar a lista de comandos do dry-run.
9. Rodar `.\.venv\Scripts\python.exe src\main.py validate-commands`.
10. Executar coleta real: `.\.venv\Scripts\python.exe src\main.py collect --execute`.

## Checklist de primeira execucao

Use `docs/checklist-primeira-coleta.md` antes da primeira coleta real.

## Como revisar relatorio

Revise servicos administrativos, firewall, NAT, VPN, IPsec e logs de erro. O relatorio nao inventa causa; quando nao ha certeza, ele marca como nao avaliado automaticamente.

## Como armazenar exports

Armazene somente exports sanitizados. Nomes com `raw`, `sensitive`, `.backup` ou `.rsc.sensitive` sao ignorados pelo Git.

## Como comparar coletas

```powershell
.\.venv\Scripts\python.exe src\main.py diff --before "exports\antigo.txt" --after "exports\novo.txt"
```

## Frequencia recomendada

Para uso manual, execute apos mudancas planejadas e em revisoes periodicas. Evite automatizar alteracoes; esta fase e somente coleta e auditoria.

## Rotina futura

Fases futuras podem gerar plano de mudanca, validacao e aprovacao humana. A execucao automatica de escrita nao faz parte desta versao.

