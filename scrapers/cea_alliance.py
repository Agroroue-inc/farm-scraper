import re
from typing import List, Dict, Any
from urllib.parse import urlparse
from lxml import html
from .base import BaseScraper

class CEAAllianceScraper(BaseScraper):
    name = "cea_alliance"
    url = "https://ceaalliance.com/our-members/"

    def scrape(self) -> List[Dict[str, Any]]:
        records = []
        try:
            r = self.session.get(self.url, timeout=20)
            if r.status_code != 200:
                print(f"[cea_alliance] HTTP {r.status_code}")
                return records

            tree = html.fromstring(r.content)
            # Find all links with images inside member rows
            links = tree.xpath("//div[contains(@class, 'et_pb_row')]//a[.//img]")
            seen_urls = set()

            current_category = "Producteur CEA (Controlled Environment Agriculture)"
            
            for l in links:
                href = l.attrib.get("href", "").strip()
                if not href or href in seen_urls or "ceaalliance.com" in href:
                    continue
                seen_urls.add(href)

                # Determine name from img title, alt, or domain
                img = l.xpath(".//img")[0]
                title = img.attrib.get("title", "").strip()
                alt = img.attrib.get("alt", "").strip()
                
                name_cand = title or alt
                # Clean title e.g. "AeroFarms_Gradient_Logo_with_Tagline" -> "AeroFarms"
                name_cand = re.sub(r'[_\-]+', ' ', name_cand)
                name_cand = re.sub(r'(Logo|Icon|Final|Print|Full Color|\d+x\d+|\.jpg|\.png).*$', '', name_cand, flags=re.IGNORECASE).strip()
                
                # If still empty or generic, infer from hostname
                parsed = urlparse(href)
                domain_name = parsed.netloc.replace("www.", "").split(".")[0].capitalize()
                
                nom = name_cand if (name_cand and len(name_cand) > 2) else domain_name

                # Determine country
                pays = "Canada" if href.endswith(".ca") else "États-Unis / International"
                province = "Canada" if pays == "Canada" else ""

                notes = f"Source: CEA Alliance (Membre officiel)"

                record = self.make_record(
                    nom=nom,
                    proprietaire="",
                    region_province=province,
                    pays=pays,
                    superficie="",
                    type_culture=current_category,
                    courriel="",
                    telephone="",
                    site_web=href,
                    adresse="",
                    ville="",
                    code_postal="",
                    certifications="CEA Alliance",
                    statut="prospect",
                    notes=notes
                )
                records.append(record)

        except Exception as e:
            print(f"[cea_alliance] Erreur: {e}")

        return records
