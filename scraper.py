import json
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

DATA_FILE = "annonces.json"

# Charger les annonces existantes pour la détection "Nouveau"
existing_annonces = {}
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            existing_annonces = {item["id"]: item for item in data.get("annonces", [])}
    except Exception as e:
        print(f"Erreur lecture annonces.json: {e}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
}

annonces_trouvees = []

# --- FONCTION DE SCRAPING EXEMPLE : Cibles Agences Angers ---
def scrape_agences_angers():
    results = []
    
    # Exemple avec une recherche type sur une agence locale / portail régional
    # On cherche des appartements à Angers avec prix max 125000
    urls = [
        # Remplacez / ajoutez ici les URLs de recherche directes des agences d'Angers
        # Ex: "https://www.exemple-agence-angers.fr/achat/appartement/angers/max-125000"
    ]
    
    for url in urls:
        try:
            req = requests.get(url, headers=headers, timeout=15)
            if req.status_code == 200:
                soup = BeautifulSoup(req.text, "html.parser")
                
                # Exemple de parsing générique d'annonces
                cards = soup.select(".annonce-item, .card-immo, article.annonce")
                for card in cards:
                    title_elem = card.select_one(".title, .titre, h2, h3")
                    price_elem = card.select_one(".price, .prix")
                    link_elem = card.select_one("a[href]")
                    desc_elem = card.select_one(".description, .text, .details")
                    
                    if title_elem and price_elem and link_elem:
                        # Extraire le prix numérique
                        prix_numbers = re.sub(r"[^\d]", "", price_elem.text)
                        if not prix_numbers:
                            continue
                        prix = int(prix_numbers)
                        
                        # Filtre strict < 125 000 €
                        if prix <= 125000:
                            link = link_elem["href"]
                            if not link.startswith("http"):
                                link = "https://www.agences-angers.fr" + link
                                
                            results.append({
                                "id": link,
                                "titre": title_elem.text.strip(),
                                "prix": prix,
                                "url": link,
                                "description": desc_elem.text.strip() if desc_elem else "Appartement à vendre sur Angers.",
                                "agence": "Agence Angers",
                                "date_ajout": datetime.now().strftime("%Y-%m-%d")
                            })
        except Exception as e:
            print(f"Erreur sur {url}: {e}")
            
    return results

# Exécution
scraped = scrape_agences_angers()

# Traitement des nouveautés
final_list = []
for item in scraped:
    item_id = item["id"]
    if item_id in existing_annonces:
        item["is_new"] = existing_annonces[item_id].get("is_new", False)
    else:
        item["is_new"] = True
    final_list.append(item)

# Mise à jour du JSON
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump({
        "last_updated": datetime.now().strftime("%d/%m/%Y à %H:%M"),
        "annonces": final_list
    }, f, ensure_ascii=False, indent=2)

print(f"Extraction terminée : {len(final_list)} annonces enregistrées.")
