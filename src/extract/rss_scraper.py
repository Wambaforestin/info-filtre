import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def load_sources(config_path="config/sources.json"):
    """Charge le fichier de configuration JSON."""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)["news_sources"]

def scrape_rss_feeds():
    """Parcourt les sources, extrait les flux RSS et gère les pannes."""
    sources = load_sources()
    all_articles = []

    for source in sources:
        print(f"Extraction en cours pour : {source['name']}...")
        
        try:
            # Le timeout=10 est crucial : si le site est lent, on ne bloque pas le pipeline
            response = requests.get(source['url'], timeout=10)
            response.raise_for_status() # Lève une erreur si le statut n'est pas 200 (ex: 404)
            
            # Parsing du XML
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            for item in items:
                # Sécurisation au cas où une balise serait manquante
                title = item.title.text if item.title else ""
                summary = item.description.text if item.description else ""
                pub_date = item.pubDate.text if item.pubDate else ""
                
                all_articles.append({
                    "source_name": source['name'],
                    "title": title,
                    "summary": summary,
                    "event_date": pub_date,       # Date brute du RSS
                    "publication_date": pub_date, # On garde la même pour le moment
                    "is_satire": source['is_satire'] # ce champ est utilisé pour voir si le modèle vérifie ou pas
                })
            
            print(f"{len(items)} articles récupérés depuis {source['name']}.")
            
        except Exception as e:
            # STRATÉGIE MVP : En cas de panne, on affiche l'erreur et on passe au suivant
            print(f"Échec pour {source['name']} : {e}. On ignore et on continue.")
            continue

    return all_articles

# Petit bloc pour tester ce script tout seul
if __name__ == "__main__":
    print("Démarrage du test d'extraction...")
    articles = scrape_rss_feeds()
    print(f"\nTotal d'articles extraits : {len(articles)}")
    if articles:
        print("\nExemple du premier article brut :")
        print(json.dumps(articles[0], indent=2, ensure_ascii=False))