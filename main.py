import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any

from scrapers import ALL_SCRAPERS
from exporters import export_to_csv, export_to_excel
from consolidation import consolidate_records

DATA_DIR = Path("data")
SOURCES_DIR = DATA_DIR / "sources"

def run_scraper(name: str, scraper_cls, **kwargs) -> List[Dict[str, Any]]:
    print(f"\n==================================================")
    print(f"  Démarrage du scraper : {name}")
    print(f"==================================================")
    try:
        scraper = scraper_cls()
        if name == "apmquebec" and "max_items" in kwargs and kwargs["max_items"]:
            records = scraper.scrape(max_items=kwargs["max_items"])
        elif name == "origa" and "max_items" in kwargs and kwargs["max_items"]:
            records = scraper.scrape(fetch_details=True, max_per_region=max(1, kwargs["max_items"] // 10))
        elif name == "pages_jaunes" and "max_items" in kwargs and kwargs["max_items"]:
            records = scraper.scrape(max_pages=max(1, kwargs["max_items"] // 25))
        else:
            records = scraper.scrape()
        print(f"-> Succès [{name}] : {len(records)} exploitations extraites.")
        
        # Save individual source
        source_csv = SOURCES_DIR / f"{name}.csv"
        export_to_csv(records, source_csv)
        print(f"   Export individuel sauvegardé dans : {source_csv}")
        return records
    except Exception as e:
        print(f"-> Erreur sur [{name}] : {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Scraper multi-sources pour fermes, serres et maraîchers (Agroroue)")
    parser.add_argument("--all", action="store_true", help="Exécuter tous les scrapers")
    parser.add_argument("--source", type=str, choices=list(ALL_SCRAPERS.keys()), help="Exécuter un scraper spécifique")
    parser.add_argument("--max-items", type=int, default=None, help="Limiter le nombre d'éléments pour tester rapidement")
    args = parser.parse_args()

    if not args.all and not args.source:
        print("Usage:")
        print("  py main.py --all                    (Lance tous les scrapers)")
        print(f"  py main.py --source <nom>           (Choix: {', '.join(ALL_SCRAPERS.keys())})")
        print("  py main.py --all --max-items 10     (Mode test rapide)")
        sys.exit(0)

    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    all_extracted: List[Dict[str, Any]] = []

    to_run = ALL_SCRAPERS.items() if args.all else [(args.source, ALL_SCRAPERS[args.source])]

    for name, scraper_cls in to_run:
        records = run_scraper(name, scraper_cls, max_items=args.max_items)
        all_extracted.extend(records)

    print(f"\n==================================================")
    print(f"  BILAN GLOBAL & CONSOLIDATION")
    print(f"==================================================")
    print(f"Total brut extrait : {len(all_extracted)} fiches")

    consolidated = consolidate_records(all_extracted)
    print(f"Total unique après déduplication : {len(consolidated)} fermes / exploitations")

    # Exports finaux consolidés
    csv_path = DATA_DIR / "fermes_consolidees.csv"
    xlsx_path = DATA_DIR / "fermes_consolidees.xlsx"
    
    export_to_csv(consolidated, csv_path)
    export_to_excel(consolidated, xlsx_path)

    # Statistiques enrichissement
    phones_count = sum(1 for r in consolidated if r.get("Téléphone"))
    emails_count = sum(1 for r in consolidated if r.get("Courriel"))
    websites_count = sum(1 for r in consolidated if r.get("Site Web"))
    address_count = sum(1 for r in consolidated if r.get("Adresse"))

    print(f"\nExports consolidés générés :")
    print(f" - CSV (UTF-8 avec BOM pour Excel) : {csv_path.resolve()}")
    print(f" - Excel (.xlsx)                   : {xlsx_path.resolve()}")
    print(f"\nTaux d'enrichissement :")
    print(f" - Téléphones : {phones_count} / {len(consolidated)} ({phones_count*100//max(1, len(consolidated))}%)")
    print(f" - Courriels   : {emails_count} / {len(consolidated)} ({emails_count*100//max(1, len(consolidated))}%)")
    print(f" - Sites web   : {websites_count} / {len(consolidated)} ({websites_count*100//max(1, len(consolidated))}%)")
    print(f" - Adresses    : {address_count} / {len(consolidated)} ({address_count*100//max(1, len(consolidated))}%)")
    print("Extraction terminée avec succès !")

if __name__ == "__main__":
    main()
