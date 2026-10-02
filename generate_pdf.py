#!/usr/bin/env python3
"""
Génère un CV en PDF (et en HTML) à partir de resume.json (format JSON Resume)
et du template.html / style.css.

Usage :
    python generate_pdf.py                  # nom déduit de basics.name + basics.label
    python generate_pdf.py -o cv-candidature  # nom imposé

Sorties (NOM = nom choisi ou déduit) :
    output/NOM.html  -> version publiable telle quelle sur un site perso
    output/NOM.pdf   -> version PDF pour candidature
"""

import argparse
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

MOIS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def format_date(value):
    """Convertit une date ISO JSON Resume en "mois année" (ex. "2025-03" -> "mars 2025").

    Une date réduite à l'année ("2010") est affichée telle quelle.
    """
    if not value:
        return value
    parts = str(value).split("-")
    year = parts[0]
    if len(parts) >= 2 and parts[1].isdigit() and 1 <= int(parts[1]) <= 12:
        return f"{MOIS[int(parts[1]) - 1]} {year}"
    return year


def format_duration(start, end=None):
    """Durée d'une expérience, mois de début et de fin inclus.

    "2025-03" -> "2026-08" donne "1 an et 6 mois" (mars à août inclus).
    Sans date de fin (poste en cours), la durée court jusqu'au mois actuel.
    Renvoie "" si une date n'est pas au format "AAAA-MM".
    """
    def months(value):
        parts = str(value or "").split("-")
        if len(parts) < 2 or not (parts[0].isdigit() and parts[1].isdigit()):
            return None
        return int(parts[0]) * 12 + int(parts[1]) - 1

    if end:
        end_m = months(end)
    else:
        today = date.today()
        end_m = today.year * 12 + today.month - 1
    start_m = months(start)
    if start_m is None or end_m is None or end_m < start_m:
        return ""
    total = end_m - start_m + 1
    years, rest = divmod(total, 12)
    parts = []
    if years:
        parts.append(f"{years} an{'s' if years > 1 else ''}")
    if rest:
        parts.append(f"{rest} mois")
    return " et ".join(parts)


def slugify(text):
    """"Ingénieur Cybersécurité" -> "ingenieur-cybersecurite"."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def default_output_name(basics):
    """Compose "cv-<nom>-<titre>" à partir de basics.name et basics.label.

    Seule la partie du label avant le premier "|", "(" ou "," est gardée,
    pour éviter un nom de fichier à rallonge.
    """
    label = re.split(r"[|(,]", basics.get("label", ""), maxsplit=1)[0]
    parts = ["cv", slugify(basics.get("name", "")), slugify(label)]
    return "-".join(p for p in parts if p)


def parse_args():
    parser = argparse.ArgumentParser(description="Génère le CV en HTML et PDF.")
    parser.add_argument(
        "-o", "--output",
        help="nom des fichiers de sortie, sans extension "
             "(par défaut : déduit de basics.name et basics.label)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(BASE_DIR / "resume.json", encoding="utf-8") as f:
        data = json.load(f)

    # Repli propre si aucune photo n'est présente sur le disque
    image_name = data.get("basics", {}).get("image", "")
    photo_available = bool(image_name) and (BASE_DIR / image_name).is_file()
    name_parts = data.get("basics", {}).get("name", "").split()
    initials = "".join(p[0].upper() for p in name_parts[:2] if p)

    env = Environment(loader=FileSystemLoader(str(BASE_DIR)))
    env.filters["date_fr"] = format_date
    env.globals["duree"] = format_duration
    template = env.get_template("template.html")
    rendered_html = template.render(
        **data,
        photo_available=photo_available,
        initials=initials,
    )

    output_name = args.output or default_output_name(data.get("basics", {}))

    html_path = OUTPUT_DIR / f"{output_name}.html"
    html_path.write_text(rendered_html, encoding="utf-8")
    print(f"HTML généré : {html_path}")

    pdf_path = OUTPUT_DIR / f"{output_name}.pdf"
    HTML(string=rendered_html, base_url=str(BASE_DIR)).write_pdf(str(pdf_path))
    print(f"PDF généré  : {pdf_path}")


if __name__ == "__main__":
    main()
