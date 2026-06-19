import duckdb
import pandas as pd
import os

# Chemin vers la base de données (le dossier 'data' doit exister) 
DB_PATH = "data/pipeline.db"

def init_db():
    """Initialise la base de données et crée la table si elle n'existe pas."""
    # S'assure que le dossier data/ existe
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    con = duckdb.connect(DB_PATH)
    
    # Création de la table avec une contrainte UNIQUE sur le titre et la source
    # pour éviter d'insérer les mêmes articles toutes les 15 minutes.
    con.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            source_name VARCHAR,
            title VARCHAR,
            summary VARCHAR,
            event_date TIMESTAMP,
            publication_date TIMESTAMP,
            is_satire BOOLEAN,
            ml_prediction VARCHAR,
            is_fact_checked BOOLEAN DEFAULT FALSE,
            final_status VARCHAR DEFAULT NULL,
            UNIQUE(source_name, title)
        )
    """)
    con.close()
    print("[INFO] Base de données DuckDB initialisée avec succès.")

def save_articles(df):
    """Sauvegarde le DataFrame Pandas dans DuckDB en ignorant les doublons."""
    if df is None or df.empty:
        print("[INFO] Aucun article à sauvegarder.")
        return

    init_db()
    con = duckdb.connect(DB_PATH)
    
    try:
        # DuckDB peut lire directement la variable 'df' depuis l'environnement Python !
        # On ajoute nos deux colonnes par défaut pour le futur batch de 6 heures.
        con.execute("""
            INSERT INTO articles (
                source_name, title, summary, event_date, publication_date, is_satire, ml_prediction
            )
            SELECT 
                source_name, title, summary, CAST(event_date AS TIMESTAMP), CAST(publication_date AS TIMESTAMP), is_satire, ml_prediction
            FROM df
            ON CONFLICT (source_name, title) DO NOTHING
        """)
        
        # Petit comptage pour le log
        count = con.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        print(f"[SUCCESS] Données insérées. La base contient maintenant {count} articles uniques.")
        
    except Exception as e:
        print(f"[ERROR] Échec lors de la sauvegarde dans DuckDB : {e}")
    finally:
        con.close()

if __name__ == "__main__":
    # Test unitaire de la base de données
    print("[INFO] Démarrage du test de chargement DuckDB...")
    
    # On simule le DataFrame qui sort de ton cleaner.py
    sample_data = pd.DataFrame([{
        "source_name": "Le Monde",
        "title": "Baisse des taux directeurs",
        "summary": "La banque centrale annonce une réduction majeure...",
        "event_date": "2026-06-18 04:00:20",
        "publication_date": "2026-06-18 04:00:20",
        "is_satire": False,
        "ml_prediction": '{"result": "Fake"}'
    }])
    
    # On insère deux fois pour tester l'anti-doublon
    print("\n--- Première insertion ---")
    save_articles(sample_data)
    
    print("\n--- Deuxième insertion (ne devrait rien ajouter) ---")
    save_articles(sample_data)