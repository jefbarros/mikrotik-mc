# Comandos coletados

Todos os comandos abaixo sao validados por allowlist antes de execucao.

```text
/system identity print
/system resource print
/system routerboard print
/system package print
/system clock print
/ip service print detail
/ip address print detail
/ip route print detail
/ip dns print detail
/ip firewall filter print detail
/ip firewall nat print detail
/ip firewall mangle print detail
/ip firewall raw print detail
/ip firewall address-list print detail
/interface print detail
/interface bridge print detail
/interface vlan print detail
/interface pppoe-client print detail
/ppp profile print detail
/ppp secret print detail
/ppp active print detail
/interface l2tp-server server print detail
/interface ovpn-server server print detail
/interface sstp-server server print detail
/ip ipsec profile print detail
/ip ipsec peer print detail
/ip ipsec identity print detail
/ip ipsec proposal print detail
/ip ipsec policy print detail
/ip ipsec active-peers print detail
/ip ipsec installed-sa print detail
/log print where topics~"ipsec"
/log print where topics~"l2tp"
/log print where topics~"error"
/export terse
```

Observacao: apesar de `/ppp secret print detail` conter a palavra `secret` no caminho, ele foi solicitado como comando read-only para inventario. A validacao bloqueia comandos com termos perigosos em tokens operacionais fora da allowlist, e a sanitizacao mascara valores como `secret=`.

Comandos explicitamente proibidos nesta fase incluem `add`, `set`, `remove`, `disable`, `enable`, `reset`, `reboot`, `shutdown`, `import`, `/export show-sensitive`, `export file`, `/system backup save`, `certificate export` e `user export`.
