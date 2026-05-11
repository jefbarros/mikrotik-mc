# Roadmap

## Fase 1 - Coleta read-only via SSH

Coletar informacoes operacionais e configuracao textual sanitizada sem alterar o MikroTik.

## Fase 2 - Provisionamento inicial seguro do MikroTik

Gerar profile YAML, bootstrap `.rsc`, configuracao completa revisavel, validacoes de lockout e provisionamento controlado com flags explicitas.

## Fase 3 - Comparacao de exports antes/depois

Comparar exports sanitizados em Git para identificar diferencas e mudancas de configuracao.

## Fase 4 - Relatorio de risco com IA

Usar os dados sanitizados para gerar analise assistida por IA, sem enviar segredos.

## Fase 5 - Geracao de plano de mudanca

Criar propostas de alteracao documentadas, revisaveis e separadas da execucao.

## Fase 6 - Aplicacao assistida com aprovacao humana

Permitir aplicacao controlada apenas apos aprovacao explicita, com rollback planejado.
Uma fase futura podera gerar `change_plan.json`, validar comandos, exigir aprovacao humana, criar backup pre-mudanca, executar de forma controlada e documentar rollback. Nenhum comando `apply` funcional existe na fase read-only.

## Fase 7 - Integracao com Ansible

Converter rotinas aprovadas em automacao declarativa e versionada.

## Fase 8 - Painel interno ou n8n

Criar fluxo interno para orquestrar coletas, relatorios e aprovacoes.

## Fase 9 - Monitoramento com Zabbix/LibreNMS/Grafana

Integrar dados operacionais com monitoramento continuo e alertas.
