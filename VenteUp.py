import streamlit as st
import pandas as pd
from supabase import create_client

# --- CONFIGURATION SUPABASE ---
URL = "https://enikglfabczfpahbfzvq.supabase.co"
KEY = "sb_publishable_h169bGdSBk_SpbiXwH0KbQ_JE6Cm7lS"

@st.cache_resource
def init_connection():
    return create_client(URL, KEY)

db = init_connection()

st.set_page_config(page_title="VenteUp Pro", layout="centered")

if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# --- ECRAN D'ACCÈS ---
if st.session_state['user_id'] is None:
    st.title("📈 VenteUp Pro")
    tab1, tab2 = st.tabs(["Connexion", "S'inscrire"])
    
    with tab1:
        u = st.text_input("Pseudo", key="l_u").strip()
        p = st.text_input("Mot de passe", type="password", key="l_p").strip()
        if st.button("Se connecter", use_container_width=True):
            res = db.table("users").select("*").eq("username", u).eq("password", p).execute()
            if res.data:
                st.session_state['user_id'] = res.data[0]['id']
                st.rerun()
            else:
                st.error("Identifiants incorrects. Créez un compte si ce n'est pas fait.")

    with tab2:
        nu = st.text_input("Choisir un Pseudo", key="r_u").strip()
        ne = st.text_input("Nom de la Boutique", key="r_e").strip()
        np = st.text_input("Choisir un Mot de passe", type="password", key="r_p").strip()
        if st.button("Créer le compte", use_container_width=True):
            try:
                db.table("users").insert({"username": nu, "password": np, "nom_ent": ne}).execute()
                st.success("Compte créé ! Connectez-vous maintenant.")
            except Exception as e:
                st.error(f"Erreur : {e}")
    st.stop()

# --- INTERFACE PRINCIPALE ---
user_id = st.session_state['user_id']
user_data = db.table("users").select("*").eq("id", user_id).execute().data[0]

with st.sidebar:
    st.header(f"🏪 {user_data['nom_ent']}")
    menu = st.radio("Navigation", ["Dashboard", "Stock", "Vendre", "Déconnexion"])
    st.divider()
    st.caption(f"✍️ Dev: ISSA DIALLO | 610 51 89 73")

if menu == "Dashboard":
    st.subheader(f"Bienvenue, {user_data['username']}")
    st.write("Votre système de gestion est opérationnel.")

elif menu == "Stock":
    st.subheader("📦 Gestion du Stock")
    with st.form("add_stock"):
        n = st.text_input("Nom de l'article")
        pv = st.number_input("Prix de vente", min_value=0)
        q = st.number_input("Quantité", min_value=1)
        if st.form_submit_button("Ajouter"):
            db.table("produits").insert({"user_id": user_id, "nom": n, "p_vente": pv, "qte": q}).execute()
            st.success("Produit ajouté !")
            st.rerun()

elif menu == "Déconnexion":
    st.session_state['user_id'] = None
    st.rerun()
