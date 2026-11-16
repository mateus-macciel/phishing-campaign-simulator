#!/usr/bin/env python3
"""Analyse the simulated campaign: metrics, summary.md and Power BI tables.

Usage:
    python src/analyze.py                       # reads data/, writes output/
    python src/analyze.py --data data --out output
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

MIN_GROUP = 20  # groups smaller than this are not ranked (too noisy, may identify people)
OUTCOMES = [  # (code, label in Portuguese), in priority order
    ("submitted", "Informou dados"), ("clicked", "Clicou"), ("reported", "Reportou"),
    ("opened", "Abriu sem agir"), ("ignored", "Não interagiu"), ("undelivered", "Não entregue"),
]
EVENT_TIME_COLS = ["sent_at", "opened_at", "clicked_at", "submitted_at", "reported_at"]


@dataclass
class Data:
    employees: pd.DataFrame
    campaigns: pd.DataFrame
    templates: pd.DataFrame
    events: pd.DataFrame


def load_data(data_dir: str | Path) -> Data:
    d = Path(data_dir)
    campaigns = pd.read_csv(d / "campaigns.csv", parse_dates=["send_date"])
    campaigns = campaigns.sort_values("send_date").reset_index(drop=True)
    campaigns["wave"] = range(1, len(campaigns) + 1)
    return Data(
        employees=pd.read_csv(d / "employees.csv"),
        campaigns=campaigns,
        templates=pd.read_csv(d / "templates.csv"),
        events=pd.read_csv(d / "events.csv", parse_dates=EVENT_TIME_COLS),
    )


def enrich(data: Data) -> pd.DataFrame:
    """One row per (campaign, employee) with 0/1 flags, minutes since sending and context."""
    ev = data.events.copy()
    for name in ["opened", "clicked", "submitted", "reported"]:
        ev[name] = ev[f"{name}_at"].notna().astype(int)
    ev["delivered"] = ev["delivered"].astype(int)
    for name in ["open", "click", "submit", "report"]:
        col = {"open": "opened", "click": "clicked", "submit": "submitted", "report": "reported"}[name]
        ev[f"minutes_to_{name}"] = (ev[f"{col}_at"] - ev["sent_at"]).dt.total_seconds() / 60
    ev["hour_clicked"] = ev["clicked_at"].dt.hour
    ev["outcome"] = np.select(
        [ev["submitted"] == 1, ev["clicked"] == 1, ev["reported"] == 1,
         ev["opened"] == 1, ev["delivered"] == 1],
        ["submitted", "clicked", "reported", "opened", "ignored"], default="undelivered")

    camp = data.campaigns[["campaign_id", "name", "wave", "send_date", "template_id"]]
    camp = camp.rename(columns={"name": "campaign_name"})
    tpl = data.templates[["template_id", "name", "category", "difficulty"]]
    tpl = tpl.rename(columns={"name": "template_name"})
    ev = ev.merge(camp, on="campaign_id", how="left").merge(tpl, on="template_id", how="left")
    ev = ev.merge(data.employees, on="employee_id", how="left")
    return ev


def rates(df: pd.DataFrame, by) -> pd.DataFrame:
    """Funnel counts and rates (over delivered messages) per group."""
    g = df.groupby(by, observed=True).agg(
        sent=("employee_id", "count"), delivered=("delivered", "sum"),
        opened=("opened", "sum"), clicked=("clicked", "sum"),
        submitted=("submitted", "sum"), reported=("reported", "sum")).reset_index()
    delivered = g["delivered"].replace(0, np.nan)
    for k in ["opened", "clicked", "submitted", "reported"]:
        g[f"{k}_rate"] = g[k] / delivered
    g["report_to_click"] = g["reported"] / g["clicked"].replace(0, np.nan)
    return g


def behaviour(ev: pd.DataFrame) -> dict:
    """Aggregate behaviour indicators (never per-person)."""
    per_emp = ev.groupby("employee_id").agg(clicks=("clicked", "sum"), reports=("reported", "sum"))
    clicks = ev[ev["clicked"] == 1]
    reports = ev[ev["reported"] == 1]
    delivered = ev[ev["delivered"] == 1]
    mobile = rates(delivered, "device").set_index("device")
    return {
        "employees": int(per_emp.shape[0]),
        "repeat_clickers": int((per_emp["clicks"] >= 2).sum()),
        "never_clicked": int((per_emp["clicks"] == 0).sum()),
        "repeat_reporters": int((per_emp["reports"] >= 2).sum()),
        "median_minutes_to_click": float(clicks["minutes_to_click"].median()) if len(clicks) else np.nan,
        "median_minutes_to_report": float(reports["minutes_to_report"].median()) if len(reports) else np.nan,
        "clicks_within_15min": float((clicks["minutes_to_click"] <= 15).mean()) if len(clicks) else np.nan,
        "clicks_within_1h": float((clicks["minutes_to_click"] <= 60).mean()) if len(clicks) else np.nan,
        "click_rate_mobile": float(mobile.loc["mobile", "clicked_rate"]) if "mobile" in mobile.index else np.nan,
        "click_rate_desktop": float(mobile.loc["desktop", "clicked_rate"]) if "desktop" in mobile.index else np.nan,
    }


# --------------------------------------------------------------------------- #
# Summary (Portuguese, ready to paste into an e-mail)
# --------------------------------------------------------------------------- #
def pct(x: float) -> str:
    return "n/d" if pd.isna(x) else f"{x * 100:.1f}%".replace(".", ",")


def pp(x: float) -> str:
    """Difference in percentage points, Portuguese decimal comma."""
    return f"{x * 100:+.1f}".replace(".", ",") + " p.p."


def write_summary(ev: pd.DataFrame, path: Path) -> None:
    by_wave = rates(ev, ["wave", "campaign_name", "template_name"]).sort_values("wave")
    overall = rates(ev.assign(all="all"), "all").iloc[0]
    b = behaviour(ev)
    first, last = by_wave.iloc[0], by_wave.iloc[-1]
    n_emp = b["employees"]

    lines = [
        "# Resumo da campanha de simulação de phishing",
        "",
        "> Simulação estatística com dados sintéticos: nenhum e-mail foi enviado e nenhuma pessoa real está envolvida.",
        "",
        "## Visão geral",
        "",
        f"- {len(by_wave)} ondas para {n_emp} pessoas ({int(overall['sent'])} mensagens, "
        f"{int(overall['delivered'])} entregues)",
        f"- Clique médio: **{pct(overall['clicked_rate'])}** · dados informados: **{pct(overall['submitted_rate'])}** · "
        f"reporte: **{pct(overall['reported_rate'])}**",
        f"- Evolução do clique: **{pct(first['clicked_rate'])}** na 1ª onda → **{pct(last['clicked_rate'])}** na última "
        f"({pp(last['clicked_rate'] - first['clicked_rate'])})",
        f"- Evolução do reporte: **{pct(first['reported_rate'])}** → **{pct(last['reported_rate'])}** "
        f"({pp(last['reported_rate'] - first['reported_rate'])})",
        "",
        "## Por onda",
        "",
        "| Onda | Modelo | Entregues | Abertura* | Clique | Dados informados | Reporte | Reportes por clique |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in by_wave.to_dict("records"):
        ratio = "n/d" if pd.isna(r["report_to_click"]) else f"{r['report_to_click']:.1f}".replace(".", ",")
        lines.append(f"| {r['campaign_name']} | {r['template_name']} | {int(r['delivered'])} | "
                     f"{pct(r['opened_rate'])} | {pct(r['clicked_rate'])} | {pct(r['submitted_rate'])} | "
                     f"{pct(r['reported_rate'])} | {ratio} |")
    lines += ["", "\\* Abertura por pixel é aproximada (bloqueio de imagens, proteção de privacidade): "
              "use clique e reporte como indicadores principais.", ""]

    dept = rates(ev, "department")
    dept = dept[dept["delivered"] >= MIN_GROUP].sort_values("clicked_rate", ascending=False)
    lines += ["## Áreas com maior e menor clique", "", "| Área | Entregues | Clique | Reporte |", "|---|---:|---:|---:|"]
    for r in pd.concat([dept.head(3), dept.tail(2)]).drop_duplicates("department").to_dict("records"):
        lines.append(f"| {r['department']} | {int(r['delivered'])} | {pct(r['clicked_rate'])} | {pct(r['reported_rate'])} |")

    lines += [
        "", "## Comportamento", "",
        f"- Tempo mediano até o clique: **{b['median_minutes_to_click']:.0f} min** após o envio; "
        f"**{pct(b['clicks_within_15min'])}** dos cliques em até 15 min e **{pct(b['clicks_within_1h'])}** em até 1 h",
        f"- Tempo mediano até o reporte: **{b['median_minutes_to_report']:.0f} min**",
        f"- Clique no celular: **{pct(b['click_rate_mobile'])}** x desktop: **{pct(b['click_rate_desktop'])}**",
        f"- Reincidentes (clicaram em 2 ou mais ondas): **{b['repeat_clickers']}** pessoas ({pct(b['repeat_clickers'] / n_emp)})",
        f"- Nunca clicaram: **{b['never_clicked']}** ({pct(b['never_clicked'] / n_emp)}) · "
        f"reportaram em 2 ou mais ondas: **{b['repeat_reporters']}**",
        "", "## Ações recomendadas", "",
    ]
    actions = []
    if last["clicked_rate"] < first["clicked_rate"]:
        actions.append("O clique caiu entre a 1ª e a última onda: manter o ciclo de microtreinamento imediato após o clique.")
    else:
        actions.append("O clique não caiu: revisar o conteúdo do treinamento e a frequência das campanhas.")
    if last["reported_rate"] > last["clicked_rate"]:
        actions.append("O reporte já supera o clique na última onda: divulgar o botão de reporte e dar retorno rápido a quem reporta.")
    else:
        actions.append("O reporte ainda está abaixo do clique: simplificar e divulgar o botão de reporte.")
    if len(dept):
        top = dept.iloc[0]
        actions.append(f"Reforçar o treinamento em **{top['department']}** (clique de {pct(top['clicked_rate'])}).")
    if b["clicks_within_15min"] > 0.4:
        actions.append("Boa parte dos cliques ocorre nos primeiros 15 minutos: a resposta do SOC precisa ser rápida.")
    if b["click_rate_mobile"] - b["click_rate_desktop"] >= 0.03:
        actions.append("Quem lê no celular clica mais: ensinar a conferir o link e o remetente no mobile.")
    lines += [f"{i}. {a}" for i, a in enumerate(actions, start=1)]
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Power BI export
# --------------------------------------------------------------------------- #
def export_powerbi(data: Data, ev: pd.DataFrame, out_dir: Path) -> None:
    out = out_dir / "powerbi"
    out.mkdir(parents=True, exist_ok=True)

    def save(df: pd.DataFrame, name: str) -> None:
        df.to_csv(out / f"{name}.csv", index=False, date_format="%Y-%m-%d %H:%M")

    emp = data.employees.copy()
    emp["tenure_band"] = pd.cut(emp["tenure_months"], [0, 6, 24, 60, 1000],
                                labels=["0-6 meses", "7-24 meses", "2-5 anos", "5+ anos"]).astype(str)
    save(emp, "dim_employee")

    camp = data.campaigns.merge(data.templates.rename(columns={"name": "template_name"}),
                                on="template_id", how="left")
    camp = camp.rename(columns={"name": "campaign_name"})
    save(camp[["campaign_id", "campaign_name", "wave", "send_date", "audience", "template_id",
               "template_name", "category", "difficulty", "subject", "sender_name",
               "sender_address", "red_flags_count"]], "dim_campaign")

    order = {code: i + 1 for i, (code, _) in enumerate(OUTCOMES)}
    fact = ev.copy()
    fact["outcome_order"] = fact["outcome"].map(order)
    save(fact[["campaign_id", "employee_id", "sent_at", "delivered", "opened", "clicked",
               "submitted", "reported", "minutes_to_open", "minutes_to_click",
               "minutes_to_submit", "minutes_to_report", "hour_clicked", "device",
               "outcome", "outcome_order"]], "fact_event")
    save(pd.DataFrame([{"outcome": c, "label_pt": l, "outcome_order": order[c]} for c, l in OUTCOMES]),
         "dim_outcome")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description="Analyse the simulated phishing campaign.")
    p.add_argument("--data", default=str(root / "data"))
    p.add_argument("--out", default=str(root / "output"))
    args = p.parse_args()

    data = load_data(args.data)
    ev = enrich(data)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_summary(ev, out / "summary.md")
    export_powerbi(data, ev, out)

    by_wave = rates(ev, ["wave", "campaign_name"]).sort_values("wave")
    print("Análise da campanha")
    for r in by_wave.to_dict("records"):
        print(f"  {r['campaign_name']:<22} entregues={int(r['delivered']):>4}  "
              f"clique={r['clicked_rate'] * 100:4.1f}%  reporte={r['reported_rate'] * 100:4.1f}%")
    print(f"  Relatórios em: {out}")


if __name__ == "__main__":
    main()
