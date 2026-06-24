import urllib.parse
import requests
from bs4 import BeautifulSoup
import duckdb

DB_PATH = "data/pipeline.db"

def scrape_afp_factuel(article_title):
    """
    Simule une recherche sur le site AFP Factuel en utilisant BeautifulSoup.
    """
    # 1. Préparation des mots-clés (on prend les 5 premiers mots du titre pour élargir la recherche)
    mots_cles = " ".join(article_title.split()[:5])
    query = urllib.parse.quote(mots_cles)
    
    # URL de recherche du site AFP Factuel
    url = f"https://factuel.afp.com/search/site/{query}"
    
    # On ajoute un User-Agent pour simuler un vrai navigateur et éviter d'être bloqué par le site
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        # Si la page n'existe pas ou bloque, on arrête proprement
        if response.status_code != 200:
            return "Recherche impossible (Bloqué ou site injoignable)"
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # L'AFP liste souvent ses résultats de recherche dans des balises <article> ou <div> avec des titres <h4>
        # Nous cherchons simplement la présence d'un titre de démenti dans le HTML renvoyé
        articles_trouves = soup.find_all('article')
        
        if articles_trouves:
            # S'il y a des résultats, on extrait le texte brut du premier article trouvé
            premier_resultat = articles_trouves[0].text.strip().replace('\n', ' ')
            # On tronque à 50 caractères pour que ça rentre proprement dans la base DuckDB
            return f"Trouvé AFP : {premier_resultat[:50]}..."
            
        return "Aucun démenti trouvé sur l'AFP"
        
    except Exception as e:
        print(f"[ERROR] Échec du scraping de l'AFP Factuel : {e}")
        return "Erreur de scraping"

def run_validation_batch():
    """Récupère les articles non vérifiés de DuckDB et lance le scraping."""
    print("[INFO] Démarrage du Batch de Validation (Web Scraping AFP)...")
    
    con = duckdb.connect(DB_PATH)
    
    try:
        # Sélection des articles non vérifiés et non satiriques
        unverified_articles = con.execute("""
            SELECT source_name, title 
            FROM articles 
            WHERE is_fact_checked = FALSE 
            AND is_satire = FALSE
        """).fetchall()

        if not unverified_articles:
            print("[INFO] Aucun nouvel article à vérifier pour le moment.")
            return

        print(f"[INFO] {len(unverified_articles)} articles en attente de vérification sur le site AFP.")

        # Vérification article par article, row est un tuple (source_name, title)
        for row in unverified_articles:
            source_name, title = row
            
            print(f"[PROCESS] Scraping AFP en cours pour le titre : '{title[:30]}...'")
            final_status = scrape_afp_factuel(title)
            
            # Mise à jour dans la base
            con.execute("""
                UPDATE articles 
                SET is_fact_checked = TRUE, 
                    final_status = ? 
                WHERE source_name = ? AND title = ?
            """, (final_status, source_name, title))

        print("[SUCCESS] Le Batch de Validation est terminé.")
        
    except Exception as e:
        print(f"[ERROR] Problème lors du batch de validation : {e}")
    finally:
        con.close()

if __name__ == "__main__":
    # Exécution directe pour tester le web scraping
    run_validation_batch()
    
    # Affichage du résultat en base
    print("\n[INFO] Résultat dans la base de données :")
    con = duckdb.connect(DB_PATH)
    result = con.execute("SELECT title, is_fact_checked, final_status FROM articles").df()
    print(result.to_string())
    con.close()