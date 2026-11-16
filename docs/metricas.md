# Métricas da campanha

Todas as taxas usam como denominador as mensagens **entregues**, não as enviadas.

| Métrica | Definição | Observação |
|---|---|---|
| Entregues | Enviadas menos falhas de entrega | Falhas simuladas: cerca de 1,5% |
| Abertura | Entregues com abertura registrada ÷ entregues | Aproximada: bloqueio de imagens e proteção de privacidade distorcem o pixel |
| Clique | Quem clicou no link ÷ entregues | Indicador principal de risco (em outras ferramentas, "phish-prone percentage") |
| Dados informados | Quem preencheu dados no modelo ÷ entregues | Simulado: não existe formulário no projeto |
| Reporte | Quem reportou ÷ entregues | Indicador principal de cultura de segurança |
| Reportes por clique | Reportes ÷ cliques | Acima de 1 indica que mais gente reporta do que clica |
| Tempo até o clique/reporte | Minutos entre o envio e o evento | A mediana é mais robusta que a média |
| Reincidentes | Pessoas que clicaram em 2 ou mais ondas | Métrica agregada, sem listar nomes |

## Cuidados na interpretação

- **Compare modelos com cautela.** Cada modelo tem uma dificuldade; uma queda de clique entre ondas
  pode estar mascarada por um modelo mais difícil.
- **Evite grupos pequenos.** Grupos com menos de 20 pessoas não são ranqueados no resumo: o número é
  instável e pode identificar indivíduos.
- **Meça cultura, não culpa.** Resultados por pessoa não devem ser usados para punição; o objetivo é
  educar e aumentar o reporte.
- **Benchmarks variam.** Taxas de outras empresas dependem de modelo, setor e metodologia.
