import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# ==========================================
# 🔑 CONFIGURATION SUPABASE
# ==========================================
SUPABASE_URL = "https://enikglfabczfpahbfzvq.supabase.co"
SUPABASE_KEY = "sb_publishable_h169bGdSBk_SpbiXwH0KbQ_JE6Cm7lS"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

db = get_supabase()

# --- CONFIGURATION ---
st.set_page_config(page_title="VenteUp Pro", layout="wide")

if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# --- CONNEXION SIMPLE ---
if st.session_state['user_id'] is None:
    st.title("📈 VenteUp Pro")
    u = st.text_input("Pseudo")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter", use_container_width=True):
        res = db.table("users").select("*").eq("username", u).eq("password", p).execute()
        if res.data:
            st.session_state['user_id'] = res.data[0]['id']
            st.rerun()
        else:
            st.error("Erreur de connexion")
    st.stop()

# INFOS UTILISATEUR
user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]

# --- MENU LATÉRAL ---
with st.sidebar:
    st.title(f"🏪 {user_info['nom_ent']}")
    menu = st.radio("Aller à :", ["Tableau de bord", "Vendre", "Stock", "Dépenses"])
    st.divider()
    if st.button("Quitter"):
        st.session_state['user_id'] = None
        st.rerun()
    st.write("---")
    st.caption(f"✍️ Développeur : **ISSA DIALLO**")
    st.caption(f"📞 610 51 89 73")

# --- PAGES ---

if menu == "Tableau de bord":
    st.header("Bilan de la boutique")
    v = db.table("ventes").select("total").eq("user_id", user_id).execute().data
    total = sum([x['total'] for x in v])
    st.metric("Ventes totales", f"{total:,} FG")

elif menu == "Vendre":
    st.header("🛒 Faire une vente")
    prods = db.table("produits").select("*").eq("user_id", user_id).execute().data
    if prods:
        nom_p = st.selectbox("Choisir l'article", [x['nom'] for x in prods])
        qte = st.number_input("Quantité", min_value=1)
        client = st.text_input("Nom du client", "Passager")
        
        if st.button("Valider la vente"):
            p_sel = [x for x in prods if x['nom'] == nom_p][0]
            prix_t = qte * p_sel['p_vente']
            # Enregistrement
            db.table("ventes").insert({"user_id": user_id, "nom_prod": nom_p, "qte_v": qte, "total": prix_t}).execute()
            db.table("produits").update({"qte": p_sel['qte'] - qte}).eq("id", p_sel['id']).execute()
            st.success(f"Vendu ! Total : {prix_t:,} FG")
            
            # Affichage Facture Simple
            st.divider()
            st.subheader("FACTURE")
            st.write(f"**Boutique :** {user_info['nom_ent']}")
            st.write(f"**Client :** {client}")
            st.write(f"**Article :** {nom_p} x {qte}")
            st.write(f"### TOTAL : {prix_t:,} FG")
            st.caption("✅ PAYÉ")

elif menu == "Stock":
    st.header("📦 Mon Stock")
    with st.form("ajout"):
        n = st.text_input("Nom de l'article")
        pv = st.number_input("Prix de vente", min_value=0)
        q = st.number_input("Quantité", min_value=1)
        if st.form_submit_button("Ajouter"):
            db.table("produits").insert({"user_id": user_id, "nom": n, "p_vente": pv, "qte": q}).execute()
            st.rerun()
    
    res = db.table("produits").select("*").eq("user_id", user_id).execute().data
    if res:
        st.table(pd.DataFrame(res)[['nom', 'p_vente', 'qte']])

elif menu == "Dépenses":
    st.header("💸 Mes Dépenses")
    motif = st.text_input("Motif")
    mt = st.number_input("Montant", min_value=0)
    if st.button("Enregistrer"):
        db.table("depenses").insert({"user_id": user_id, "motif": motif, "montant": mt}).execute()
        st.success("Dépense enregistrée")
