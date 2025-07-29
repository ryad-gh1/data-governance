import requests
from requests.auth import HTTPBasicAuth

ATLAS_BASE_URL = "http://localhost:21000/api/atlas/v2"
USERNAME = "admin"
PASSWORD = "admin"

def get_entity_guid_by_name(entity_name):
    url = f"{ATLAS_BASE_URL}/search/basic"
    payload = {
        "typeName": "postgres_table",
        "excludeDeletedEntities": True,
        "limit": 100
    }
    response = requests.post(url, json=payload, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    if response.status_code != 200:
        print(f"Erreur lors de la récupération des entités : {response.status_code}")
        return None

    entities = response.json().get("entities", [])
    for entity in entities:
        attr = entity.get("attributes", {})
        name = attr.get("name")
        if name and name.lower() == entity_name.lower():  # comparaison insensible à la casse
            print(f"Trouvé '{name}' avec GUID : {entity['guid']}")
            return entity["guid"]
    print(f"Entité '{entity_name}' non trouvée.")
    return None

def delete_entity_by_guid(guid):
    url = f"{ATLAS_BASE_URL}/entity/guid/{guid}"
    response = requests.delete(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    if response.status_code == 200:
        print(f"Suppression réussie pour GUID : {guid}")
    else:
        print(f"Erreur suppression GUID {guid} : {response.status_code} - {response.text}")

# Supprimer les tables Clients et Assurances (insensible à la casse)
for table_name in ["clients", "assurances"]:
    guid = get_entity_guid_by_name(table_name)
    if guid:
        delete_entity_by_guid(guid)
