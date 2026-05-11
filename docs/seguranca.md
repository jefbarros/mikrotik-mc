# Seguranca

## Modelo de seguranca

O projeto roda localmente no Windows e acessa o MikroTik somente via SSH read-only. O fluxo esperado e: operador revisa ambiente, executa dry-run, testa TCP, executa coleta read-only, salva export sanitizado, gera relatorio e versiona apenas artefatos seguros.

## Usuario dedicado

Use um usuario especifico, por exemplo `ia-automation`, com permissao minima para leitura. Evite `admin`. Isso melhora rastreabilidade, reduz impacto de vazamento de credencial e facilita revogacao.

## Rede local ou VPN

SSH, API e REST do RouterOS nao devem ficar expostos na internet. Acesso administrativo deve ocorrer por rede local, VPN ou origem administrativa restrita.

## Segredos e sanitizacao

O sanitizer mascara campos como `password=`, `secret=`, `shared-secret=`, `private-key=`, `token=`, certificados, chaves, emails e outros campos sensiveis. Ainda assim, revise exports e relatorios antes de commit.

## GitOps seguro

Git deve armazenar codigo, docs, relatorios e exports sanitizados. `.env`, chaves privadas, backups reais, exports raw e arquivos sensiveis nunca devem ser commitados.

## Export sanitizado vs backup real

O export sanitizado serve para auditoria, diff e analise. Ele nao substitui backup real do RouterOS. Backups reais devem ser armazenados fora deste repositorio, com controle de acesso e criptografia.

## Limites da automacao

Esta fase nao altera configuracao. Comandos de escrita sao bloqueados por allowlist e denylist. Fases futuras de mudanca precisam de plano, aprovacao humana, backup previo, validacao e rollback documentado.
