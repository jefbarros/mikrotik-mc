# Troubleshooting

## Activate.ps1 bloqueado

Use o Python da venv diretamente:

```powershell
.\.venv\Scripts\python.exe src\main.py collect
```

## TCP/SSH inacessivel

Rode:

```powershell
.\.venv\Scripts\python.exe src\main.py ssh-check
```

No MikroTik, revise:

```routeros
/ip service print detail where name=ssh
```

Verifique firewall input, `address=` no servico SSH, IP correto e conectividade por rede local/VPN.

## Timeout SSH

Pode indicar rota incorreta, firewall, VPN fora, porta errada ou servico SSH desabilitado.

## Authentication failed

Revise usuario, senha e permissao. Use usuario dedicado e evite `admin`.

## Host key changed

Confirme se o IP pertence ao MikroTik esperado. Se `MIKROTIK_STRICT_HOST_KEY_CHECKING=true`, a host key precisa estar conhecida pelo sistema.

## Comando bloqueado

O comando nao esta na allowlist ou contem termo perigoso. Esta fase aceita apenas comandos read-only definidos em `src/commands.py`.

## Relatorio vazio

Confirme permissoes do usuario read-only e se os comandos retornaram saida. Veja tambem o export sanitizado.

## Export nao gerado

Verifique permissao de escrita em `exports/` e erros no terminal. Logs ficam em `logs/YYYY-MM-DD_mikrotik_ai.log`.

## Permissao read-only insuficiente

Alguns menus podem exigir politicas especificas de leitura no RouterOS. Ajuste o grupo do usuario sem conceder permissoes de escrita.

## Algoritmo SSH incompativel

RouterOS antigo ou politicas SSH restritivas podem falhar com Paramiko. Confirme RouterOS v7.22.2, host key e algoritmos aceitos.
