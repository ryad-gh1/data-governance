import streamlit as st
import requests
import pandas as pd
from requests.auth import HTTPBasicAuth

# 🔧 Configuration Atlas
ATLAS_BASE_URL = "http://localhost:21000/api/atlas/v2"
USERNAME = "admin"
PASSWORD = "admin"

# 📥 Obtenir toutes les entités postgres_table
def get_all_postgres_tables():
    url = f"{ATLAS_BASE_URL}/search/basic"
    payload = {
        "typeName": "postgres_table",
        "excludeDeletedEntities": True,
        "limit": 100
    }
    response = requests.post(url, json=payload, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    if response.status_code == 200:
        return response.json().get("entities", [])
    else:
        st.error(f"Erreur Atlas : {response.status_code}")
        return []

# 📄 Obtenir détails d'une table par GUID
def get_entity_with_classification(guid):
    url = f"{ATLAS_BASE_URL}/entity/guid/{guid}"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    if response.status_code == 200:
        return response.json().get("entity", {})
    else:
        return None

# 🧠 Extraire informations utiles
def extract_info(entity):
    attr = entity.get("attributes", {})
    table_name = attr.get("name", "Inconnu")
    classifications = entity.get("classifications", [])

    if classifications:
        classification = classifications[0].get("typeName", "Non classifiée")
        statut = "✅"
    else:
        classification = "Non classifiée"
        statut = "❌"

    return {
        "Nom de la table": table_name,
        "Niveau de classification": classification,
        "Statut": statut
    }

# 🚀 Application Streamlit
st.set_page_config(page_title="📊 Dashboard Classification", layout="wide")
st.title("📊 Dashboard de classification des tables Atlas")

if st.button("🔄 Charger les données depuis Apache Atlas"):
    with st.spinner("Chargement des tables..."):
        raw_entities = get_all_postgres_tables()
        data = []

        for entity in raw_entities:
            guid = entity.get("guid")
            full_entity = get_entity_with_classification(guid)
            if full_entity:
                info = extract_info(full_entity)
                data.append(info)

        # Nettoyage et filtrage
        data = [item for item in data 
                if item.get("Nom de la table") 
                and isinstance(item["Nom de la table"], str) 
                and item["Nom de la table"][0].islower()]

        df = pd.DataFrame(data)

        # Calcul des KPI
        total_tables = len(df)
        classified_df = df[df["Statut"] == "✅"]
        non_classified_df = df[df["Statut"] == "❌"]
        nb_classified = len(classified_df)
        nb_non_classified = len(non_classified_df)
        pct_classified = (nb_classified / total_tables * 100) if total_tables > 0 else 0

        # Ajouter les KPIs à chaque ligne
        df["Nombre total de tables"] = total_tables
        df["Nombre de tables classifiées"] = nb_classified
        df["Nombre de tables non classifiées"] = nb_non_classified
        df["% de tables classifiées"] = f"{pct_classified:.2f}%"

        # Réorganisation des colonnes
        df = df[[
            "Nom de la table",
            "Niveau de classification",
            "Statut",
            "Nombre total de tables",
            "Nombre de tables classifiées",
            "Nombre de tables non classifiées",
            "% de tables classifiées"
        ]]

        # Affichage
        st.success("✅ Données chargées avec succès !")
        st.dataframe(df)

        # 📤 Export CSV
        csv = df.to_csv(index=False, sep=';', encoding='utf-8')
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name="dashboard_classification.csv",
            mime="text/csv"
        )
