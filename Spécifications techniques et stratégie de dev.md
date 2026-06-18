# Spécifications techniques et stratégie de dev (ETL) (rendu: 19/06/2026)

Le processus de développement du projet `info-filtre` est incrémental ; pour la première phase, il est conçu en mode "MVP selon les règles du 80-20" : je priorise ce qui apporte le plus de valeur rapidement, tout en posant des fondations solides.

## 1. Analyse des besoins des utilisateurs

### Sources de Données

- Le Monde (Généraliste/International) : https://www.lemonde.fr/
- Les Échos (Économique/Financier) : https://www.lesechos.fr/
- Fact Check AFP (Vérité/Vérification) : https://factcheck.afp.com/
- Le Gorafi (Bruit/Satire) : https://www.legorafi.fr/

### Les besoins des utilisateurs

L'objectif est d'alimenter un système d'aide à la décision pour anticiper l'évolution des marchés financiers. Le besoin strict est de fournir un flux d'actualités structuré, en temps réel, capable d'isoler la vérité des fake news. Le système doit ingérer la donnée en continu, tout en étant capable de recalculer toute la fiabilité de l'historique toutes les 6 heures pour.

## 2. Conception du pipeline de données

### Découverte (Ingestion)

`Méthode` : Web Scraping ciblé sur les pages d'accueil.
`Format d'origine` : Code source HTML brut.
`Fréquence de mise à jour` : Faire un scraping régulier toutes les 5 à 15 minutes pour simuler le flux "temps réel" sans surcharger les serveurs sources.

### Structuration (Mapping)

`Mapping` : Identification des sélecteurs (CSS/XPath) spécifiques à chaque site pour isoler les 4 champs cibles.

**Types de données requis (Schéma Cible):**

- `title` : Chaîne de caractères (String)
- `summary` : Chaîne de caractères courte (String)
- `event_date` : Date et Heure (Datetime)
- `publication_date` : Date et Heure (Datetime)

### Nettoyage (Transformations)

- `Transformations` : Suppression de toutes les balises HTML, scripts et publicités pour ne conserver que le texte brut du titre et du résumé.
- `Formatage des dates (Standardisation)` : Conversion de tous les formats temporels disparates (ex: "il y a 2h", "18/06/2026") vers le format strict demandé : YYYY-MM-DD HH:MM:SS (ex : 2026-02-11 19:00:00).
- `Troncature` : je vais potentiellement tronquer le champ summary à une limite stricte de mots (ex: 30 à 50 mots maximum) si la source fournit un texte trop long.

### Enrichissement (Temps Réel)

- `Détection ML en temps réel` : Concaténation du titre et du résumé, et envoi via requête HTTP (POST) au [module local de détection](https://github.com/josumsc/fake-news-detector).
- `Ajout du score` : Récupération de la probabilité (Fake/Real) et ajout dans la colonne ml_prediction
- `Stockage initial` : Écriture immédiate de la donnée enrichie dans la base DuckDB pour qu'elle soit consultable sans délai par les utilisateurs.

### Validation et Publication (Retraitement Batch - Toutes les 6h)

- `Extraction de l'historique` : Requête sur la base DuckDB pour récupérer toutes les actualités ingérées au cours des dernières heures.
- `Croisement Fact-Check` : Interrogation de la Google Fact Check Tools API (qui inclut l'AFP Factuel) à partir des titres de nos articles pour vérifier si un démenti officiel a été publié entre-temps.
- `Mise à jour et Certification (Match)` : * Si une correspondance est trouvée : le pipeline met à jour la ligne dans DuckDB (UPDATE), écrase la prédiction ML, et applique un tag définitif "Vrai" ou "Faux - Certifié AFP".
- `Si aucune correspondance n'est trouvée`  : le score ML initial est conservé.
  
**Publication** : La table DuckDB consolidée est exposée et prête à être connectée à l'outil de visualisation ou d'analyse des analystes financiers.

### image de l'architecture du pipeline

[architecture](images/archi-info-filtre.png)
