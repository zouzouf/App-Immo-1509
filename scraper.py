import json
import os
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

DATA_FILE = "annonces.json"

# Charger les annonces existantes pour conserver le statut 'is_new'
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
    # Ne garder que les chiffres
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None

annonces_trouvees = []

# Liste des cibles d'agences / portails
CIBLES = [
    {
        "nom": "Nicole Joubert",
        "url": "https://www.nicolejoubert.fr/achat/appartement/angers?prix_max=125000",
        "domain": "https://www.nicolejoubert.fr"
    },
    {
        "nom": "L'Adresse Angers",
        "url": "https://www.ladresse.fr/achat/appartement/angers?prix_max=125000",
        "domain": "https://www.ladresse.fr"
    },
    {
        "nom": "Ouest-France Immo Angers",
        "url": "https://www.ouestfrance-immo.com/achetez/appartement/angers-49-49007/?prix_max=125000",
        "domain": "https://www.ouestfrance-immo.com"
    }
]

def run_scraper():
    results = []
    
    with sync_playwright() as p:
        # Lancement d'un navigateur Chromium avec un User-Agent réaliste
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="fr-FR"
        )
        page = context.new_page()

        for cible in CIBLES:
            print(f"Scraping en cours : {cible['nom']}...")
            try:
                # Chargement de la page et attente de l'exécution du JavaScript (max 20s par site)
                page.goto(cible["url"], timeout=20000, wait_until="networkidle")
                page.wait_for_timeout(3000) # Attente de rendu complémentaire

                # Extraction de tous les liens de la page contenant des indices d'annonces
                links = page.query_selector_all("a[href]")
                
                for link in links:
                    href = link.get_attribute("href")
                    if not href:
                        continue

                    # Construction de l'URL absolue
                    if not href.startswith("http"):
                        full_url = cible["domain"] + href
                    else:
                        full_url = href

                    # Récupération du texte englobant le lien (ou du parent)
                    parent = link.evaluate_handle("node => node.closest('article, li, div.card, div.annonce, div.item') or node")
                    text_content = parent.inner_text() if parent else link.inner_text()

                    # Vérification des mots-clés du prix et filtrage
                    if "€" in text_content:
                        prix = clean_price(text_content)
                        if prix and 20000 <= prix <= 125000:
                            # Titre propre
                            lines = [line.strip() for line in text_content.split("\n") if line.strip()]
                            titre = lines[0] if lines else f"Appartement Angers ({cible['nom']})"
                            if len(titre) > 80:
                                titre = f"Appartement Angers - {prix:,} €".replace(",", " ")

                            results.append({
                                "id": full_url,
                                "titre": titre,
                                "prix": prix,
                                "url": full_url,
                                "description": text_content.replace("\n", " ")[:180] + "...",
                                "agence": cible["nom"]
                            })
            except Exception as e:
                print(f"Erreur lors de la visite de {cible['nom']}: {e}")

        browser.close()
    return results

# Exécution de la collecte Playwright
annonces_trouvees = run_scraper()

# Déduplication par ID / URL
unique_annonces = {}
for item in annonces_trouvees:
    if item["id"] not in unique_annonces:
        unique_annonces[item["id"]] = item

# Traitement du statut "Nouveau"
final_annonces = []
for aid, item in unique_annonces.items():
    if aid in existing_annonces:
        item["is_new"] = False
        item["date_ajout"] = existing_annonces[aid].get("date_ajout", datetime.now().strftime("%Y-%m-%d"))
    else:
        item["is_new"] = True
        item["date_ajout"] = datetime.now().strftime("%Y-%m-%d")
        
    final_annonces.append(item)

# Tri par prix croissant
final_annonces.sort(key=lambda x: x["prix"])

# Sauvegarde dans le fichier JSON
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump({
        "last_updated": datetime.now().strftime("%d/%m/%Y à %H:%M"),
        "annonces": final_annonces
    }, f, ensure_ascii=False, indent=2)

print(f"Extraction Playwright réussie ! Total : {len(final_annonces)} annonces enregistrées.")
