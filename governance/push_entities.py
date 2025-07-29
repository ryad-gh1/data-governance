import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

ATLAS_URL = os.getenv("ATLAS_URL", "http://localhost:21000/api/atlas/v2")
AUTH = (os.getenv("ATLAS_USER", "admin"), os.getenv("ATLAS_PASSWORD", "admin"))
HEADERS = {"Content-Type": "application/json"}

with open("entities_banque.json", "r") as f:
    entities_data = json.load(f)

response = requests.post(
    f"{ATLAS_URL}/entity/bulk",
    headers=HEADERS,
    auth=AUTH,
    json=entities_data
)

if response.status_code in (200, 202):
    print("✅ Entités créées avec succès dans Apache Atlas")
else:
    print(f"❌ Erreur lors de la création des entités ({response.status_code}):")
    print(response.text)
