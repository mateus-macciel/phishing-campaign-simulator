#!/usr/bin/env python3
"""Render the training e-mail templates as HTML previews (nothing is sent).

For each template it writes two files to output/preview/:
  * <id>.html          the e-mail as the recipient would see it
  * <id>_anotado.html  the same e-mail followed by the list of red flags (training material)
It also renders the educational landing page shown after a click.

Usage:
    python src/render_templates.py
"""
from __future__ import annotations

import argparse
import html
from pathlib import Path

from catalog import TEMPLATES

SAMPLE_NAME = "Ana Souza"  # fictitious


def fill(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def annotated(email_html: str, tpl: dict) -> str:
    flags = "".join(f"<li style='margin-bottom:6px'>{html.escape(f)}</li>" for f in tpl["red_flags"])
    panel = (
        "<section style=\"max-width:600px;margin:20px auto;background:#fffbeb;border:1px solid #f59e0b;"
        "border-radius:8px;padding:18px 22px;font-family:Arial,Helvetica,sans-serif;color:#1f2937\">"
        f"<h2 style='margin:0 0 4px;font-size:17px'>Versão comentada: {html.escape(tpl['name'])}</h2>"
        f"<p style='margin:0 0 10px;font-size:13px;color:#6b7280'>Gatilho: {html.escape(tpl['category'])} · "
        f"Dificuldade: {html.escape(tpl['difficulty'])} · Remetente real: "
        f"{html.escape(tpl['sender_address'])}</p>"
        f"<p style='margin:0 0 6px;font-weight:bold;font-size:14px'>Sinais de alerta</p>"
        f"<ol style='margin:0;padding-left:20px;font-size:14px;line-height:1.5'>{flags}</ol></section>"
    )
    return email_html.replace("</body>", panel + "\n</body>")


def render_all(templates_dir: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for tpl in TEMPLATES:
        raw = (templates_dir / tpl["file"]).read_text(encoding="utf-8")
        email = fill(raw, {"nome": SAMPLE_NAME, "link": tpl["link"]})
        stem = tpl["file"].removesuffix(".html")
        for name, content in ((f"{stem}.html", email), (f"{stem}_anotado.html", annotated(email, tpl))):
            path = out_dir / name
            path.write_text(content, encoding="utf-8")
            written.append(path)

    landing = (templates_dir / "landing_educativa.html").read_text(encoding="utf-8")
    sinais = "".join(f"<li>{html.escape(f)}</li>" for f in TEMPLATES[0]["red_flags"])
    path = out_dir / "landing_educativa.html"
    path.write_text(fill(landing, {"template_nome": TEMPLATES[0]["name"], "sinais": sinais}),
                    encoding="utf-8")
    written.append(path)
    return written


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description="Render e-mail template previews (nothing is sent).")
    p.add_argument("--templates", default=str(root / "templates"))
    p.add_argument("--out", default=str(root / "output" / "preview"))
    args = p.parse_args()
    for path in render_all(Path(args.templates), Path(args.out)):
        print(f"  {path}")


if __name__ == "__main__":
    main()
