# CV as code — resume.json → HTML/PDF

Pipeline minimal : vos données au format standard **JSON Resume**, un template
HTML/CSS que vous maîtrisez entièrement, et un export PDF fidèle au CSS via
**WeasyPrint**.

## Fichiers

- `resume.json` — vos données (format JSON Resume). C'est le seul fichier à
  éditer au quotidien.
- `template.html` — le gabarit Jinja2 qui structure le CV.
- `style.css` — le style visuel (colonne sombre à gauche sur chaque page).
- `generate_pdf.py` — script qui assemble le tout et génère `output/NOM.html`
  et `output/NOM.pdf` (voir « Nom des fichiers » ci-dessous).
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

   **Nom des fichiers** : par défaut, il est composé à partir de
   `basics.name` et du début de `basics.label` (jusqu'au premier `|`, `(` ou
   `,`), par exemple `cv-benoit-buzens-ingenieur-cybersecurite`. Pour
   l'imposer :

   ```bash
   python generate_pdf.py -o cv-candidature-acme
   ```

4. Récupérez `output/NOM.pdf` pour vos candidatures, et `output/NOM.html` pour
   une publication directe sur votre site personnel (copiez `style.css` à
   côté).

## Points d'attention

- **Compatibilité ATS** : la mise en page en deux colonnes (sidebar) est
  esthétique mais certains outils de parsing automatisés lisent le texte
  dans l'ordre du HTML, qui peut ne pas correspondre à l'ordre visuel. Le
  DOM actuel place la sidebar avant le contenu principal ; si vous
  postulez via un ATS strict, gardez un export PDF/texte de secours en une
  colonne.
- **Deux pages** : la colonne de gauche porte photo, contact, compétences
  et langues en page 1, certifications et centres d'intérêt en page 2.
  Chaque partie doit tenir sur sa page ; si elle déborde, raccourcissez
  les compétences.
- **Poste visé** : `basics.label` au format `Poste | précision`
  (ex. `Ingénieur Cybersécurité | Stage de 4 à 5 mois, dès avril 2027`)
  s'affiche en titre de la colonne principale.
- **Mise en gras** : dans `resume.json`, entourez de `**...**` le passage à
  faire ressortir (ex. `portée de **20 à 80 %**`) ; le reste de la puce
  reste en texte normal.
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
