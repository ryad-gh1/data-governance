import os
from dotenv import load_dotenv
from push_justification import push_justification_to_atlas

# 🔐 Charger les variables d’environnement (.env)
load_dotenv()

# 🔧 Exemple de test : GUID valide + nom + justification fictive
if __name__ == "__main__":
    # ➤ Remplace ce GUID par un vrai GUID d'une table ou collection déjà créée dans Atlas
    fake_guid = "12345678-90ab-cdef-1234-567890abcdef"
    fake_name = "clients"  # Nom réel de la table ou collection
    fake_justification = "📝 Justification finale : Cette table contient des données personnelles sensibles protégées par la loi 09-08 et le RGPD."
    fake_level = 3  # Niveau entre 1 et 5

    try:
        push_justification_to_atlas(fake_guid, fake_name, fake_justification, fake_level)
        print("✅ Justification testée avec succès.")
    except Exception as e:
        print(f"❌ Erreur pendant le test : {e}")