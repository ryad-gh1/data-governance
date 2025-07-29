import streamlit as st
import pandas as pd
import psycopg2
import pymongo
import os
import re
import json
import requests
from dotenv import load_dotenv
from google.generativeai import configure, GenerativeModel

# 🔐 Charger les variables d'environnement
load_dotenv()

# ➤ Connexions & Configuration
configure(api_key=os.getenv("API_KEY_GOOGLE"))
model = GenerativeModel(os.getenv("LLM_MODEL"))

ATLAS_URL = os.getenv("ATLAS_URL", "http://localhost:21000/api/atlas/v2")
AUTH = (os.getenv("ATLAS_USER", "admin"), os.getenv("ATLAS_PASSWORD", "admin"))
HEADERS = {"Content-Type": "application/json"}

# PostgreSQL
pg_conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD")
)

# MongoDB
mongo_client = pymongo.MongoClient(os.getenv("MONGO_URI"))
mongo_db = mongo_client[os.getenv("MONGO_DB")]

PROMPT_STRUCTURED_PATH = os.getenv("PROMPT_STRUCTURED_PATH")
PROMPT_UNSTRUCTURED_PATH = os.getenv("PROMPT_UNSTRUCTURED_PATH")

# ➤ Apache Atlas: création + classification robuste
def push_entity_to_atlas(name, niveau, libelle, source_type, justification):
    entity_type = "postgres_table" if source_type == "postgres" else "mongo_collection"
    qualified_name = f"{name}@stage"

    # ➤ Étape 1 : création entité
    entity_payload = {
        "entity": {
            "typeName": entity_type,
            "attributes": {
                "qualifiedName": qualified_name,
                "name": name,
                "justification": justification
            }
        }
    }

    create_response = requests.post(
        f"{ATLAS_URL}/entity",
        headers=HEADERS,
        auth=AUTH,
        data=json.dumps(entity_payload)
    )

    if create_response.status_code not in [200, 201]:
        print(f"❌ Erreur création entité {name} :", create_response.text)
        return False

    # ➤ Étape 2 : récupérer le GUID via qualifiedName
    search_response = requests.get(
        f"{ATLAS_URL}/entity/uniqueAttribute/type/{entity_type}?attr:qualifiedName={qualified_name}",
        headers=HEADERS,
        auth=AUTH
    )

    if search_response.status_code != 200:
        print("❌ Échec récupération GUID :", search_response.text)
        return False

    try:
        guid = search_response.json()["entity"]["guid"]
    except:
        print("❌ GUID non trouvé dans la réponse.")
        return False

    # ➤ Étape 3 : classification
    classification_type = libelle.strip().capitalize()
    classification_payload = [
        {
            "typeName": classification_type,
            "attributes": {
                "niveau": niveau,
                "description": justification
            }
        }
    ]

    classify_response = requests.post(
        f"{ATLAS_URL}/entity/guid/{guid}/classifications",
        headers=HEADERS,
        auth=AUTH,
        data=json.dumps(classification_payload)
    )

    if classify_response.status_code not in [200, 201, 204]:
        print(f"❌ Erreur classification {classification_type} :", classify_response.text)
        return False

    print(f"✅ Entité '{name}' classifiée : {classification_type} ({niveau})")
    return True

# ➤ Fonctions auxiliaires
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

def detect_source_from_question(question):
    if "table" in question.lower(): return "postgres"
    elif "collection" in question.lower(): return "mongo"
    return None

def extract_target_name(question):
    parts = question.lower().split(" ")
    for i, part in enumerate(parts):
        if part in ["table", "collection"] and i+1 < len(parts):
            return parts[i+1]
    return None

def load_prompt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

import re

def parse_llm_response(response_text, source_type):
    try:
        # 1. Détection du nom (table ou collection)
        if source_type == "postgres":
            name_match = re.search(r"(?:📌\s*)?Table\s*:\s*([\w\-]+)", response_text, re.IGNORECASE)
        else:
            name_match = re.search(r"(?:📚\s*)?(?:Nom de la\s+)?Collection\s*:\s*([\w\-]+)", response_text, re.IGNORECASE)

        # 2. Classification finale (ex : Restreint (2))
        classif_match = re.search(r"Classification finale\s*:\s*(.*?)\s*\((\d+)\)", response_text, re.IGNORECASE)

        # 3. Justification finale multi-ligne
        justif_match = re.search(r"Justification finale\s*:\s*(.+)", response_text, re.DOTALL | re.IGNORECASE)

        # 4. Debug si un des éléments est manquant
        if not name_match or not classif_match or not justif_match:
            print("❌ Échec parsing")
            print("Texte reçu:\n", response_text)
            print(f"→ Nom : {name_match}")
            print(f"→ Classification : {classif_match}")
            print(f"→ Justification : {justif_match}")
            return None

        # 5. Résultat structuré
        return {
            "source_type": source_type,
            "name": name_match.group(1).strip(),
            "classification": classif_match.group(1).strip(),
            "niveau": int(classif_match.group(2).strip()),
            "justification": justif_match.group(1).strip()
        }

    except Exception as e:
        print("❌ Exception parsing :", e)
        return None

# ➤ Classification complète
def classify(question):
    source = detect_source_from_question(question)
    target = extract_target_name(question)
    if not source or not target:
        return "❌ Question invalide."

    if source == "postgres":
        try:
            df = get_postgres_table_preview(target)
            cols = df.dtypes.reset_index()
            cols.columns = ["nom", "type"]
            description = "\n".join([f"- {row['nom']} ({row['type']})" for _, row in cols.iterrows()])
            prompt = load_prompt(PROMPT_STRUCTURED_PATH)
        except:
            return "❌ Table PostgreSQL introuvable."
    else:
        try:
            docs = mongo_db[target].find_one()
            description = f"Nom de la collection : {target}\nContenu exemple : {docs if docs else 'vide'}"
            prompt = load_prompt(PROMPT_UNSTRUCTURED_PATH)
        except:
            return "❌ Collection MongoDB introuvable."

    full_prompt = f"{prompt}\n\n{description}"
    response = model.generate_content(full_prompt)
    parsed = parse_llm_response(response.text, source)

    if not parsed:
        return "❌ Échec parsing réponse LLM."

    push_entity_to_atlas(
        name=parsed["name"],
        niveau=parsed["niveau"],
        libelle=parsed["classification"],
        source_type=parsed["source_type"],
        justification=parsed["justification"]
    )

    return response.text

# ➤ UI Streamlit
st.set_page_config(layout="wide")
st.title("🔐 Classification des Données Sensibles")

source_type = st.radio("Type de source à afficher :", ["Table PostgreSQL", "Collection MongoDB"], horizontal=True)

if source_type == "Table PostgreSQL":
    tables = get_postgres_tables()
    selected_table = st.selectbox("Choisir une table :", tables)
    st.dataframe(get_postgres_table_preview(selected_table), use_container_width=True)
else:
    collections = get_mongodb_collections()
    selected_collection = st.selectbox("Choisir une collection :", collections)
    st.dataframe(get_mongodb_preview(selected_collection), use_container_width=True)

st.markdown("---")
st.header("🤖 Chatbot de Classification")

question = st.text_input("Posez votre question (ex: classifie la table assurances)")
if st.button("Envoyer"):
    with st.spinner("⏳ Classification en cours..."):
        reponse = classify(question)
        st.markdown(reponse)
