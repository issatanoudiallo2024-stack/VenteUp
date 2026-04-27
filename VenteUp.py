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
                st.error("Erreur : Ce pseudo existe déjà ou le RLS est activé.")
    st.stop()

# RÉCUPÉRATION INFOS
user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]

# --- MENU LATÉRAL ---
with st.sidebar:
    st.header(f"🏪 {user_info.get('nom_ent')}")
    menu = st.radio("Navigation", ["📊 Dashboard", "🛒 Caisse", "📦 Stock", "💸 Dépenses", "⚙️ Paramètres", "ℹ️ À propos"])
    st.divider()
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state['user_id'] = None
        st.rerun()
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.caption(f"🛠️ Dev: ISSA DIALLO")
    st.caption(f"📞 610 51 89 73")

# --- PAGES ---

if menu == "ℹ️ À propos":
    st.title("ℹ️ Informations Développeur")
    st.info("Ce projet est une preuve de concept originale développée pour le dossier universitaire d'Issa Diallo.")
    st.write("**Développeur :** ISSA DIALLO (Étudiant L1 Informatique - UGANC)")
    st.write("**Contact :** issatanoudiallo2024@gmail.com")
    st.write("**Technos :** Python, Streamlit, PostgreSQL (Supabase)")

elif menu == "⚙️ Paramètres":
    st.title("⚙️ Paramètres de la Boutique")
    with st.form("settings"):
        n_b = st.text_input("Nom de la Boutique", value=user_info.get('nom_ent', ''))
        a_b = st.text_input("Adresse", value=user_info.get('adresse', ''))
        t_b = st.text_input("Téléphone", value=user_info.get('telephone', ''))
        e_b = st.text_input("Email Boutique", value=user_info.get('email_boutique', ''))
        if st.form_submit_button("Sauvegarder"):
            db.table("users").update({"nom_ent": n_b, "adresse": a_b, "telephone": t_b, "email_boutique": e_b}).eq("id", user_id).execute()
            st.success("Paramètres mis à jour !")

elif menu == "🛒 Caisse":
    st.title("🛒 Caisse & Facturation")
    prods = db.table("produits").select("*").eq("user_id", user_id).gt("qte", 0).execute().data
    if prods:
        c1, c2 = st.columns([1, 1.3])
        with c1:
            with st.form("v_form"):
                p_n = st.selectbox("Article", [x['nom'] for x in prods])
                q = st.number_input("Quantité", min_value=1)
                remise = st.number_input("Remise / Rabais (FG)", min_value=0)
                st.markdown("**👤 Client**")
                cl_n = st.text_input("Nom Client", "Passager")
                cl_t = st.text_input("Téléphone")
                cl_a = st.text_input("Adresse")
                cl_m = st.text_input("Email")
                etat = st.selectbox("Statut", ["PAYÉ", "NON PAYÉ"])
                if st.form_submit_button("Générer Facture"):
                    p_i = [x for x in prods if x['nom'] == p_n][0]
                    total = (q * p_i['p_vente']) - remise
                    db.table("ventes").insert({"user_id": user_id, "nom_prod": p_n, "qte_v": q, "total": total}).execute()
                    db.table("produits").update({"qte": p_i['qte'] - q}).eq("id", p_i['id']).execute()
                    st.session_state['facture'] = {"n":cl_n,"t":cl_t,"a":cl_a,"m":cl_m,"p":p_n,"q":q,"pu":p_i['p_vente'],"tot":total,"r":remise,"e":etat}
                    st.rerun()

        if 'facture' in st.session_state:
            f = st.session_state['facture']
            with c2:
                # FACTURE SANS NOM DE DÉVELOPPEUR (100% CLIENT)
                facture_html = f"""
                <div style="background: white; padding: 25px; color: black; border: 1px solid #ddd; border-radius: 10px;">
                    <div style="display: flex; justify-content: space-between;">
                        <div style="width: 50%;">
                            <h3 style="margin:0; color:#1E88E5;">{user_info.get('nom_ent')}</h3>
                            <p style="font-size:12px; margin:2px;">📍 {user_info.get('adresse', 'N/A')}</p>
                            <p style="font-size:12px; margin:2px;">📞 {user_info.get('telephone', 'N/A')}</p>
                            <p style="font-size:12px; margin:2px;">✉️ {user_info.get('email_boutique', 'N/A')}</p>
                        </div>
                        <div style="width: 45%; text-align: right;">
                            <h4 style="margin:0; color: gray;">CLIENT</h4>
                            <p style="font-size:13px; margin:2px;"><b>{f['n']}</b></p>
                            <p style="font-size:12px; margin:2px;">{f['t']}</p>
                            <p style="font-size:12px; margin:2px;">{f['a']}</p>
                            <p style="font-size:12px; margin:2px;">{f['m']}</p>
                        </div>
                    </div>
                    <hr>
                    <table style="width:100%; border-collapse: collapse; margin-top: 10px;">
                        <tr style="background:#f9f9f9; font-size:13px;">
                            <th style="text-align:left; padding:8px;">Désignation</th>
                            <th style="text-align:center;">Qté</th>
                            <th style="text-align:right; padding:8px;">Total</th>
                        </tr>
                        <tr style="font-size:14px;">
                            <td style="padding:10px; border-bottom:1px solid #eee;">{f['p']}</td>
                            <td style="text-align:center; border-bottom:1px solid #eee;">{f['q']}</td>
                            <td style="text-align:right; padding:10px; border-bottom:1px solid #eee;">{f['tot']:,} FG</td>
                        </tr>
                    </table>
                    <div style="text-align:right; margin-top:10px;">
                        <p style="margin:0; font-size:12px;">Rabais : -{f['r']:,} FG</p>
                        <h2 style="margin:5px 0; color:#1E88E5;">NET À PAYER : {f['tot']:,} FG</h2>
                    </div>
                    <div style="border:3px solid {'green' if f['e']=='PAYÉ' else 'red'}; color:{'green' if f['e']=='PAYÉ' else 'red'}; width:fit-content; padding:5px 15px; font-weight:bold; transform:rotate(-10deg); font-size:22px; margin-top:10px;">
                        {f['e']}
                    </div>
                </div>
                """
                st.markdown(facture_html, unsafe_allow_html=True)
                if st.button("Nouvelle Vente"):
                    del st.session_state['facture']
                    st.rerun()
    else: st.warning("Stock vide.")

elif menu == "📊 Dashboard":
    st.title("Dashboard")
    v = db.table("ventes").select("total").eq("user_id", user_id).execute().data
    d = db.table("depenses").select("montant").eq("user_id", user_id).execute().data
    tv, td = sum([x['total'] for x in v]), sum([x['montant'] for x in d])
    col1, col2, col3 = st.columns(3)
    col1.metric("Recettes", f"{tv:,} FG")
    col2.metric("Dépenses", f"{td:,} FG")
    col3.metric("Bénéfice", f"{tv-td:,} FG")

elif menu == "📦 Stock":
    st.title("Inventaire")
    with st.form("s_f"):
        n, pa, pv, qt = st.text_input("Article"), st.number_input("Prix Achat"), st.number_input("Prix Vente"), st.number_input("Quantité", 1)
        if st.form_submit_button("Ajouter"):
            db.table("produits").insert({"user_id": user_id, "nom": n, "p_achat": pa, "p_vente": pv, "qte": qt}).execute()
            st.success("Produit ajouté !")
    res = db.table("produits").select("*").eq("user_id", user_id).execute().data
    if res: st.dataframe(pd.DataFrame(res)[['nom', 'p_achat', 'p_vente', 'qte']])

elif menu == "💸 Dépenses":
    st.title("Dépenses")
    with st.form("d_f"):
        m, mt = st.text_input("Motif"), st.number_input("Montant")
        if st.form_submit_button("Enregistrer"):
            db.table("depenses").insert({"user_id": user_id, "motif": m, "montant": mt}).execute()
            st.success("Dépense enregistrée !")
