from src.database.postgres_utils import get_all_tables
from src.database.mongo_utils import get_all_collections

print("📦 Tables PostgreSQL disponibles :")
for t in get_all_tables():
    print(f"- {t}")

print("\n📚 Collections MongoDB disponibles :")
for c in get_all_collections():
    print(f"- {c}")
