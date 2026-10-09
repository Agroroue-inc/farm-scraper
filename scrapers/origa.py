import re
from typing import List, Dict, Any
from lxml import html
from .base import BaseScraper

REGIONS = [
    ("Montérégie", "https://origa.ca/fermes/monteregie"),
    ("Estrie", "https://origa.ca/fermes/estrie"),
    ("Laurentides", "https://origa.ca/fermes/laurentides"),
    ("Lanaudière", "https://origa.ca/fermes/lanaudiere"),
    ("Mauricie", "https://origa.ca/fermes/mauricie"),
    ("Centre-du-Québec", "https://origa.ca/fermes/centre-du-quebec"),
    ("Chaudière-Appalaches", "https://origa.ca/fermes/chaudiere-appalaches"),
    ("Capitale-Nationale", "https://origa.ca/fermes/quebec"),
    ("Charlevoix", "https://origa.ca/fermes/charlevoix"),
    ("Bas-Saint-Laurent", "https://origa.ca/fermes/bas-saint-laurent"),
    ("Saguenay-Lac-Saint-Jean", "https://origa.ca/fermes/saguenay-lac-saint-jean"),
    ("Gaspésie-Îles-de-la-Madeleine", "https://origa.ca/fermes/gaspesie"),
    ("Abitibi-Témiscamingue", "https://origa.ca/fermes/abitibi-temiscamingue"),
    ("Côte-Nord", "https://origa.ca/fermes/cote-nord"),
    ("Outaouais", "https://origa.ca/fermes/outaouais"),
    ("Montréal", "https://origa.ca/fermes/montreal"),
    ("Laval", "https://origa.ca/fermes/laval"),
]

class OrigaScraper(BaseScraper):
    name = "origa"

    def scrape(self, fetch_details: bool = True, max_per_region: int = None) -> List[Dict[str, Any]]:
        records = []
        seen_names = set()

        for reg_name, reg_url in REGIONS:
            print(f"[origa] Exploration région: {reg_name}...")
            try:
                r = self.session.get(reg_url, timeout=15)
                if r.status_code != 200:
                    continue

                tree = html.fromstring(r.content)
                # Farm cards: <a> with /farm/
                farm_cards = tree.xpath("//a[contains(@href, '/farm/')]")
                if max_per_region:
                    farm_cards = farm_cards[:max_per_region]

                for card in farm_cards:
                    farm_href = card.attrib.get("href", "")
                    h3 = card.xpath(".//h3/text()")
                    nom = h3[0].strip() if h3 else ""
                    if not nom or nom in seen_names:
                        continue
                    seen_names.add(nom)

                    p_texts = [p.text_content().strip() for p in card.xpath(".//p") if p.text_content().strip()]
                    ville = p_texts[0] if len(p_texts) >= 1 else ""
                    culture = p_texts[1] if len(p_texts) >= 2 else "Ferme maraîchère / locale"

                    badges = [b.text_content().strip() for b in card.xpath(".//span") if b.text_content().strip()]
                    certifications = ", ".join(badges)

                    # Detail page for website & exact address
                    website = ""
                    adresse = ""
                    telephone = ""
                    courriel = ""
                    full_url = f"https://origa.ca{farm_href}" if farm_href.startswith("/") else farm_href

                    if fetch_details and farm_href:
                        try:
                            self.sleep()
                            r_det = self.session.get(full_url, timeout=10)
                            if r_det.status_code == 200:
                                d_tree = html.fromstring(r_det.content)
                                # External links (excluding app store, apple, origa, social)
                                ext_links = d_tree.xpath(
                                    "//a[starts-with(@href, 'http') and "
                                    "not(contains(@href, 'origa.ca')) and "
                                    "not(contains(@href, 'apple.com')) and "
                                    "not(contains(@href, 'google.com/store')) and "
                                    "not(contains(@href, 'facebook.com')) and "
                                    "not(contains(@href, 'instagram.com'))]/@href"
                                )
                                if ext_links:
                                    website = ext_links[0]

                                # Check phone or email in detail text
                                tel_matches = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', r_det.text)
                                if tel_matches:
                                    telephone = tel_matches[0]

                                email_matches = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', r_det.text)
                                valid_em = [e for e in email_matches if "origa.ca" not in e and not e.endswith(".png")]
                                if valid_em:
                                    courriel = valid_em[0]

                                # Address if google maps link present
                                gmap_links = d_tree.xpath("//a[contains(@href, 'google.com/maps')]/@href")
                                if gmap_links:
                                    m_query = re.search(r'query=([^&]+)', gmap_links[0])
                                    if m_query:
                                        from urllib.parse import unquote
                                        adresse = unquote(m_query.group(1)).replace("+", " ")
                        except Exception:
                            pass

                    notes_parts = ["Source: Origa"]
                    if full_url:
                        notes_parts.append(f"Fiche Origa: {full_url}")

                    rec = self.make_record(
                        nom=nom,
                        proprietaire="",
                        region_province=f"{reg_name}, Québec",
                        pays="Canada",
                        superficie="",
                        type_culture=culture,
                        courriel=courriel,
                        telephone=telephone,
                        site_web=website,
                        adresse=adresse,
                        ville=ville,
                        code_postal="",
                        certifications=certifications,
                        statut="prospect",
                        notes=" | ".join(notes_parts)
                    )
                    records.append(rec)

            except Exception as e:
                print(f"[origa] Erreur région {reg_name}: {e}")

            self.sleep()

        return records
