import subprocess
import json
import re
from typing import List, Dict, Any
from lxml import html
from .base import BaseScraper

class PagesJaunesScraper(BaseScraper):
    name = "pages_jaunes"
    base_url = "https://www.pagesjaunes.ca/search/si/{page}/serres/Quebec+QC"

    def _fetch_page(self, page_num: int) -> str:
        url = self.base_url.format(page=page_num)
        cmd = [
            "curl.exe", "-s",
            "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "-H", "Accept-Language: fr-CA,fr;q=0.9,en;q=0.8",
            url
        ]
        try:
            return subprocess.check_output(cmd, text=True, encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"[pages_jaunes] Erreur curl page {page_num}: {e}")
            return ""

    def scrape(self, max_pages: int = 5) -> List[Dict[str, Any]]:
        records = []
        seen_names = set()

        for page in range(1, max_pages + 1):
            print(f"[pages_jaunes] Extraction page {page}...")
            out = self._fetch_page(page)
            if not out or "itemListElement" not in out:
                break

            # 1. Parse JSON-LD
            json_lds = re.findall(r'<script type="application/ld\+json">(.*?)</script>', out, re.DOTALL)
            page_items = {}
            for s in json_lds:
                try:
                    data = json.loads(s)
                    items = data.get("@graph", []) if isinstance(data, dict) else (data if isinstance(data, list) else [data])
                    for it in items:
                        if it.get("@type") == "ItemList":
                            for elem in it.get("itemListElement", []):
                                bus = elem.get("item", {})
                                name = bus.get("name")
                                if name:
                                    page_items[name] = bus
                except Exception:
                    pass

            if not page_items:
                break

            # 2. Extract phone numbers from HTML
            tree = html.fromstring(out)
            listings = tree.xpath("//div[contains(@class, 'listing__content')]")
            phone_map = {}
            for l in listings:
                names = l.xpath(".//h3//text() | .//a[contains(@class, 'listing__name--link')]//text()")
                cleaned_name = " ".join([n.strip() for n in names if n.strip()])
                phones = l.xpath(".//*[contains(@class, 'phone')]//text() | .//a[@data-phone]/@data-phone")
                valid_phones = [p.strip() for p in phones if re.search(r'\d{3}[-\s.]\d{3}[-\s.]\d{4}', p.strip())]
                if cleaned_name and valid_phones and cleaned_name not in phone_map:
                    phone_map[cleaned_name] = valid_phones[0]

            # 3. Create records
            for nom, bus in page_items.items():
                if nom in seen_names:
                    continue
                seen_names.add(nom)

                addr_dict = bus.get("address", {})
                adresse = addr_dict.get("streetAddress", "")
                ville = addr_dict.get("addressLocality", "Québec")
                province = addr_dict.get("addressRegion", "Québec")
                if province == "QC":
                    province = "Québec"
                code_postal = addr_dict.get("postalCode", "")
                url = bus.get("url", "")
                geo = bus.get("geo", {})
                lat = geo.get("latitude", "")
                lng = geo.get("longitude", "")

                # Match phone
                phone = phone_map.get(nom, "")
                if not phone:
                    # Try partial match
                    for k, v in phone_map.items():
                        if nom in k or k in nom:
                            phone = v
                            break

                notes_parts = ["Source: Pages Jaunes (Serres Québec)"]
                if url:
                    notes_parts.append(f"Fiche PJ: {url}")
                if lat and lng:
                    notes_parts.append(f"GPS: ({lat}, {lng})")

                rec = self.make_record(
                    nom=nom,
                    proprietaire="",
                    region_province=province,
                    pays="Canada",
                    superficie="",
                    type_culture="Serre & Horticulture",
                    courriel="",
                    telephone=phone,
                    site_web=url,
                    adresse=adresse,
                    ville=ville,
                    code_postal=code_postal,
                    certifications="",
                    statut="prospect",
                    notes=" | ".join(notes_parts)
                )
                records.append(rec)

            self.sleep()

        return records
