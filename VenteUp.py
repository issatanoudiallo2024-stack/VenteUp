import streamlit as st
import pandas as pd
from supabase import create_client

# --- CONFIGURATION ---
URL = "https://enikglfabczfpahbfzvq.supabase.co"
KEY = "sb_publishable_h169bGdSBk_SpbiXwH0KbQ_JE6Cm7lS"

@st.cache_resource
def init_db():
    return create_client(URL, KEY)

db = init_db()
st.set_page_config(page_title="VenteUp Pro", layout="wide", page_icon="💰")

if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# --- ACCÈS ---
if st.session_state['user_id'] is None:
    st.title("🚀 VenteUp Pro")
    t1, t2 = st.tabs(["Connexion", "S'inscrire"])
    with t1:
        u_l = st.text_input("Pseudo", key="log_u").strip()
        p_l = st.text_input("Mot de passe", type="password", key="log_p").strip()
        if st.button("Se connecter", key="log_btn", use_container_width=True):
            res = db.table("users").select("*").eq("username", u_l).eq("password", p_l).execute()
            if res.data:
                st.session_state['user_id'] = res.data[0]['id']
                st.rerun()
            else: st.error("Pseudo ou mot de passe incorrect.")
    with t2:
        nu = st.text_input("Pseudo", key="reg_u")
        ne = st.text_input("Nom Boutique", key="reg_e")
        np = st.text_input("Mot de passe", type="password", key="reg_p")
        if st.button("Créer le compte", key="reg_btn"):
            db.table("users").insert({"username":nu, "nom_ent":ne, "password":np}).execute()
            st.success("Compte créé !")
    st.stop()

# --- INFOS BOUTIQUE ---
user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]
devise = "FG"

with st.sidebar:
    st.header(f"🏪 {user_info['nom_ent']}")
    menu = st.radio("Menu", ["📊 Bilan", "🛒 Vendre", "📦 Stock", "💸 Dépenses"])
    st.divider()
    if st.button("🚪 Déconnexion"):
        st.session_state['user_id'] = None
        st.rerun()
    st.caption("✍️ Dev: ISSA DIALLO")
    st.caption("📧 issatanoudiallo2024@gmail.com")
    st.caption("📞 610 51 89 73")

# --- BILAN ---
if menu == "📊 Bilan":
    st.header("📊 État de la Caisse")
    v = db.table("ventes").select("total").eq("user_id", user_id).execute().data
    d = db.table("depenses").select("montant").eq("user_id", user_id).execute().data
    tot_v, tot_d = sum([x['total'] for x in v]), sum([x['montant'] for x in d])
    c1, c2, c3 = st.columns(3)
    c1.metric("Ventes", f"{tot_v:,} {devise}")
    c2.metric("Dépenses", f"{tot_d:,} {devise}")
    c3.metric("Solde Net", f"{tot_v - tot_d:,} {devise}")

# --- VENDRE ---
elif menu == "🛒 Vendre":
    st.header("🛒 Terminal de Vente")
    prods = db.table("produits").select("*").eq("user_id", user_id).gt("qte", 0).execute().data
    if prods:
        with st.form("vente_pro"):
            p_n = st.selectbox("Article", [x['nom'] for x in prods])
            q = st.number_input("Quantité", min_value=1, value=1)
            if st.form_submit_button("Valider la vente"):
                sel = [x for x in prods if x['nom'] == p_n][0]
                total_net = q * sel['p_vente']
                db.table("ventes").insert({"user_id":user_id, "nom_prod":p_n, "qte_v":q, "total":total_net}).execute()
                db.table("produits").update({"qte": sel['qte'] - q}).eq("id", sel['id']).execute()
                st.success(f"Vendu : {total_net:,} {devise}")
                st.rerun()

# --- STOCK ---
elif menu == "📦 Stock":
    st.header("📦 Gestion Stock")
    res = db.table("produits").select("*").eq("user_id", user_id).execute().data
    if res:
        st.table(pd.DataFrame(res)[['nom', 'p_vente', 'qte']])
    with st.expander("Ajouter un produit"):
        with st.form("st_f"):
            n, pv, q = st.text_input("Nom"), st.number_input("Prix Vente"), st.number_input("Qté", min_value=1)
            if st.form_submit_button("Ajouter"):
                db.table("produits").insert({"user_id":user_id, "nom":n, "p_vente":pv, "qte":q}).execute()
                st.rerun()

# --- DÉPENSES ---
elif menu == "💸 Dépenses":
    st.header("💸 Sorties de caisse")
    with st.form("dp_f"):
        m, mt = st.text_input("Motif"), st.number_input("Montant")
        if st.form_submit_button("Enregistrer"):
            db.table("depenses").insert({"user_id":user_id, "motif":m, "montant":mt}).execute()
            st.success("Dépense enregistrée")
