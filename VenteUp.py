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

# --- AUTHENTIFICATION (VERSION SIMPLE) ---
if st.session_state['user_id'] is None:
    st.title("🚀 VenteUp Pro")
    t1, t2 = st.tabs(["Connexion", "Créer un compte"])
    
    with t1:
        u = st.text_input("Pseudo", key="l_u")
        p = st.text_input("Mot de passe", type="password", key="l_p")
        if st.button("Se connecter", use_container_width=True):
            # On compare le mot de passe en texte normal
            res = db.table("users").select("*").eq("username", u).eq("password", p).execute()
            if res.data:
                st.session_state['user_id'] = res.data[0]['id']
                st.rerun()
            else:
                st.error("Identifiants incorrects.")

    with t2:
        nu = st.text_input("Nouveau Pseudo", key="s_u")
        ne = st.text_input("Nom Boutique", key="s_e")
        np = st.text_input("Mot de passe", type="password", key="s_p")
        if st.button("S'inscrire", use_container_width=True):
            try:
                # On enregistre le mot de passe en texte normal
                db.table("users").insert({"username": nu, "password": np, "nom_ent": ne}).execute()
                st.success("Compte créé ! Connecte-toi.")
            except:
                st.error("Pseudo déjà pris.")
    st.stop()

# --- RESTE DU CODE (Dashboard, Stock, etc.) ---
user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]

with st.sidebar:
    st.header(f"🏪 {user_info['nom_ent']}")
    menu = st.radio("Menu", ["📊 Dashboard", "🛒 Caisse", "📦 Stock", "💸 Dépenses"])
    if st.button("Déconnexion"):
        st.session_state['user_id'] = None
        st.rerun()

if menu == "📊 Dashboard":
    st.title("Bilan Financier")
    v = db.table("ventes").select("total").eq("user_id", user_id).execute().data
    d = db.table("depenses").select("montant").eq("user_id", user_id).execute().data
    tv, td = sum([x['total'] for x in v]), sum([x['montant'] for x in d])
    c1, c2, c3 = st.columns(3)
    c1.metric("Ventes", f"{tv:,} FG")
    c2.metric("Dépenses", f"{td:,} FG")
    c3.metric("Bénéfice", f"{tv-td:,} FG")

elif menu == "🛒 Caisse":
    st.title("Vente")
    prods = db.table("produits").select("*").eq("user_id", user_id).gt("qte", 0).execute().data
    if prods:
        with st.form("v_f"):
            p_n = st.selectbox("Article", [x['nom'] for x in prods])
            q = st.number_input("Quantité", min_value=1)
            if st.form_submit_button("Vendre"):
                p_d = [x for x in prods if x['nom'] == p_n][0]
                mt = q * p_d['p_vente']
                db.table("ventes").insert({"user_id": user_id, "nom_prod": p_n, "qte_v": q, "total": mt}).execute()
                db.table("produits").update({"qte": p_d['qte'] - q}).eq("id", p_d['id']).execute()
                st.success(f"Vendu : {mt:,} FG")

elif menu == "📦 Stock":
    st.title("Stock")
    with st.form("s_f"):
        n, pa, pv, qt = st.text_input("Nom"), st.number_input("Achat"), st.number_input("Vente"), st.number_input("Qté", min_value=1)
        if st.form_submit_button("Ajouter"):
            db.table("produits").insert({"user_id": user_id, "nom": n, "p_achat": pa, "p_vente": pv, "qte": qt}).execute()
            st.success("Ajouté !")

elif menu == "💸 Dépenses":
    st.title("Dépenses")
    with st.form("d_f"):
        mot = st.text_input("Motif")
        mt_d = st.number_input("Montant", min_value=0)
        if st.form_submit_button("Enregistrer"):
            db.table("depenses").insert({"user_id": user_id, "motif": mot, "montant": mt_d}).execute()
            st.success("Dépense enregistrée !")
