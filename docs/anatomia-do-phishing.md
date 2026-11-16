# Anatomia dos modelos de phishing

Material de apoio para treinamento. Os três modelos de `templates/` usam uma empresa e domínios
fictícios (`.test`). Cada um explora um gatilho psicológico diferente e traz sinais de alerta que o
usuário (e a equipe de segurança) podem identificar.

## Resumo

| Modelo | Gatilho | Dificuldade | Remetente real (fictício) |
|---|---|---|---|
| T01 Reembolso de despesas | Recompensa | Média | `financeiro@empresa-exemplo.test` |
| T02 Senha de rede expirando | Urgência e medo | Fácil | `ti-suporte@empresaexemplo-ti.test` |
| T03 Documento compartilhado | Colaboração e autoridade social | Difícil | `no-reply@docs-empresaexemplo.test` |

O domínio corporativo fictício é `empresaexemplo.test`. Os remetentes acima são parecidos, mas
diferentes dele: esse é o sinal mais comum em phishing real.

## T01: Reembolso de despesas (recompensa)

**Sinais de alerta**
1. Domínio do remetente parecido, mas diferente do corporativo.
2. Benefício inesperado: um reembolso que a pessoa não solicitou.
3. Prazo curto (48 horas) para pressionar a decisão.
4. Saudação genérica e protocolo sem contexto.
5. O link leva a um domínio externo, não ao portal corporativo.

**Reação esperada:** não clicar, abrir o portal da empresa digitando o endereço, e reportar.

## T02: Senha de rede expirando (urgência)

**Sinais de alerta**
1. Ameaça de bloqueio da conta para forçar uma ação imediata.
2. Prazo de 24 horas e tom de alerta automático.
3. Domínio do remetente com sufixo extra (`-ti`).
4. Troca de senha pedida por link, e não pelo portal oficial.
5. Sem identificação de quem enviou nem canal para confirmar.

**Reação esperada:** nunca trocar senha por link recebido; usar o portal oficial e reportar.

## T03: Documento compartilhado (colaboração)

**Sinais de alerta**
1. O nome exibido é de uma colega, mas o endereço real é de um serviço externo.
2. Arquivo inesperado, com pedido de resposta "ainda hoje".
3. Mensagem curta e sem contexto.
4. O link abre um domínio externo, não o repositório oficial.
5. Pedido de "ok" rápido para reduzir a checagem.

**Reação esperada:** confirmar com a colega por outro canal antes de abrir; reportar se não reconhecer.

## O que a equipe de segurança observa

- **Cabeçalhos:** alinhamento de SPF, DKIM e DMARC, e diferença entre `From`, `Reply-To` e `Return-Path`.
- **Domínios parecidos:** registros recentes e variações do domínio corporativo.
- **URLs:** reputação, redirecionamentos e diferença entre o texto do link e o destino.
- **Reportes:** quantos usuários reportam e em quanto tempo; os primeiros reportes ajudam a bloquear
  a campanha para todos.

## Checklist de 10 segundos para o usuário

1. O remetente é quem diz ser? Confira o endereço, não só o nome.
2. Estou esperando isso? Se não, desconfie.
3. Há pressa, ameaça ou prêmio? É o truque mais comum.
4. Para onde o link realmente aponta? Passe o mouse antes de clicar.
5. Na dúvida, não clique: confirme por outro canal e use o botão de reporte.
