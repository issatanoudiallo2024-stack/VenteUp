import streamlit as st
import pandas as pd
from supabase import create_client

# --- CONFIGURATION SUPABASE ---
URL = "https://enikglfabczfpahbfzvq.supabase.co"
KEY = "sb_publishable_h169bGdSBk_SpbiXwH0KbQ_JE6Cm7lS"

@st.cache_resource
def init_db():
    return create_client(URL, KEY)

db = init_db()

# --- INTERFACE & DESIGN (CSS) ---
st.set_page_config(page_title="VenteUp Pro", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    .bill-card {
        background: white;
        color: black;
        padding: 30px;
        border-radius: 15px;
        border: 1px solid #ddd;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        font-family: 'Arial', sans-serif;
    }
    .sidebar-text { font-size: 13px; color: #666; }
    </style>
""", unsafe_allow_html=True)

if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# --- AUTHENTIFICATION ---
if st.session_state['user_id'] is None:
    st.title("🚀 VenteUp Pro")
    t1, t2 = st.tabs(["Connexion", "Inscription"])
    with t1:
        with st.form("login"):
            u = st.text_input("Pseudo").strip()
            p = st.text_input("Mot de passe", type="password").strip()
            if st.form_submit_button("Se connecter", use_container_width=True):
                res = db.table("users").select("*").eq("username", u).eq("password", p).execute()
                if res.data:
                    st.session_state['user_id'] = res.data[0]['id']
                    st.rerun()
                else: st.error("Identifiants incorrects.")
    with t2:
        with st.form("signup"):
            nu, ne, np = st.text_input("Pseudo"), st.text_input("Nom Boutique"), st.text_input("Pass", type="password")
            if st.form_submit_button("Créer le compte", use_container_width=True):
                db.table("users").insert({"username":nu, "nom_ent":ne, "password":np}).execute()
                st.success("Compte créé !")
    st.stop()

# --- DONNÉES BOUTIQUE ---
user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]
devise = user_info.get('devise', 'FG')

with st.sidebar:
    st.title(f"🏪 {user_info['nom_ent']}")
    menu = st.radio("NAVIGATION", ["📊 Bilan", "🛒 Caisse", "📦 Stock", "💸 Dépenses", "⚙️ Paramètres"])
    st.divider()
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state['user_id'] = None
        st.rerun()
    st.markdown(f"""
    <div class="sidebar-text">
        <b>Développeur:</b> ISSA DIALLO<br>
        📧 issatanoudiallo2024@gmail.com<br>
        📞 610 51 89 73
    </div>
    """, unsafe_allow_html=True)

# --- 1. BILAN ---
if menu == "📊 Bilan":
    st.header("📊 Performance")
    v = db.table("ventes").select("total").eq("user_id", user_id).execute().data
    d = db.table("depenses").select("montant").eq("user_id", user_id).execute().data
    tot_v, tot_d = sum([x['total'] for x in v]), sum([x['montant'] for x in d])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Chiffre d'Affaires", f"{tot_v:,} {devise}")
    c2.metric("Total Dépenses", f"{tot_d:,} {devise}", delta_color="inverse")
    c3.metric("Bénéfice Net", f"{tot_v - tot_d:,} {devise}")

# --- 2. CAISSE & FACTURE ---
elif menu == "🛒 Caisse":
    st.header("🛒 Nouvelle Vente")
    prods = db.table("produits").select("*").eq("user_id", user_id).gt("qte", 0).execute().data
    if prods:
        col_form, col_fact = st.columns([1, 1.3])
        with col_form:
            with st.form("vente_pro", clear_on_submit=True):
                art = st.selectbox("Article", [x['nom'] for x in prods])
                qte = st.number_input("Quantité", min_value=1, value=1)
                rab = st.number_input("Rabais / Remise", min_value=0, value=0)
                st.write("---")
                c_nom = st.text_input("Nom Client")
                c_tel = st.text_input("Téléphone")
                c_adr = st.text_input("Adresse")
                if st.form_submit_button("Finaliser la vente", use_container_width=True):
                    sel = [x for x in prods if x['nom'] == art][0]
                    net = (qte * sel['p_vente']) - rab
                    db.table("ventes").insert({"user_id":user_id, "nom_prod":art, "qte_v":qte, "total":net, "client_nom":c_nom, "client_tel":c_tel, "client_adresse":c_adr, "rabais":rab}).execute()
                    db.table("produits").update({"qte": sel['qte'] - qte}).eq("id", sel['id']).execute()
                    st.session_state['fact'] = {"n":c_nom,"t":c_tel,"a":c_adr,"p":art,"q":qte,"net":net,"r":rab, "pv":sel['p_vente']}
                    st.rerun()
        
        if 'fact' in st.session_state:
            f = st.session_state['fact']
            with col_fact:
                st.markdown(f"""
                <div class="bill-card">
                    <div style="display:flex; justify-content:space-between;">
                        <div>
                            <h2 style="margin:0; color:#1e293b;">{user_info['nom_ent']}</h2>
                            <p style="font-size:12px; color:gray;">
                                {user_info.get('adresse','')}<br>
                                {user_info.get('telephone','')}<br>
                                {user_info.get('email_boutique','')}
                            </p>
                        </div>
                        <div style="text-align:right; border-left: 2px solid #eee; padding-left: 15px;">
                            <b style="color:gray; font-size:11px;">FACTURE POUR</b><br>
                            <b>{f['n']}</b><br>
                            <span style="font-size:12px;">{f['t']}<br>{f['a']}</span>
                        </div>
                    </div>
                    <hr style="margin:20px 0; border:0; border-top:1px solid #eee;">
                    <table style="width:100%; border-collapse:collapse;">
                        <tr style="text-align:left; border-bottom:1px solid #eee;"><th style="padding:10px 0;">Désignation</th><th style="text-align:right;">Total</th></tr>
                        <tr><td style="padding:15px 0;">{f['p']} (x{f['q']})</td><td style="text-align:right;">{f['pv']*f['q']:,}</td></tr>
                        {f'<tr style="color:red;"><td>Remise</td><td style="text-align:right;">- {f["r"]:,}</td></tr>' if f['r']>0 else ''}
                    </table>
                    <div style="margin-top:20px; padding:15px; background:#f8f9fa; border-radius:10px; display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:bold;">NET À PAYER</span>
                        <span style="font-size:24px; font-weight:bold; color:#10b981;">{f['net']:,} {devise}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# --- 3. STOCK ---
elif menu == "📦 Stock":
    st.header("📦 Inventaire")
    res = db.table("produits").select("*").eq("user_id", user_id).execute().data
    if res:
        st.dataframe(pd.DataFrame(res)[['nom', 'p_achat', 'p_vente', 'qte']], use_container_width=True)
    with st.expander("➕ Ajouter un article"):
        with st.form("add_art"):
            n, q = st.text_input("Nom"), st.number_input("Quantité", min_value=1)
            pa, pv = st.number_input("Prix Achat"), st.number_input("Prix Vente")
            if st.form_submit_button("Ajouter"):
                db.table("produits").insert({"user_id":user_id, "nom":n, "p_achat":pa, "p_vente":pv, "qte":q}).execute()
                st.rerun()

# --- 4. DÉPENSES ---
elif menu == "💸 Dépenses":
    st.header("💸 Sorties de caisse")
    with st.form("dep"):
        m, mt = st.text_input("Motif"), st.number_input("Montant", min_value=0)
        if st.form_submit_button("Enregistrer"):
            db.table("depenses").insert({"user_id":user_id, "motif":m, "montant":mt}).execute()
            st.success("Dépense enregistrée.")

# --- 5. PARAMÈTRES ---
elif menu == "⚙️ Paramètres":
    st.header("⚙️ Configuration")
    with st.form("settings"):
        c1, c2 = st.columns(2)
        n_e = c1.text_input("Nom Boutique", value=user_info['nom_ent'])
        e_b = c2.text_input("Email Boutique", value=user_info.get('email_boutique',''))
        adr = c1.text_input("Adresse Boutique", value=user_info.get('adresse',''))
        tel = c2.text_input("Téléphone Boutique", value=user_info.get('telephone',''))
        dev = st.selectbox("Devise", ["FG", "GNF", "FCFA", "USD", "EUR"], index=0)
        if st.form_submit_button("Sauvegarder les modifications", use_container_width=True):
            db.table("users").update({"nom_ent":n_e, "email_boutique":e_b, "adresse":adr, "telephone":tel, "devise":dev}).eq("id", user_id).execute()
            st.success("Paramètres mis à jour !")
            st.rerun()
