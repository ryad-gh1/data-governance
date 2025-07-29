import os
import requests
from dotenv import load_dotenv

load_dotenv()

ATLAS_URL = os.getenv("ATLAS_BASE_URL")
ATLAS_USER = os.getenv("ATLAS_USER")
ATLAS_PASSWORD = os.getenv("ATLAS_PASSWORD")

HEADERS = {"Content-Type": "application/json"}

def push_entity_and_classify(name: str, type_name: str, level: str, llm_result: str):
    """
    Crée ou récupère une entité dans Apache Atlas,
    puis lui assigne une classification.

    Args:
        name (str): Nom de l'entité (table ou collection).
        type_name (str): Type de l'entité (ex: 'postgres_table', 'mongo_collection').
        level (str): Niveau de classification (ex: 'Secret', 'Confidentiel', etc.).
        llm_result (str): Justification/description issue du LLM.
    Returns:
        guid (str): Identifiant unique de l'entité dans Atlas.
    """

    # Exemple simplifié : création entité JSON
    entity_data = {
        "entity": {
            "typeName": type_name,
            "attributes": {
                "name": name,
                "qualifiedName": f"{name}@mycluster",
                "description": llm_result,
                "level": level
            }
        }
    }

    # Création entité dans Atlas
    url = f"{ATLAS_URL}/api/atlas/v2/entity"
    response = requests.post(url, auth=(ATLAS_USER, ATLAS_PASSWORD), json=entity_data, headers=HEADERS)
    if not response.ok:
        # En cas d'erreur, vérifier si entité existe déjà, récupérer son GUID
        # Pour simplifier, on raise l’erreur
        raise Exception(f"❌ Erreur lors de l'envoi vers Atlas : {response.text}")

    # Récupérer GUID entité créée
    guid = response.json().get("guidAssignments", {}).get(name)
    if not guid:
        # Si pas dans guidAssignments, essayer dans entities
        entities = response.json().get("entities", [])
        if entities and "guid" in entities[0]:
            guid = entities[0]["guid"]

    if not guid:
        raise Exception("❌ Impossible de récupérer le GUID de l'entité.")

    # Assigner la classification avec le nom de tag, par exemple 'classification_tag'
    classification_name = "classification_tag"
    classification_url = f"{ATLAS_URL}/api/atlas/v2/entity/guid/{guid}/classifications"
    classification_data = {
        "classificationName": classification_name,
        "attributes": {
            "level": level,
            "justification": llm_result
        }
    }

    class_response = requests.post(classification_url, auth=(ATLAS_USER, ATLAS_PASSWORD), json=classification_data, headers=HEADERS)
    # Gestion si classification déjà existante
    if class_response.status_code == 400 and "already associated with classification" in class_response.text:
        print(f"ℹ️ Classification '{classification_name}' déjà présente sur {name}.")
    elif not class_response.ok:
        raise Exception(f"❌ Erreur lors de l'ajout de classification : {class_response.text}")

    print(f"✅ Entité '{name}' créée et classifiée avec niveau {level}.")

    return guid


def get_all_entities_from_atlas():
    """
    Récupère toutes les entités de type postgres_table et mongo_collection
    avec leurs classifications depuis Apache Atlas.
    """
    url = f"{ATLAS_URL}/api/atlas/v2/search/basic"
    params = {
        "typeName": "postgres_table,mongo_collection",
        "excludeDeletedEntities": "true",
        "includeClassification": "true"
    }
    response = requests.get(url, auth=(ATLAS_USER, ATLAS_PASSWORD), params=params, headers=HEADERS)
    if not response.ok:
        raise Exception(f"Erreur lors de la récupération des entités : {response.text}")
    results = response.json().get("entities", [])
    entities_list = []
    for ent in results:
        attr = ent.get("attributes", {})
        classifications = ent.get("classificationNames", [])
        level = attr.get("level", "N/A")
        llm_result = attr.get("description", "N/A")
        entities_list.append({
            "name": attr.get("name", "N/A"),
            "type": ent.get("typeName", "N/A"),
            "level": level,
            "llm_result": llm_result,
            "classifications": classifications
        })
    return entities_list