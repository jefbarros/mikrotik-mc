# Provisionamento inicial seguro

## Diferenca entre collect e provision

`collect` e a Fase 1: read-only, coleta estado e gera relatorios. `provision` e a Fase 2: prepara configuracao inicial e pode alterar o roteador somente com flags explicitas e confirmacao textual.

## Quando usar render-bootstrap

Use `render-bootstrap` quando a RB foi resetada e voce ainda nao sabe se IP/SSH estao disponiveis. O comando nao conecta no MikroTik e gera um `.rsc` para colar no Winbox Terminal.

```powershell
.\.venv\Scripts\python.exe src\main.py render-bootstrap --profile profiles\minha-rb.yaml
```

## Quando usar provision --execute

Use apenas quando SSH estiver acessivel, o profile estiver validado, o script `.rsc` tiver sido revisado e voce aceitar alterar o roteador.

```powershell
.\.venv\Scripts\python.exe src\main.py provision --profile profiles\minha-rb.yaml --execute --i-understand-this-changes-router
```

Antes de aplicar, o projeto gera script, plano Markdown, tenta coletar estado anterior e exige digitar `APLICAR`.

## Riscos

Provisionamento pode causar lockout se IP, firewall, portas ou origem de gerenciamento estiverem errados. Por isso o profile valida acesso Winbox/SSH restrito, drop final depois das regras allow e bloqueia reset/reboot/import/fetch.

## Fluxo recomendado

1. Copiar profile exemplo.
2. Validar profile.
3. Renderizar bootstrap.
4. Acessar via Winbox MAC.
5. Colar bootstrap.
6. Testar SSH.
7. Coletar estado.
8. Renderizar configuracao completa.
9. Aplicar via SSH somente se necessario.

