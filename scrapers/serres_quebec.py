from typing import List, Dict, Any
from .base import BaseScraper

class SerresQuebecScraper(BaseScraper):
    name = "serres_quebec"
    api_url = "https://www.serres.quebec/wp-admin/admin-ajax.php"

    CENTERS = [
        ("Québec", 46.8138, -71.2079),
        ("Montréal", 45.5017, -73.5673),
        ("Sherbrooke", 45.4042, -71.8929),
        ("Saguenay", 48.4284, -71.0664),
        ("Rimouski", 48.4488, -68.5239),
        ("Gatineau", 45.4765, -75.7013),
        ("Trois-Rivières", 46.3432, -72.5477),
        ("Saint-Hyacinthe", 45.6275, -72.9555),
        ("Joliette", 46.0167, -73.4333),
        ("Rouyn-Noranda", 48.2430, -79.0189),
        ("Gaspé", 48.8317, -64.4811),
        ("Saint-Georges", 46.1206, -70.6698),
    ]

    def scrape(self) -> List[Dict[str, Any]]:
        seen_ids = set()
        records = []

        for name, lat, lng in self.CENTERS:
            params = {
                "action": "store_search",
                "lat": str(lat),
                "lng": str(lng),
                "max_results": "100",
                "radius": "2000",
                "autoload": "1"
            }
            try:
                r = self.session.get(self.api_url, params=params, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    for item in data:
                        store_id = item.get("id") or item.get("store")
                        if not store_id or store_id in seen_ids:
                            continue
                        seen_ids.add(store_id)

                        nom = item.get("store", "")
                        addr1 = item.get("address", "")
                        addr2 = item.get("address2", "")
                        adresse = f"{addr1} {addr2}".strip()
                        ville = item.get("city", "")
                        province = item.get("state") or "Québec"
                        pays = item.get("country") or "Canada"
                        code_postal = item.get("zip", "")
                        phone = item.get("phone", "")
                        email = item.get("email", "")
                        site_web = item.get("url", "")
                        hours = item.get("hours", "")
                        lat_val = item.get("lat", "")
                        lng_val = item.get("lng", "")

                        notes_parts = ["Source: serres.quebec"]
                        if hours:
                            notes_parts.append(f"Heures: {hours}")
                        if lat_val and lng_val:
                            notes_parts.append(f"GPS: ({lat_val}, {lng_val})")

                        record = self.make_record(
                            nom=nom,
                            proprietaire="",
                            region_province=province,
                            pays=pays,
                            superficie="",
                            type_culture="Producteur en serre",
                            courriel=email,
                            telephone=phone,
                            site_web=site_web,
                            adresse=adresse,
                            ville=ville,
                            code_postal=code_postal,
                            certifications="",
                            statut="prospect",
                            notes=" | ".join(notes_parts)
                        )
                        records.append(record)
            except Exception as e:
                print(f"[serres_quebec] Erreur pour centre {name}: {e}")
            self.sleep()

        return records
