import re
from typing import List, Dict, Any

def normalize_key(name: str, city: str = "") -> str:
    n = name.lower()
    for drop in ["inc.", "inc", "ltee", "ltée", "ltd.", "ltd", "senc", "s.e.n.c.", "ferme", "les", "la", "le", "de", "des", "du"]:
        n = re.sub(rf'\b{drop}\b', '', n)
    n = re.sub(r'[^a-z0-9]', '', n)
    c = re.sub(r'[^a-z0-9]', '', city.lower())
    return f"{n}_{c}"

def normalize_phone(phone: str) -> str:
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits if len(digits) == 10 else ""

def merge_records(primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(primary)
    
    # Fill in empty fields
    for field in [
        "Propriétaire", "Région / Province", "Pays", "Superficie (ha ou m²)",
        "Type de culture", "Courriel", "Téléphone", "Site Web",
        "Adresse", "Ville", "Code Postal"
    ]:
        if not merged.get(field) and secondary.get(field):
            merged[field] = secondary[field]

    # Combine certifications
    certs = set()
    for c in [primary.get("Certifications", ""), secondary.get("Certifications", "")]:
        if c:
            for item in c.split(","):
                if item.strip():
                    certs.add(item.strip())
    if certs:
        merged["Certifications"] = ", ".join(sorted(certs))

    # Combine notes
    notes_p = primary.get("Notes", "")
    notes_s = secondary.get("Notes", "")
    if notes_s and notes_s not in notes_p:
        merged["Notes"] = f"{notes_p} | {notes_s}".strip(" |")

    return merged

def consolidate_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged_by_key: Dict[str, Dict[str, Any]] = {}
    phone_to_key: Dict[str, str] = {}
    email_to_key: Dict[str, str] = {}

    for rec in records:
        name = rec.get("Nom de la ferme", "")
        city = rec.get("Ville", "")
        phone = normalize_phone(rec.get("Téléphone", ""))
        email = rec.get("Courriel", "").strip().lower()

        # Check existing match
        match_key = None
        if phone and phone in phone_to_key:
            match_key = phone_to_key[phone]
        elif email and email in email_to_key:
            match_key = email_to_key[email]
        else:
            cand_key = normalize_key(name, city)
            if cand_key in merged_by_key:
                match_key = cand_key

        if match_key:
            existing = merged_by_key[match_key]
            merged_by_key[match_key] = merge_records(existing, rec)
        else:
            new_key = normalize_key(name, city) or f"id_{len(merged_by_key)}"
            merged_by_key[new_key] = rec
            if phone:
                phone_to_key[phone] = new_key
            if email:
                email_to_key[email] = new_key

    return list(merged_by_key.values())
