# Checklist da primeira coleta

- Confirmar IP do MikroTik.
- Confirmar SSH habilitado.
- Confirmar SSH restrito ao IP do PC ou VPN.
- Confirmar usuario `ia-automation`.
- Confirmar grupo read-only ou permissao minima necessaria.
- Confirmar que nao esta usando `admin`.
- Confirmar `.env` fora do Git.
- Rodar `.\.venv\Scripts\python.exe src\main.py doctor`.
- Rodar `.\.venv\Scripts\python.exe src\main.py ssh-check`.
- Rodar `.\.venv\Scripts\python.exe src\main.py collect`.
- Rodar `.\.venv\Scripts\python.exe src\main.py validate-commands`.
- Rodar `.\.venv\Scripts\python.exe src\main.py collect --execute`.
- Revisar export sanitizado.
- Revisar relatorio.
- Fazer `git status`.
- Commitar apenas arquivos seguros.

