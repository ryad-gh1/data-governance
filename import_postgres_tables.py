#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Importer automatiquement toutes les tables PostgreSQL (schéma public)
comme entités postgres_table dans Apache Atlas.

Prérequis :
  pip install psycopg2-binary requests python-dotenv
"""

import os
import json
import psycopg2
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Chargement des variables d'environnement depuis .env
load_dotenv()

# DEBUG temporaire: vérifier que la variable est bien chargée
print("DEBUG PG_PASSWORD:", repr(os.getenv("PG_PASSWORD")))

# Paramètres PostgreSQL
PG_DB       = os.getenv("PG_DB",       "banque")
PG_USER     = os.getenv("PG_USER",     "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")
PG_HOST     = os.getenv("PG_HOST",     "localhost")
PG_PORT     = int(os.getenv("PG_PORT", "5433"))  # Met 5432 par défaut

# Paramètres Apache Atlas
ATLAS_HOST      = os.getenv("ATLAS_HOST", "http://localhost:21000")
ATLAS_USER      = os.getenv("ATLAS_USER", "admin")
ATLAS_PASSWORD  = os.getenv("ATLAS_PASSWORD", "admin")
ATLAS_CLUSTER   = os.getenv("ATLAS_CLUSTER", "cluster01")   # suffixe du qualifiedName
ATLAS_API       = f"{ATLAS_HOST.rstrip('/')}/api/atlas/v2/entity"

HEADERS = {"Content-Type": "application/json"}

def get_tables(schema: str = "public") -> list:
    """Retourne la liste des tables d'un schéma PostgreSQL."""
    conn = psycopg2.connect(
        host     = PG_HOST,
        port     = PG_PORT,
        dbname   = PG_DB,
        user     = PG_USER,
        password = PG_PASSWORD
    )
    cur = conn.cursor()
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s AND table_type = 'BASE TABLE';
        """,
        (schema,)
    )
    tables = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return tables


def build_payload(table_name: str, schema: str = "public") -> dict:
    """Construit le JSON attendu par Atlas pour une table PostgreSQL."""
    qualified_name = f"{PG_DB}.{schema}.{table_name}@{ATLAS_CLUSTER}"
    schema_qualified_name = f"{PG_DB}.{schema}@{ATLAS_CLUSTER}"
    db_qualified_name = f"{PG_DB}@{ATLAS_CLUSTER}"

    return {
        "entities": [
            {
                "typeName": "postgres_table",
                "attributes": {
                    "name": table_name,
                    "qualifiedName": qualified_name,
                    "owner": PG_USER,
                    "description": f"Table PostgreSQL '{schema}.{table_name}' importée automatiquement",
                    "schema": {
                        "typeName": "postgres_schema",
                        "uniqueAttributes": {
                            "qualifiedName": schema_qualified_name
                        }
                    },
                    "db": {
                        "typeName": "postgres_db",
                        "uniqueAttributes": {
                            "qualifiedName": db_qualified_name
                        }
                    }
                }
            }
        ]
    }


def send_to_atlas(payload: dict) -> None:
    """Envoie le payload à l'API Atlas et affiche le résultat."""
    table = payload["entities"][0]["attributes"]["name"]
    print(f"\n🔄  Création de la table '{table}' dans Atlas…")
    print("Payload ➜")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    try:
        resp = requests.post(
            ATLAS_API,
            headers=HEADERS,
            data=json.dumps(payload),
            auth=HTTPBasicAuth(ATLAS_USER, ATLAS_PASSWORD),
            timeout=30
        )
    except requests.exceptions.RequestException as exc:
        print(f"💥  Exception réseau : {exc}")
        return

    if resp.status_code in (200, 201):
        print(f"✅  Succès : table '{table}' importée.")
    else:
        print(f"❌  Erreur {resp.status_code} pour '{table}' :")
        try:
            print(json.dumps(resp.json(), indent=2))
        except ValueError:
            print(resp.text)


if __name__ == "__main__":
    print("📡  Connexion à PostgreSQL…")
    try:
        tables = get_tables()
    except psycopg2.Error as db_err:
        print(f"💥  Impossible de se connecter à PostgreSQL : {db_err}")
        exit(1)

    if not tables:
        print("⚠️  Aucune table trouvée dans le schéma 'public'.")
        exit(0)

    print(f"🔎  {len(tables)} table(s) détectée(s) : {tables}")

    for tbl in tables:
        payload = build_payload(tbl)
        send_to_atlas(payload)

    print("\n🏁  Import terminé.")
