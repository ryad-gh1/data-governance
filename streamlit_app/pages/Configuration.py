import streamlit as st
import os
import psycopg2
from pymongo import MongoClient
import requests
from dotenv import load_dotenv
import pandas as pd

# Charger les variables d’environnement depuis .env
load_dotenv()

# Configuration Streamlit
st.set_page_config(page_title="Configuration", page_icon="⚙️", layout="wide")
st.title("⚙️ Configuration du Système")
st.write("Testez les connexions aux bases de données et à Apache Atlas.")

# 🔁 Bouton de test
if st.button("🔁 Tester à nouveau"):
    st.rerun()

# 📘 Récupération des variables
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DBNAME = os.getenv("MONGO_DB")

ATLAS_BASE_URL = os.getenv("ATLAS_BASE_URL")
ATLAS_USER = os.getenv("ATLAS_USER")
ATLAS_PASSWORD = os.getenv("ATLAS_PASSWORD")

# 🟢 Variables de statut
pg_status = "❌ Erreur"
mongo_status = "❌ Erreur"
atlas_status = "❌ Erreur"

# ✅ Test PostgreSQL
try:
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    pg_status = "✅ Connecté"
    conn.close()
except:
    pg_status = "❌ Erreur"

# ✅ Test MongoDB
try:
    client = MongoClient(MONGO_URI)
    if MONGO_DBNAME in client.list_database_names():
        mongo_status = "✅ Connecté"
    else:
        mongo_status = "⚠️ DB non trouvée"
except:
    mongo_status = "❌ Erreur"

# ✅ Test Apache Atlas
try:
    response = requests.get(f"{ATLAS_BASE_URL}/api/atlas/v2/types/typedefs", auth=(ATLAS_USER, ATLAS_PASSWORD))
    if response.status_code == 200:
        atlas_status = "✅ Connecté"
    else:
        atlas_status = f"⚠️ Code {response.status_code}"
except:
    atlas_status = "❌ Erreur"

# 📊 Tableau récapitulatif
status_data = {
    "Service": ["PostgreSQL", "MongoDB", "Apache Atlas"],
    "Statut": [pg_status, mongo_status, atlas_status],
    "Port par défaut": ["5432", "27017", "21000"],
    "Type": ["Base relationnelle", "Base NoSQL", "Gouvernance"]
}
df_status = pd.DataFrame(status_data)
st.dataframe(df_status, use_container_width=True)

# 🔍 Détails en dessous
st.markdown("---")
st.subheader("🔍 Détails des Connexions")

with st.expander("🔹 PostgreSQL"):
    st.code(f"Hôte : {POSTGRES_HOST}\nPort : {POSTGRES_PORT}\nDB : {POSTGRES_DB}\nUtilisateur : {POSTGRES_USER}", language="bash")

with st.expander("🔹 MongoDB"):
    st.code(f"URI : {MONGO_URI}\nNom de la base : {MONGO_DBNAME}", language="bash")

with st.expander("🔹 Apache Atlas"):
    st.code(f"URL : {ATLAS_BASE_URL}\nUtilisateur : {ATLAS_USER}", language="bash")

st.markdown("---")
st.caption("📁 Fichier `.env` chargé automatiquement depuis la racine du projet.")
