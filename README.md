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
functions/api/*.js      3 funções do Cloudflare Pages: yahoo, cds, selic (fontes sem CORS)
docs/ATUALIZACAO.md     quem escreve cada arquivo de dados e quando
```

## Publicar no Cloudflare Pages

1. Cloudflare, Workers & Pages, Create, Pages, Connect to Git, escolha este repositório.
2. Framework preset: None. Build command: vazio. Build output directory: `/` (a raiz).
3. Depois do primeiro deploy: Custom domains, Set up a custom domain, e siga o passo de DNS.

A pasta `functions/` é publicada junto, sem configuração. Cada commit na `main` publica de novo.

Para ver local: `python3 -m http.server 8000` e abrir `http://localhost:8000`. As rotas `/api/*` só existem no Cloudflare. Local, o Yahoo, o CDS e a Selic aparecem como indisponíveis e o resto funciona.

## Avisos

- Leitura de sinais de mercado e julgamento do autor. Não é recomendação de compra ou venda.
- Os pesos dos cenários são julgamento, não previsão de modelo.
- O SILO é lido com a chave pública (`sb_publishable_…`), que só dá leitura ao schema `api`. Ela pode ficar no código.
