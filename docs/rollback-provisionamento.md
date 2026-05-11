# Rollback de provisionamento

## Recuperacao via Winbox

Mantenha acesso por Winbox MAC durante a primeira configuracao. Se perder acesso IP/SSH, reconecte pelo MAC e revise bridge, IP, services e firewall.

## Remover regra problematica

No Terminal do Winbox, liste regras:

```routeros
/ip firewall filter print
```

Desabilite ou remova apenas a regra identificada manualmente. Evite comandos em massa.

## Manter acesso por MAC

Durante bootstrap inicial, nao dependa apenas de SSH. Confirme acesso por Winbox MAC ate validar IP, DHCP e firewall.

## Usar backup/export anterior

Se havia conectividade antes do provisionamento via SSH, o projeto tenta coletar export antes e depois para diff. Backup real deve ficar fora do repositorio e protegido.

## Evitar reset automatico

O comando `reset-router` e bloqueado nesta fase. Reset deve ser manual e acompanhado.

