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

# --- RÉCUPÉRATION INFOS ---
user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]
devise = user_info.get('devise', 'FG')

with st.sidebar:
    st.header(f"🏪 {user_info['nom_ent']}")
    menu = st.radio("Menu", ["📊 Bilan", "🛒 Vendre", "📦 Stock", "💸 Dépenses", "⚙️ Paramètres"])
    st.divider()
    if st.button("🚪 Déconnexion"):
        st.session_state['user_id'] = None
        st.rerun()
    st.caption("✍️ Dev: ISSA DIALLO")
    st.caption("📧 issatanoudiallo2024@gmail.com")
    st.caption("📞 610 51 89 73")

# --- 1. BILAN ---
if menu == "📊 Bilan":
    st.header("📊 État de la Caisse")
    v = db.table("ventes").select("total").eq("user_id", user_id).execute().data
    d = db.table("depenses").select("montant").eq("user_id", user_id).execute().data
    tot_v, tot_d = sum([x['total'] for x in v]), sum([x['montant'] for x in d])
    
    st.markdown(f"""
    <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;">
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; min-width: 200px; text-align: center; border-left: 5px solid #2E7D32;">
            <p style="margin:0; color: #666;">Ventes</p>
            <h2 style="margin:0; color: #2E7D32;">{tot_v:,} {devise}</h2>
        </div>
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; min-width: 200px; text-align: center; border-left: 5px solid #D32F2F;">
            <p style="margin:0; color: #666;">Dépenses</p>
            <h2 style="margin:0; color: #D32F2F;">{tot_d:,} {devise}</h2>
        </div>
        <div style="background-color: #2E7D32; padding: 20px; border-radius: 10px; min-width: 200px; text-align: center; color: white;">
            <p style="margin:0; opacity: 0.8;">Solde Net</p>
            <h2 style="margin:0;">{tot_v - tot_d:,} {devise}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 2. VENDRE (FACTURE CLIENT DROITE + EMAIL BOUTIQUE) ---
elif menu == "🛒 Vendre":
    st.header("🛒 Terminal de Vente")
    prods = db.table("produits").select("*").eq("user_id", user_id).gt("qte", 0).execute().data
    if prods:
        c1, c2 = st.columns([1, 1.3])
        with c1:
            with st.form("vente_pro"):
                p_n = st.selectbox("Article", [x['nom'] for x in prods])
                q = st.number_input("Quantité", min_value=1, value=1)
                rab = st.number_input("Rabais", min_value=0, value=0)
                st.markdown("**👤 Infos Client**")
                cn = st.text_input("Nom")
                ct = st.text_input("Numéro")
                cm = st.text_input("Mail")
                ca = st.text_input("Adresse")
                if st.form_submit_button("Valider la Vente", use_container_width=True):
                    sel = [x for x in prods if x['nom'] == p_n][0]
                    t_net = (q * sel['p_vente']) - rab
                    db.table("ventes").insert({"user_id":user_id, "nom_prod":p_n, "qte_v":q, "total":t_net, "client_nom":cn, "client_tel":ct, "client_mail":cm, "client_adresse":ca, "rabais":rab}).execute()
                    db.table("produits").update({"qte": sel['qte'] - q}).eq("id", sel['id']).execute()
                    st.session_state['f'] = {"n":cn,"t":ct,"m":cm,"a":ca,"p":p_n,"q":q,"net":t_net,"r":rab, "pv":sel['p_vente']}
                    st.rerun()
        if 'f' in st.session_state:
            f = st.session_state['f']
            with c2:
                st.markdown(f"""
                <div style="background:white; color:black; padding:30px; border:1px solid #ccc; border-radius:15px; font-family: sans-serif;">
                    <div style="display:flex; justify-content:space-between;">
                        <div style="width:48%; text-align:left;">
                            <h3 style="margin:0; color:#333;">{user_info['nom_ent']}</h3>
                            <p style="margin:2px 0; font-size:12px;">{user_info.get('adresse','')}</p>
                            <p style="margin:2px 0; font-size:12px;">Tel: {user_info.get('telephone','')}</p>
                            <p style="margin:2px 0; font-size:12px;">Email: {user_info.get('email_boutique','')}</p>
                        </div>
                        <div style="width:48%; text-align:right; border-left: 1px solid #eee; padding-left: 10px;">
                            <b style="color:gray; font-size:10px;">CLIENT</b><br>
                            <b>{f['n']}</b><br>
                            <small>{f['t']}<br>{f['m']}<br>{f['a']}</small>
                        </div>
                    </div>
                    <hr style="margin:20px 0; border: 0; border-top: 1px dashed #eee;">
                    <table style="width:100%;">
                        <tr style="border-bottom: 1px solid #eee;"><th style="text-align:left;">Désignation</th><th style="text-align:right;">Total</th></tr>
                        <tr><td>{f['p']} ({f['q']} x {f['pv']:,})</td><td style="text-align:right;">{f['pv']*f['q']:,} {devise}</td></tr>
                        {f'<tr style="color:red;"><td>Rabais</td><td style="text-align:right;">- {f["r"]:,} {devise}</td></tr>' if f['r']>0 else ''}
                    </table>
                    <div style="margin-top:20px; border-top: 2px solid #333; padding-top:10px; display:flex; justify-content:space-between;">
                        <h3 style="margin:0;">NET À PAYER</h3>
                        <h2 style="margin:0; color:#2E7D32;">{f['net']:,} {devise}</h2>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# --- 3. STOCK ---
elif menu == "📦 Stock":
    st.header("📦 Gestion Stock")
    res = db.table("produits").select("*").eq("user_id", user_id).execute().data
    if res:
        st.dataframe(pd.DataFrame(res)[['nom', 'p_achat', 'p_vente', 'qte']], use_container_width=True)
    with st.expander("Ajouter un produit"):
        with st.form("st_f"):
            n, pa, pv, q = st.text_input("Nom"), st.number_input("Prix Achat"), st.number_input("Prix Vente"), st.number_input("Qté", min_value=1)
            if st.form_submit_button("Ajouter"):
                db.table("produits").insert({"user_id":user_id, "nom":n, "p_achat":pa, "p_vente":pv, "qte":q}).execute()
                st.rerun()

# --- 4. DÉPENSES ---
elif menu == "💸 Dépenses":
    with st.form("dp_f"):
        m, mt = st.text_input("Motif"), st.number_input("Montant")
        if st.form_submit_button("Enregistrer"):
            db.table("depenses").insert({"user_id":user_id, "motif":m, "montant":mt}).execute()
            st.success("Enregistré")

# --- 5. PARAMÈTRES (AVEC EMAIL BOUTIQUE) ---
elif menu == "⚙️ Paramètres":
    st.header("⚙️ Configuration Boutique")
    with st.form("conf_f"):
        n_e = st.text_input("Nom Boutique", value=user_info['nom_ent'])
        em_b = st.text_input("Email Boutique", value=user_info.get('email_boutique',''))
        addr = st.text_input("Adresse Boutique", value=user_info.get('adresse',''))
        tel = st.text_input("Téléphone", value=user_info.get('telephone',''))
        dev = st.selectbox("Devise", ["FG", "GNF", "FCFA", "EURO", "DOLLAR"], index=0)
        if st.form_submit_button("Sauvegarder", use_container_width=True):
            db.table("users").update({"nom_ent":n_e, "email_boutique":em_b, "adresse":addr, "telephone":tel, "devise":dev}).eq("id", user_id).execute()
            st.success("Paramètres mis à jour !")
            st.rerun()
