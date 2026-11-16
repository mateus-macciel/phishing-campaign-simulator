"""Catalog: e-mail templates, campaign waves and behavioural parameters.

Every organisation, person and domain here is FICTITIOUS. Domains use the
reserved `.test` TLD (RFC 2606), so they can never resolve to a real site.
"""
from __future__ import annotations

CORPORATE_DOMAIN = "empresaexemplo.test"

TEMPLATES = [
    {
        "template_id": "T01", "file": "T01_reembolso.html",
        "name": "Reembolso de despesas", "category": "Recompensa", "difficulty": "Média",
        "subject": "Reembolso de despesas aprovado: confirme seus dados",
        "sender_name": "Financeiro Empresa Exemplo",
        "sender_address": "financeiro@empresa-exemplo.test",
        "link": "https://reembolso.empresa-exemplo.test/confirmar",
        "base_click": 0.17, "submit_rate": 0.45,
        "red_flags": [
            "Domínio do remetente parecido, mas diferente do corporativo (empresa-exemplo.test x empresaexemplo.test)",
            "Benefício inesperado: um reembolso que você não solicitou",
            "Prazo curto (48 horas) para pressionar a decisão",
            "Saudação genérica e protocolo sem contexto",
            "O link leva a um domínio externo, não ao portal corporativo",
        ],
    },
    {
        "template_id": "T02", "file": "T02_senha.html",
        "name": "Senha de rede expirando", "category": "Urgência", "difficulty": "Fácil",
        "subject": "Sua senha expira em 24 horas",
        "sender_name": "Suporte de TI",
        "sender_address": "ti-suporte@empresaexemplo-ti.test",
        "link": "https://senha.empresaexemplo-ti.test/atualizar",
        "base_click": 0.22, "submit_rate": 0.55,
        "red_flags": [
            "Ameaça de bloqueio da conta para forçar uma ação imediata",
            "Prazo de 24 horas e tom de alerta automático",
            "Domínio do remetente com sufixo extra (-ti) diferente do corporativo",
            "Pede para atualizar a senha por um link, e não pelo portal oficial",
            "Sem identificação de quem enviou nem canal para confirmar",
        ],
    },
    {
        "template_id": "T03", "file": "T03_documento.html",
        "name": "Documento compartilhado", "category": "Colaboração", "difficulty": "Difícil",
        "subject": "Carla Mendes compartilhou um documento com você",
        "sender_name": "Carla Mendes (via Docs)",
        "sender_address": "no-reply@docs-empresaexemplo.test",
        "link": "https://docs-empresaexemplo.test/abrir/orcamento-2027",
        "base_click": 0.20, "submit_rate": 0.30,
        "red_flags": [
            "O nome exibido é de uma colega, mas o endereço real é de um serviço externo",
            "Arquivo que você não estava esperando, com pedido de resposta 'ainda hoje'",
            "Mensagem curta e sem contexto sobre o assunto do documento",
            "O link abre um domínio externo, não o repositório oficial da empresa",
            "Pedido de 'ok' rápido para reduzir a checagem",
        ],
    },
]

# Three waves, one Tuesday every four weeks.
CAMPAIGNS = [
    {"campaign_id": "C01", "name": "Onda 1: Reembolso", "template_id": "T01", "send_date": "2026-09-08"},
    {"campaign_id": "C02", "name": "Onda 2: Senha", "template_id": "T02", "send_date": "2026-10-06"},
    {"campaign_id": "C03", "name": "Onda 3: Documento", "template_id": "T03", "send_date": "2026-11-03"},
]

# department -> (share of headcount, click multiplier, share reading e-mail on mobile)
DEPARTMENTS = {
    "Tecnologia": (0.24, 0.70, 0.25),
    "Segurança da Informação": (0.06, 0.35, 0.20),
    "Financeiro": (0.12, 1.15, 0.25),
    "Operações": (0.18, 1.15, 0.30),
    "Atendimento": (0.16, 1.30, 0.20),
    "Comercial": (0.10, 1.35, 0.50),
    "Jurídico": (0.03, 0.90, 0.25),
    "RH": (0.04, 1.10, 0.25),
    "Risco e Compliance": (0.07, 0.80, 0.25),
}
