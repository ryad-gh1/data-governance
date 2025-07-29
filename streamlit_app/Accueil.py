import streamlit as st

st.set_page_config(page_title="Accueil", layout="centered")

st.title("Tableau de Bord – Classification des Données Sensibles")
st.markdown("Bienvenue sur la plateforme. Choisissez une action ci-dessous.")
st.markdown("---")

# Lien vers les autres pages
st.subheader("1. Classification")
st.markdown("- 👉 [Lancer le Chatbot Intelligent](pages/Chatbot_Intelligent.py)")
st.markdown("- 📄 [Voir les Résultats de Classification](pages/Classification.py)")

st.subheader("2. Analyse & Outils")
st.markdown("- ⚙️ [Configuration du Système](pages/Configuration.py)")
st.markdown("- 🧾 [Historique des Classifications](pages/Historique.py)")
st.markdown("- 🛰️ [Visualiser dans Atlas FCRO](pages/Atlas_FCRO.py)")

st.markdown("---")
st.caption("Projet PFE – EMSI 2025 – Gouvernance des Données Sensibles")
