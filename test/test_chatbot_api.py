import requests
import os
from src.database.postgres_utils import get_all_tables
from src.database.mongo_utils import get_all_collections
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/chatbot/classify")

def test_classify_name(name):
    try:
        response = requests.post(API_URL, json={"name": name})
        if response.status_code == 200:
            print(f"✅ Classification réussie pour '{name}':")
            print(response.json())
        else:
            print(f"❌ Erreur {response.status_code} pour '{name}': {response.text}")
    except Exception as e:
        print(f"❌ Exception pour '{name}': {e}")

def main():
    print("🧪 Récupération des tables PostgreSQL...")
    tables = get_all_tables()
    print(f"Tables : {tables}\n")

    print("🧪 Récupération des collections MongoDB...")
    collections = get_all_collections()
    print(f"Collections : {collections}\n")

    print("🚀 Démarrage des classifications...\n")

    for name in tables + collections:
        print(f"--- Classification de : {name} ---")
        test_classify_name(name)
        print()

if __name__ == "__main__":
    main()
