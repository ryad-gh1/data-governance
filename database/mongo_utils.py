import os
import pymongo
from dotenv import load_dotenv

load_dotenv()

mongo_client = pymongo.MongoClient(os.getenv("MONGO_URI"))
mongo_db = mongo_client[os.getenv("MONGO_DB")]

def get_collection_info(collection_name: str):
    collection = mongo_db[collection_name]
    # Option 1: Return description or list of keys from first doc
    first_doc = collection.find_one()
    if first_doc:
        # Remove _id for privacy
        first_doc.pop("_id", None)
        return {"description": "Exemple de document:\n" + str(first_doc)}
    else:
        return {"description": "Collection vide"}

def get_all_collections():
    return mongo_db.list_collection_names()
