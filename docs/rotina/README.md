# Rotina diária única

Estado: implementação local, sem agendamento ativo. Não depende de artifacts do claude.ai nem de provedor de IA. A tarefa “Brazil rates daily monitor” foi removida por Pedro.

## Desenho mínimo e decisões pendentes

Uma execução reúne fatos com fontes, lê o fechamento do DI1F29 pela API pública do SILO, aplica apenas fatores aprovados, calcula o “agora” a partir da partida, valida e prepara um lote fora do checkout. A atualização entra por branch e PR. O comando não faz commit, push, merge ou deploy.

Proposta operacional (Julgamento, a confirmar): execução diária às **11h20 de Brasília**, `America/Sao_Paulo` (14h20 UTC no regime atual). Mesmo em fins de semana e feriados pode haver fatos novos; o DI continua sendo o último pregão anterior. O site documenta carga do SILO por volta das **03h de Brasília** (Dado: `metodo.html`, informação operacional ainda sem SLA). Não tentar usar o pregão corrente antes de fechar.

**Onde agendar:** em um único executor externo que obtenha o checkout, execute o comando e abra um PR, com armazenamento de logs e execução serial. O produto de agendamento ainda não foi escolhido. Opções para decisão de Pedro: automação do Codex com ambiente configurado; cron em executor próprio; GitHub Actions. Nenhuma foi configurada. Não há arquivo de workflow, cron, credencial de escrita ou provedor de IA novo neste PR. Se houver IA futuramente, ela poderá propor fatos e trechos; não escolherá fatores nem escreverá números de mercado.

Antes de ativar: escolher executor, retenção de logs, autenticação para branches/PRs e processo de revisão dos fatos; confirmar o calendário; inspecionar a tarefa semanal e retirar a regra antiga somente com autorização. O relato de que ela usa `0,3` não foi verificado neste chat. Evitar duas rotinas escrevendo os mesmos arquivos.

## Executar

Python 3.11 ou superior, apenas biblioteca padrão. Sem instalação de pacotes e sem acesso direto a Postgres.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/daily_monitor.py validate
python3 scripts/daily_monitor.py prepare \
  --facts docs/rotina/fatos.example.json \
  --date 2026-11-04 \
  --output /tmp/lula4-2026-11-04
```

Sem `--date`, usa a data atual de Brasília. `[]` é uma declaração explícita de que não há fatos novos aprovados naquele lote; o programa não afirma ter feito uma busca jornalística completa. Cabe ao coletor/revisor reunir os fatos. Não se implementa uma pesquisa autônoma sem escolher fontes e provedor.

O destino deve estar fora do checkout e não pode existir. A preparação só entrega o diretório final após todas as verificações. Contém os arquivos permitidos, o ledger, `report.json`, `manifest.json` e a resposta bruta `silo-response.json`. O relatório registra data do pregão, consulta, hashes das fontes, trechos, origens, partida antes/depois, fatores e cálculo. Guardar o lote e os logs no executor escolhido; retenção ainda pendente.

Após revisar o relatório e o diff, numa branch exclusiva:

```sh
python3 scripts/daily_monitor.py apply --batch /tmp/lula4-2026-11-04
python3 scripts/daily_monitor.py validate
git diff --check
git diff -- data/relatorio data/dominancia docs/rotina/state.json
```

`apply` confere o hash de cada entrada e saída, monta uma cópia candidata e valida antes de escrever. Recusa checkout que mudou e lote alterado. Escreve apenas pesos, fatos, cenários, histórico e ledger; não toca agenda, parâmetros, páginas, intraday. Substitui arquivos individualmente e tenta restaurar os originais em exceções; uma interrupção abrupta do processo pode deixar aplicação parcial. Usar checkout exclusivo e nunca publicar durante essa etapa. Recuperar do Git e reaplicar o lote validado após interrupção. O executor futuro precisa impedir concorrência.

Depois da validação, o operador pode fazer commit e abrir PR na branch. Não aplicar na main. A main publica automaticamente segundo o README existente; este PR não executa essa publicação.

## Contrato dos fatos

Fatos novos usam as colunas existentes de `fatos.json`, mais os campos abaixo. O leitor atual do site ignora colunas extras.

| Campo | Conteúdo |
| --- | --- |
| `id` | Identificador estável e único do acontecimento |
| `origin` | Norma, Dado, Cálculo, Regressão, Literatura, Julgamento ou Projeção |
| `channel` | Canal canônico; reutilizar o existente para o mesmo assunto |
| `evidence_quote` | Trecho literal na resposta UTF-8 da URL HTTPS, ao menos 40 caracteres (Norma operacional para evitar evidência vazia) |
| `approval` | `{"by":"Pedro","reference":"https://…","origin":"Julgamento"}`; referência real à aprovação dos fatores |
| `status` | `Na partida`, somente após aprovação |

O comando confere a presença da referência e do trecho, não autentica a autoria da aprovação nem interpreta a notícia. O revisor precisa confirmar ambos. Uma resposta HTTP boa com paywall ou desafio não basta: sem trecho, falha. Sites renderizados por JS ou outras codificações precisam de adaptação explícita futura, sem contornar o bloqueio com números inventados. Não incluir instruções ao leitor nem recomendação de compra/venda nos textos destinados ao site.

Identificador já aplicado e conteúdo idêntico é ignorado. Conteúdo diferente com o mesmo ID é erro. Mesma URL e texto normalizado com outro ID é erro. Paráfrases do mesmo acontecimento não são detectadas semanticamente: o revisor deve preservar o ID canônico. Canal repetido admite no máximo o degrau fraco; os canais legados foram inicializados das descrições existentes. Dois acontecimentos do mesmo canal no lote também ficam sujeitos ao limite.

## Cálculos e origem dos números

| Item | Origem e referência |
| --- | --- |
| Partida inicial 49/31/20 | Julgamento: decisão de Pedro em 04/11/2026, snapshot `6b023ca`, `pesos.json`; não reconstruída retroativamente |
| Marcas +50/+180/+320 bp | Julgamento: marcas existentes em `pesos.json` e `index.html`, preservadas |
| Base 12,640% de 23/10/2026 | Dado: base de referência definida no monitor e reafirmada por Pedro; preservada |
| σ = 100 bp | Dado: calibração descrita em `metodo.html`; não reestimada neste PR |
| Fatores permitidos 0,77/0,87/0,95/1/1,05/1,15/1,30 | Julgamento: escala de Pedro, `relatorio.html`, preservada inclusive arredondamentos publicados |
| Nova partida | Cálculo: normalizar partida × fatores aprovados, em ordem do lote, sem arredondar valores armazenados |
| Movimento acumulado | Cálculo: (taxa SILO em % − 12,640) × 100; não é variação diária |
| Agora | Cálculo: normalizar partida × exp(−(movimento − marca)² / (2 × 100²)); implementação equivalente em log para estabilidade |
| Referência em +232 bp | Cálculo: 18,70/54,15/27,15, arredondado somente para exibição |

`state.json` começa com os fatos já incorporados marcados como aplicados. Os hashes impedem alterações dos datasets por fora da rotina passarem despercebidas. Não é prova criptográfica de aprovação: Git e revisão continuam necessários. Cada novo lote guarda no ledger as fontes, julgamentos, fatores, partida antes/depois e resultado. Repetir a mesma data com os mesmos dados é idempotente; novos fatos ou fechamento diferente após fechar o lote são conflitos que exigem revisão, não substituição automática. O dia seguinte sempre recalcula a partir de `start`, nunca da posterior anterior.

## Fontes, validações e falhas

Mercado: SILO API `api.future_series`, `p_ticker=DI1F29`, `p_from=2026-10-23`, mesma rota pública usada em `index.html`. Headers de schema `api`, chave pública de leitura já usada pelo site. Não usa Postgres nem segredo de banco. Valida unidade percentual, base, datas únicas, último pregão esperado e números finitos; nenhuma substituição por preço ao vivo ou valor anterior em caso de falha. O calendário usa `feriados.json` e fins de semana; cobertura operacional limitada de 03/11/2026 a 31/12/2027 (Norma operacional desta implementação), sujeita à revisão do calendário da B3. Não presume feriado desconhecido como dia sem pregão.

Fatos: URL, fonte, trecho literal, hash da resposta, aprovação e canal. Origem do relato não se confunde com origem do fator: o fator é sempre Julgamento; o peso derivado é Cálculo.

Valida todos os JSONs de `data/` quanto à sintaxe e finitude. Para os datasets da rotina, verifica IDs, escala, somas, marcas, datas, igualdade entre pesos/cenários, histórico e ledger. Para os lotes novos verifica também a posterior determinística. Os valores legados arredondados não são corrigidos nem submetidos retroativamente à regra atual. Isto não é auditoria econômica de todos os demais datasets.

Falha retorna status diferente de zero e JSON em stderr com data de Brasília e motivo. Não gera diretório final nem novos pesos em falhas de coleta/preparação. O executor deve registrar início/fim com timestamp de Brasília e UTC, código de saída e stderr; notificar falhas, sem publicar o lote. Não registrar segredos. Reexecução usa novo destino; não sobrescreve lotes anteriores.

### Ensaio real de 04/11/2026

Consulta somente de leitura: SILO retornou `settlement_rate=12.642` para 23/10 (Dado: B3 `b3_price_report`, `settlement_status=F`). A diferença para a base fixada de 12,640% é **0,2 bp** (Cálculo). O fechamento de 03/11 veio como 15,132% (Dado, mesma API). A rotina recusou a base divergente e **não gerou pesos**. Não alterar a base automaticamente nem relaxar a validação para liberar publicação. Decisão de conciliação pendente de Pedro.

**Conciliação (Pedro, 08/11/2026):** a base continua 12,640%. A origem é Dado: o Price Report da B3 de 26/10 publica esse valor como `prev_settlement_rate` do DI1F29, via a mesma série do SILO. A rotina agora confere a base nesse campo da sessão seguinte a 23/10. A linha de 23/10 (12,642%) segue sem uso. A diferença de 0,2 bp fica registrada aqui.

Primeiro lote real: 08/11/2026, fatos f14 (Copom 04/11) e f15 (Fazenda, centro da meta), aprovados por Pedro no chat do projeto. Os testes usam uma cópia fixa do ledger de 02/11 em `tests/fixtures/baseline-2026-11-02/`, para que lotes reais não alterem os testes.

## Investigação da partida de 30/10

O histórico Git disponível tem `78adf4d` (29/10) com partida 46/31/23 e `6b023ca` (02/11) com 49/31/20. Não há commit de dados de 30/10. No commit de 02/11 foram acrescentadas retroativamente as linhas de 30/10 ao histórico, com a ressalva explícita de que o arquivo de fatos não contém a justificativa de 48/32/20. Os fatos novos nesse commit são f11–f13. Isso não permite recuperar uma justificativa para a mudança de 30/10. A referência à sessão do claude.ai no commit não foi usada como dependência nem como prova de fato.

A lacuna fica preservada e visível nos relatórios; o bootstrap parte do snapshot aceito, sem reaplicar f1–f13, sem inventar f14 nem ajustar pesos para fechar a conta. A tarefa semanal permanece pendente de inspeção do prompt. Demais achados da revisão estão fora deste PR.
