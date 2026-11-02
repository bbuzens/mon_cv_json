#!/usr/bin/env python3
"""
Génère une variante « ATS » du CV (Glassdoor, Workday, Taleo, Welcome to the
Jungle...) à partir du même resume.json que generate_pdf.py.

Différences avec la version graphique :
  - une seule colonne, ordre de lecture = ordre du document ;
  - pas de photo, d'icône, de tableau, de couleur ni d'en-tête/pied de page ;
  - intitulés de sections classiques (Profil, Compétences, Expérience
    professionnelle, Formation...) et dates au format MM/AAAA ;
  - police standard (Arial / Calibri), ligatures désactivées ;
  - métadonnées réduites à l'auteur et au titre.

Usage :
    python generate_ats.py                     # resume.json, nom déduit
    python generate_ats.py -i resume_full.json # autre source
    python generate_ats.py -o cv-ats-acme      # nom imposé
    python generate_ats.py --author "Prénom NOM"

Sorties (NOM = nom choisi, ou nom par défaut suffixé de « -ats ») :
    output/NOM.pdf   -> PDF texte une colonne
    output/NOM.docx  -> Word natif (styles Titre 1/2, puces Word)
"""

import argparse
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor
from jinja2 import Environment, FileSystemLoader
from pypdf import PdfReader, PdfWriter
from weasyprint import HTML

from generate_pdf import BASE_DIR, OUTPUT_DIR, default_output_name, emph, short_url


def date_num(value):
    """"2025-03" -> "03/2025" ; "2010" -> "2010". Format le mieux reconnu des ATS."""
    if not value:
        return value
    parts = str(value).split("-")
    if len(parts) >= 2 and parts[1].isdigit():
        return f"{int(parts[1]):02d}/{parts[0]}"
    return parts[0]


def plain(text):
    """Retire les marqueurs **...** et normalise les caractères typographiques
    que certains parseurs gèrent mal (tiret cadratin, point médian)."""
    text = str(text or "").replace("**", "")
    return text.replace(" — ", " - ").replace(" · ", ", ").replace("·", ",")


def default_author(basics):
    """"Benoît Buzens" -> "Benoît BUZENS" (convention française)."""
    parts = basics.get("name", "").split()
    if len(parts) < 2:
        return basics.get("name", "")
    return " ".join(parts[:-1] + [parts[-1].upper()])


# --------------------------------------------------------------------- PDF

def build_pdf(data, author, pdf_path):
    env = Environment(loader=FileSystemLoader(str(BASE_DIR)))
    env.filters["date_num"] = date_num
    env.filters["short_url"] = short_url
    env.filters["emph"] = emph
    html = env.get_template("template_ats.html").render(**data, author=author)

    raw_path = pdf_path.with_suffix(".tmp.pdf")
    HTML(string=html, base_url=str(BASE_DIR)).write_pdf(str(raw_path))

    # Réécriture des métadonnées : uniquement auteur, titre, sujet.
    reader = PdfReader(str(raw_path))
    writer = PdfWriter(clone_from=reader)
    info = writer._info.get_object()  # dictionnaire /Info
    for key in list(info.keys()):
        del info[key]
    writer.add_metadata({
        "/Author": author,
        "/Title": f"CV {author}",
        "/Subject": plain(data["basics"].get("label", "")),
    })
    for key in ("/Producer", "/Creator"):
        if key in info:
            del info[key]
    if "/Metadata" in writer._root_object:
        del writer._root_object["/Metadata"]
    with open(pdf_path, "wb") as f:
        writer.write(f)
    raw_path.unlink()


# -------------------------------------------------------------------- DOCX

def add_rich(paragraph, text):
    """Ajoute le texte au paragraphe, en gras pour les passages **...**."""
    for i, part in enumerate(plain_keep_bold(text).split("**")):
        if part:
            paragraph.add_run(part).bold = bool(i % 2)


def plain_keep_bold(text):
    return plain(str(text or "").replace("**", "\0")).replace("\0", "**")


def build_docx(data, author, docx_path):
    b = data.get("basics", {})
    doc = Document()

    section = doc.sections[0]
    section.page_height, section.page_width = Mm(297), Mm(210)
    section.top_margin = section.bottom_margin = Mm(15)
    section.left_margin = section.right_margin = Mm(18)

    def style_font(name, size, bold=None, italic=None):
        st = doc.styles[name]
        st.font.name = "Calibri"
        rfonts = st.element.get_or_add_rPr().get_or_add_rFonts()
        for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rfonts.set(qn(attr), "Calibri")
        for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
            rfonts.attrib.pop(qn(attr), None)
        st.font.size = Pt(size)
        st.font.color.rgb = RGBColor(0, 0, 0)
        if bold is not None:
            st.font.bold = bold
        if italic is not None:
            st.font.italic = italic
        return st

    normal = style_font("Normal", 10.5)
    normal.paragraph_format.space_after = Pt(2)
    normal.paragraph_format.line_spacing = 1.1
    for name, size in (("Title", 18), ("Heading 1", 12.5), ("Heading 2", 11)):
        st = style_font(name, size, bold=True)
        st.paragraph_format.keep_with_next = True
    doc.styles["Heading 1"].paragraph_format.space_before = Pt(10)
    doc.styles["Heading 1"].paragraph_format.space_after = Pt(3)
    doc.styles["Heading 2"].paragraph_format.space_before = Pt(5)
    doc.styles["Heading 2"].paragraph_format.space_after = Pt(0)
    doc.styles["Title"].paragraph_format.space_after = Pt(2)
    style_font("List Bullet", 10.5).paragraph_format.space_after = Pt(1)
    # Pas de bordure décorative sous le style Titre
    pPr = doc.styles["Title"].element.get_or_add_pPr()
    for el in pPr.findall(qn("w:pBdr")):
        pPr.remove(el)

    def h1(text):
        doc.add_heading(text.upper(), level=1)

    def h2(text):
        doc.add_heading(plain(text), level=2)

    def para(text, italic=False, bold=False):
        p = doc.add_paragraph()
        add_rich(p, text)
        for r in p.runs:
            r.italic = r.italic or italic
            r.bold = r.bold or bold
        return p

    def bullets(items):
        for it in items:
            add_rich(doc.add_paragraph(style="List Bullet"), it)

    doc.add_heading(b.get("name", ""), level=0)
    para(b.get("label", "").replace("|", "-"), bold=True)
    contact = [b.get("email"), b.get("phone"),
               (b.get("location") or {}).get("city"), short_url(b.get("url"))]
    para(" | ".join(c for c in contact if c))

    if b.get("summary"):
        h1("Profil")
        for line in b["summary"].split("\n"):
            if line.strip():
                para(line.strip())

    if data.get("education"):
        h1("Formation")
        for e in data["education"]:
            h2(e.get("studyType", "") + (f", {e['area']}" if e.get("area") else ""))
            dates = (f"{date_num(e['startDate'])} - " if e.get("startDate") else "") + date_num(e.get("endDate", ""))
            org = e.get("institution", "") + (f", {e['location']}" if e.get("location") else "")
            para(f"{org} | {dates}", italic=True)
            if e.get("summary"):
                para(e["summary"])

    if data.get("skills"):
        h1("Compétences")
        for s in data["skills"]:
            p = doc.add_paragraph(style="List Bullet")
            p.add_run(f"{s['name']} : ").bold = True
            p.add_run(", ".join(s.get("keywords", [])))

    if data.get("work"):
        h1("Expérience professionnelle")
        for w in data["work"]:
            h2(w.get("position", ""))
            end = date_num(w.get("endDate")) if w.get("endDate") else "Présent"
            org = w.get("name", "") + (f", {w['location']}" if w.get("location") else "")
            para(f"{org} | {date_num(w.get('startDate'))} - {end}", italic=True)
            if w.get("description"):
                para(w["description"])
            if w.get("summary"):
                para(w["summary"])
            bullets((w.get("activities") or []) + (w.get("highlights") or []))

    if data.get("certificates"):
        h1("Certifications")
        bullets(
            c["name"] + (f", {c['issuer']}" if c.get("issuer") else "")
            + (f" ({c['date']})" if c.get("date") else "")
            for c in data["certificates"]
        )

    if data.get("projects"):
        h1("Projets")
        for pr in data["projects"]:
            h2(pr.get("name", ""))
            if pr.get("description"):
                para(pr["description"], italic=True)
            bullets(pr.get("highlights") or [])

    if data.get("languages"):
        h1("Langues")
        bullets(f"{l['language']} : {l['fluency']}" for l in data["languages"])

    if data.get("interests"):
        h1("Centres d'intérêt")
        bullets(
            i["name"] + (f" : {', '.join(i['keywords'])}" if i.get("keywords") else "")
            for i in data["interests"]
        )

    cp = doc.core_properties
    cp.author = author
    cp.last_modified_by = author
    cp.title = f"CV {author}"
    cp.subject = plain(b.get("label", ""))
    cp.comments = ""
    cp.keywords = ""
    cp.category = ""
    cp.revision = 1
    cp.created = cp.modified = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
    doc.save(str(docx_path))
    neutralize_app_props(docx_path)


APP_XML = (
    "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>\n"
    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
    'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"/>'
)


def neutralize_app_props(docx_path):
    """Remplace docProps/app.xml (application et version héritées du modèle
    python-docx) par un bloc de propriétés vide."""
    tmp = docx_path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(docx_path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = APP_XML.encode() if item.filename == "docProps/app.xml" else src.read(item)
            dst.writestr(item, data)
    tmp.replace(docx_path)


# -------------------------------------------------------------------- main

def parse_args():
    parser = argparse.ArgumentParser(description="Génère la variante ATS du CV (PDF + DOCX).")
    parser.add_argument("-i", "--input", default="resume.json", help="fichier JSON Resume source")
    parser.add_argument("-o", "--output", help="nom des fichiers de sortie, sans extension")
    parser.add_argument("--author", help="auteur des métadonnées (défaut : Prénom NOM)")
    return parser.parse_args()


def main():
    args = parse_args()
    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(BASE_DIR / args.input, encoding="utf-8") as f:
        data = json.load(f)

    basics = data.get("basics", {})
    author = args.author or default_author(basics)
    name = args.output or f"{default_output_name(basics)}-ats"

    pdf_path = OUTPUT_DIR / f"{name}.pdf"
    build_pdf(data, author, pdf_path)
    print(f"PDF généré  : {pdf_path}")

    docx_path = OUTPUT_DIR / f"{name}.docx"
    build_docx(data, author, docx_path)
    print(f"DOCX généré : {docx_path}")


if __name__ == "__main__":
    main()
