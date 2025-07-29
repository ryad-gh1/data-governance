import os
import requests
from dotenv import load_dotenv

load_dotenv()

ATLAS_URL = os.getenv("ATLAS_BASE_URL")
ATLAS_USER = os.getenv("ATLAS_USER")
ATLAS_PASSWORD = os.getenv("ATLAS_PASSWORD")
HEADERS = {"Content-Type": "application/json"}

def push_llm_justification(source_name, source_type, fcro, justification):
    """
    Crée une entité `llm_justification` et la lie à la table/collection d'origine.
    """
    entity = {
        "entity": {
            "typeName": "llm_justification",
            "attributes": {
                "source_name": source_name,
                "source_type": source_type,
                "fcro_f": fcro.get("F", 0),
                "fcro_c": fcro.get("C", 0),
                "fcro_r": fcro.get("R", 0),
                "fcro_o": fcro.get("O", 0),
                "justification_finale": justification
            }
        }
    }

    res = requests.post(
        f"{ATLAS_URL}/api/atlas/v2/entity",
        auth=(ATLAS_USER, ATLAS_PASSWORD),
        headers=HEADERS,
        json=entity
    )

    if res.status_code == 200:
        print(f"✅ Justification LLM ajoutée pour {source_name}")
    else:
        print(f"❌ Erreur d'ajout justification pour {source_name} :", res.text)