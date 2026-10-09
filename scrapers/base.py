import time
from typing import Dict, Any, Optional
import requests

class BaseScraper:
    name: str = "base"

    def __init__(self, delay: float = 0.5):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "fr-CA,fr;q=0.9,en;q=0.8",
        })

    def make_record(
        self,
        nom: str,
        proprietaire: str = "",
        region_province: str = "Québec",
        pays: str = "Canada",
        superficie: str = "",
        type_culture: str = "",
        courriel: str = "",
        telephone: str = "",
        site_web: str = "",
        adresse: str = "",
        ville: str = "",
        code_postal: str = "",
        certifications: str = "",
        statut: str = "prospect",
        notes: str = ""
    ) -> Dict[str, Any]:
        return {
            "Nom de la ferme": nom.strip(),
            "Propriétaire": proprietaire.strip(),
            "Région / Province": region_province.strip(),
            "Pays": pays.strip(),
            "Superficie (ha ou m²)": superficie.strip(),
            "Type de culture": type_culture.strip(),
            "Courriel": courriel.strip(),
            "Téléphone": telephone.strip(),
            "Site Web": site_web.strip(),
            "Adresse": adresse.strip(),
            "Ville": ville.strip(),
            "Code Postal": code_postal.strip(),
            "Certifications": certifications.strip(),
            "Statut": statut.strip(),
            "Notes": notes.strip(),
        }

    def sleep(self):
        if self.delay > 0:
            time.sleep(self.delay)

    def scrape(self):
        raise NotImplementedError
