import json
import os
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

DATA_FILE = "annonces.json"

# Historique des annonces
existing_annonces = {}
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            existing_annonces = {item["id"]: item for item in data.get("annonces", [])}
    except Exception as e:
        print(f"Erreur de lecture de {DATA_FILE}: {e}")

def clean_price(text):
    if not text:
        return None
    # Extraction des chiffres uniquement
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None

results = []

print("Lancement du scraper...")

with sync_playwright() as p:
    # Utilisation d'un navigateur avec configuration réaliste
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        locale="fr-FR",
        ignore_https_errors=True
    )
    page = context.new_page()

    # Liste des sources à scruter à Angers (Budget max ~125 000 €)
    sources = [
        {
            "nom": "Ouest-France Immo",
            "url": "https://www.ouestfrance-immo.com/achetez/appartement/angers-49-49007/?prix_max=125000",
            "domain": "https://www.ouestfrance-immo.com"
        },
        {
            "nom": "Nestenn Angers",
            "url": "https://immobilier-angers.nestenn.com/achat-appartement-angers?prix_max=125000",
            "domain": "https://immobilier-angers.nestenn.com"
        },
        {
            "nom": "Nicole Joubert",
            "url": "https://www.nicolejoubert.fr/ventes",
            "domain": "https://www.nicolejoubert.fr"
        }
    ]

    for source in sources:
        print(f"Extraction en cours : {source['nom']}...")
        try:
            page.goto(source["url"], timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            # Recherche globale des balises contenant des liens d'annonces
            # Recherche de tous les liens hypertextes dans la page qui pointent vers des annonces
            links = page.query_selector_all("a[href]")
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    text = link.inner_text()
                    
                    if not href or not text:
                        continue

                    # Nettoyage et construction de l'URL absolue
                    full_url = href if href.startswith("http") else source["domain"] + href
                    
                    # Vérification si le bloc contient un prix (€) et concerne Angers/Appartement
                    if "€" in text and ("angers" in text.lower() or "appartement" in text.lower() or "studio" in text.lower() or "t1" in text.lower() or "t2" in text.lower()):
                        price = clean_price(text)
                        
                        # Filtrage sur la tranche de prix souhaitée (ex: entre 30 000 € et 130 000 €)
                        if price and 30000 <= price <= 130000:
                            lines = [l.strip() for l in text.split("\n") if l.strip()]
                            titre = lines[0] if lines else f"Appartement à Angers ({price:,} €)"
                            
                            results.append({
                                "id": full_url,
                                "titre": titre[:90],
                                "prix": price,
                                "url": full_url,
                                "description": text.replace("\n", " ")[:160] + "...",
                                "agence": source["nom"]
                            })
                except Exception as inner_err:
                    continue

        except Exception as err:
            print(f"Erreur sur {source['nom']}: {err}")

    browser.close()

# Traitement et déduplication des annonces
final_list = []
seen_ids = set()

for item in results:
    if item["id"] in seen_ids:
        continue
    seen_ids.add(item["id"])

    aid = item["id"]
    if aid in existing_annonces:
        item["is_new"] = False
        item["date_ajout"] = existing_annonces[aid].get("date_ajout", datetime.now().strftime("%Y-%m-%d"))
    else:
        item["is_new"] = True
        item["date_ajout"] = datetime.now().strftime("%Y-%m-%d")

    final_list.append(item)

# Tri par prix croissant
final_list.sort(key=lambda x: x["prix"])

# Sauvegarde dans annonces.json
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump({
        "last_updated": datetime.now().strftime("%d/%m/%Y à %H:%M"),
        "annonces": final_list
    }, f, ensure_ascii=False, indent=2)

print(f"Extraction terminée avec succès : {len(final_list)} vraies annonces trouvées.")
