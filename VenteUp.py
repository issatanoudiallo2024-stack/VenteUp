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
devise = user_info.get('devise', 'FG')

with st.sidebar:
    st.header(f"🏪 {user_info['nom_ent']}")
    menu = st.radio("Menu", ["📊 Bilan", "🛒 Vendre", "📦 Stock", "💸 Dépenses", "⚙️ Paramètres"])
    st.divider()
    if st.button("🚪 Déconnexion"):
        st.session_state['user_id'] = None
        st.rerun()
    # TA SIGNATURE RÉTABLIE
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

# --- VENDRE (FACTURE DESIGN CLIENT DROITE) ---
elif menu == "🛒 Vendre":
    st.header("🛒 Terminal de Vente")
    prods = db.table("produits").select("*").eq("user_id", user_id).gt("qte", 0).execute().data
    if prods:
        c1, c2 = st.columns([1, 1.2])
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
                if st.form_submit_button("Valider et Générer Facture"):
                    sel = [x for x in prods if x['nom'] == p_n][0]
                    total_net = (q * sel['p_vente']) - rab
                    db.table("ventes").insert({
                        "user_id":user_id, "nom_prod":p_n, "qte_v":q, "total":total_net,
                        "client_nom":cn, "client_tel":ct, "client_mail":cm, "client_adresse":ca, "rabais":rab
                    }).execute()
                    db.table("produits").update({"qte": sel['qte'] - q}).eq("id", sel['id']).execute()
                    st.session_state['f'] = {"n":cn,"t":ct,"m":cm,"a":ca,"p":p_n,"q":q,"net":total_net,"r":rab, "pv":sel['p_vente']}
                    st.rerun()
        
        if 'f' in st.session_state:
            f = st.session_state['f']
            with c2:
                st.markdown(f"""
                <div style="background:white; color:black; padding:25px; border:1px solid #ccc; border-radius:10px;">
                    <div style="display:flex; justify-content:space-between;">
                        <div style="width:48%; text-align:left;">
                            <h3 style="margin:0;">{user_info['nom_ent']}</h3>
                            <small>{user_info.get('adresse','')}<br>{user_info.get('telephone','')}</small>
                        </div>
                        <div style="width:48%; text-align:right;">
                            <b style="color:#666;">CLIENT</b><br>
                            <b>{f['n']}</b><br>
                            <small>{f['t']}<br>{f['m']}<br>{f['a']}</small>
                        </div>
                    </div>
                    <hr style="margin:20px 0;">
                    <table style="width:100%;">
                        <tr><td><b>Désignation</b></td><td style="text-align:right;"><b>Total</b></td></tr>
                        <tr><td>{f['p']} ({f['pv']:,} x {f['q']})</td><td style="text-align:right;">{f['pv']*f['q']:,} {devise}</td></tr>
                        {f'<tr style="color:red;"><td>Rabais</td><td style="text-align:right;">- {f["r"]:,} {devise}</td></tr>' if f['r']>0 else ''}
                    </table>
                    <h2 style="text-align:right; color:#2E7D32; margin-top:20px;">NET À PAYER : {f['net']:,} {devise}</h2>
                </div>
                """, unsafe_allow_html=True)

# --- STOCK ---
elif menu == "📦 Stock":
    st.header("📦 Gestion Stock")
    res = db.table("produits").select("*").eq("user_id", user_id).execute().data
    if res:
        st.table(pd.DataFrame(res)[['nom', 'p_achat', 'p_vente', 'qte']])
    with st.expander("Ajouter un produit"):
        with st.form("st_f"):
            n, pa, pv, q = st.text_input("Nom"), st.number_input("Prix Achat"), st.number_input("Prix Vente"), st.number_input("Qté", min_value=1)
            if st.form_submit_button("Ajouter"):
                db.table("produits").insert({"user_id":user_id, "nom":n, "p_achat":pa, "p_vente":pv, "qte":q}).execute()
                st.rerun()

# --- DÉPENSES ---
elif menu == "💸 Dépenses":
    with st.form("dp_f"):
        m, mt = st.text_input("Motif"), st.number_input("Montant")
        if st.form_submit_button("OK"):
            db.table("depenses").insert({"user_id":user_id, "motif":m, "montant":mt}).execute()
            st.success("Enregistré")

# --- PARAMÈTRES ---
elif menu == "⚙️ Paramètres":
    st.header("⚙️ Configuration")
    with st.form("conf_f"):
        n_e = st.text_input("Nom Boutique", value=user_info['nom_ent'])
        addr = st.text_input("Adresse Boutique", value=user_info.get('adresse',''))
        tel = st.text_input("Téléphone", value=user_info.get('telephone',''))
        dev = st.selectbox("Devise", ["FG", "GNF", "FCFA", "EURO", "DOLLAR", "£", "$"], index=0)
        if st.form_submit_button("Sauvegarder"):
            db.table("users").update({"nom_ent":n_e, "adresse":addr, "telephone":tel, "devise":dev}).eq("id", user_id).execute()
            st.success("Paramètres mis à jour !")
            st.rerun()
