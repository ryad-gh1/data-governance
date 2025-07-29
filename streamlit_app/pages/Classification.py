import streamlit as st
import os
import pandas as pd
import psycopg2
import pymongo
from dotenv import load_dotenv

# 🌍 Configuration Streamlit
st.set_page_config(page_title="Visualisation des Données", layout="wide")
load_dotenv()

# Connexion PostgreSQL
pg_conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
    port=os.getenv("POSTGRES_PORT"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD")
)

# Connexion MongoDB
mongo_client = pymongo.MongoClient(os.getenv("MONGO_URI"))
mongo_db = mongo_client[os.getenv("MONGO_DB")]

# Fonctions de récupération
def get_postgres_tables():
    with pg_conn.cursor() as cur:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        return [row[0] for row in cur.fetchall()]

def get_postgres_table_preview(table):
    return pd.read_sql_query(f"SELECT * FROM {table} LIMIT 20", con=pg_conn)

def get_mongodb_collections():
    return mongo_db.list_collection_names()

def get_mongodb_preview(collection):
    docs = list(mongo_db[collection].find().limit(20))
    for doc in docs:
        doc.pop("_id", None)
    return pd.DataFrame(docs)

# --- Interface Streamlit ---
st.markdown("## 📊 Visualisation des données existantes")

col1, col2 = st.columns([1, 3])

with col1:
    source_type = st.radio("Source à afficher :", ["PostgreSQL", "MongoDB"])

# Initialisation variable sélection stockée dans session_state
if 'selected' not in st.session_state:
    st.session_state.selected = None

with col2:
    if source_type == "PostgreSQL":
        tables = get_postgres_tables()
        if not tables:
            st.warning("Aucune table PostgreSQL disponible.")
            st.session_state.selected = None
        else:
            # Reset selection si non valide
            if st.session_state.selected not in tables:
                st.session_state.selected = tables[0]
            st.session_state.selected = st.selectbox("Choisir une table :", tables, index=tables.index(st.session_state.selected))
    else:
        collections = get_mongodb_collections()
        if not collections:
            st.warning("Aucune collection MongoDB disponible.")
            st.session_state.selected = None
        else:
            # Reset selection si non valide
            if st.session_state.selected not in collections:
                st.session_state.selected = collections[0]
            st.session_state.selected = st.selectbox("Choisir une collection :", collections, index=collections.index(st.session_state.selected))

selected = st.session_state.selected

if selected:
    st.markdown(f"### 🗂 Aperçu de `{selected}`")

    try:
        if source_type == "PostgreSQL":
            # Vérifie si la table existe encore avant de charger
            tables = get_postgres_tables()
            if selected not in tables:
                st.error(f"La table PostgreSQL '{selected}' n'existe pas.")
            else:
                df = get_postgres_table_preview(selected)
                st.dataframe(df, use_container_width=True)
        else:
            collections = get_mongodb_collections()
            if selected not in collections:
                st.error(f"La collection MongoDB '{selected}' n'existe pas.")
            else:
                df = get_mongodb_preview(selected)
                st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Erreur lors de la lecture des données : {e}")

else:
    st.info("Veuillez sélectionner une table ou une collection pour voir l'aperçu.")
