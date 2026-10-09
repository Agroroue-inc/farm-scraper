import re
from typing import List, Dict, Any
from lxml import html
from .base import BaseScraper

PROVINCES_MAP = {
    "QC": "Québec",
    "ON": "Ontario",
    "BC": "Colombie-Britannique",
    "AB": "Alberta",
    "MB": "Manitoba",
    "SK": "Saskatchewan",
    "NB": "Nouveau-Brunswick",
    "NS": "Nouvelle-Écosse",
    "PE": "Île-du-Prince-Édouard",
    "NL": "Terre-Neuve-et-Labrador",
}

class CFIAInspectionScraper(BaseScraper):
    name = "cfia_inspection"
    url = "https://inspection.canada.ca/fr/protection-vegetaux/phytoravageurs-plantes-envahissantes/directives/horticulture/16-02/etablissements-autorises"

    def scrape(self) -> List[Dict[str, Any]]:
        records = []
        try:
            r = self.session.get(self.url, timeout=20)
            if r.status_code != 200:
                print(f"[cfia] Erreur HTTP: {r.status_code}")
                return records

            tree = html.fromstring(r.content)
            rows = tree.xpath("//table[contains(@class, 'table')]//tbody/tr")
            for row in rows:
                cols = row.xpath("./td")
                if len(cols) >= 4:
                    num_auth = cols[0].text_content().strip()
                    nom = cols[1].text_content().strip()
                    ville = cols[2].text_content().strip()
                    prov_code = cols[3].text_content().strip()
                    province = PROVINCES_MAP.get(prov_code, prov_code)

                    notes = f"Source: ACIA/CFIA Directive D-16-02 | N° d'autorisation: {num_auth}"

                    record = self.make_record(
                        nom=nom,
                        proprietaire="",
                        region_province=province,
                        pays="Canada",
                        superficie="",
                        type_culture="Serre certifiée exportation GCP",
                        courriel="",
                        telephone="",
                        site_web="",
                        adresse="",
                        ville=ville,
                        code_postal="",
                        certifications=f"GCP ({num_auth})",
                        statut="prospect",
                        notes=notes
                    )
                    records.append(record)
        except Exception as e:
            print(f"[cfia] Erreur scraping: {e}")

        return records
