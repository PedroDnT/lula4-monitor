# Revisão e plano da reforma

Base: main após PR #17. A reforma preserva pesos, marcas, datasets e Cenário Lara.

## Análise e metodologia

- **Alta, erro:** Fiscal descrevia interpolação e a antiga regra de 30%, embora Agora use verossimilhanças normais. Corrigida a descrição; cálculos e arquivos não foram alterados.
- **Alta, limitação metodológica:** fatos podem alterar tanto a partida quanto o DI; isso pode contar a mesma informação duas vezes. Recomendação: explicitar o limite e estudar uma especificação condicional antes de calibrar qualquer ajuste. O viés não é quantificável com a informação disponível.
- **Alta, limitação metodológica:** σ = 100 bp é escolha baseada na dispersão entre episódios, não estimativa validada dentro de cada cenário. Recomendação: estudo fora da reforma, com horizontes e episódios identificados; não alterar σ sem decisão de Pedro.
- **Média, escolha:** marcas fixas e DI bruto misturam dinâmica doméstica, global e passagem do tempo. Recomendação: comparar especificações e sensibilidade antes de mudar pesos. A alternativa multivariada exige estimação e correlações adicionais.
- **Alta, dado:** o SILO retornou ajuste de 12,642% em 23/10, contra a base definida de 12,640%. A conciliação continua pendente; não corrigida automaticamente.
- **Alta, dado:** falta justificativa para a mudança da partida em 30/10. O histórico preserva a lacuna. A revisão semanal antiga não foi inspecionada nesta sessão.

## Apresentação e execução

- **Alta, erro:** Método e Fiscal descreviam tarefas automáticas removidas. Textos atualizados para indicar revisão operacional e possível defasagem.
- **Média, apresentação:** pesos registrados e leitura ao vivo podiam parecer equivalentes. A identificação agora acompanha as duas leituras.
- **Média, apresentação:** reforçada a hierarquia visual do cabeçalho e do painel principal, com adaptações para celular e foco de teclado.
- **Limites da entrega:** não foi feita auditoria completa de fontes externas, regressões, links, contraste ou todos os estados de falha; não há nova calibração nem números publicados novos. O Cenário Lara segue no Parking Lot. A revisão completa e a definição do executor continuam pendentes.
