import streamlit as st
import pandas as pd
from supabase import create_client

# CONFIGURATION
SUPABASE_URL = "https://enikglfabczfpahbfzvq.supabase.co"
SUPABASE_KEY = "sb_publishable_h169bGdSBk_SpbiXwH0KbQ_JE6Cm7lS"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

db = get_supabase()

st.set_page_config(page_title="VenteUp Pro", layout="wide")

if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# --- AUTHENTIFICATION ---
if st.session_state['user_id'] is None:
    st.title("🚀 VenteUp Pro")
    t1, t2 = st.tabs(["Connexion", "Créer un compte"])
    
    with t1:
        u = st.text_input("Pseudo", key="l_u")
        p = st.text_input("Mot de passe", type="password", key="l_p")
        if st.button("Se connecter", use_container_width=True):
            # Version ultra-simple sans aucun cryptage
            res = db.table("users").select("*").eq("username", u.strip()).eq("password", p.strip()).execute()
            if res.data:
                st.session_state['user_id'] = res.data[0]['id']
                st.rerun()
            else:
                st.error("Échec : Pseudo ou mot de passe incorrect.")

    with t2:
        nu = st.text_input("Nouveau Pseudo", key="s_u")
        ne = st.text_input("Nom Boutique", key="s_e")
        np = st.text_input("Mot de passe", type="password", key="s_p")
        if st.button("S'inscrire", use_container_width=True):
            try:
                db.table("users").insert({"username": nu.strip(), "password": np.strip(), "nom_ent": ne}).execute()
                st.success(f"Compte '{nu}' créé ! Connecte-toi maintenant.")
            except Exception as e:
                st.error(f"Erreur : {e}")
    st.stop()

# --- SI CONNECTÉ ---
user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]

st.success(f"Bienvenue dans la boutique {user_info['nom_ent']} !")
if st.button("Déconnexion"):
    st.session_state['user_id'] = None
    st.rerun()
