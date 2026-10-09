import re
from typing import List, Dict, Any
from lxml import html
from .base import BaseScraper

def decode_cf_email(cf_hex: str) -> str:
    try:
        r = int(cf_hex[:2], 16)
        return ''.join([chr(int(cf_hex[i:i+2], 16) ^ r) for i in range(2, len(cf_hex), 2)])
    except Exception:
        return ""

class APMQuebecScraper(BaseScraper):
    name = "apmquebec"
    url = "https://apmquebec.com/repertoire/"

    def scrape(self, max_items: int = None) -> List[Dict[str, Any]]:
        records = []
        try:
            r = self.session.get(self.url, timeout=20)
            if r.status_code != 200:
                print(f"[apmquebec] HTTP {r.status_code}")
                return records

            tree = html.fromstring(r.content)
            cards = tree.xpath("//li[contains(@class, 'card')]")
            if max_items:
                cards = cards[:max_items]

            print(f"[apmquebec] {len(cards)} fiches de producteurs trouvées. Extraction en cours...")

            for idx, c in enumerate(cards, 1):
                nom = c.attrib.get("data-name", "").strip()
                fiche_url = c.attrib.get("data-url", "").strip()
                lat = c.attrib.get("data-lat", "").strip()
                lng = c.attrib.get("data-lng", "").strip()

                ville_list = c.xpath(".//p[@class='city']/text()")
                region_list = c.xpath(".//p[@class='region']/text()")
                ville = ville_list[0].strip() if ville_list else ""
                region = region_list[0].strip() if region_list else "Québec"

                # Valeurs par défaut
                adresse = ""
                code_postal = ""
                proprietaire = ""
                telephone = ""
                courriel = ""
                certifications = ""
                type_culture = "Maraîcher"
                website = ""
                produits = []

                if fiche_url:
                    try:
                        self.sleep()
                        r_fiche = self.session.get(fiche_url, timeout=12)
                        if r_fiche.status_code == 200:
                            f_tree = html.fromstring(r_fiche.content)
                            
                            # Recherche emails (Cloudflare data-cfemail ou regex)
                            cf_nodes = f_tree.xpath("//*[@data-cfemail]")
                            for cf in cf_nodes:
                                dec = decode_cf_email(cf.attrib.get("data-cfemail", ""))
                                if dec and "@" in dec and not courriel:
                                    courriel = dec

                            if not courriel:
                                raw_text = r_fiche.text
                                email_matches = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', raw_text)
                                valid_emails = [e for e in email_matches if "wght@" not in e and "example.com" not in e and not e.endswith(".png") and not e.endswith(".jpg")]
                                if valid_emails:
                                    courriel = valid_emails[0]

                            # Adresse complète
                            addr_blocks = f_tree.xpath("//*[contains(text(), 'Adresse compl')]/following-sibling::div | //*[contains(text(), 'Adresse compl')]/parent::*")
                            for b in addr_blocks:
                                lines = [line.strip() for line in b.text_content().split("\n") if line.strip() and "Adresse" not in line]
                                if lines:
                                    adresse = lines[0]
                                    # postal code regex A1A 1A1
                                    for line in lines:
                                        m_post = re.search(r'[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d', line)
                                        if m_post:
                                            code_postal = m_post.group(0).upper()
                                    break

                            # Représentants & téléphones
                            rep_blocks = f_tree.xpath("//*[contains(text(), 'Représentant')]/parent::*")
                            contacts = []
                            tels = []
                            for rb in rep_blocks:
                                rb_lines = [line.strip() for line in rb.text_content().split("\n") if line.strip() and "Représentant" not in line]
                                for l in rb_lines:
                                    if "Tél:" in l or "Mobile:" in l or re.search(r'\(\d{3}\)\s*\d{3}-\d{4}', l):
                                        tels.append(l)
                                    elif len(l) > 2 and len(l) < 50:
                                        contacts.append(l)
                            if contacts:
                                clean_contacts = [c for c in contacts if "[email" not in c]
                                proprietaire = ", ".join(list(dict.fromkeys(clean_contacts))[:3])
                            if tels:
                                telephone = " | ".join(list(dict.fromkeys(tels))[:2])

                            # Certifications
                            cert_blocks = f_tree.xpath("//*[contains(text(), 'Certifications')]/parent::*")
                            certs = []
                            for cb in cert_blocks:
                                c_lines = [line.strip() for line in cb.text_content().split("\n") if line.strip() and "Certification" not in line]
                                certs.extend(c_lines)
                            if certs:
                                certifications = ", ".join(list(dict.fromkeys(certs)))

                            # Produits / arrivages
                            prod_nodes = f_tree.xpath("//div[contains(@class, 'produit')]//h3 | //ul[contains(@class, 'produit')]//li | //div[contains(@class, 'arrivage')]//p")
                            for p in prod_nodes:
                                p_txt = p.text_content().strip()
                                if p_txt and len(p_txt) < 50:
                                    produits.append(p_txt)

                            # Site web
                            ext_links = f_tree.xpath("//a[starts-with(@href, 'http') and not(contains(@href, 'apmquebec.com')) and not(contains(@href, 'google.com')) and not(contains(@href, 'facebook.com')) and not(contains(@href, 'instagram.com')) and not(contains(@href, 'linkedin.com'))]/@href")
                            if ext_links:
                                website = ext_links[0]

                    except Exception as e_fiche:
                        pass

                if produits:
                    type_culture = f"Maraîcher ({', '.join(produits[:5])})"

                notes_parts = ["Source: APMQ (Association des producteurs maraîchers du Québec)"]
                if fiche_url:
                    notes_parts.append(f"Fiche APMQ: {fiche_url}")
                if lat and lng:
                    notes_parts.append(f"GPS: ({lat}, {lng})")
                if len(produits) > 5:
                    notes_parts.append(f"Autres cultures: {', '.join(produits[5:])}")

                rec = self.make_record(
                    nom=nom,
                    proprietaire=proprietaire,
                    region_province=f"{region}, Québec" if region else "Québec",
                    pays="Canada",
                    superficie="",
                    type_culture=type_culture,
                    courriel=courriel,
                    telephone=telephone,
                    site_web=website,
                    adresse=adresse,
                    ville=ville,
                    code_postal=code_postal,
                    certifications=certifications,
                    statut="prospect",
                    notes=" | ".join(notes_parts)
                )
                records.append(rec)
                if idx % 25 == 0 or idx == len(cards):
                    print(f"[apmquebec] Progression: {idx}/{len(cards)} producteurs extraits")

        except Exception as e:
            print(f"[apmquebec] Erreur: {e}")

        return records
