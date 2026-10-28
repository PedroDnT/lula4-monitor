# lula4-monitor

Site estático público com 3 monitores sobre juros, câmbio e fiscal depois da eleição de 2026, mais uma aba de método.

| Aba | Arquivo | O que é |
| --- | --- | --- |
| Intraday | `index.html` | Preços ao vivo, pesos de agora dos 3 cenários, 6 sinais de dominância |
| Dominância fiscal | `dominancia.html` | Conta da dívida, rolagem, âncora de inflação, orçamento 2027 |
| Relatório diário | `relatorio.html` | Pesos de partida (só fatos), fechamento da curva DI, Copom contra Focus |
| Método | `metodo.html` | Como cada página funciona, fontes e limites |

Sem build e sem dependência de servidor próprio: HTML, CSS e JS puros. Os gráficos usam d3 pelo CDN.

## Estrutura

```
index.html  dominancia.html  relatorio.html  metodo.html
assets/style.css        tokens de cor e o cabeçalho com as abas
assets/dash-shim.js     lê os arquivos de data/ e a API pública do SILO para as 2 páginas de dashboard
data/relatorio/*.json   pesos, fatos, agenda, calendário do Copom, feriados, params
data/dominancia/*.json  cenários, histórico, LFT, rolagem, orçamento, calibração, params
data/intraday/history.json   histórico-base do painel intraday
worker.js  wrangler.jsonc  3 rotas /api/yahoo, /api/cds, /api/selic (fontes sem CORS)
docs/ATUALIZACAO.md     quem escreve cada arquivo de dados e quando
```

## Publicar no Cloudflare (Workers)

O site roda como um Worker com arquivos estáticos (`wrangler.jsonc`). O `worker.js` atende só `/api/*`; o resto vem direto dos arquivos.

1. Cloudflare, Workers & Pages, Create, Import a repository, escolha este repositório.
2. Build command vazio. Deploy command: `npx wrangler deploy`. Branch `main`.
3. Depois do deploy, em Settings, Domains & Routes, adicione o domínio próprio e siga o passo de DNS.

Cada commit na `main` publica de novo. O `.assetsignore` impede que `worker.js`, `docs/` e `README.md` sejam servidos como arquivos.

Para ver local: `npx wrangler dev` (serve as 4 abas e as rotas `/api/*`).

## Avisos

- Leitura de sinais de mercado e julgamento do autor. Não é recomendação de compra ou venda.
- Os pesos dos cenários são julgamento, não previsão de modelo.
- O SILO é lido com a chave pública (`sb_publishable_…`), que só dá leitura ao schema `api`. Ela pode ficar no código.
