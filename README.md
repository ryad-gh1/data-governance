\# Chatbot Classification Project

&nbsp;   I.STRUCTURE DU PROJET 

&nbsp;      

&nbsp;      

&nbsp;       chatbot\_classification/

│

├── .env                                #  Clés API et infos sensibles

├── requirements.txt                    #  Dépendances Python

├── README.md                           #  Documentation projet

├── main.py                             #  Entrée principale (test global ou démo)

│

│

├── data/

│   ├── structured/                     #  Données PostgreSQL (CSV / SQL)

│   │   ├── cleaned/

│   │   └── structure\_banque.sql

│   └── unstructured/                  #  Données MongoDB (PDF, emails, .txt…)

│       ├── raw/

│       └── cleaned/

│

├── models/                             #  Modèles LLM locaux (.gguf) ou checkpoints

│

├── prompts/

│   └── prompt\_structured.txt            #  Prompt de classification (F, C, R, O)

│   └── prompt\_unstructured.txt

├── src/

│   ├── chatbot/                        #  Logique du chatbot

│   │   └── chatbot\_engine.py

│

│   ├── classification/                #  Code de classification

│   │   ├── test\_md.py

│   │   └── test\_pg.py

│

│

│   ├── database/                      #  Connexion PostgreSQL \& MongoDB

│   │   ├── postgres\_utils.py

│   │   └── mongo\_utils.py

│

│   ├── dashboard/                     #  Interface utilisateur (Streamlit ou autre)

│   │   ├── app.py                       # Test simple de prompt sans interface

|   |

│   ├── governance/                   # 🛰️ Code pour Atlas (json, tagging, API)

|   |

│   │   ├── entity\_types.json

│   │   ├── db\_entity.py

│   │   └── create\_entity\_types.py

|   |

│   |   └── docker-compose.yml

│   

|    ├── streamlit\_app/                   # 🛰️ Code pour Atlas (json, tagging, API)

|   |

│   │   ├── Accueil.py

│   │   ├── config.toml

│   │   └── pages/

│   |    └── Atlas\_FCRO.py

&nbsp;        └── Chatbot\_Intelligent.py

&nbsp;        └── Classification.py

&nbsp;        └── Configuration.py

&nbsp;        └── Historique.py

&nbsp;        



&nbsp;   II\_ETAPES DE PROJET 



&nbsp;   1.Installer les dépendances

&nbsp;       pip install -r requirements.txt



&nbsp;   2.CREATION DU FICHIER .env 

\#########################################

\# 🔐 Clés API \& Modèle LLM

\#########################################



API\_KEY\_GOOGLE=  

LLM\_PROVIDER=

LLM\_MODEL=

LLM\_TEMPERATURE=

LLM\_MAX\_TOKENS=



\#########################################

\# 🛢️ PostgreSQL

\#########################################



POSTGRES\_HOST=

POSTGRES\_PORT= 

POSTGRES\_DB= 

POSTGRES\_USER= 

POSTGRES\_PASSWORD= 



\#########################################

\# 🍃 MongoDB

\#########################################



MONGO\_URI=

MONGO\_DB= 



\#########################################

\# 📄 Prompts

\#########################################



PROMPT\_STRUCTURED\_PATH=

PROMPT\_UNSTRUCTURED\_PATH=



\#########################################

\# 📄 Atlas 

\#########################################



ATLAS\_BASE\_URL=

ATLAS\_USER=

ATLAS\_PASSWORD=



&nbsp;   3.Creer une image apache atlas dans docker 

&nbsp;   ../../governance>docker-compose up -d



&nbsp;   4.Activer votre environnement virtuel LLama 

&nbsp;   ./Chatbot\_Classification>python -m venv llama\_env

&nbsp;                           >llama\_env\\Scripts\\activate



&nbsp;   

&nbsp;   5.Verification des donnees strcutures et non structures et assurer leurs importation

&nbsp;       L'emplacement des donnees : ../../data



&nbsp;   6.Creation des classifications dans apache atlas:

&nbsp;   Public,Restreint,Confidentiel,Secret,Tres secret      



&nbsp;   7.Lancement du projet :

&nbsp;   ./Chatbot\_classification>streamlit run streamlit\_app/Accueil.py



&nbsp;   SI VOUS AVEZ RENCONTRE DES PROBLEMES VEUILLEZ ME CONTACTER SUR : hassan.benkrikch@uir.ac.ma



&nbsp;   (LE PROJET RESTE EN COURS DE DEVELOPPEMENT )







