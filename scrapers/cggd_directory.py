import json
import re
from typing import List, Dict, Any
from .base import BaseScraper

class CGGDDirectoryScraper(BaseScraper):
    name = "cggd_flipbook"
    config_url = "https://online.fliphtml5.com/oudeu/2026-CGGD-final_web/files/search/search_config.js"

    def scrape(self) -> List[Dict[str, Any]]:
        records = []
        try:
            r = self.session.get(self.config_url, timeout=20)
            if r.status_code != 200:
                print(f"[cggd] Erreur chargement config: HTTP {r.status_code}")
                return records

            m = re.search(r'var textForPages\s*=\s*(\[.*\]);?', r.text, re.DOTALL)
            if not m:
                print("[cggd] Impossible de trouver textForPages")
                return records

            pages = json.loads(m.group(1))
            for page_idx, page_text in enumerate(pages):
                page_records = self._parse_page(page_text, page_idx + 1)
                records.extend(page_records)

        except Exception as e:
            print(f"[cggd] Erreur pendant le scraping: {e}")

        return records

    def _parse_page(self, text: str, page_num: int) -> List[Dict[str, Any]]:
        page_records = []
        
        # Clean page header lines like "18 | www.theflowerdirectory.com"
        lines = [line.strip() for line in text.replace('\r', '').split('\n')]
        
        # We split text into blocks based on TEL: or business names
        # Let's find entries starting with business names
        # Business names in CGGD are followed by an address line and city/province/postal code and TEL:
        tel_indices = [i for i, line in enumerate(lines) if line.startswith("TEL:")]
        
        for idx in tel_indices:
            # Look backwards for Name and Address
            # Lines between previous block and this TEL:
            start_idx = max(0, idx - 4)
            # Find postal code line (usually right above TEL:)
            postal_line_idx = idx - 1
            if postal_line_idx < 0:
                continue

            city_prov_postal = lines[postal_line_idx]
            address_line = lines[postal_line_idx - 1] if postal_line_idx - 1 >= 0 else ""
            
            # Name line can be 1 or 2 lines above
            name_candidates = []
            for k in range(max(0, postal_line_idx - 3), postal_line_idx - 1):
                cand = lines[k]
                if cand and not cand.startswith("www.") and not re.match(r'^\d+\s*\|', cand) and "WHOLESALERS" not in cand and "indicates" not in cand:
                    name_candidates.append(cand)
            nom = " ".join(name_candidates).strip()
            if not nom:
                nom = address_line
                address_line = ""

            # Parse city, province, postal code: e.g. "St. Davids, Ontario, L0S 1P0"
            ville = ""
            province = "Ontario"
            postal_code = ""
            parts = [p.strip() for p in city_prov_postal.split(',')]
            if len(parts) >= 3:
                ville = parts[0]
                province = parts[1]
                postal_code = parts[2]
            elif len(parts) == 2:
                ville = parts[0]
                province_postal = parts[1].split()
                if len(province_postal) >= 2:
                    postal_code = " ".join(province_postal[-2:])
                    province = " ".join(province_postal[:-2])
                else:
                    province = parts[1]

            # Parse fields following TEL:
            tel = lines[idx].replace("TEL:", "").split("|")[0].strip()
            
            # Scan forward until the next business block or page end
            email = ""
            website = ""
            contacts = []
            size = ""
            products = []
            
            for j in range(idx + 1, min(len(lines), idx + 25)):
                curr = lines[j]
                if curr.startswith("TEL:") or "WHOLESALERS" in curr or re.match(r'^\d+\s*\|', curr):
                    break
                if curr.startswith("EMAIL:"):
                    email = curr.replace("EMAIL:", "").strip()
                elif curr.startswith("WEBSITE:"):
                    website = curr.replace("WEBSITE:", "").strip()
                elif curr.startswith("CONTACT:"):
                    contacts.append(curr.replace("CONTACT:", "").strip())
                elif curr.startswith("GREENHOUSE SIZE:"):
                    size = curr.replace("GREENHOUSE SIZE:", "").strip()
                elif curr.startswith("PRODUCT/SERVICE:"):
                    products.append(curr.replace("PRODUCT/SERVICE:", "").strip())
                elif contacts and not size and not products and not curr.startswith("YEAR"):
                    contacts.append(curr)
                elif products and not curr.startswith("YEAR"):
                    products.append(curr)

            proprietaire = ", ".join(contacts).strip()
            type_culture = " ".join(products).strip()
            if len(type_culture) > 250:
                type_culture_short = type_culture[:250] + "..."
            else:
                type_culture_short = type_culture

            notes = f"Source: CGGD 2026 Flipbook (p. {page_num})"
            if size:
                notes += f" | Taille déclarée: {size}"
            if type_culture and type_culture != type_culture_short:
                notes += f" | Produits complets: {type_culture}"

            # Only add if we have at least a name and a phone/email
            if nom and (tel or email):
                page_records.append(self.make_record(
                    nom=nom,
                    proprietaire=proprietaire,
                    region_province=province,
                    pays="Canada",
                    superficie=size,
                    type_culture=type_culture_short or "Serres / Horticulture",
                    courriel=email,
                    telephone=tel,
                    site_web=website,
                    adresse=address_line,
                    ville=ville,
                    code_postal=postal_code,
                    certifications="",
                    statut="prospect",
                    notes=notes
                ))

        return page_records
