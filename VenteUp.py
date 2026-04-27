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
                st.error("Identifiants incorrects.")
    with t2:
        nu = st.text_input("Nouveau Pseudo", key="s_u")
        ne = st.text_input("Nom de la Boutique", key="s_e")
        np = st.text_input("Mot de passe", type="password", key="s_p")
        if st.button("S'inscrire", use_container_width=True):
            try:
                db.table("users").insert({"username": nu.strip(), "password": np.strip(), "nom_ent": ne}).execute()
                st.success("Compte créé ! Connectez-vous.")
            except:
                st.error("Erreur d'inscription.")
    st.stop()

# --- INFOS BOUTIQUE ---
user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]

with st.sidebar:
    st.header(f"🏪 {user_info.get('nom_ent')}")
    menu = st.radio("Navigation", ["📊 Dashboard", "🛒 Caisse & Facture", "📦 Stock", "💸 Dépenses", "⚙️ Paramètres"])
    st.divider()
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state['user_id'] = None
        st.rerun()
    st.caption(f"🛠️ Développeur : **ISSA DIALLO**")
    st.caption(f"📞 610 51 89 73")
    st.caption(f"📧 issatanoudiallo2024@gmail.com")

# --- PAGES ---

if menu == "⚙️ Paramètres":
    st.title("⚙️ Configuration de la Boutique")
    with st.form("settings"):
        n_b = st.text_input("Nom de la Boutique", value=user_info.get('nom_ent', ''))
        a_b = st.text_input("Adresse", value=user_info.get('adresse', ''))
        t_b = st.text_input("Téléphone", value=user_info.get('telephone', ''))
        e_b = st.text_input("Email de la boutique", value=user_info.get('email_boutique', ''))
        if st.form_submit_button("Sauvegarder"):
            db.table("users").update({"nom_ent": n_b, "adresse": a_b, "telephone": t_b, "email_boutique": e_b}).eq("id", user_id).execute()
            st.success("Paramètres mis à jour !")

elif menu == "🛒 Caisse & Facture":
    st.title("🛒 Caisse")
    prods = db.table("produits").select("*").eq("user_id", user_id).gt("qte", 0).execute().data
    if prods:
        c1, c2 = st.columns([1, 1.3])
        with c1:
            with st.form("v_form"):
                p_n = st.selectbox("Article", [x['nom'] for x in prods])
                q = st.number_input("Quantité", min_value=1)
                rabais = st.number_input("Rabais / Remise (FG)", min_value=0)
                st.markdown("**👤 Infos Client**")
                cl_n = st.text_input("Nom Client", "Passager")
                cl_t = st.text_input("Téléphone Client")
                cl_a = st.text_input("Adresse Client")
                cl_m = st.text_input("Email Client")
                etat = st.selectbox("Statut de paiement", ["PAYÉ", "NON PAYÉ"])
                if st.form_submit_button("Générer Facture"):
                    p_i = [x for x in prods if x['nom'] == p_n][0]
                    total_brut = q * p_i['p_vente']
                    total_net = total_brut - rabais
                    db.table("ventes").insert({"user_id": user_id, "nom_prod": p_n, "qte_v": q, "total": total_net}).execute()
                    db.table("produits").update({"qte": p_i['qte'] - q}).eq("id", p_i['id']).execute()
                    st.session_state['f'] = {"n":cl_n,"t":cl_t,"a":cl_a,"m":cl_m,"p":p_n,"q":q,"pu":p_i['p_vente'],"brut":total_brut,"net":total_net,"r":rabais,"e":etat}
                    st.rerun()

        if 'f' in st.session_state:
            f = st.session_state['f']
            with c2:
                facture_html = f"""
                <div style="background: white; padding: 25px; color: black; border-radius: 10px; border: 1px solid #ddd;">
                    <div style="display: flex; justify-content: space-between;">
                        <div style="width: 45%;">
                            <h3 style="margin:0; color:#1E88E5;">{user_info.get('nom_ent')}</h3>
                            <p style="font-size:12px; margin:2px;">📍 {user_info.get('adresse', 'N/A')}</p>
                            <p style="font-size:12px; margin:2px;">📞 {user_info.get('telephone', 'N/A')}</p>
                            <p style="font-size:12px; margin:2px;">✉️ {user_info.get('email_boutique', 'N/A')}</p>
                        </div>
                        <div style="width: 45%; text-align: right;">
                            <h4 style="margin:0;">CLIENT</h4>
                            <p style="font-size:12px; margin:2px;"><b>{f['n']}</b></p>
                            <p style="font-size:12px; margin:2px;">{f['t']}</p>
                            <p style="font-size:12px; margin:2px;">{f['a']}</p>
                            <p style="font-size:12px; margin:2px;">{f['m']}</p>
                        </div>
                    </div>
                    <hr>
                    <p style="font-size:12px;"><b>Date :</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                    <table style="width:100%; border-collapse: collapse;">
                        <tr style="background:#f4f4f4;">
                            <th style="text-align:left; padding:8px;">Article</th>
                            <th style="text-align:center;">Qté</th>
                            <th style="text-align:right; padding:8px;">Total</th>
                        </tr>
                        <tr>
                            <td style="padding:8px; border-bottom:1px solid #eee;">{f['p']}</td>
                            <td style="text-align:center; border-bottom:1px solid #eee;">{f['q']}</td>
                            <td style="text-align:right; padding:8px; border-bottom:1px solid #eee;">{f['brut']:,} FG</td>
                        </tr>
                    </table>
                    <div style="text-align:right; margin-top:10px;">
                        <p style="margin:2px;">Rabais : -{f['r']:,} FG</p>
                        <h2 style="margin:0; color:#1E88E5;">NET : {f['net']:,} FG</h2>
                    </div>
                    <div style="margin-top:20px; border:3px solid {'green' if f['e']=='PAYÉ' else 'red'}; color:{'green' if f['e']=='PAYÉ' else 'red'}; width:fit-content; padding:5px 15px; font-weight:bold; transform:rotate(-5deg); font-size:20px;">
                        {f['e']}
                    </div>
                    <div style="margin-top:40px; text-align:center; font-size:10px; color:gray; border-top:1px solid #eee; padding-top:10px;">
                        Logiciel par ISSA DIALLO (610 51 89 73) | issatanoudiallo2024@gmail.com
                    </div>
                </div>
                """
                st.markdown(facture_html, unsafe_allow_html=True)
                if st.button("Nouvelle Vente"):
                    del st.session_state['f']
                    st.rerun()
    else: st.warning("Stock vide.")

elif menu == "📊 Dashboard":
    st.title("Dashboard")
    v = db.table("ventes").select("total").eq("user_id", user_id).execute().data
    d = db.table("depenses").select("montant").eq("user_id", user_id).execute().data
    tv, td = sum([x['total'] for x in v]), sum([x['montant'] for x in d])
    c1, c2, c3 = st.columns(3)
    c1.metric("Recettes", f"{tv:,} FG")
    c2.metric("Dépenses", f"{td:,} FG")
    c3.metric("Bénéfice", f"{tv-td:,} FG")

elif menu == "📦 Stock":
    st.title("Stock")
    with st.form("s_f"):
        n, pa, pv, qt = st.text_input("Article"), st.number_input("Prix Achat"), st.number_input("Prix Vente"), st.number_input("Qté", 1)
        if st.form_submit_button("Ajouter"):
            db.table("produits").insert({"user_id": user_id, "nom": n, "p_achat": pa, "p_vente": pv, "qte": qt}).execute()
            st.success("Ajouté !")
    res = db.table("produits").select("*").eq("user_id", user_id).execute().data
    if res: st.dataframe(pd.DataFrame(res)[['nom', 'p_achat', 'p_vente', 'qte']])

elif menu == "💸 Dépenses":
    st.title("Dépenses")
    with st.form("d_f"):
        m, mt = st.text_input("Motif"), st.number_input("Montant")
        if st.form_submit_button("Enregistrer"):
            db.table("depenses").insert({"user_id": user_id, "motif": m, "montant": mt}).execute()
            st.success("Enregistré !")
