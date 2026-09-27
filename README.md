# CV as code — resume.json → HTML/PDF

Pipeline minimal : vos données au format standard **JSON Resume**, un template
HTML/CSS que vous maîtrisez entièrement, et un export PDF fidèle au CSS via
**WeasyPrint**.

## Fichiers

- `resume.json` — vos données (format JSON Resume). C'est le seul fichier à
  éditer au quotidien.
- `template.html` — le gabarit Jinja2 qui structure le CV.
- `style.css` — le style visuel (sidebar sombre, une page A4).
- `generate_pdf.py` — script qui assemble le tout et génère `output/cv.html`
  et `output/cv.pdf`.
- `photo.jpg` (optionnel) — à ajouter vous-même à la racine du projet. Sans
  ce fichier, un cercle avec vos initiales est affiché à la place.

## Installation

```bash
pip install jinja2 weasyprint
```

## Utilisation

1. Éditez `resume.json` avec vos informations (respectez le [schéma JSON
   Resume](https://jsonresume.org/schema/)).
2. (Optionnel) Placez une photo carrée à la racine sous le nom indiqué dans
   `basics.image` de `resume.json`.
3. Lancez :

   ```bash
   python generate_pdf.py
   ```

4. Récupérez `output/cv.pdf` pour vos candidatures, et `output/cv.html` pour
   une publication directe sur votre site personnel (copiez `style.css` à
   côté).

## Points d'attention

- **Compatibilité ATS** : la mise en page en deux colonnes (sidebar) est
  esthétique mais certains outils de parsing automatisés lisent le texte
  dans l'ordre du HTML, qui peut ne pas correspondre à l'ordre visuel. Le
  DOM actuel place la sidebar avant le contenu principal ; si vous
  postulez via un ATS strict, gardez un export PDF/texte de secours en une
  colonne.
- **Une page** : le CSS est calé pour tenir sur une page A4. Si votre
  expérience s'allonge, il faudra soit réduire `font-size`/marges, soit
  accepter une deuxième page (retirez alors `min-height: 297mm` sur
  `.page`).
- **Conversion vers d'autres outils** : `resume.json` étant au format
  standard, vous pouvez le réutiliser tel quel avec n'importe quel thème
  de l'écosystème JSON Resume (`resume-cli`) si vous voulez comparer un
  rendu alternatif.

## Prochaines évolutions possibles

- Personnaliser les couleurs dans `style.css` (variables `#1f2d3d`,
  `#2e3f53`, `#7fa8cc`).
- Ajouter une section "Certifications" ou "Publications" (déjà prévues par
  le schéma JSON Resume, à intégrer dans `template.html` si besoin).
- Générer une variante one-column pour un dépôt ATS-safe en parallèle de la
  version sidebar.
