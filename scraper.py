import json
import os
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

DATA_FILE = "annonces.json"

# Récupération de l'historique
existing_annonces = {}
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            existing_annonces = {item["id"]: item for item in data.get("annonces", [])}
    except Exception as e:
        print(f"Erreur lecture {DATA_FILE}: {e}")

def clean_price(text):
    if not text:
        return None
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None

results = []

print("Démarrage du robot de scraping...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        locale="fr-FR",
        ignore_https_errors=True
    )
    page = context.new_page()

    # Domaines et cibles exactes
    sources = [
        {
            "nom": "L'Adresse Immobilier",
            "url": "https://www.ladresse.com/achat/appartement/angers-49000?prix_max=125000",
            "domain": "https://www.ladresse.com"
        },
        {
            "nom": "Ouest-France Immo",
            "url": "https://www.ouestfrance-immo.com/achetez/appartement/angers-49-49007/?prix_max=125000",
            "domain": "https://www.ouestfrance-immo.com"
        },
        {
            "nom": "Nicole Joubert",
            "url": "https://www.nicolejoubert.fr/vente/1",
            "domain": "https://www.nicolejoubert.fr"
        }
    ]

    for source in sources:
        print(f"Visite : {source['nom']} ({source['url']})...")
        try:
            page.goto(source["url"], timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            # Recherche de toutes les ancres avec des liens réels
            links = page.query_selector_all("a[href]")
            for link in links:
                try:
                    href = link.get_attribute("href")
                    text = link.inner_text()

                    if not href or not text or len(text.strip()) < 10:
                        continue

                    # Construction de l'URL absolue correcte
                    if href.startswith("http"):
                        full_url = href
                    elif href.startswith("/"):
                        full_url = source["domain"] + href
                    else:
                        full_url = source["domain"] + "/" + href

                    # Filtrage sur les critères immo Angers
                    if "€" in text:
                        price = clean_price(text)
                        if price and 25000 <= price <= 130000:
                            lines = [l.strip() for l in text.split("\n") if l.strip()]
                            titre = lines[0] if lines else f"Appartement Angers ({price:,} €)"
                            
                            results.append({
                                "id": full_url,
                                "titre": titre[:80],
                                "prix": price,
                                "url": full_url,
                                "description": text.replace("\n", " ")[:150] + "...",
                                "agence": source["nom"],
                                "is_fictive": False
                            })
                except Exception:
                    continue
        except Exception as e:
            print(f"Erreur lors du scraping de {source['nom']}: {e}")

    browser.close()

# Si le scraping direct échoue, injection d'un fallback avec de VRAIS liens de recherche réels à Angers
if not results:
    print("Activation du fallback (liens de recherche réels et fonctionnels).")
    results = [
        {
            "id": "https://www.ladresse.com/achat/appartement/angers-49000",
            "titre": "Annonces Appartements L'Adresse Angers",
            "prix": 115000,
            "url": "https://www.ladresse.com/achat/appartement/angers-49000",
            "description": "Lien direct vers la liste mise à jour des appartements à vendre à Angers sur L'Adresse.",
            "agence": "L'Adresse Immobilier",
            "is_fictive": True
        },
        {
            "id": "https://www.nicolejoubert.fr/ventes",
            "titre": "Biens à vendre Nicole Joubert Angers",
            "prix": 98000,
            "url": "https://www.nicolejoubert.fr/ventes",
            "description": "Lien direct vers le catalogue de l'agence locale Nicole Joubert Angers.",
            "agence": "Nicole Joubert",
            "is_fictive": True
        },
        {
            "id": "https://www.ouestfrance-immo.com/achetez/appartement/angers-49-49007/",
            "titre": "Annonces Ouest-France Immo Angers",
            "prix": 120000,
            "url": "https://www.ouestfrance-immo.com/achetez/appartement/angers-49-49007/",
            "description": "Portail régional de référence pour les offres sur Angers et l'Anjou.",
            "agence": "Ouest-France Immo",
            "is_fictive": True
        }
    ]

# Déduplication et calcul de l'ancienneté
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

final_list.sort(key=lambda x: x["prix"])

# Sauvegarde
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump({
        "last_updated": datetime.now().strftime("%d/%m/%Y à %H:%M"),
        "annonces": final_list
    }, f, ensure_ascii=False, indent=2)

print(f"Operation terminee avec {len(final_list)} annonces.")
