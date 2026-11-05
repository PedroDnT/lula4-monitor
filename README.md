# lula4-monitor

Site estático público com 3 monitores sobre juros, câmbio e fiscal depois da eleição de 2026, uma aba de método e uma versão simples para leigos. As páginas funcionam no celular: tabelas de texto viram cartões e o laço fiscal vira lista.

| Aba | Arquivo | O que é |
| --- | --- | --- |
| Agora | `index.html` | Preços ao vivo, pesos de agora dos 3 cenários, 6 sinais de dominância |
| Agora (segunda vista) | `relatorio.html` | Pesos de partida (só fatos), fechamento da curva DI, Copom contra Focus |
| Fiscal | `dominancia.html` | Conta da dívida, rolagem, âncora de inflação, orçamento 2027 |
| Método | `metodo.html` | De onde vem cada número, como cada página funciona, fontes, limites e conceitos |
| Versão simples | `simples.html` | A conta do governo em 6 passos, para quem não é da área; página que pode ser compartilhada sozinha |

Sem build e sem dependência de servidor próprio: HTML, CSS e JS puros. Os gráficos usam d3 pelo CDN.

## Estrutura

```
index.html  dominancia.html  relatorio.html  metodo.html  simples.html
assets/style.css        tokens de cor e o cabeçalho com as abas
assets/leia.js          blocos "o que é, o que mostra, o que implica" por seção e o glossário
assets/leia.css         estilo desses blocos e da seção Conceitos do Método
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
3. Grave um JWT de usuário Supabase Auth em `SILO_USER_JWT` nos Secrets do Worker
   (`npx wrangler secret put SILO_USER_JWT`). O token precisa estar válido; a
   política de expiração e renovação deve ser definida antes de ativar a rotina.
4. Depois do deploy, em Settings, Domains & Routes, adicione o domínio próprio e siga o passo de DNS.

Cada commit na `main` publica de novo. O `.assetsignore` impede que `worker.js`, `docs/` e `README.md` sejam servidos como arquivos.

Para ver local: `npx wrangler dev` (serve as 3 abas e as rotas `/api/*`).

## Avisos

- Leitura de sinais de mercado e julgamento do autor. Não é recomendação de compra ou venda.
- Os pesos dos cenários são julgamento, não previsão de modelo.
- O SILO é lido pela API REST v2 autenticada. O JWT de usuário fica no secret
  `SILO_USER_JWT` do Cloudflare Worker e nunca é enviado ao navegador.
