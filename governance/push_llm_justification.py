import requests
import os
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

# 🔐 Authentification Atlas
ATLAS_USER = os.getenv("ATLAS_USER")
ATLAS_PASSWORD = os.getenv("ATLAS_PASSWORD")
ATLAS_URL = os.getenv("ATLAS_API", "http://localhost:21000")

def push_llm_justification(entity_name: str, entity_type: str, justification_text: str, level: str):
    """
    Enregistre une justification LLM dans Apache Atlas en tant qu'entité 'llm_justification'
    """
    url = f"{ATLAS_URL}/api/atlas/v2/entity"

    # 📦 Définition de l'entité justification
    entity_data = {
        "entities": [
            {
                "typeName": "llm_justification",
                "attributes": {
                    "name": f"justif_{entity_name}",
                    "related_entity": entity_name,
                    "related_type": entity_type,
                    "level": level,
                    "text": justification_text
                },
                "status": "ACTIVE"
            }
        ]
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(
        url,
        json=entity_data,
        headers=headers,
        auth=HTTPBasicAuth(ATLAS_USER, ATLAS_PASSWORD)
    )

    if response.status_code == 200:
        print(f"✅ Justification ajoutée pour : {entity_name}")
    else:
        print(f"❌ Erreur en ajoutant la justification ({response.status_code})")
        print(response.text)