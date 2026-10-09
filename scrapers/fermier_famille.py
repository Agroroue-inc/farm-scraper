import re
from typing import List, Dict, Any
from lxml import html
from .base import BaseScraper

class FermierFamilleScraper(BaseScraper):
    name = "fermier_famille"
    url = "https://www.fermierdefamille.com/fr/listing/"

    def scrape(self) -> List[Dict[str, Any]]:
        records = []
        try:
            r = self.session.get(self.url, timeout=20)
            if r.status_code != 200:
                print(f"[fermier_famille] HTTP {r.status_code}")
                return records

            tree = html.fromstring(r.content)
            panels = tree.xpath("//div[contains(@class, 'panel-default')]")
            seen_names = set()

            for p in panels:
                # Region title
                h2 = p.xpath(".//h2//text()")
                region_title = " ".join([h.strip() for h in h2 if h.strip() and h.strip() not in ['+', '-']])
                if not region_title:
                    region_title = "Québec"

                # Farm rows
                farm_rows = p.xpath(".//div[contains(@class, 'farm')]")
                for farm in farm_rows:
                    h3 = farm.xpath(".//h3/text()")
                    nom = h3[0].strip() if h3 else ""
                    if not nom or nom in seen_names:
                        continue
                    seen_names.add(nom)

                    # Location
                    h4 = farm.xpath(".//h4[contains(@class, 'place')]/text()")
                    place = h4[0].strip() if h4 else ""
                    ville = ""
                    prov = "Québec"
                    if place:
                        parts = [x.strip() for x in place.split(",")]
                        ville = parts[0]
                        if "N.-B." in place or "Nouveau-Brunswick" in place:
                            prov = "Nouveau-Brunswick"

                    # Description / Culture
                    p_desc = farm.xpath(".//p[not(a)]/text()")
                    desc = " ".join([d.strip() for d in p_desc if d.strip()])
                    desc_short = (desc[:200] + "...") if len(desc) > 200 else desc

                    # Website link
                    site_a = farm.xpath(".//a[contains(text(), 'Site') or contains(@class, 'btn-outline-green')]/@href")
                    website = site_a[0].strip() if site_a else ""

                    # Subscription / profile link
                    sub_a = farm.xpath(".//a[contains(@class, 'btn-green')]/@href")
                    sub_url = ""
                    if sub_a:
                        sub_href = sub_a[0].strip()
                        sub_url = f"https://www.fermierdefamille.com{sub_href}" if sub_href.startswith("/") else sub_href

                    notes_parts = [
                        "Source: Réseau des Fermiers de Famille (CAPÉ)",
                        f"Région: {region_title}"
                    ]
                    if sub_url:
                        notes_parts.append(f"Abonnement paniers: {sub_url}")
                    if desc and desc != desc_short:
                        notes_parts.append(f"Description: {desc}")

                    rec = self.make_record(
                        nom=nom,
                        proprietaire="",
                        region_province=f"{region_title}, {prov}",
                        pays="Canada",
                        superficie="",
                        type_culture="Maraîcher biologique (Paniers bio ASC)",
                        courriel="",
                        telephone="",
                        site_web=website,
                        adresse="",
                        ville=ville,
                        code_postal="",
                        certifications="Certifié ou pré-certifié biologique (Réseau des Fermiers de famille)",
                        statut="prospect",
                        notes=" | ".join(notes_parts)
                    )
                    records.append(rec)

        except Exception as e:
            print(f"[fermier_famille] Erreur: {e}")

        return records
