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

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="VenteUp Pro", layout="wide", page_icon="📈")

# Initialisation de la session
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# --- ECRAN D'AUTHENTIFICATION ---
if st.session_state['user_id'] is None:
    st.title("🚀 VenteUp Pro")
    st.subheader("Logiciel de Gestion Multi-Boutique")
    
    tab_log, tab_sign = st.tabs(["Connexion", "Créer un compte"])
    
    with tab_log:
        u = st.text_input("Pseudo", key="login_user")
        p = st.text_input("Mot de passe", type="password", key="login_pass")
        if st.button("Se connecter", use_container_width=True):
            res = db.table("users").select("*").eq("username", u.strip()).eq("password", p.strip()).execute()
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
                db.table("users").insert({"username": nu.strip(), "password": np.strip(), "nom_ent": ne}).execute()
                st.success(f"Compte '{nu}' créé avec succès ! Connectez-vous.")
            except Exception as e:
                st.error(f"Erreur : Ce pseudo est peut-être déjà utilisé.")
    st.stop()

# --- INFOS UTILISATEUR CONNECTÉ ---
user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]

# --- MENU LATÉRAL ---
with st.sidebar:
    st.header(f"🏪 {user_info['nom_ent']}")
    menu = st.radio("Navigation", ["📊 Dashboard", "🛒 Caisse & Facture", "📦 Stock", "💸 Dépenses"])
    st.divider()
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state['user_id'] = None
        st.rerun()
    st.caption("---")
    st.caption(f"🛠️ Développeur : **ISSA DIALLO**")
    st.caption(f"📞 610 51 89 73")
    st.caption(f"📧 issatanoudiallo2024@gmail.com")

# --- PAGES ---

if menu == "📊 Dashboard":
    st.title("Bilan de la Boutique")
    v_data = db.table("ventes").select("total").eq("user_id", user_id).execute().data
    d_data = db.table("depenses").select("montant").eq("user_id", user_id).execute().data
    total_v = sum([x['total'] for x in v_data])
    total_d = sum([x['montant'] for x in d_data])
    benefice = total_v - total_d
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Ventes Totales", f"{total_v:,} FG")
    c2.metric("Dépenses Totales", f"{total_d:,} FG", delta_color="inverse")
    c3.metric("Bénéfice Net", f"{benefice:,} FG")

elif menu == "🛒 Caisse & Facture":
    st.title("🛒 Terminal de Vente")
    prods = db.table("produits").select("*").eq("user_id", user_id).gt("qte", 0).execute().data
    
    if prods:
        col_form, col_facture = st.columns([1, 1])
        
        with col_form:
            st.subheader("Nouvelle Transaction")
            with st.form("form_vente"):
                p_nom = st.selectbox("Article à vendre", [x['nom'] for x in prods])
                q_v = st.number_input("Quantité", min_value=1)
                st.divider()
                st.markdown("**👤 Infos Client**")
                c_nom = st.text_input("Nom complet", value="Passager")
                c_tel = st.text_input("Téléphone client")
                c_adr = st.text_input("Adresse client")
                cachet = st.checkbox("Ajouter le cachet 'PAYÉ'")
                if st.form_submit_button("Générer la Facture"):
                    p_info = [x for x in prods if x['nom'] == p_nom][0]
                    montant = q_v * p_info['p_vente']
                    
                    # Enregistrement
                    db.table("ventes").insert({"user_id": user_id, "nom_prod": p_nom, "qte_v": q_v, "total": montant}).execute()
                    db.table("produits").update({"qte": p_info['qte'] - q_v}).eq("id", p_info['id']).execute()
                    
                    st.session_state['last_facture'] = {
                        "client": c_nom, "tel": c_tel, "adr": c_adr, 
                        "prod": p_nom, "qte": q_v, "pu": p_info['p_vente'], 
                        "total": montant, "cachet": cachet
                    }
                    st.rerun()

        if 'last_facture' in st.session_state:
            f = st.session_state['last_facture']
            with col_facture:
                with st.container(border=True):
                    st.markdown(f"<h2 style='text-align:center;'>{user_info['nom_ent']}</h2>", unsafe_allow_html=True)
                    st.write(f"**Date:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                    st.divider()
                    st.write(f"**CLIENT:** {f['client']}")
                    if f['tel']: st.write(f"📞 {f['tel']}")
                    st.divider()
                    st.write(f"**Désignation:** {f['prod']}")
                    st.write(f"**Quantité:** {f['qte']}")
                    st.write(f"**Prix Unitaire:** {f['pu']:,} FG")
                    st.markdown(f"### TOTAL : {f['total']:,} FG")
                    
                    if f['cachet']:
                        st.markdown("<h3 style='color:red; border:3px solid red; width:fit-content; padding:5px; transform: rotate(-10deg);'>✅ PAYÉ</h3>", unsafe_allow_html=True)
                    
                    st.divider()
                    st.caption(f"Développeur : ISSA DIALLO | 📞 610 51 89 73")
                    st.caption(f"📧 issatanoudiallo2024@gmail.com")
                if st.button("Nouvelle vente"):
                    del st.session_state['last_facture']
                    st.rerun()
    else:
        st.warning("Votre stock est vide. Ajoutez des produits d'abord.")

elif menu == "📦 Stock":
    st.title("Gestion de l'inventaire")
    with st.form("form_stock"):
        n = st.text_input("Nom du produit")
        pa = st.number_input("Prix d'achat", min_value=0)
        pv = st.number_input("Prix de vente", min_value=0)
        qt = st.number_input("Quantité initiale", min_value=1)
        if st.form_submit_button("Ajouter au stock"):
            db.table("produits").insert({"user_id": user_id, "nom": n, "p_achat": pa, "p_vente": pv, "qte": qt}).execute()
            st.success("Produit ajouté !")
    
    stock = db.table("produits").select("*").eq("user_id", user_id).execute().data
    if stock:
        st.dataframe(pd.DataFrame(stock)[['nom', 'p_achat', 'p_vente', 'qte']])

elif menu == "💸 Dépenses":
    st.title("Suivi des charges")
    with st.form("form_dep"):
        motif = st.text_input("Motif de la dépense")
        mt = st.number_input("Montant", min_value=0)
        if st.form_submit_button("Enregistrer la dépense"):
            db.table("depenses").insert({"user_id": user_id, "motif": motif, "montant": mt}).execute()
            st.success("Dépense enregistrée !")
