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

print("=== DÉMARRAGE DU SCRAPING REEL ===")

with sync_playwright() as p:
    # Lancement Chromium avec arguments anti-détection bot
    browser = p.chromium.launch(
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox'
        ]
    )
    
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        locale="fr-FR",
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True
    )
    
    page = context.new_page()

    # Cibles avec recherche ciblée sur Angers
    sources = [
        {
            "nom": "Ouest-France Immo",
            "url": "https://www.ouestfrance-immo.com/achetez/appartement/angers-49-49007/?prix_max=125000",
            "domain": "https://www.ouestfrance-immo.com",
            "card_selector": "article, .annCard, .item-annonce, li[class*='annonce']"
        },
        {
            "nom": "L'Adresse Immobilier",
            "url": "https://www.ladresse.com/achat/appartement/angers-49000?prix_max=125000",
            "domain": "https://www.ladresse.com",
            "card_selector": ".card, .annonce, article, div[class*='product']"
        }
    ]

    for source in sources:
        print(f"--> Connexion à {source['nom']}...")
        try:
            # Navigation avec timeout plus long
            response = page.goto(source["url"], timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

            # Vérification du code HTTP
            status = response.status if response else "Inconnu"
            print(f"Status HTTP {source['nom']}: {status}")

            cards = page.query_selector_all(source["card_selector"])
            print(f"Éléments détectés sur {source['nom']}: {len(cards)}")

            for card in cards:
                try:
                    text = card.inner_text()
                    if not text or "€" not in text:
                        continue

                    price = clean_price(text)
                    if price and 30000 <= price <= 130000:
                        link_el = card.query_selector("a[href]")
                        if link_el:
                            href = link_el.get_attribute("href")
                            if not href or href == "#":
                                continue

                            full_url = href if href.startswith("http") else source["domain"] + (href if href.startswith("/") else "/" + href)
                            
                            lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 3]
                            titre = lines[0] if lines else f"Appartement à Angers ({price:,} €)"

                            results.append({
                                "id": full_url,
                                "titre": titre[:90],
                                "prix": price,
                                "url": full_url,
                                "description": text.replace("\n", " ")[:150] + "...",
                                "agence": source["nom"],
                                "is_fictive": False
                            })
                except Exception as card_err:
                    continue

        except Exception as err:
            print(f"Erreur sur {source['nom']}: {err}")

    browser.close()

print(f"Extraction terminée : {len(results)} vraies annonces extraites par Playwright.")

# Déduplication
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

# Sauvegarde dans annonces.json
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump({
        "last_updated": datetime.now().strftime("%d/%m/%Y à %H:%M"),
        "annonces": final_list
    }, f, ensure_ascii=False, indent=2)

print(f"Mise à jour de {DATA_FILE} effectuée avec succès.")
