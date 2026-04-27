import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# CONFIGURATION
URL = "https://enikglfabczfpahbfzvq.supabase.co"
KEY = "sb_publishable_h169bGdSBk_SpbiXwH0KbQ_JE6Cm7lS"

@st.cache_resource
def init_db():
    return create_client(URL, KEY)

db = init_db()

st.set_page_config(page_title="VenteUp Pro", layout="wide")

if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# --- ACCÈS ---
if st.session_state['user_id'] is None:
    st.title("📈 VenteUp Pro")
    mode = st.radio("Action", ["Connexion", "Créer un compte"], horizontal=True)
    if mode == "Connexion":
        u = st.text_input("Pseudo").strip()
        p = st.text_input("Mot de passe", type="password").strip()
        if st.button("Se connecter", use_container_width=True):
            res = db.table("users").select("*").eq("username", u).eq("password", p).execute()
            if res.data:
                st.session_state['user_id'] = res.data[0]['id']
                st.rerun()
            else: st.error("Identifiants incorrects.")
    else:
        nu = st.text_input("Nouveau Pseudo")
        ne = st.text_input("Nom de la Boutique")
        np = st.text_input("Mot de passe", type="password")
        if st.button("S'inscrire"):
            db.table("users").insert({"username": nu, "password": np, "nom_ent": ne}).execute()
            st.success("Compte créé !")
    st.stop()

user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]

# --- SIDEBAR ---
with st.sidebar:
    st.header(f"🏪 {user_info.get('nom_ent')}")
    menu = st.radio("Menu", ["📊 Bilan", "📈 Statistiques", "🛒 Vendre", "📦 Stock", "💸 Dépenses", "⚙️ Paramètres"])
    st.divider()
    if st.button("🚪 Quitter"):
        st.session_state['user_id'] = None
        st.rerun()
    st.caption("✍️ Dev: ISSA DIALLO")
    st.caption("📧 issatanoudiallo2024@gmail.com")
    st.caption("📞 610 51 89 73")

# --- PAGES ---

if menu == "📊 Bilan":
    st.header("Bilan Financier")
    v = db.table("ventes").select("total").eq("user_id", user_id).execute().data
    d = db.table("depenses").select("montant").eq("user_id", user_id).execute().data
    
    recettes = sum([x['total'] for x in v])
    depenses = sum([x['montant'] for x in d])
    benefice = recettes - depenses
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Recettes Totales", f"{recettes:,} FG")
    c2.metric("Dépenses Totales", f"{depenses:,} FG", delta_color="inverse")
    c3.metric("Bénéfice Net", f"{benefice:,} FG")

elif menu == "📈 Statistiques":
    st.header("📈 Analyse des Ventes")
    v_data = db.table("ventes").select("created_at, total").eq("user_id", user_id).execute().data
    if v_data:
        df_v = pd.DataFrame(v_data)
        df_v['date'] = pd.to_datetime(df_v['created_at']).dt.date
        stats = df_v.groupby('date')['total'].sum()
        st.line_chart(stats)
    else:
        st.info("Aucune donnée statistique pour le moment.")

elif menu == "🛒 Vendre":
    st.header("🛒 Terminal de Vente")
    prods = db.table("produits").select("*").eq("user_id", user_id).gt("qte", 0).execute().data
    if prods:
        c1, c2 = st.columns([1, 1.3])
        with c1:
            with st.form("v_form"):
                nom_p = st.selectbox("Article", [x['nom'] for x in prods])
                qte = st.number_input("Quantité", min_value=1)
                st.markdown("**Infos Client**")
                cl_n = st.text_input("Nom du Client")
                cl_t = st.text_input("Téléphone")
                cl_m = st.text_input("Email")
                cl_a = st.text_input("Adresse")
                if st.form_submit_button("Générer Facture"):
                    p_s = [x for x in prods if x['nom'] == nom_p][0]
                    tot = qte * p_s['p_vente']
                    db.table("ventes").insert({"user_id":user_id, "nom_prod":nom_p, "qte_v":qte, "total":tot}).execute()
                    db.table("produits").update({"qte": p_s['qte'] - qte}).eq("id", p_s['id']).execute()
                    st.session_state['fact'] = {"n":cl_n, "t":cl_t, "m":cl_m, "a":cl_a, "p":nom_p, "q":qte, "pu":p_s['p_vente'], "tot":tot}
                    st.rerun()

        if 'fact' in st.session_state:
            f = st.session_state['fact']
            with c2:
                fact_html = f"""
                <div style="background:white; padding:25px; color:black; border:1px solid #ccc; border-radius:10px;">
                    <div style="display: flex; justify-content: space-between;">
                        <div style="text-align: left; width: 45%;">
                            <h3 style="margin:0;">{user_info.get('nom_ent')}</h3>
                            <p style="font-size:12px;">📍 {user_info.get('adresse', 'N/A')}<br>📞 {user_info.get('telephone', 'N/A')}</p>
                        </div>
                        <div style="text-align: right; width: 45%; border-left: 1px solid #eee; padding-left:10px;">
                            <h4 style="margin:0; color:gray;">CLIENT</h4>
                            <p style="font-size:13px;"><b>{f['n']}</b><br>{f['t']}<br>{f['m']}<br>{f['a']}</p>
                        </div>
                    </div>
                    <hr>
                    <table style="width:100%; border-collapse:collapse;">
                        <tr style="background:#f2f2f2;"><th>Article</th><th>Qté</th><th>Total</th></tr>
                        <tr><td>{f['p']}</td><td style="text-align:center;">{f['q']}</td><td style="text-align:right;">{f['tot']:,} FG</td></tr>
                    </table>
                    <h2 style="text-align:right; color:#2E7D32;">TOTAL : {f['tot']:,} FG</h2>
                </div>
                """
                st.markdown(fact_html, unsafe_allow_html=True)
                st.caption("Capture d'écran pour enregistrer l'image.")

elif menu == "📦 Stock":
    st.header("📦 Stock & Réapprovisionnement")
    res = db.table("produits").select("*").eq("user_id", user_id).execute().data
    if res:
        df = pd.DataFrame(res)
        alerte = df[df['qte'] <= 5]
        if not alerte.empty:
            st.error(f"⚠️ RÉAPPROVISIONNEMENT URGENT : {', '.join(alerte['nom'].tolist())}")
        st.table(df[['nom', 'p_vente', 'qte']])
    
    with st.expander("Ajouter un nouvel article"):
        with st.form("add"):
            n = st.text_input("Nom")
            pv = st.number_input("Prix Vente", min_value=0)
            q = st.number_input("Quantité", min_value=1)
            if st.form_submit_button("Enregistrer"):
                db.table("produits").insert({"user_id": user_id, "nom": n, "p_vente": pv, "qte": q}).execute()
                st.rerun()

elif menu == "💸 Dépenses":
    st.header("💸 Sorties de caisse")
    with st.form("dep"):
        m = st.text_input("Motif")
        mt = st.number_input("Montant", min_value=0)
        if st.form_submit_button("Enregistrer la dépense"):
            db.table("depenses").insert({"user_id": user_id, "motif": m, "montant": mt}).execute()
            st.success("Dépense enregistrée.")

elif menu == "⚙️ Paramètres":
    st.header("⚙️ Infos Boutique")
    with st.form("set"):
        nb = st.text_input("Nom Entreprise", value=user_info.get('nom_ent'))
        ad = st.text_input("Adresse", value=user_info.get('adresse'))
        tl = st.text_input("Téléphone", value=user_info.get('telephone'))
        if st.form_submit_button("Mettre à jour"):
            db.table("users").update({"nom_ent": nb, "adresse": ad, "telephone": tl}).eq("id", user_id).execute()
            st.success("Modifié !")
            st.rerun()
