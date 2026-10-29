/* Explainers and glossary for the Monitor LULA4 pages.
   One source: LEIA holds the per-section blocks, GLOSS holds the Conceitos page. */
(function () {
  var GLOSS = [
    ["Juros", [
      ["selic", "Selic", "A taxa básica de juros do país, fixada pelo Copom.", "Selic alta encarece o crédito e segura a inflação. Cortes fazem o contrário."],
      ["copom", "Copom", "O comitê do Banco Central que decide a Selic. Reúne-se 8 vezes por ano.", "Pausa ou alta depois de uma série de cortes é sinal de cautela com inflação ou fiscal."],
      ["focus", "Focus", "Pesquisa semanal do Banco Central com a previsão de economistas para Selic, inflação, câmbio e dívida.", "A mediana é o que os economistas esperam. O painel compara com o que o mercado paga."],
      ["di", "DI futuro", "Contrato da B3 que trava o juro até um vencimento. O preço é uma taxa ao ano.", "Taxa sobe: o mercado espera juro maior ou cobra mais risco. Taxa cai: o oposto."],
      ["dijan29", "DI jan/29", "O contrato DI1F29: o juro médio esperado até janeiro de 2029. É o termômetro principal do site.", "Longo o bastante para refletir o risco fiscal, curto o bastante para ter negócio todo dia."],
      ["cdi", "CDI", "Taxa dos empréstimos entre bancos. Fica cerca de 0,10 ponto abaixo da Selic.", "É o juro que o DI futuro compõe dia a dia."],
      ["curva", "Curva de juros", "Os juros de vários prazos lado a lado.", "Curva que sobe com o prazo é normal. Subir mais no longo que no curto é o mercado cobrando pelo risco."],
      ["inclinacao", "Inclinação", "Juro longo menos juro curto (por exemplo, DI jan/33 menos jan/27).", "Aumenta: o mercado cobra mais pelo prazo longo, sinal de risco fiscal."],
      ["bp", "Ponto-base (bp)", "0,01 ponto percentual. 100 bp = 1 ponto.", "+50 bp leva um DI de 12,00% a 12,50%."],
      ["premio", "Prêmio (DI menos Focus)", "O quanto o DI paga acima da Selic que o Focus prevê.", "Mistura risco fiscal e prêmio de prazo. Com estes dados, os dois não se separam."],
      ["jurorea", "Juro real", "O juro depois de descontar a inflação esperada.", "Sobe junto com a inflação implícita: o mercado exige mais para financiar a dívida."],
      ["infimp", "Inflação implícita", "A inflação que o mercado embute no preço: juro prefixado contra juro real.", "Sobe: o mercado espera mais inflação. Acima de 4,5% no longo prazo: descrença na meta."],
      ["bootstrap", "Bootstrap da curva", "Método que tira a Selic de cada reunião do Copom a partir dos contratos de DI.", "Reuniões distantes são ruidosas, porque os contratos curtos negociam pouco."]
    ]],
    ["Câmbio e risco", [
      ["ptax", "PTAX", "Média oficial do dólar no dia, calculada pelo Banco Central.", "O painel compara o dólar de agora com a PTAX do último dia útil."],
      ["dol", "Dólar futuro (DOL)", "Contrato da B3 para travar o dólar numa data futura.", "Fica acima do dólar à vista por causa do diferencial de juros (cerca de 5,5% ao ano). Não é uma previsão pura."],
      ["cupom", "Cupom cambial", "O juro em dólar embutido no dólar futuro.", "Salto de um dia para o outro: o futuro e o dólar à vista descolaram. Desconfie do número."],
      ["usdt", "USDT/BRL", "Dólar digital (stablecoin) cotado em reais. Negocia a qualquer hora.", "Serve de dólar de madrugada. O painel desconta um prêmio de 0,4%."],
      ["cds", "CDS de 5 anos", "Seguro contra calote do Brasil. O preço, em bp, mede o risco-país.", "Sobe: o mercado vê mais risco. Acima de 250 bp é um dos sinais de estresse."],
      ["ewz", "EWZ", "Fundo de Nova York que replica ações brasileiras, em dólar.", "Cai por dois motivos: o real perde valor e as ações caem em reais."],
      ["adr", "ADR", "Recibo de uma ação brasileira negociado em Nova York (Itaú, Petrobras, Vale).", "Mostra como a ação reage antes de a B3 abrir."],
      ["local", "Choque local", "A parte do movimento que não vem do mundo (peso mexicano, rand, Treasury de 10 anos).", "O resto do movimento é do Brasil. Quase todo o movimento do DI é local."]
    ]],
    ["Dívida e orçamento", [
      ["dbgg", "Dívida bruta (DBGG)", "Tudo que o governo geral deve, em % do PIB.", "Subir sem parar é o que o mercado teme."],
      ["primario", "Resultado primário", "Receitas menos despesas, sem contar os juros.", "Positivo: sobra dinheiro para a dívida. A meta de 2027 é 0,50% do PIB, com piso de 0,25%."],
      ["rg", "r − g", "r é o juro que a dívida paga. g é o crescimento nominal do PIB.", "r maior que g: a dívida cresce sozinha. Só um superávit primário segura."],
      ["estabiliza", "Primário que estabiliza a dívida", "O superávit necessário para a dívida parar de subir como % do PIB.", "A lacuna é esse número menos o primário de hoje. Lacuna grande: o esforço está longe do que se faz."],
      ["rolagem", "Rolagem", "Trocar a dívida que vence por dívida nova.", "Vencimento grande e prazo curto: o Tesouro depende do humor do mercado."],
      ["dpf", "DPF", "Dívida Pública Federal: a dívida em títulos do Tesouro.", "É nela que se mede prazo médio e vencimentos."],
      ["lft", "LFT", "Título do Tesouro que paga a Selic.", "Muita LFT: o risco de juro fica com o governo. Teto do plano de financiamento: 53% da DPF."],
      ["paf", "PAF", "Plano Anual de Financiamento: as metas do Tesouro para prazo e vencimentos.", "Fora das faixas do PAF, o Tesouro está sob pressão."],
      ["arcabouco", "Arcabouço fiscal", "Regras (LC 200) que ligam o gasto à receita: a despesa real só cresce entre 0,6% e 2,5% ao ano, e há meta de primário.", "Quando o governo afrouxa o arcabouço, o mercado cobra juro maior."],
      ["ploa", "PLOA e PLDO", "Projetos de lei do orçamento e das diretrizes do ano seguinte, enviados ao Congresso.", "Mostram a meta fiscal e o gasto que o governo pretende fazer."],
      ["dominancia", "Dominância fiscal", "A dívida é vista como tão alta que subir juro piora a dívida e não segura a inflação.", "Sinal de mercado: juro sobe, real cai e inflação esperada sobe, tudo junto."],
      ["ancora", "Âncora de inflação", "A meta de 3%, com tolerância de 1,5 ponto (teto de 4,5%), e a confiança nela.", "Desancorar é a inflação esperada se afastar da meta. Isso encarece os juros do orçamento."],
      ["contab", "Contabilidade criativa", "Deduções e exceções que fazem a meta parecer cumprida sem o gasto mudar.", "Meta cumprida no papel, dívida sem melhora."]
    ]],
    ["Como o painel calcula", [
      ["cenario", "Cenário", "Uma história possível para os próximos meses: Âncora retomada, Deriva fiscal ou Estresse e espiral.", "O painel não prevê. Ele mede qual história o preço de hoje paga."],
      ["partida", "Peso de partida", "A probabilidade inicial de cada cenário, definida só por fatos no relatório diário.", "Muda uma vez por dia."],
      ["agora", "Peso de agora", "A partida atualizada por Bayes com o nível do DI jan/29 desde 23/10: partida × verossimilhança de cada marca, com σ = 100 bp.", "Muda ao longo do dia, com os preços."],
      ["degrau", "Degrau do fato", "Força do fato: fraco ×1,05, moderado ×1,15 e forte ×1,30. Contra o cenário, vale o inverso.", "Boato pesa pouco. Decisão oficial pesa muito."],
      ["sinais", "6 sinais de dominância", "Juro e dólar sobem juntos; juro real; inflação implícita; CDS; inclinação da curva; DI além do que o câmbio explica.", "Quanto mais acesos e por mais tempo, mais perto de dominância."],
      ["correlacao", "Correlação de 20 dias", "O quanto o DI e o dólar andam juntos nos últimos 20 pregões. Vai de −1 a +1.", "Acima de 0,4 é sinal aceso. Em qualquer susto os dois sobem juntos por alguns dias; semanas pesam mais."],
      ["precedentes", "Precedentes", "Choques passados (2014, 2017, 2018, 2022, 2024, 2026) comparados com hoje em 7 variáveis.", "100% é igual a hoje. Serve para ver se o susto costuma passar ou durar."],
      ["desvio", "Desvio padrão", "Medida do tamanho de um movimento normal.", "Movimento de 2 desvios é raro. Mostra quanto uma ação cai além do normal."],
      ["leque", "Leque da dívida", "2.000 trajetórias simuladas da dívida até 2030.", "Faixa larga: muita incerteza. Não é previsão e supõe que a política não muda."]
    ]]
  ];

  var LEIA = {
    "topo:index": {
      o: "Um termômetro do medo fiscal depois da eleição. Compara o que o mercado paga hoje com 3 histórias possíveis.",
      m: "3 pesos que somam 100% (julgamento, não modelo) e os preços ao vivo que os movem ao longo do dia.",
      i: "Peso alto em Deriva fiscal ou Estresse: o mercado exige mais juro para financiar o governo. Isso encarece a dívida e o crédito.",
      up: "DI e dólar sobem juntos: o mercado desconfia mais.", dn: "Os dois recuam: a desconfiança diminui.", g: ["cenario", "di", "ptax"]
    },
    "s-sc": {
      o: "Os 3 cenários lado a lado, cada um com um peso.",
      m: "Início: só fatos. Agora: o início ajustado pelo DI. O DI precifica: o cenário que a alta do DI jan/29 já paga.",
      i: "Se Agora e O DI precifica divergem muito, ou o mercado exagera, ou o julgamento está atrasado.",
      up: "Peso de Deriva ou Estresse sobe: mais risco fiscal no preço.", dn: "Peso de Âncora sobe: o mercado volta a acreditar na meta.", g: ["partida", "agora", "dijan29"]
    },
    "s-dom": {
      o: "Dominância fiscal: a dívida é vista como tão alta que subir juro não ajuda mais.",
      m: "6 sinais de mercado. Cada sinal aceso soma 1 ponto no placar.",
      i: "Quase todos acesos e por semanas: o mercado duvida da dívida. Poucos e por um dia: foi só uma notícia.",
      up: "Mais sinais acesos: mais perto de dominância.", dn: "Sinais apagam: o choque foi passageiro.", g: ["dominancia", "sinais", "correlacao", "jurorea", "infimp"]
    },
    "s-di": {
      o: "O DI é o preço do juro futuro. O DI jan/29 é o juro médio esperado até janeiro de 2029.",
      m: "A curva de ontem contra a de agora, e a parte da alta que o dólar não explica.",
      i: "Subir mais no longo que no curto: o mercado cobra prêmio pelo risco fiscal. A parte que o dólar não explica pesa mais.",
      up: "Juro futuro sobe: crédito e dívida mais caros.", dn: "Juro futuro cai: alívio.", g: ["di", "bp", "curva", "inclinacao", "premio", "local"]
    },
    "s-fx": {
      o: "O dólar de agora, antes de a PTAX (média oficial do dia) existir.",
      m: "Cada fonte contra a PTAX do último dia útil. A fonte que destoa é descartada.",
      i: "Dólar mais caro encarece importados e pressiona a inflação. O Banco Central pode manter o juro alto por mais tempo.",
      up: "Dólar sobe: o real perde valor.", dn: "Dólar cai: o real ganha.", g: ["ptax", "usdt", "dol"]
    },
    "s-cup": {
      o: "O cupom cambial é o juro em dólar embutido no dólar futuro.",
      m: "O dólar futuro contra os 3 cenários, e o cupom de cada vencimento.",
      i: "Salto do cupom de um dia para o outro: o futuro e o dólar à vista descolaram. O número não é um sinal.",
      g: ["dol", "cupom"]
    },
    "s-eq": {
      o: "O EWZ é o Ibovespa em dólar, negociado em Nova York. Ele abre antes da B3.",
      m: "A queda dividida em parte do real e parte das ações, e quais ações caem além do normal.",
      i: "Queda maior do que o dólar explica: a bolsa pode estar exagerando. Queda explicada pelo dólar: o problema é o câmbio.",
      up: "EWZ sobe: real e ações ganham.", dn: "EWZ cai: real e ações perdem.", g: ["ewz", "adr", "desvio"]
    },
    "s-hist": {
      o: "O diário do painel.",
      m: "A última leitura de cada dia: dólar, DI jan/29, CDS, pesos e placar.",
      i: "Mostra se o choque de hoje é novo ou continua os dias anteriores. Dias seguidos pesam mais que um dia.",
      g: ["cds"]
    },
    "topo:dominancia": {
      o: "O fundo: o que muda devagar e decide se a dívida é sustentável.",
      m: "O laço no topo, e 5 blocos: conta da dívida, rolagem, âncora de inflação, orçamento 2027 e gatilhos. Cada número tem uma etiqueta: Norma, Dado, Cálculo, Julgamento ou Simulação.",
      i: "Aqui, alerta aceso quer dizer risco de médio prazo, não pânico do dia. O pânico do dia está no Intraday.",
      g: ["dominancia", "dbgg", "rg"]
    },
    "divida": {
      o: "A dívida cresce sozinha quando o juro que ela paga (r) é maior que o crescimento da economia (g).",
      m: "r, g, a diferença r − g, e o superávit que o governo precisaria fazer para a dívida parar de subir.",
      i: "r − g acima de zero: a conta só fecha com superávit. Lacuna grande: o esforço necessário está longe do que se faz.",
      up: "r − g sobe: a dívida cresce mais rápido.", dn: "r − g cai: a dívida fica mais fácil de controlar.", g: ["rg", "estabiliza", "primario", "leque"]
    },
    "rolagem": {
      o: "Rolagem é trocar a dívida que vence por dívida nova.",
      m: "Quanto vence em 12 meses, o prazo médio e os leilões do Tesouro.",
      i: "Muita dívida vencendo, prazo curto e leilões cancelados: o mercado só empresta no curto prazo. É o primeiro sinal de crise.",
      up: "Vencimento em 12 meses sobe: mais dívida a refinanciar ao juro de hoje.", dn: "Prazo médio cai: o Tesouro só consegue vender dívida curta.", g: ["rolagem", "dpf", "paf", "lft"]
    },
    "ancora": {
      o: "Âncora de inflação é a confiança de que a inflação volta para a meta de 3% (teto de 4,5%).",
      m: "Inflação implícita, juro real, o IPCA do Focus e a fatia da dívida em LFT.",
      i: "Inflação implícita e juro real subindo juntos: o mercado descrê da meta e cobra mais para financiar a dívida.",
      up: "Inflação implícita sobe: o mercado espera mais inflação.", dn: "Inflação implícita cai: a âncora segura.", g: ["ancora", "infimp", "jurorea", "focus"]
    },
    "cenarios": {
      o: "O histórico dos 3 pesos, dia a dia.",
      m: "Uma cópia dos pesos que o relatório e o painel Intraday calculam.",
      i: "Mostra a direção do humor do mercado. Esta página não calcula nem muda nenhum peso.",
      g: ["cenario", "partida"]
    },
    "orcamento": {
      o: "O Orçamento 2027 mostra quanto o governo gasta, arrecada e economiza.",
      m: "A conta para estabilizar a dívida, o espaço para cortar gasto, o custo dos juros e as manobras contábeis.",
      i: "Os juros ficam fora do teto de gasto e da meta primária. Quando o juro sobe, o orçamento aperta sem o governo ter gastado a mais.",
      g: ["arcabouco", "ploa", "primario", "contab"]
    },
    "alertas": {
      o: "Os 10 gatilhos do monitor, num só lugar.",
      m: "Cada gatilho acende quando o dado passa do limite. A coluna Origem diz se o limite é de lei, de mercado (calibrado) ou escolha nossa.",
      i: "Em 11 crises desde 2010, o alerta de inflação implícita acendeu antes em 7 ou 8. Alertas de fundo (r − g, lacuna) são condição, não alarme de curto prazo.",
      g: ["infimp", "rg"]
    },
    "topo:relatorio": {
      o: "A foto do dia: os fatos e o fechamento da B3.",
      m: "Pesos de partida, curva DI, o que a curva diz sobre o Copom, fatos e agenda.",
      i: "Fixa o ponto de partida. O painel Intraday se move a partir dele, com os preços.",
      g: ["partida", "di", "copom"]
    },
    "pesos": {
      o: "A probabilidade inicial de cada cenário, só com fatos.",
      m: "Cada fato multiplica o peso de cada cenário. Depois os pesos voltam a somar 100%.",
      i: "O fato que favorece um cenário o infla, e os outros encolhem. O mesmo fato não conta duas vezes.",
      up: "Fator acima de 1: o fato favorece o cenário.", dn: "Fator abaixo de 1: o fato enfraquece o cenário.", g: ["partida", "degrau", "cenario"]
    },
    "curva": {
      o: "A curva DI é o juro futuro por prazo, no fechamento da B3.",
      m: "Cada vértice contra o dia anterior e contra 23/10, o último fechamento antes do 2º turno.",
      i: "Inclinação positiva e crescente: o mercado cobra mais pelo prazo longo, o que é risco fiscal.",
      up: "Taxa sobe: o mercado espera juro maior.", dn: "Taxa cai: o mercado espera juro menor.", g: ["curva", "inclinacao", "bp"]
    },
    "copom": {
      o: "O Copom decide a Selic. A curva diz que Selic o mercado espera em cada reunião.",
      m: "A Selic de cada reunião tirada do DI, contra a mediana do Focus.",
      i: "DI acima do Focus: o mercado espera juro mais alto que os economistas, ou cobra prêmio de risco.",
      up: "DI − Focus sobe: mais risco no preço.", dn: "DI − Focus cai: o mercado concorda com os economistas.", g: ["copom", "focus", "premio", "bootstrap"]
    },
    "fatos": {
      o: "As notícias que mudam a probabilidade dos cenários.",
      m: "Cada fato com fonte, o fator por cenário e o degrau (fraco, moderado ou forte).",
      i: "Fato oficial e forte move muito. Boato move pouco. Preço não entra aqui, porque já entra no Intraday.",
      g: ["degrau", "partida"]
    },
    "agenda": {
      o: "Os próximos eventos que podem mudar o quadro.",
      m: "O que cada evento precisa mostrar para favorecer cada cenário.",
      i: "Serve para ler o resultado de um evento no mesmo minuto em que ele sai.",
      g: ["copom", "ploa"]
    }
  };

  // Sources for the terms that are a law, a target or an official plan (the popups cite them).
  var SRC = {
    ancora: ["BCB, Metas para a inflação", "https://www.bcb.gov.br/controleinflacao/metainflacao"],
    arcabouco: ["Lei Complementar 200/2023", "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp200.htm"],
    paf: ["Tesouro Nacional, Plano Anual de Financiamento", "https://www.gov.br/tesouronacional"],
    lft: ["Tesouro Direto", "https://www.tesourodireto.com.br"],
    dpf: ["Tesouro Nacional, Relatório Mensal da Dívida", "https://www.gov.br/tesouronacional"],
    dbgg: ["BCB, Estatísticas fiscais", "https://www.bcb.gov.br/estatisticas/estatisticasfiscais"],
    focus: ["BCB, Boletim Focus", "https://www.bcb.gov.br/publicacoes/focus"],
    ploa: ["Ministério do Planejamento e Orçamento", "https://www.gov.br/planejamento"]
  };
  var gmap = {};
  GLOSS.forEach(function (grp) { grp[1].forEach(function (t) { gmap[t[0]] = t[1]; }); });
  var root = document.documentElement;
  var KEY = "lula4-leia";
  function get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function set(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  // Explanations start hidden on the Agora page (prices first) and on phones; the toggle remembers the reader's choice.
  var phone = window.matchMedia && window.matchMedia("(max-width: 600px)").matches;
  if (get() === "off" || (get() === null && (phone || /(^|\/)(index\.html)?$/.test(location.pathname)))) root.setAttribute("data-leia", "off");

  function block(d) {
    var h = '<div><b>O que é</b><p>' + esc(d.o) + '</p></div><div><b>O que mostra</b><p>' + esc(d.m) + '</p></div><div><b>O que implica</b><p>' + esc(d.i) + '</p></div>';
    if (d.up || d.dn) {
      h += '<div class="mv">' + (d.up ? '<span><i>▲ Sobe</i>' + esc(d.up) + '</span>' : '') + (d.dn ? '<span><i>▼ Cai</i>' + esc(d.dn) + '</span>' : '') + '</div>';
    }
    if (d.g && d.g.length) {
      h += '<div class="gl">Conceitos:' + d.g.map(function (id) { return gmap[id] ? '<a href="metodo.html#' + id + '">' + esc(gmap[id]) + '</a>' : ''; }).join('') + '</div>';
    }
    var el = document.createElement("div");
    el.className = "leia";
    el.setAttribute("role", "note");
    el.innerHTML = h;
    return el;
  }

  function inject() {
    var page = (location.pathname.split("/").pop() || "index.html").replace(/\.html$/, "") || "index";
    if (page === "") page = "index";
    Object.keys(LEIA).forEach(function (k) {
      var id = k, host;
      if (k.indexOf("topo:") === 0) {
        if (k !== "topo:" + page) return;
        host = document.querySelector("header.head, header#topo");
        if (host) host.appendChild(block(LEIA[k]));
        return;
      }
      host = document.getElementById(id);
      if (!host) return;
      var anchor = /^H[1-6]$/.test(host.tagName) ? host : host.querySelector("h2, h3");
      if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(block(LEIA[k]), anchor.nextSibling);
    });
    var head = document.querySelector(".site-head .in");
    if (head && !document.getElementById("gloss-list")) {
      var b = document.createElement("button");
      b.type = "button"; b.className = "leia-toggle";
      var sync = function () { var off = root.getAttribute("data-leia") === "off"; b.textContent = off ? "Mostrar explicações" : "Ocultar explicações"; b.setAttribute("aria-pressed", String(!off)); };
      b.addEventListener("click", function () { var off = root.getAttribute("data-leia") === "off"; if (off) { root.removeAttribute("data-leia"); set("on"); } else { root.setAttribute("data-leia", "off"); set("off"); } sync(); });
      sync(); head.appendChild(b);
    }
  }

  function gloss() {
    var host = document.getElementById("gloss-list");
    if (!host) return;
    var q = document.getElementById("gloss-q");
    function draw() {
      var s = (q.value || "").toLowerCase(), n = 0, h = "";
      GLOSS.forEach(function (grp) {
        var items = grp[1].filter(function (t) { return !s || (t[1] + " " + t[2] + " " + t[3]).toLowerCase().indexOf(s) >= 0; });
        if (!items.length) return;
        n += items.length;
        h += '<h2>' + esc(grp[0]) + '</h2><dl>' + items.map(function (t) {
          return '<div class="it" id="' + t[0] + '"><dt>' + esc(t[1]) + '</dt><dd>' + esc(t[2]) + '</dd><dd class="r"><i>Como ler</i>' + esc(t[3]) + '</dd></div>';
        }).join('') + '</dl>';
      });
      host.innerHTML = n ? h : '<p class="none">Nenhum conceito com esse texto.</p>';
      if (location.hash && !s) { var t = document.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView(); }
    }
    q.addEventListener("input", draw);
    draw();
  }

  // Popups: a .term button opens the glossary entry under it, with its source when there is one.
  function terms() {
    var pop = null;
    function find(id) { var out = null; GLOSS.forEach(function (grp) { grp[1].forEach(function (t) { if (t[0] === id) out = t; }); }); return out; }
    function close() { if (pop) { pop.remove(); pop = null; } }
    document.addEventListener("click", function (e) {
      var b = e.target.closest(".term");
      if (!b) { if (pop && !e.target.closest(".term-pop")) close(); return; }
      e.preventDefault();
      var id = b.getAttribute("data-term"), t = find(id);
      if (!t) return;
      if (pop && pop.getAttribute("data-term") === id) { close(); return; }
      close();
      var s = SRC[id];
      pop = document.createElement("div");
      pop.className = "term-pop"; pop.setAttribute("data-term", id); pop.setAttribute("role", "dialog");
      pop.innerHTML = "<b>" + esc(t[1]) + "</b>" + esc(t[2]) + " <i>Como ler:</i> " + esc(t[3]) +
        '<span class="src">' + (s ? "Fonte: <a href=\"" + esc(s[1]) + "\" target=\"_blank\" rel=\"noopener\">" + esc(s[0]) + "</a> · " : "") + '<a href="metodo.html#' + esc(id) + '">glossário</a></span>';
      document.body.appendChild(pop);
      var r = b.getBoundingClientRect(), w = pop.offsetWidth, vw = document.documentElement.clientWidth;
      pop.style.left = Math.max(8, Math.min(r.left, vw - w - 8) + window.scrollX) + "px";
      pop.style.top = (r.bottom + window.scrollY + 6) + "px";
    });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });
  }

  // On phones a table with long text becomes one card per row, each cell labelled by its column header.
  // Pages render tables after load and on refresh, so a mutation observer labels new tables too.
  function cards() {
    document.querySelectorAll("table:not([data-cards])").forEach(function (t) {
      var hs = Array.prototype.map.call(t.querySelectorAll("thead th"), function (th) { return th.textContent.trim(); });
      var rows = t.querySelectorAll("tbody tr");
      if (hs.length < 3 || !rows.length) return;
      var long = Array.prototype.some.call(t.querySelectorAll("tbody td"), function (td) { return td.textContent.trim().length > 50; });
      if (!long) return;
      t.setAttribute("data-cards", "");
      t.classList.add("as-cards");
    });
    document.querySelectorAll("table.as-cards").forEach(function (t) {
      var hs = Array.prototype.map.call(t.querySelectorAll("thead th"), function (th) { return th.textContent.trim(); });
      t.querySelectorAll("tbody tr").forEach(function (tr) {
        Array.prototype.forEach.call(tr.children, function (c, i) { if (i > 0 && hs[i] && !c.hasAttribute("data-label")) c.setAttribute("data-label", hs[i]); });
      });
    });
  }
  function watchTables() {
    if (!phone) return;
    cards();
    var queued = false;
    new MutationObserver(function () {
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () { queued = false; cards(); });
    }).observe(document.body, { childList: true, subtree: true });
  }

  function init() { inject(); gloss(); terms(); watchTables(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
