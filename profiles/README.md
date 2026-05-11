# Profiles

Este diretorio contem perfis YAML de provisionamento. Use `example.branch-reset.yaml` como base e crie um arquivo local por roteador.

Nao coloque senhas reais no YAML. Segredos devem vir de variaveis de ambiente, por exemplo `MIKROTIK_AUTOMATION_PASSWORD`.

Arquivos `profiles/*secret*` e `profiles/*.local.yaml` sao ignorados pelo Git.

