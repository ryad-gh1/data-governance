import os
import google.generativeai as genai
from dotenv import load_dotenv
import re

# Charger les variables d’environnement
load_dotenv()

# Vérifier que la clé API est bien présente
api_key = os.getenv("API_KEY_GOOGLE")
if not api_key:
    raise ValueError("❌ Clé API Google manquante. Vérifie ton fichier .env")
genai.configure(api_key=api_key)

def load_prompt(template_type: str) -> str:
    prompt_path = f"prompts/prompt_{template_type}.txt"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ Fichier prompt introuvable : {prompt_path}")

def classify_data(template_type: str, entity_name: str, data: list) -> tuple:
    system_prompt = load_prompt(template_type)

    # Formater les données en fonction du type
    if template_type == "structured":
        cols_str = "\n".join([f"- {col['name']} ({col['type']})" for col in data])
        final_prompt = f"{system_prompt}\n\n📊 Table : {entity_name}\n\n🧱 Colonnes :\n{cols_str}"
    else:
        if isinstance(data, dict) and "description" in data:
            fields_str = data["description"]
        elif isinstance(data, list):
            fields_str = "\n".join([f"- {field}" for field in data])
        else:
            fields_str = str(data)
        final_prompt = f"{system_prompt}\n\n📚 Collection : {entity_name}\n\n📄 Champs :\n{fields_str}"

    # Afficher le prompt pour debug
    print("\n🔎 Prompt envoyé à Gemini :\n", final_prompt)

    # Appel au modèle Gemini
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(final_prompt)
        output = response.text
    except Exception as e:
        return f"❌ Erreur lors de la génération : {e}", "Erreur"

    print("\n📄 Réponse de Gemini :\n", output)

    # Extraction du niveau de classification
    level_match = re.search(r"Classification finale\s*:\s*([^\(\n]+)\s*\((\d)\)", output)
    level = level_match.group(1).strip() if level_match else "Non classifié"

    return output, level
