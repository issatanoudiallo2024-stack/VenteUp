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
        u_l = st.text_input("Pseudo", key="login_u").strip()
        p_l = st.text_input("Mot de passe", type="password", key="login_p").strip()
        if st.button("Se connecter", key="btn_login", use_container_width=True):
            res = db.table("users").select("*").eq("username", u_l).eq("password", p_l).execute()
            if res.data:
                st.session_state['user_id'] = res.data[0]['id']
                st.rerun()
            else: st.error("Identifiants incorrects.")
    with t2:
        nu = st.text_input("Nouveau Pseudo", key="reg_u")
        ne = st.text_input("Nom de la Boutique", key="reg_e")
        np = st.text_input("Mot de passe", type="password", key="reg_p")
        if st.button("Créer le compte", key="btn_reg"):
            db.table("users").insert({"username":nu, "nom_ent":ne, "password":np}).execute()
            st.success("Compte créé ! Connectez-vous.")
    st.stop()

# --- INFOS UTILISATEUR ---
user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]

with st.sidebar:
    st.header(f"🏪 {user_info['nom_ent']}")
    menu = st.radio("Menu", ["📊 Bilan", "🛒 Vendre", "📦 Stock", "💸 Dépenses", "⚙️ Paramètres"])
    st.divider()
    if st.button("🚪 Déconnexion"):
        st.session_state['user_id'] = None
        st.rerun()
    st.caption("✍️ Issa Diallo | UGANC")

# --- 1. BILAN ---
if menu == "📊 Bilan":
    st.header("📊 État de la Caisse")
    v = db.table("ventes").select("total").eq("user_id", user_id).execute().data
    d = db.table("depenses").select("montant").eq("user_id", user_id).execute().data
    
    tot_v = sum([x['total'] for x in v])
    tot_d = sum([x['montant'] for x in d])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Ventes", f"{tot_v:,} FG")
    c2.metric("Total Dépenses", f"{tot_d:,} FG", delta_color="inverse")
    c3.metric("Solde Net", f"{tot_v - tot_d:,} FG")

# --- 2. VENDRE (AVEC RABAIS) ---
elif menu == "🛒 Vendre":
    st.header("🛒 Terminal de Vente")
    prods = db.table("produits").select("*").eq("user_id", user_id).gt("qte", 0).execute().data
    if prods:
        c1, c2 = st.columns([1, 1.2])
        with c1:
            with st.form("vente_form"):
                p_n = st.selectbox("Article", [x['nom'] for x in prods])
                q = st.number_input("Quantité", min_value=1, value=1)
                rabais = st.number_input("Rabais (Remise en FG)", min_value=0, value=0)
                st.write("---")
                cn = st.text_input("Nom du Client")
                ct = st.text_input("Téléphone")
                if st.form_submit_button("Valider la Vente"):
                    sel = [x for x in prods if x['nom'] == p_n][0]
                    total_net = (q * sel['p_vente']) - rabais
                    # Update DB
                    db.table("ventes").insert({"user_id":user_id, "nom_prod":p_n, "qte_v":q, "total":total_net}).execute()
                    db.table("produits").update({"qte": sel['qte'] - q}).eq("id", sel['id']).execute()
                    # Info facture
                    st.session_state['f'] = {"n":cn,"t":ct,"p":p_n,"q":q,"net":total_net,"r":rabais}
                    st.rerun()
        
        if 'f' in st.session_state:
            f = st.session_state['f']
            with c2:
                st.markdown(f"""
                <div style="background:white; color:black; padding:20px; border:1px solid #ddd; border-radius:10px;">
                    <center><h3>{user_info['nom_ent']}</h3></center>
                    <hr>
                    <p><b>Client:</b> {f['n']} | {f['t']}</p>
                    <p><b>Article:</b> {f['p']} (x{f['q']})</p>
                    <p style="color:red;">Rabais: - {f['r']:,} FG</p>
                    <hr>
                    <h2 style="text-align:right; color:#2E7D32;">TOTAL: {f['net']:,} FG</h2>
                </div>
                """, unsafe_allow_html=True)
    else: st.warning("Stock vide. Ajoutez des produits.")

# --- 3. STOCK (AVEC PRIX ACHAT) ---
elif menu == "📦 Stock":
    st.header("📦 Gestion du Stock")
    res = db.table("produits").select("*").eq("user_id", user_id).execute().data
    if res:
        df = pd.DataFrame(res)
        st.table(df[['nom', 'p_achat', 'p_vente', 'qte']])
    
    with st.expander("Ajouter / Réapprovisionner"):
        with st.form("stock_form"):
            n = st.text_input("Nom de l'article")
            pa = st.number_input("Prix d'Achat", min_value=0)
            pv = st.number_input("Prix de Vente", min_value=0)
            q = st.number_input("Quantité", min_value=1)
            if st.form_submit_button("Enregistrer"):
                db.table("produits").insert({"user_id":user_id, "nom":n, "p_achat":pa, "p_vente":pv, "qte":q}).execute()
                st.rerun()

# --- 4. DÉPENSES ---
elif menu == "💸 Dépenses":
    st.header("💸 Sorties de caisse")
    with st.form("depense_form"):
        m = st.text_input("Motif")
        mt = st.number_input("Montant", min_value=0)
        if st.form_submit_button("Enregistrer"):
            db.table("depenses").insert({"user_id":user_id, "motif":m, "montant":mt}).execute()
            st.success("Dépense notée.")

# --- 5. PARAMÈTRES ---
elif menu == "⚙️ Paramètres":
    st.header("⚙️ Infos Boutique")
    with st.form("params_form"):
        ne = st.text_input("Nom Boutique", value=user_info['nom_ent'])
        ad = st.text_input("Adresse", value=user_info.get('adresse',''))
        tl = st.text_input("Téléphone", value=user_info.get('telephone',''))
        if st.form_submit_button("Mettre à jour"):
            db.table("users").update({"nom_ent":ne, "adresse":ad, "telephone":tl}).eq("id", user_id).execute()
            st.rerun()
