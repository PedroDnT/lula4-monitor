# Como os dados do site se atualizam

## Ao vivo (sem commit)

O navegador lê os dados do SILO pela rota `/api/silo` do próprio Worker. O Worker
autentica na API REST v2 privada com `SILO_USER_JWT`; não há acesso direto a
Postgres nem credencial no navegador. B3, Binance e BCB completam as fontes ao vivo.
O `worker.js` também cobre Yahoo, CDS e Selic.

## Rotina por arquivos

A tarefa “Brazil rates daily monitor” foi removida por Pedro. Não há substituta agendada. A implementação e a proposta de execução diária às 11h20 de Brasília (Julgamento operacional, ainda a confirmar), fontes, cálculos, bloqueios e pendências estão em [rotina/README.md](rotina/README.md).

A nova rotina prepara um lote validado diretamente para este repositório, independente de artifacts do claude.ai. Atualização por branch e PR, sem commit direto na main. O agendador e qualquer provedor de IA continuam por escolher.

| Arquivo | Responsabilidade |
| --- | --- |
| `data/relatorio/pesos.json` | Partida aprovada e agora calculado deterministicamente |
| `data/relatorio/fatos.json` | Fatos com fonte, fatores aprovados e controle contra reaplicação |
| `data/dominancia/scenarios.json` | Mesmos pesos e marcas de `pesos.json` |
| `data/dominancia/scenario_history.json` | Histórico de partida e agora; lacunas legadas preservadas |
| `docs/rotina/state.json` | Ledger de aplicações, hashes, fontes e mudanças |
| `data/relatorio/agenda.json`, `params.json`, `copom_cal.json`, `feriados.json` | Revisão manual, fora da escrita automática deste PR |
| Demais arquivos fiscais e `data/intraday/history.json` | Responsabilidade anterior; sem novo coletor neste PR |

As colunas existentes são preservadas. Os pesos de partida usam somente fatos e julgamento aprovado; preço entra apenas no cálculo de agora. Pesos, marcas e metodologia não podem ser alterados pela rotina por iniciativa própria.
