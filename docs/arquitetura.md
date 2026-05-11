# Arquitetura

## Fluxo geral

```text
Operador -> Codex/IA -> Projeto local -> SSH read-only -> MikroTik
                                    -> export sanitizado -> relatorio -> Git
```

## Componentes internos

- `main.py`: CLI e orquestracao.
- `config.py`: leitura e validacao do `.env`.
- `commands.py`: allowlist e denylist.
- `ssh_client.py`: conexao SSH e execucao validada.
- `collector.py`: coleta, tolerancia a erro por comando e export sanitizado.
- `sanitizer.py`: mascara segredos.
- `report.py`: relatorio tecnico.
- `diff.py`: comparacao de coletas.
- `doctor.py`: diagnostico local e teste TCP.
- `logger.py`: logs seguros.
- `exceptions.py`: erros amigaveis.
- `paths.py`: caminhos padronizados.

## Fluxo de coleta

1. Operador roda dry-run.
2. CLI valida allowlist.
3. Com `--execute`, carrega `.env` e solicita senha se necessario.
4. SSH conecta no MikroTik.
5. Cada comando passa por validacao.
6. Saida e erro sao sanitizados antes de salvar.
7. Export e relatorio sao gerados.
8. Logs registram comandos, status e caminhos, sem conteudo bruto.

## Fluxo de diff

1. Operador informa dois exports sanitizados.
2. O projeto sanitiza novamente o conteudo lido.
3. As secoes por comando sao comparadas.
4. Um relatorio Markdown de diferencas e gravado em `reports/`.

## Futuro plano de mudanca

Uma fase futura pode gerar plano de mudanca com aprovacao humana, backup previo, validacao de comandos, execucao controlada e rollback documentado. Esta versao nao implementa aplicacao de mudancas.

