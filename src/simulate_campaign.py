#!/usr/bin/env python3
"""Statistical simulation of a phishing-awareness campaign (three waves).

IMPORTANT: this script NEVER sends e-mail and involves NO real person. It draws
synthetic employees and simulates how they might react, so that the analysis and
the dashboard can be built and tested end to end.

Behaviour model (all parameters are in src/catalog.py or at the top of this file):
  * P(click) = template base rate x department x tenure x work mode x device x learning
  * "learning": each wave everybody improves a bit (x0.85 per wave); people who clicked
    before improve a lot (x0.5, micro-training on the educational page); people who
    reported before click less (x0.7) and report more (x1.8)
  * Timing: send throttled over 2 h; open delay is log-normal (median 25 min) with 18% of
    people reading the next day; click/report happen minutes after the open

Usage:
    python src/simulate_campaign.py --employees 600 --seed 42
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from catalog import CAMPAIGNS, DEPARTMENTS, TEMPLATES

TEMPLATE_BY_ID = {t["template_id"]: t for t in TEMPLATES}
SENIORITY = [("Júnior", 0.35), ("Pleno", 0.35), ("Sênior", 0.20), ("Gestão", 0.10)]
WORK_MODE = [("Presencial", 0.30), ("Híbrido", 0.55), ("Remoto", 0.15)]
P_DELIVER = 0.985
P_OPEN = 0.62  # share of delivered messages that are opened


def simulate(n_employees: int, seed: int) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)

    def chance(p: float) -> bool:
        return bool(rng.random() < p)

    def lognorm(median: float, sigma: float) -> float:
        return float(rng.lognormal(np.log(median), sigma))

    def draw(options, n):
        names = [o[0] for o in options]
        probs = np.array([o[1] for o in options], dtype=float)
        return [names[int(i)] for i in rng.choice(len(names), size=n, p=probs / probs.sum())]

    # ---- population -------------------------------------------------------- #
    dept_names = list(DEPARTMENTS)
    dept_probs = np.array([DEPARTMENTS[d][0] for d in dept_names], dtype=float)
    depts = [dept_names[int(i)]
             for i in rng.choice(len(dept_names), size=n_employees, p=dept_probs / dept_probs.sum())]
    seniority = draw(SENIORITY, n_employees)
    work_mode = draw(WORK_MODE, n_employees)
    tenure = [int(x) for x in rng.integers(1, 120, size=n_employees)]
    employees = pd.DataFrame({
        "employee_id": [f"E{i + 1:04d}" for i in range(n_employees)],
        "department": depts, "seniority": seniority, "work_mode": work_mode,
        "tenure_months": tenure,
    })

    # per-person memory carried from wave to wave
    clicked_before = [False] * n_employees
    reported_before = [False] * n_employees

    # ---- waves ------------------------------------------------------------- #
    rows: list[dict] = []
    for w, camp in enumerate(CAMPAIGNS):
        tpl = TEMPLATE_BY_ID[camp["template_id"]]
        start = datetime.fromisoformat(camp["send_date"]) + timedelta(hours=10)
        for i in range(n_employees):
            dept = depts[i]
            _, dept_mult, mobile_share = DEPARTMENTS[dept]
            mobile = chance(mobile_share)
            learn = (0.85 ** w) * (0.5 if clicked_before[i] else 1.0) \
                * (0.7 if reported_before[i] else 1.0)
            p_click = min(0.6, tpl["base_click"] * dept_mult
                          * (1.3 if tenure[i] < 6 else 1.0)
                          * (1.1 if work_mode[i] == "Remoto" else 1.0)
                          * (1.15 if mobile else 1.0) * learn)
            p_click_if_open = min(0.9, p_click / P_OPEN)

            sent_at = start + timedelta(minutes=float(rng.uniform(0, 120)))
            event = {"campaign_id": camp["campaign_id"], "employee_id": employees.at[i, "employee_id"],
                     "sent_at": sent_at, "delivered": 0, "opened_at": None, "clicked_at": None,
                     "submitted_at": None, "reported_at": None,
                     "device": "mobile" if mobile else "desktop"}

            if chance(P_DELIVER):
                event["delivered"] = 1
                if chance(P_OPEN):
                    delay = lognorm(25, 1.1)
                    if chance(0.18):  # reads it the next day
                        delay += float(rng.uniform(14 * 60, 28 * 60))
                    opened_at = sent_at + timedelta(minutes=min(delay, 5 * 24 * 60))
                    event["opened_at"] = opened_at
                    if chance(p_click_if_open):
                        clicked_at = opened_at + timedelta(minutes=lognorm(1.5, 0.9))
                        event["clicked_at"] = clicked_at
                        if chance(tpl["submit_rate"] * (0.6 if clicked_before[i] else 1.0)):
                            event["submitted_at"] = clicked_at + timedelta(minutes=lognorm(1.2, 0.6))
                        if chance(0.06):  # a few people report after clicking
                            event["reported_at"] = clicked_at + timedelta(minutes=lognorm(10, 1.0))
                    else:
                        p_report = min(0.85, (0.09 + 0.05 * w) * 1.4
                                       * (1.8 if reported_before[i] else 1.0)
                                       * (1.2 if clicked_before[i] else 1.0))
                        if chance(p_report):
                            event["reported_at"] = opened_at + timedelta(minutes=lognorm(12, 1.0))

            if event["clicked_at"] is not None:
                clicked_before[i] = True
            if event["reported_at"] is not None:
                reported_before[i] = True
            rows.append(event)

    events = pd.DataFrame(rows)
    for col in ["sent_at", "opened_at", "clicked_at", "submitted_at", "reported_at"]:
        events[col] = pd.to_datetime(events[col])

    campaigns = pd.DataFrame(CAMPAIGNS)
    campaigns["audience"] = n_employees
    templates = pd.DataFrame([{
        "template_id": t["template_id"], "name": t["name"], "category": t["category"],
        "difficulty": t["difficulty"], "subject": t["subject"],
        "sender_name": t["sender_name"], "sender_address": t["sender_address"],
        "red_flags_count": len(t["red_flags"]), "red_flags": " | ".join(t["red_flags"]),
    } for t in TEMPLATES])
    return {"employees": employees, "campaigns": campaigns, "templates": templates, "events": events}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description="Simulate a phishing-awareness campaign (no e-mail is sent).")
    p.add_argument("--employees", type=int, default=600, help="number of synthetic employees (min 100)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default=str(root / "data"))
    args = p.parse_args()
    if args.employees < 100:
        p.error("--employees must be at least 100")

    tables = simulate(args.employees, args.seed)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_csv(out / f"{name}.csv", index=False, date_format="%Y-%m-%d %H:%M")
    meta = {
        "synthetic": True,
        "note": "Simulação estatística: nenhum e-mail foi enviado e nenhuma pessoa real está envolvida.",
        "seed": args.seed, "employees": args.employees,
        "rows": {k: int(len(v)) for k, v in tables.items()},
    }
    (out / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
                                       encoding="utf-8")
    print(f"Campanha simulada em {out}")
    for k, v in meta["rows"].items():
        print(f"  {k:<10} {v:>5} linhas")


if __name__ == "__main__":
    main()
