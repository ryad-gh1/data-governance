import streamlit as st
import os
import json
import requests
import psycopg2
from dotenv import load_dotenv
import google.generativeai as genai
import re
import pandas as pd

# Chargement des variables d’environnement
load_dotenv()
API_KEY = os.getenv("API_KEY_GOOGLE")
LLM_MODEL = os.getenv("LLM_MODEL")
PROMPT_STRUCTURED_PATH = os.getenv("PROMPT_STRUCTURED_PATH")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
ATLAS_URL = os.getenv("ATLAS_BASE_URL")
ATLAS_USER = os.getenv("ATLAS_USER")
ATLAS_PASSWORD = os.getenv("ATLAS_PASSWORD")

# Connexion PostgreSQL
pg_conn = psycopg2.connect(
    host=POSTGRES_HOST, port=POSTGRES_PORT,
    dbname=POSTGRES_DB, user=POSTGRES_USER,
    password=POSTGRES_PASSWORD
)
pg_cursor = pg_conn.cursor()

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(LLM_MODEL)

level_mapping = {
    1: ("0", "Public"),
    2: ("1", "Restreint"),
    3: ("2", "Confidentiel"),
    4: ("3", "Secret"),
    5: ("4", "Très secret")
}

def format_classification(level_key):
    level_str, name = level_mapping.get(level_key, ("0", "Public"))
    return f"{name} ({int(level_str)})"

def extract_fcros_structured(justification):
    try:
        match = re.findall(r'F\s*:\s*(\d).?C\s:\s*(\d).?R\s:\s*(\d).?O\s:\s*(\d)', justification.replace("(", "").replace(")", ""))
        if match:
            f, c, r, o = map(int, match[0])
            return max(f, c, r, o)
    except:
        pass
    return 1

def detect_level_from_comment(comment):
    if comment:
        comment = comment.lower()

        mapping_text_level = {
            "public": 1,
            "restreint": 2,
            "confidentiel": 3,
            "secret": 4,
            "tres secret": 5,
            "très secret": 5
        }

        for keyword, level in mapping_text_level.items():
            if keyword in comment:
                return level

        match = re.search(r'niveau\s*(\d)', comment)
        if match:
            level = int(match.group(1))
            if 1 <= level <= 5:
                return level

    return None

st.title("🤖 Chatbot Intelligent – Classification des Données Sensibles")

pg_cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
tables = [row[0] for row in pg_cursor.fetchall()]

entity_name = st.selectbox("Sélectionnez une table PostgreSQL :", options=tables)

if "rows" not in st.session_state:
    st.session_state.rows = []
if "entity_name" not in st.session_state:
    st.session_state.entity_name = ""
if "classification_level" not in st.session_state:
    st.session_state.classification_level = ""
if "tag" not in st.session_state:
    st.session_state.tag = ""
if "result_text" not in st.session_state:
    st.session_state.result_text = ""
if "justification_finale" not in st.session_state:
    st.session_state.justification_finale = ""
if "commentaires" not in st.session_state:
    st.session_state.commentaires = {}

def classify_table(table_name):
    pg_cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s", (table_name,))
    columns = pg_cursor.fetchall()
    context = f"🧾 Table : {table_name}\n\nColonnes :\n" + "\n".join([f"- {col[0]} ({col[1]})" for col in columns])

    with open(PROMPT_STRUCTURED_PATH, "r", encoding="utf-8") as f:
        prompt = f.read()

    full_prompt = prompt.replace("{context}", context)
    response = model.generate_content(full_prompt)
    result = response.text.strip()

    justification_finale = ""
    rows = []
    max_niveau_global = 1
    for line in result.splitlines():
        if "Justification finale" in line:
            justification_finale = line.split(":", 1)[-1].strip()
        if "|" in line and not any(kw in line for kw in ["Colonne", "Sensible", "Justification"]) and "---" not in line:
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) >= 5:
                niveau = extract_fcros_structured(parts[4])
                max_niveau_global = max(max_niveau_global, niveau)
                parts.append(niveau)
                rows.append(parts)

    classification_level, tag = level_mapping.get(max_niveau_global, ("0", "Public"))

    return rows, max_niveau_global, classification_level, tag, result, justification_finale

# Lancer la classification initiale
if st.button("🚀 Lancer la classification"):
    rows, max_level_key, classification_level, tag, result, justification_finale = classify_table(entity_name)
    st.session_state.rows = rows
    st.session_state.entity_name = entity_name
    st.session_state.classification_level = classification_level
    st.session_state.tag = tag
    st.session_state.result_text = result
    st.session_state.justification_finale = justification_finale
    st.session_state.commentaires = {}

    st.markdown("### ✅ Résultat initial :")
    st.markdown(f"🔐 Classification finale : {format_classification(max_level_key)}")
    st.markdown(f"📝 Justification finale : {justification_finale}")
    df = pd.DataFrame(rows, columns=["Colonne", "Type", "Sensible ?", "Niveau LLM", "Justification", "MAX_FCRO"])
    st.dataframe(df.drop(columns=["MAX_FCRO"]), use_container_width=True)

# Afficher commentaires pour chaque colonne
if st.session_state.rows:
    st.markdown("### 📝 Ajouter un commentaire pour chaque colonne :")
    for row in st.session_state.rows:
        col_name = row[0]
        comment = st.text_input(f"Commentaire pour '{col_name}'", value=st.session_state.commentaires.get(col_name, ""), key=f"comment_{col_name}")
        st.session_state.commentaires[col_name] = comment

# Reclassification avec commentaires
if st.session_state.rows and st.button("🔄 Recalculer la classification avec commentaires"):
    rows_modif = []
    max_niveau_global = 1
    for row in st.session_state.rows:
        col_name, col_type, sens, niveau_llm, justification, max_score = row
        commentaire = st.session_state.commentaires.get(col_name, "")

        forced_level = detect_level_from_comment(commentaire)
        col_level = forced_level if forced_level is not None else max_score

        max_niveau_global = max(max_niveau_global, col_level)

        rows_modif.append([col_name, col_type, sens, str(col_level), justification, col_level])

    st.session_state.rows = rows_modif
    st.session_state.classification_level, st.session_state.tag = level_mapping.get(max_niveau_global, ("0", "Public"))

    st.success("✅ Classification recalculée avec commentaires.")
    st.markdown(f"🔐 Classification finale : {format_classification(max_niveau_global)}")
    st.markdown(f"📝 Justification finale : (basée sur les commentaires)")
    df = pd.DataFrame(rows_modif, columns=["Colonne", "Type", "Sensible ?", "Niveau LLM", "Justification", "MAX_FCRO"])
    st.dataframe(df.drop(columns=["MAX_FCRO"]), use_container_width=True)

# Sélection des colonnes pour reclassification automatique Gemini
if st.session_state.rows:
    st.markdown("### 🤖 Sélectionnez les colonnes à reclassifier automatiquement par Gemini :")
    cols_to_reclassify = st.multiselect("Choisissez les colonnes :", [row[0] for row in st.session_state.rows])

    if st.button("🤖 Reclassification automatique par Gemini"):
        if not cols_to_reclassify:
            st.warning("Veuillez sélectionner au moins une colonne pour la reclassification.")
        else:
            # Récupérer la classification actuelle dans st.session_state.rows
            rows_updated = []
            max_niveau_global = 1

            for row in st.session_state.rows:
                col_name, col_type, sens, niveau_llm, justification, max_score = row
                if col_name in cols_to_reclassify:
                    # Faire reclassification Gemini pour cette colonne seulement
                    # Ici, on peut soit appeler classify_table pour toute la table et ne garder que les colonnes,
                    # ou idéalement, envoyer uniquement la colonne à Gemini.
                    # Pour simplifier, on fait une requête globale et on remplace uniquement les colonnes sélectionnées

                    # Appel Gemini pour la table entière (option simple)
                    rows_gemini, max_level_key, classification_level, tag, result, justification_finale = classify_table(entity_name)

                    # Trouver la nouvelle ligne pour la colonne actuelle
                    new_row = next((r for r in rows_gemini if r[0] == col_name), None)
                    if new_row:
                        niveau = new_row[-1]  # MAX_FCRO
                        max_niveau_global = max(max_niveau_global, niveau)
                        rows_updated.append(new_row)
                    else:
                        # Si non trouvée, garder l'ancienne ligne
                        max_niveau_global = max(max_niveau_global, max_score)
                        rows_updated.append(row)
                else:
                    max_niveau_global = max(max_niveau_global, max_score)
                    rows_updated.append(row)

            st.session_state.rows = rows_updated
            st.session_state.classification_level, st.session_state.tag = level_mapping.get(max_niveau_global, ("0", "Public"))
            st.session_state.justification_finale = justification_finale  # On met la justification de la dernière requête Gemini
            st.success("✅ Reclassification automatique réalisée sur les colonnes sélectionnées.")

            st.markdown(f"🔐 Classification finale : {format_classification(max_niveau_global)}")
            st.markdown(f"📝 Justification finale : {justification_finale}")
            df = pd.DataFrame(rows_updated, columns=["Colonne", "Type", "Sensible ?", "Niveau LLM", "Justification", "MAX_FCRO"])
            st.dataframe(df.drop(columns=["MAX_FCRO"]), use_container_width=True)

# Enregistrer dans Apache Atlas
if st.session_state.rows and st.button("💾 Enregistrer la classification dans Apache Atlas"):
    if not st.session_state.entity_name:
        st.error("❌ Aucune entité sélectionnée.")
        st.stop()

    entity_type = "postgres_table"
    main_entity_data = {
        "entity": {
            "typeName": entity_type,
            "attributes": {
                "qualifiedName": st.session_state.entity_name,
                "name": st.session_state.entity_name,
                "level": st.session_state.classification_level,
                "llm_result": st.session_state.result_text,
                "description": "Classification globale calculée"
            },
            "classifications": [{"typeName": st.session_state.tag}]
        }
    }

    res = requests.post(f"{ATLAS_URL}/api/atlas/v2/entity",
                        auth=(ATLAS_USER, ATLAS_PASSWORD),
                        headers={"Content-Type": "application/json"},
                        data=json.dumps(main_entity_data))

    if res.status_code == 200:
        st.success("✅ Classification globale enregistrée dans Apache Atlas.")
    else:
        st.error(f"❌ Erreur lors de l'enregistrement globale : {res.status_code} - {res.text}")
