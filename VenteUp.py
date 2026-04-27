import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
from supabase import create_client

# ==========================================
# 🔑 CONFIGURATION SUPABASE (ISSA DIALLO)
# ==========================================
SUPABASE_URL = "https://enikglfabczfpahbfzvq.supabase.co"
SUPABASE_KEY = "sb_publishable_h169bGdSBk_SpbiXwH0KbQ_JE6Cm7lS"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

db = get_supabase()

# --- SÉCURITÉ DES MOTS DE PASSE ---
def hash_p(p):
    return hashlib.sha256(str.encode(p)).hexdigest()

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="VenteUp Pro", layout="wide", page_icon="📈")

# Initialisation de la session utilisateur
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# --- ECRAN D'AUTHENTIFICATION ---
if st.session_state['user_id'] is None:
    st.title("🚀 VenteUp Pro")
    st.subheader("Logiciel de Gestion par Issa Diallo")
    
    tab_log, tab_sign = st.tabs(["Connexion", "Créer un compte"])
    
    with tab_log:
        u = st.text_input("Pseudo", key="login_user")
        p = st.text_input("Mot de passe", type="password", key="login_pass")
        if st.button("Se connecter", use_container_width=True):
            res = db.table("users").select("*").eq("username", u).eq("password", hash_p(p)).execute()
            if res.data:
                st.session_state['user_id'] = res.data[0]['id']
                st.rerun()
            else:
                st.error("Pseudo ou mot de passe incorrect.")

    with tab_sign:
        nu = st.text_input("Nouveau Pseudo", key="sign_user")
        ne = st.text_input("Nom de votre Boutique", key="sign_ent")
        np = st.text_input("Nouveau Mot de passe", type="password", key="sign_pass")
        if st.button("Valider l'inscription", use_container_width=True):
            try:
                db.table("users").insert({"username": nu, "password": hash_p(np), "nom_ent": ne}).execute()
                st.success("Compte créé avec succès ! Connectez-vous.")
            except:
                st.error("Ce pseudo est déjà utilisé.")
    st.stop()

# --- INFOS UTILISATEUR CONNECTÉ ---
user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]

# --- MENU LATÉRAL ---
with st.sidebar:
    st.header(f"🏪 {user_info['nom_ent']}")
    menu = st.radio("Navigation", ["📊 Dashboard", "🛒 Caisse", "📦 Stock", "💸 Dépenses"])
    st.divider()
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state['user_id'] = None
        st.rerun()
    st.caption("Développé par Issa Diallo")

# --- PAGES ---

if menu == "📊 Dashboard":
    st.title("Bilan Financier")
    # Calcul des Ventes
    v_data = db.table("ventes").select("total").eq("user_id", user_id).execute().data
    total_v = sum([x['total'] for x in v_data])
    
    # Calcul des Dépenses
    d_data = db.table("depenses").select("montant").eq("user_id", user_id).execute().data
    total_d = sum([x['montant'] for x in d_data])
    
    benefice = total_v - total_d
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Ventes Totales", f"{total_v:,} FG")
    c2.metric("Dépenses Totales", f"{total_d:,} FG", delta_color="inverse")
    c3.metric("Bénéfice Net", f"{benefice:,} FG")
    
    st.divider()
    st.subheader("Dernières transactions")
    histo = db.table("ventes").select("*").eq("user_id", user_id).order("date_v", desc=True).limit(5).execute().data
    if histo:
        st.dataframe(pd.DataFrame(histo))

elif menu == "🛒 Caisse":
    st.title("Nouvelle Vente")
    prods = db.table("produits").select("*").eq("user_id", user_id).gt("qte", 0).execute().data
    if prods:
        with st.form("form_vente"):
            p_nom = st.selectbox("Article", [x['nom'] for x in prods])
            q_v = st.number_input("Quantité", min_value=1)
            if st.form_submit_button("Valider la vente"):
                p_info = [x for x in prods if x['nom'] == p_nom][0]
                montant = q_v * p_info['p_vente']
                db.table("ventes").insert({"user_id": user_id, "nom_prod": p_nom, "qte_v": q_v, "total": montant}).execute()
                db.table("produits").update({"qte": p_info['qte'] - q_v}).eq("id", p_info['id']).execute()
                st.success(f"Vente validée : {montant:,} FG")
    else:
        st.warning("Aucun produit disponible en stock.")

elif menu == "📦 Stock":
    st.title("Inventaire")
    with st.form("form_stock"):
        n = st.text_input("Nom de l'article")
        pa = st.number_input("Prix d'achat", min_value=0)
        pv = st.number_input("Prix de vente", min_value=0)
        qt = st.number_input("Quantité", min_value=1)
        if st.form_submit_button("Ajouter"):
            db.table("produits").insert({"user_id": user_id, "nom": n, "p_achat": pa, "p_vente": pv, "qte": qt}).execute()
            st.success("Produit ajouté !")
    
    stock = db.table("produits").select("*").eq("user_id", user_id).execute().data
    if stock:
        st.dataframe(pd.DataFrame(stock)[['nom', 'p_achat', 'p_vente', 'qte']])

elif menu == "💸 Dépenses":
    st.title("Dépenses de l'entreprise")
    with st.form("form_dep"):
        motif = st.text_input("Motif (Ex: Loyer, Transport, Internet)")
        mt = st.number_input("Montant", min_value=0)
        if st.form_submit_button("Enregistrer"):
            db.table("depenses").insert({"user_id": user_id, "motif": motif, "montant": mt}).execute()
            st.success("Dépense enregistrée !")
    
    dep_list = db.table("depenses").select("*").eq("user_id", user_id).order("date_d", desc=True).execute().data
    if dep_list:
        st.table(pd.DataFrame(dep_list)[['date_d', 'motif', 'montant']])
