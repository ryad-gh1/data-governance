import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

ATLAS_URL = os.getenv("ATLAS_BASE_URL")
ATLAS_USER = os.getenv("ATLAS_USER")
ATLAS_PASSWORD = os.getenv("ATLAS_PASSWORD")

with open("types_def_banque.json", "r") as f:
    types_data = json.load(f)

response = requests.post(
    f"{ATLAS_URL}/api/atlas/v2/types/typedefs",
    auth=(ATLAS_USER, ATLAS_PASSWORD),
    headers={"Content-Type": "application/json"},
    json=types_data
)

if response.status_code == 200:
    print("✅ Types enregistrés dans Apache Atlas")
else:
    print("❌ Erreur lors de l'enregistrement :", response.text)
