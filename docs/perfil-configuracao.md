# Perfil de configuracao YAML

## project

Define nome do projeto, site, modelo e versao alvo do RouterOS.

## management

Campos de identidade, timezone, usuario de automacao, grupo, variavel de ambiente da senha e origens permitidas para Winbox/SSH.

Nunca use `admin` como `automation_user`. Senha deve vir de `automation_password_env`.

## interfaces

Define WAN e bridge LAN. Nesta fase, WAN suporta DHCP ou PPPoE como estrutura futura; o renderer implementa base WAN DHCP.

LAN exige bridge, portas e IP/CIDR.

## dhcp_server

Define pool, gateway e DNS do DHCP LAN. O range deve estar dentro da rede LAN.

## dns

Define servidores DNS e se o roteador respondera consultas da LAN.

## services

Winbox e SSH podem ficar habilitados, mas devem ter address restritivo. Telnet, FTP, WWW, API e API-SSL devem ficar desabilitados nesta fase.

## firewall

Ativa regras input basicas, NAT masquerade e drop final. A validacao exige drop final para evitar roteador aberto.

## hardening

Controla usuario de automacao, admin padrao e hardening basico. `disable_default_admin=true` exige `create_automation_user=true`.

## vpn e ipsec

Campos existem para fases futuras. Nesta fase devem permanecer `configure_now: false`.

## Segredos

Use variaveis de ambiente:

```env
MIKROTIK_AUTOMATION_PASSWORD=
MIKROTIK_PPPOE_USER=
MIKROTIK_PPPOE_PASSWORD=
```

Nao salve senha real em profiles versionados.

