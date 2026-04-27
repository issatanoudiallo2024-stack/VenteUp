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

# --- RÉCUPÉRATION INFOS BOUTIQUE ---
user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]

# --- MENU LATÉRAL ---
with st.sidebar:
    st.header(f"🏪 {user_info.get('nom_ent', 'Ma Boutique')}")
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
    st.title("⚙️ Paramètres de la Boutique")
    with st.form("form_settings"):
        nom_b = st.text_input("Nom de la Boutique", value=user_info.get('nom_ent', ''))
        adr_b = st.text_input("Adresse Géographique", value=user_info.get('adresse', ''))
        tel_b = st.text_input("Téléphone Boutique", value=user_info.get('telephone', ''))
        if st.form_submit_button("Enregistrer les modifications"):
            db.table("users").update({"nom_ent": nom_b, "adresse": adr_b, "telephone": tel_b}).eq("id", user_id).execute()
            st.success("Paramètres mis à jour !")

elif menu == "🛒 Caisse & Facture":
    st.title("🛒 Terminal de Vente")
    prods = db.table("produits").select("*").eq("user_id", user_id).gt("qte", 0).execute().data
    
    if prods:
        c1, c2 = st.columns([1, 1.2])
        with c1:
            with st.form("v_form"):
                p_n = st.selectbox("Article", [x['nom'] for x in prods])
                q = st.number_input("Quantité", min_value=1)
                st.markdown("**👤 Client**")
                cl_n = st.text_input("Nom Client", "Passager")
                cl_t = st.text_input("Téléphone Client")
                cachet = st.checkbox("Appliquer cachet 'PAYÉ'", value=True)
                if st.form_submit_button("Générer la Facture"):
                    p_i = [x for x in prods if x['nom'] == p_n][0]
                    total = q * p_i['p_vente']
                    db.table("ventes").insert({"user_id": user_id, "nom_prod": p_n, "qte_v": q, "total": total}).execute()
                    db.table("produits").update({"qte": p_i['qte'] - q}).eq("id", p_i['id']).execute()
                    st.session_state['facture'] = {"n": cl_n, "t": cl_t, "p": p_n, "q": q, "pu": p_i['p_vente'], "tot": total, "c": cachet}
                    st.rerun()

        if 'facture' in st.session_state:
            f = st.session_state['facture']
            with c2:
                # Design de la facture optimisé pour capture d'écran
                facture_style = f"""
                <div style="background-color: white; padding: 30px; border: 2px solid #EEE; color: black; font-family: sans-serif; border-radius: 10px;">
                    <h1 style="text-align:center; color: #1E88E5; margin-bottom: 5px;">{user_info.get('nom_ent')}</h1>
                    <p style="text-align:center; margin: 0;">📍 {user_info.get('adresse', 'Conakry, Guinée')}</p>
                    <p style="text-align:center; margin: 0;">📞 {user_info.get('telephone', '+224 -- -- --')}</p>
                    <hr style="margin: 20px 0;">
                    <p><b>Date :</b> {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
                    <p><b>Client :</b> {f['n']} {f'({f["t"]})' if f['t'] else ''}</p>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                        <thead>
                            <tr style="background-color: #F5F5F5;">
                                <th style="text-align: left; padding: 10px; border-bottom: 2px solid #DDD;">Article</th>
                                <th style="text-align: center; padding: 10px; border-bottom: 2px solid #DDD;">Qté</th>
                                <th style="text-align: right; padding: 10px; border-bottom: 2px solid #DDD;">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="padding: 15px 10px; border-bottom: 1px solid #EEE;">{f['p']}</td>
                                <td style="text-align: center; padding: 15px 10px; border-bottom: 1px solid #EEE;">{f['q']}</td>
                                <td style="text-align: right; padding: 15px 10px; border-bottom: 1px solid #EEE;">{f['tot']:,} FG</td>
                            </tr>
                        </tbody>
                    </table>
                    <h2 style="text-align: right; margin-top: 20px;">NET À PAYER : {f['tot']:,} FG</h2>
                    {"<div style='color:red; border:4px solid red; padding:10px; width:120px; text-align:center; font-weight:bold; font-size:24px; transform: rotate(-15deg); margin-top: -30px; opacity: 0.8;'>PAYÉ</div>" if f['c'] else ""}
                    <div style="margin-top: 50px; text-align: center; font-size: 10px; color: #888;">
                        <p>Logiciel conçu par ISSA DIALLO (610 51 89 73)</p>
                    </div>
                </div>
                """
                st.markdown(facture_style, unsafe_allow_html=True)
                st.info("💡 Conseil : Pour enregistrer la facture, faites une capture d'écran de la zone blanche ci-dessus.")
                if st.button("✨ Nouvelle Vente"):
                    del st.session_state['facture']
                    st.rerun()

elif menu == "📊 Dashboard":
    st.title("Tableau de bord")
    # ... (reste du code Dashboard identique)
