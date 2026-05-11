# Politica de segredos

## O que e segredo

Senha, token, chave privada, certificado sensivel, pre-shared key, API key, credencial PPP/IPsec/WireGuard/WPA, email real e qualquer valor que permita acesso ou identificacao sensivel.

## O que e mascarado

O sanitizer mascara campos como `password=`, `passwd=`, `pwd=`, `secret=`, `shared-secret=`, `pre-shared-key=`, `key=`, `private-key=`, `token=`, `api-key=`, `apikey=`, `access-token=`, `refresh-token=`, `certificate=`, `identity=`, `auth-key=`, `passphrase=`, `smtp-password=`, `wireguard-private-key=` e `wpa-pre-shared-key=`.

Emails reais tambem sao mascarados como `***@***.***`.

## O que nunca deve ser commitado

- `.env`
- backups reais
- exports raw
- arquivos com `sensitive`
- chaves `*.key`, `*.pem`, `*.p12`, `*.pfx`
- qualquer arquivo com senha ou segredo real

## Revisao antes de commit

```powershell
git status
git diff
git diff --cached
```

Procure por `password=`, `secret=`, `token=`, `private-key=`, emails reais e arquivos inesperados.

## Se um segredo for commitado por engano

1. Revogue ou troque o segredo no MikroTik/sistema de origem.
2. Remova o arquivo do Git.
3. Reescreva historico somente se necessario e com cuidado.
4. Force push apenas se a politica do repositorio permitir.
5. Registre o incidente e confirme que o segredo antigo nao funciona mais.

