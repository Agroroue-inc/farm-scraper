# 🌾 Agroroue - Scraper Multi-Sources de Fermes & Maraîchers

Programme automatisé d'extraction, de nettoyage et de consolidation de données agricoles (producteurs en serres, maraîchers, fermes biologiques) pour le projet **Agroroue**.

Ce programme interroge **8 sources officielles québécoises et canadiennes**, extrait les informations détaillées (contacts, coordonnées, types de cultures, certifications, surfaces) et génère des fichiers d'export prêts à l'importation.

---

## 📋 Table des matières
- [Sources de données](#-sources-de-données)
- [Format des données exportées](#-format-des-données-exportées)
- [Prérequis et Installation](#-prérequis-et-installation)
- [Utilisation](#-utilisation)
- [Architecture du projet](#-architecture-du-projet)
- [Ajouter une nouvelle source](#-ajouter-une-nouvelle-source)

---

## 🌐 Sources de données

Le programme regroupe actuellement **8 sources** :

| Source | Description | Volume moyen |
|---|---|---|
| **Producteurs en serres du Québec** (`serres.quebec`) | Annuaire officiel des membres serricoles au Québec | ~72 serres |
| **Canadian Greenhouse Growers' Directory 2026** (`fliphtml5.com`) | Guide national canadien des serres avec surfaces et contacts | ~216 exploitations |
| **ACIA / CFIA Établissements autorisés** | Registre fédéral des serres certifiées pour l'exportation (GCP) | ~174 serres |
| **Controlled Environment Agriculture Alliance (CEA)** | Membres officiels en agriculture en environnement contrôlé | ~58 producteurs |
| **Association des Producteurs Maraîchers du Québec (APMQ)** | Répertoire exhaustif des maraîchers québécois | ~245 producteurs |
| **Pages Jaunes (Serres Québec)** | Annuaire commercial serres et centres jardins de la région | ~24 serres |
| **Origa** | Répertoire des fermes locales à travers les 17 régions du Québec | ~288 fermes |
| **Réseau des Fermiers de Famille (CAPÉ)** | Réseau de fermes maraîchères biologiques certifiées (paniers bio) | ~87 fermes |

**Total brut** : ~1 164 fiches  
**Total après fusion & déduplication** : **1 068 fermes uniques consolidées**

---

## 📊 Format des données exportées

Le fichier consolidé et les fichiers sources respectent l'ordre exact de colonnes suivant pour votre importateur :

| # | Colonne | Description | Exemple |
|---|---|---|---|
| 1 | `Nom de la ferme` | Raison sociale ou nom commercial | *Ferme Bédard Blouin inc.* |
| 2 | `Propriétaire` | Représentant, exploitant ou contact | *Marc Bouchard* |
| 3 | `Région / Province` | Région administrative et province | *Capitale-Nationale, Québec* |
| 4 | `Pays` | Pays de l'exploitation | *Canada* |
| 5 | `Superficie (ha ou m²)` | Surface de serre ou de terrain déclarée | *27 685 sq. meters* |
| 6 | `Type de culture` | Cultures principales ou spécialités | *Maraîcher, Serre, Petits fruits* |
| 7 | `Courriel` | Courriel de contact (déchiffré si protégé) | *contact@ferme.ca* |
| 8 | `Téléphone` | Téléphone(s) et mobile(s) | *418-666-5518* |
| 9 | `Site Web` | URL du site web officiel | *https://www.fermebedardblouin.com/* |
| 10 | `Adresse` | Adresse civique | *2173 boulevard Louis XIV* |
| 11 | `Ville` | Ville ou municipalité | *Beauport* |
| 12 | `Code Postal` | Code postal canadien | *G1C 1A1* |
| 13 | `Certifications` | Normes (CanadaGAP, Bio, Écocert, etc.) | *Canada Gap, Biologique* |
| 14 | `Statut` | Statut CRM par défaut | *prospect* |
| 15 | `Notes` | Source d'origine, fiche source, GPS, etc. | *Source: APMQ \| GPS: (46.88, -71.22)* |

---

## 🚀 Prérequis et Installation

### 1. Prérequis
- Python 3.10 ou supérieur
- Accès Internet pour interroger les sites

### 2. Installation des dépendances
```bash
py -m pip install -r requirements.txt
```

Les dépendances principales sont :
- `requests` : requêtes HTTP avec gestion des sessions et headers
- `lxml` : analyse rapide du HTML / XPath
- `openpyxl` : génération de classeurs Excel (`.xlsx`)

---

## 💻 Utilisation

### 1. Lancer l'extraction de toutes les sources (Recommandé)
```bash
py main.py --all
```
Cette commande exécute séquentiellement chaque scraper, sauvegarde un CSV individuel par source dans `data/sources/`, puis fusionne, déduplique et enrichit les données dans :
- `data/fermes_consolidees.csv` (CSV encodé en UTF-8 avec BOM pour Excel)
- `data/fermes_consolidees.xlsx` (Fichier Excel complet avec en-têtes stylisés)

### 2. Lancer une seule source spécifique
```bash
py main.py --source apmquebec
py main.py --source serres_quebec
py main.py --source origa
py main.py --source cggd
py main.py --source fermier_famille
py main.py --source pages_jaunes
py main.py --source cfia
py main.py --source cea_alliance
```

### 3. Mode test rapide
Pour tester sans attendre l'extraction complète :
```bash
py main.py --all --max-items 10
```

---

## 📁 Architecture du projet

```
Agroroue/
├── scrapers/                     # Modules d'extraction
│   ├── __init__.py               # Registre de tous les scrapers disponibles
│   ├── base.py                   # Classe mère (User-Agent, sessions, make_record)
│   ├── serres_quebec.py          # API WP Store Locator (serres.quebec)
│   ├── cggd_directory.py         # Flipbook national 2026 (fliphtml5.com)
│   ├── cfia_inspection.py        # Registre officiel fédéral ACIA / CFIA
│   ├── cea_alliance.py           # Annuaire CEA Alliance
│   ├── apmquebec.py              # Association Producteurs Maraîchers (APMQ)
│   ├── pages_jaunes.py           # Pages Jaunes Québec (Schema.org)
│   ├── origa.py                  # 17 régions administratives (Origa)
│   └── fermier_famille.py        # Réseau des Fermiers de Famille (CAPÉ)
├── exporters/                    # Formats de sortie
│   ├── __init__.py
│   └── exporter.py               # Générateur CSV (utf-8-sig) et Excel (.xlsx)
├── consolidation.py              # Logique de fusion, enrichissement et déduplication
├── data/                         # Données produites
│   ├── fermes_consolidees.csv    # FICHIER FINAL POUR L'IMPORTATEUR
│   ├── fermes_consolidees.xlsx   # Version Excel
│   └── sources/                  # Sauvegardes individuelles par source
├── main.py                       # Point d'entrée en ligne de commande
├── requirements.txt              # Dépendances Python
└── README.md                     # Documentation
```

---

## ➕ Ajouter une nouvelle source

Le programme est modulaire. Pour ajouter un nouveau site :
1. Créez un fichier dans `scrapers/nouveau_site.py` héritant de `BaseScraper`.
2. Implémentez la méthode `scrape()` qui retourne une liste d'enregistrements créés avec `self.make_record(...)`.
3. Ajoutez le scraper dans `scrapers/__init__.py`.
4. Le nouveau site sera automatiquement pris en charge par `py main.py --all` et fusionné dans les fichiers finaux.
