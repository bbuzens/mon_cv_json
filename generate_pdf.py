#!/usr/bin/env python3
"""
Génère un CV en PDF (et en HTML) à partir de resume.json (format JSON Resume)
et du template.html / style.css.

Usage :
    python generate_pdf.py

Sorties :
    output/cv.html   -> version publiable telle quelle sur un site perso
    output/cv.pdf    -> version PDF pour candidature
"""

import json
import os
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


def main():
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
    # Une puce commençant par "+" est un résultat chiffré, affiché à part
    env.tests["resultat"] = lambda h: str(h).lstrip().startswith("+")
    template = env.get_template("template.html")
    rendered_html = template.render(
        **data,
        photo_available=photo_available,
        initials=initials,
    )

    html_path = OUTPUT_DIR / "cv.html"
    html_path.write_text(rendered_html, encoding="utf-8")
    print(f"HTML généré : {html_path}")

    pdf_path = OUTPUT_DIR / "cv.pdf"
    HTML(string=rendered_html, base_url=str(BASE_DIR)).write_pdf(str(pdf_path))
    print(f"PDF généré  : {pdf_path}")


if __name__ == "__main__":
    main()
