import streamlit as st
import pandas as pd
from supabase import create_client

# CONFIGURATION SUPABASE
SUPABASE_URL = "https://enikglfabczfpahbfzvq.supabase.co"
SUPABASE_KEY = "sb_publishable_h169bGdSBk_SpbiXwH0KbQ_JE6Cm7lS"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

db = get_supabase()

st.set_page_config(page_title="VenteUp Pro", layout="wide", page_icon="📈")

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
            res = db.table("users").select("*").eq("username", u.strip()).eq("password", p.strip()).execute()
            if res.data:
                st.session_state['user_id'] = res.data[0]['id']
                st.rerun()
            else:
                st.error("Pseudo ou mot de passe incorrect.")
    with t2:
        nu = st.text_input("Nouveau Pseudo", key="s_u")
        ne = st.text_input("Nom Boutique", key="s_e")
        np = st.text_input("Mot de passe", type="password", key="s_p")
        if st.button("S'inscrire", use_container_width=True):
            try:
                db.table("users").insert({"username": nu.strip(), "password": np.strip(), "nom_ent": ne}).execute()
                st.success("Compte créé ! Connecte-toi.")
            except Exception as e:
                st.error(f"Erreur : {e}")
    st.stop()

# --- SI CONNECTÉ ---
user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]

# MENU LATÉRAL
with st.sidebar:
    st.header(f"🏪 {user_info['nom_ent']}")
    menu = st.radio("Navigation", ["📊 Dashboard", "🛒 Caisse", "📦 Stock", "💸 Dépenses"])
    st.divider()
    if st.button("🚪 Déconnexion"):
        st.session_state['user_id'] = None
        st.rerun()

# PAGES
if menu == "📊 Dashboard":
    st.title("Tableau de bord")
    v_data = db.table("ventes").select("total").eq("user_id", user_id).execute().data
    d_data = db.table("depenses").select("montant").eq("user_id", user_id).execute().data
    tv = sum([x['total'] for x in v_data])
    td = sum([x['montant'] for x in d_data])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Recettes", f"{tv:,} FG")
    col2.metric("Dépenses", f"{td:,} FG")
    col3.metric("Bénéfice Net", f"{tv-td:,} FG")

elif menu == "🛒 Caisse":
    st.title("Caisse")
    prods = db.table("produits").select("*").eq("user_id", user_id).gt("qte", 0).execute().data
    if prods:
        with st.form("vente"):
            p_sel = st.selectbox("Produit", [x['nom'] for x in prods])
            q_v = st.number_input("Quantité", min_value=1)
            if st.form_submit_button("Valider la vente"):
                p_info = [x for x in prods if x['nom'] == p_sel][0]
                total = q_v * p_info['p_vente']
                db.table("ventes").insert({"user_id": user_id, "nom_prod": p_sel, "qte_v": q_v, "total": total}).execute()
                db.table("produits").update({"qte": p_info['qte'] - q_v}).eq("id", p_info['id']).execute()
                st.success(f"Vendu : {total:,} FG")
    else:
        st.warning("Ajoutez des produits au stock d'abord.")

elif menu == "📦 Stock":
    st.title("Gestion du Stock")
    with st.form("stock"):
        n = st.text_input("Nom de l'article")
        pa = st.number_input("Prix d'achat", min_value=0)
        pv = st.number_input("Prix de vente", min_value=0)
        qt = st.number_input("Quantité", min_value=1)
        if st.form_submit_button("Ajouter"):
            db.table("produits").insert({"user_id": user_id, "nom": n, "p_achat": pa, "p_vente": pv, "qte": qt}).execute()
            st.success("Produit ajouté !")
    
    res = db.table("produits").select("*").eq("user_id", user_id).execute().data
    if res:
        st.dataframe(pd.DataFrame(res)[['nom', 'p_achat', 'p_vente', 'qte']])

elif menu == "💸 Dépenses":
    st.title("Suivi des Dépenses")
    with st.form("depense"):
        motif = st.text_input("Motif")
        mt = st.number_input("Montant", min_value=0)
        if st.form_submit_button("Enregistrer"):
            db.table("depenses").insert({"user_id": user_id, "motif": motif, "montant": mt}).execute()
            st.success("Dépense enregistrée !")
