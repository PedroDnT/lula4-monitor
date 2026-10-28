# Como os dados do site se atualizam

## Ao vivo (sem commit)

O navegador lê estas fontes a cada visita: API pública do SILO (curvas, Focus, séries fiscais, PTAX, fluxo estrangeiro), B3 (DI, DOL e DAP), Binance, BCB Olinda. O `worker.js` cobre Yahoo, CDS da OBM e Selic (rotas `/api/*`).

## Por arquivo (a rotina diária faz commit)

Estes arquivos vêm de julgamento ou de fontes sem API aberta. A rotina "Brazil rates daily monitor" (dias úteis, 11:20 de Brasília, 14:20 UTC) deve gravá-los e fazer commit na `main`. O Cloudflare publica sozinho.

| Arquivo | O que muda | Quem escreve |
| --- | --- | --- |
| `data/relatorio/pesos.json` | pesos de partida e "agora" dos 3 cenários | rotina diária. O painel intraday também lê `start` e `di_jan29_move_bp` daqui |
| `data/relatorio/fatos.json` | fatos novos, com degrau e motivo | rotina diária |
| `data/relatorio/agenda.json` | agenda e gatilhos | rotina diária / revisão semanal |
| `data/relatorio/params.json` | `m1`, `m2`, `m3` (próximas 3 reuniões do Copom) e `focus_from` | rotina diária, a cada reunião |
| `data/relatorio/copom_cal.json`, `feriados.json` | calendário | manual, 1 vez por ano |
| `data/dominancia/scenarios.json`, `scenario_history.json` | cópia dos pesos e histórico | rotina diária (copia de `pesos.json`; o monitor não calcula pesos) |
| `data/dominancia/lft.json`, `rolagem.json`, `leiloes.json`, `focus_debt.json` | dados mensais do Tesouro e do Focus | rotina diária ou mensal |
| `data/dominancia/budget.json`, `canais.json`, `contabilidade.json`, `obrigatorias.json`, `calib.json` | orçamento 2027, calibração | manual, quando sair a LOA ou uma revisão |
| `data/intraday/history.json` | histórico-base do painel intraday | opcional |

Cada arquivo é um array JSON de linhas, no mesmo formato de antes. Não mude os nomes das colunas.

Os pesos de partida vêm só de fatos, nunca de preço. A coluna `probability` (peso de agora) vem da regra do DI.
