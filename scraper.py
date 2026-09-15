import json
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

DATA_FILE = "annonces.json"

# 1. Charger les annonces existantes
existing_annonces = {}
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            existing_annonces = {item["id"]: item for item in data.get("annonces", [])}
    except Exception as e:
        print(f"Erreur lecture annonces.json: {e}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
}

annonces_trouvees = []

def clean_price(price_text):
    """Extrait le prix numérique d'une chaîne de texte."""
    if not price_text:
        return None
    raw = re.sub(r"[^\d]", "", price_text)
    return int(raw) if raw else None


# ==============================================================================
# SCRAPERS DÉDIÉS AUX SITES D'AGENCES DE L'ANJOU / ANGERS
# ==============================================================================

# --- Agence 1 : Nicole Joubert ---
def scrape_nicole_joubert():
    results = []
    url = "https://www.nicolejoubert.fr/achat/appartement/angers/prix-max-125000"
    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select(".card-annonce, .annonce-item, article")
            for card in cards:
                title = card.select_one(".titre, h2, h3")
                price_el = card.select_one(".price, .prix")
                link_el = card.select_one("a[href]")
                
                if title and price_el and link_el:
                    prix = clean_price(price_el.text)
                    if prix and prix <= 125000:
                        link = link_el["href"]
                        if not link.startswith("http"):
                            link = "https://www.nicolejoubert.fr" + link
                        results.append({
                            "id": link,
                            "titre": title.text.strip(),
                            "prix": prix,
                            "url": link,
                            "description": "Appartement à Angers via Nicole Joubert.",
                            "agence": "Nicole Joubert Angers"
                        })
    except Exception as e:
        print(f"Erreur Nicole Joubert: {e}")
    return results


# --- Agence 2 : L'Adresse Angers ---
def scrape_ladresse():
    results = []
    url = "https://www.ladresse.fr/achat/appartement/angers?prix_max=125000"
    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select(".card-property, .product-item")
            for card in cards:
                title = card.select_one(".title, .card-title")
                price_el = card.select_one(".price")
                link_el = card.select_one("a[href]")
                if title and price_el and link_el:
                    prix = clean_price(price_el.text)
                    if prix and prix <= 125000:
                        link = link_el["href"]
                        if not link.startswith("http"):
                            link = "https://www.ladresse.fr" + link
                        results.append({
                            "id": link,
                            "titre": title.text.strip(),
                            "prix": prix,
                            "url": link,
                            "description": "Exclusivité / Annonce L'Adresse Angers.",
                            "agence": "L'Adresse Angers"
                        })
    except Exception as e:
        print(f"Erreur L'Adresse: {e}")
    return results


# --- Agence 3 : Alain Rousseau Immobilier ---
def scrape_alain_rousseau():
    results = []
    url = "https://www.alain-rousseau.com/achat/appartement/angers?prix_max=125000"
    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select(".item-annonce, .card")
            for card in cards:
                title = card.select_one(".titre, h3")
                price_el = card.select_one(".prix")
                link_el = card.select_one("a[href]")
                if title and price_el and link_el:
                    prix = clean_price(price_el.text)
                    if prix and prix <= 125000:
                        link = link_el["href"]
                        if not link.startswith("http"):
                            link = "https://www.alain-rousseau.com" + link
                        results.append({
                            "id": link,
                            "titre": title.text.strip(),
                            "prix": prix,
                            "url": link,
                            "description": "Annonce directe Agence Alain Rousseau Angers.",
                            "agence": "Alain Rousseau Immobilier"
                        })
    except Exception as e:
        print(f"Erreur Alain Rousseau: {e}")
    return results


# --- Agrégateur Portail (en complément des agences directes) ---
def scrape_ouestfrance_immo():
    results = []
    url = "https://www.ouestfrance-immo.com/achetez/appartement/angers-49-49007/?prix_max=125000"
    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select("li.annCard, article.annCard, .annAnnonce")
            for card in cards:
                title_el = card.select_one(".annTitre, .annType, h2")
                price_el = card.select_one(".annPrix, .prix")
                link_el = card.select_one("a[href]")
                agence_el = card.select_one(".annAgence, .proNom")
                desc_el = card.select_one(".annTexte, .annDesc")

                if price_el and link_el:
                    prix = clean_price(price_el.text)
                    if prix and prix <= 125000:
                        link = link_el["href"]
                        if not link.startswith("http"):
                            link = "https://www.ouestfrance-immo.com" + link
                        titre = title_el.text.strip() if title_el else "Appartement Angers"
                        agence = agence_el.text.strip() if agence_el else "Agence Angers"
                        desc = desc_el.text.strip() if desc_el else "Appartement à vendre sur Angers."

                        results.append({
                            "id": link,
                            "titre": titre,
                            "prix": prix,
                            "url": link,
                            "description": desc[:160] + "..." if len(desc) > 160 else desc,
                            "agence": agence
                        })
    except Exception as e:
        print(f"Erreur OuestFrance Immo: {e}")
    return results


# ==============================================================================
# EXECUTION & LOGIQUE DE FUSION DES SOURCES
# ==============================================================================

print("Lancement de la collecte multi-agences...")
annonces_trouvees.extend(scrape_nicole_joubert())
annonces_trouvees.extend(scrape_ladresse())
annonces_trouvees.extend(scrape_alain_rousseau())
annonces_trouvees.extend(scrape_ouestfrance_immo())

# Déduplication par URL / ID
unique_annonces = {}
for item in annonces_trouvees:
    if item["id"] not in unique_annonces:
        unique_annonces[item["id"]] = item

# Marquage des "Nouveautés"
final_list = []
for aid, item in unique_annonces.items():
    if aid in existing_annonces:
        # Si l'annonce existait déjà, on ne la ré-affiche pas comme "Nouveau"
        item["is_new"] = False
    else:
        # Nouvelle annonce trouvée lors de ce scan !
        item["is_new"] = True
    
    item["date_ajout"] = existing_annonces.get(aid, {}).get("date_ajout", datetime.now().strftime("%Y-%m-%d"))
    final_list.append(item)

# Sauvegarde dans le fichier JSON
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump({
        "last_updated": datetime.now().strftime("%d/%m/%Y à %H:%M"),
        "annonces": final_list
    }, f, ensure_ascii=False, indent=2)

print(f"Extraction terminée ! Total : {len(final_list)} annonces (budget <= 125 000 €).")
