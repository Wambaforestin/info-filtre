import schedule
import time
from datetime import datetime

# Importation de nos 3 modules métiers
from extract.rss_scraper import scrape_rss_feeds
from transform.cleaner import clean_and_enrich
from load.duckdb_client import save_articles
from validation.fact_checker import run_validation_batch

def job_realtime():
    """Tâche exécutée toutes les 15 minutes : Extraction -> Nettoyage -> Stockage"""
    print(f"[TEMPS RÉEL] Démarrage du cycle : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Extraction
    raw_data = scrape_rss_feeds()
    
    # 2. Transformation & ML
    clean_df = clean_and_enrich(raw_data)
    
    # 3. Sauvegarde
    save_articles(clean_df)
    
    print("[TEMPS RÉEL] Cycle terminé. Prochain run dans 15 minutes.\n")

def job_batch():
    """Tâche exécutée toutes les 6 heures : Fact-Checking AFP"""
    print(f"[BATCH 6H] Démarrage de la validation : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Lancement du script de validation
    run_validation_batch()
    
    print("[BATCH 6H] Cycle de Validation terminé. Prochain run dans 6 heures.\n")

if __name__ == "__main__":
    print("Initialisation de l'orchestrateur InfoFiltre...")
    
    # Planification des tâches selon le cahier des charges
    schedule.every(15).minutes.do(job_realtime)
    schedule.every(6).hours.do(job_batch)
    
    # Pour le MVP : on force une première exécution immédiate au démarrage
    print("\n Lancement de la première passe initiale...")
    job_realtime()
    job_batch()
    
    print("\n L'orchestrateur est maintenant en attente. Ne fermez pas ce terminal.")
    
    # Boucle infinie qui maintient le programme en vie
    try:
        while True:
            schedule.run_pending()
            time.sleep(1) # Pause d'une seconde pour ne pas surcharger le processeur
    except KeyboardInterrupt:
        print("\nArrêt manuel de l'orchestrateur.")