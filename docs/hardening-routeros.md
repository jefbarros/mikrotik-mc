# Hardening RouterOS

## Servicos inseguros

Desabilite Telnet, FTP, WWW, API e API-SSL quando nao forem necessarios. Esta fase deixa esses servicos desabilitados no profile exemplo.

## Winbox e SSH restritos

Winbox e SSH devem usar `address=` restritivo, nunca `0.0.0.0/0`. Prefira IP do PC de gerenciamento ou rede VPN.

## Usuario dedicado

Use `ia-automation` para automacao, com grupo minimo. Evite usar `admin` no dia a dia.

## Firewall input

Permita established/related, descarte invalid, permita DHCP/DNS/ICMP da LAN conforme necessidade, permita SSH/Winbox somente das origens permitidas e mantenha drop final.

## DNS seguro

Se `allow-remote-requests=yes`, permita consultas apenas da LAN no firewall input.

## API/REST

Nao exponha API ou REST na internet. Esta fase nao usa REST API.

## Admin padrao

Nao desabilite `admin` antes de confirmar que o novo usuario funciona. O profile exemplo deixa `disable_default_admin: false`.

