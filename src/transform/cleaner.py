import json
import requests
import pandas as pd

ML_API_URL = "http://localhost:5001/detect_json"

def truncate_text(text, max_words=100):
    """Tronque un texte à un nombre maximum de mots."""
    if not text:
        return ""
    words = str(text).split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + "..."
    return text

def get_ml_prediction(title, summary, is_satire):
    """Envoie le texte au modèle ML ou applique une règle métier stricte."""
    # Règle métier : On économise du temps de calcul pour le Gorafi
    if is_satire:
        return '{"label": "SATIRE", "score": 1.0}'
        
    text_to_analyze = f"{title}. {summary}"
    payload = {"text": text_to_analyze}
    
    try:
        response = requests.post(ML_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        # On retourne la réponse JSON sous forme de chaîne pour le stockage DuckDB
        return json.dumps(response.json())
        
    except requests.exceptions.RequestException as e:
        print(f"[WARNING] Erreur de connexion au modèle ML : {e}")
        return '{"error": "ML_UNAVAILABLE"}'

def clean_and_enrich(articles_list):
    """Pipeline de transformation des données via Pandas."""
    if not articles_list:
        print("[INFO] Aucun article fourni pour le nettoyage.")
        return pd.DataFrame()

    print("[INFO] Chargement des données dans Pandas...")
    df = pd.DataFrame(articles_list)

    print("[INFO] Standardisation des dates au format ISO...")
    # utc=True permet de gérer proprement les décalages horaires (+0200) présents dans les flux RSS
    for col in ['event_date', 'publication_date']:
        df[col] = pd.to_datetime(df[col], utc=True, errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')

    print("[INFO] Troncature des résumés à 100 mots maximum...")
    df['summary'] = df['summary'].apply(lambda x: truncate_text(x, 100))

    print("[INFO] Appel de l'API Machine Learning pour enrichissement...")
    # L'utilisation de apply() exécute la fonction ligne par ligne
    df['ml_prediction'] = df.apply(
        lambda row: get_ml_prediction(row['title'], row['summary'], row['is_satire']),
        axis=1
    )

    print("[INFO] Nettoyage et enrichissement terminés avec succès.")
    return df

if __name__ == "__main__":
    # Test unitaire rapide pour valider le comportement sans scraper internet
    print("[INFO] Démarrage du test de nettoyage...")
    sample_data = [{
        "source_name": "Le Monde",
        "title": "Baisse des taux directeurs",
        "summary": "La banque centrale annonce une réduction majeure pour stimuler la croissance. " * 10, # Texte long pour tester la troncature
        "event_date": "Thu, 18 Jun 2026 06:00:20 +0200",
        "publication_date": "Thu, 18 Jun 2026 06:00:20 +0200",
        "is_satire": False
    }]
    
    df_clean = clean_and_enrich(sample_data)
    print("\n[RÉSULTAT DU DATAFRAME]")
    print(df_clean.to_dict(orient="records")[0])