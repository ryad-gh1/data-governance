import os
import requests
from dotenv import load_dotenv

load_dotenv()

ATLAS_URL = os.getenv("ATLAS_URL", "http://localhost:21000/api/atlas/v2")
AUTH = (os.getenv("ATLAS_USER", "admin"), os.getenv("ATLAS_PASSWORD", "admin"))
HEADERS = {"Content-Type": "application/json"}

def push_justification_to_atlas(parent_guid, related_entity_type, related_entity_name, justification_text, niveau):
    """
    Crée une entité de type llm_justification dans Apache Atlas et la relie à une table ou collection existante.

    Args:
        parent_guid (str): GUID de la table ou collection déjà créée (postgres_table ou mongo_collection).
        justification_text (str): Texte généré par le LLM comme justification finale.
        niveau (int): Niveau de confidentialité (ex: 3).
        related_entity_name (str): Nom de l'entité d'origine (ex: clients).
        related_entity_type (str): Type d'entité ('postgres_table' ou 'mongo_collection').
    """

    entity_data = {
        "entity": {
            "typeName": "llm_justification",
            "attributes": {
                "qualifiedName": f"{related_entity_name}@justification",
                "name": f"Justification de {related_entity_name}",
                "justification_text": justification_text,
                "level": niveau,
                "related_entity_name": related_entity_name,
                "related_entity_type": related_entity_type
            },
            "relationshipAttributes": {
                "related_to": {
                    "guid": parent_guid,
                    "typeName": related_entity_type
                }
            }
        }
    }

    response = requests.post(
        f"{ATLAS_URL}/entity",
        headers=HEADERS,
        auth=AUTH,
        json=entity_data
    )

    if response.status_code == 200:
        print("✅ Justification poussée avec succès")
    else:
        raise Exception(f"Erreur Atlas ({response.status_code}) : {response.text}")