import json
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Fichier où seront stockées les annonces
DATA_FILE = "annonces.json"

# Charger les annonces existantes pour détecter les "Nouvelles"
existing_annonces = {}
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Indexer par URL
            existing_annonces = {item["url"]: item for item in data.get("annonces", [])}
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier existant: {e}")

all_annonces = []

# Exemple de fonction de scraping (Exemple indicatif à adapter par agence)
def scrape_exemple():
    results = []
    # Exemple d'URL (à remplacer par les vraies URLs de recherche d'agences à Angers)
    url = "https://example.com/immobilier-angers-appartement-125000"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Exemple fictif d'extraction d'éléments HTML
            for item in soup.select(".annonce-card"):
                titre = item.select_one(".titre")
                prix_elem = item.select_one(".prix")
                link_elem = item.select_one("a")
                
                if titre and prix_elem and link_elem:
                    prix_text = prix_elem.text.replace(" ", "").replace("€", "")
                    try:
                        prix = int(prix_text)
                    except ValueError:
                        continue
                        
                    # Filtrer budget < 125 000 €
                    if prix <= 125000:
                        link = link_elem["href"]
                        if not link.startswith("http"):
                            link = "https://example.com" + link
                            
                        results.append({
                            "id": link,
                            "titre": titre.text.strip(),
                            "prix": prix,
                            "url": link,
                            "description": "Appartement situé à Angers...",
                            "agence": "Agence Exemple",
                            "date_ajout": datetime.now().strftime("%Y-%m-%d")
                        })
    except Exception as e:
        print(f"Erreur lors du scraping de l'agence: {e}")
        
    return results

# Exécuter les fonctions de scraping
scraped_data = scrape_exemple()

# Fusionner et marquer les "Nouvelles"
final_annonces = []
for item in scraped_data:
    url = item["url"]
    if url in existing_annonces:
        # Garder le statut 'is_new' de la version existante ou le passer à False si daté
        is_new = existing_annonces[url].get("is_new", False)
        item["is_new"] = is_new
    else:
        # Nouvelle annonce détectée aujourd'hui !
        item["is_new"] = True
        
    final_annonces.append(item)

# Sauvegarder dans le fichier JSON
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump({
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "annonces": final_annonces
    }, f, ensure_ascii=False, indent=2)

print(f"Extraction terminée. {len(final_annonces)} annonces enregistrées.")
