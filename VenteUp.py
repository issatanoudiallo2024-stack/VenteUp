import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# CONFIGURATION SUPABASE
URL = "https://enikglfabczfpahbfzvq.supabase.co"
KEY = "sb_publishable_h169bGdSBk_SpbiXwH0KbQ_JE6Cm7lS"

@st.cache_resource
def init_db():
    return create_client(URL, KEY)

db = init_db()

st.set_page_config(page_title="VenteUp Pro", layout="wide")

if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# --- CONNEXION / INSCRIPTION ---
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

# --- INFOS UTILISATEUR ---
user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]

# --- MENU LATÉRAL ---
with st.sidebar:
    st.header(f"🏪 {user_info.get('nom_ent')}")
    menu = st.radio("Menu", ["📊 Bilan", "🛒 Vendre", "📦 Stock", "💸 Dépenses", "⚙️ Paramètres"])
    st.divider()
    if st.button("🚪 Quitter"):
        st.session_state['user_id'] = None
        st.rerun()
    st.caption("✍️ Dev: ISSA DIALLO")
    st.caption("📧 issatanoudiallo2024@gmail.com")
    st.caption("📞 610 51 89 73")

# --- PAGES ---

if menu == "⚙️ Paramètres":
    st.header("⚙️ Configuration de la Boutique")
    st.info("Ces informations apparaîtront sur vos factures.")
    with st.form("settings"):
        new_nom = st.text_input("Nom de l'entreprise", value=user_info.get('nom_ent', ''))
        adresse = st.text_input("Adresse", value=user_info.get('adresse', ''))
        tel = st.text_input("Téléphone", value=user_info.get('telephone', ''))
        if st.form_submit_button("Enregistrer les réglages"):
            db.table("users").update({"nom_ent": new_nom, "adresse": adresse, "telephone": tel}).eq("id", user_id).execute()
            st.success("Paramètres mis à jour !")
            st.rerun()

elif menu == "🛒 Vendre":
    st.header("🛒 Terminal de Vente")
    prods = db.table("produits").select("*").eq("user_id", user_id).gt("qte", 0).execute().data
    if prods:
        c1, c2 = st.columns([1, 1.2])
        with c1:
            with st.form("vente_form"):
                nom_p = st.selectbox("Article", [x['nom'] for x in prods])
                qte = st.number_input("Quantité", min_value=1)
                st.markdown("---")
                st.markdown("**Infos Client**")
                client_n = st.text_input("Nom du Client", "Passager")
                client_t = st.text_input("Téléphone Client")
                if st.form_submit_button("Valider la vente"):
                    p_sel = [x for x in prods if x['nom'] == nom_p][0]
                    total = qte * p_sel['p_vente']
                    db.table("ventes").insert({"user_id":user_id, "nom_prod":nom_p, "qte_v":qte, "total":total}).execute()
                    db.table("produits").update({"qte": p_sel['qte'] - qte}).eq("id", p_sel['id']).execute()
                    st.session_state['derniere_facture'] = {"c":client_n, "ct":client_t, "p":nom_p, "q":qte, "pu":p_sel['p_vente'], "tot":total}
                    st.rerun()
        
        if 'derniere_facture' in st.session_state:
            f = st.session_state['derniere_facture']
            with c2:
                st.markdown(f"""
                <div style="background:white; padding:20px; color:black; border-radius:10px; border:2px solid #eee;">
                    <center><h2>{user_info.get('nom_ent')}</h2>
                    <p>{user_info.get('adresse', '')} | Tel: {user_info.get('telephone', '')}</p></center>
                    <hr>
                    <p><b>Client :</b> {f['c']} ({f['ct']})</p>
                    <p><b>Date :</b> {datetime.now().strftime('%d/%m/%Y')}</p>
                    <table style="width:100%">
                        <tr><td>{f['p']} x {f['q']}</td><td style="text-align:right">{f['tot']:,} FG</td></tr>
                    </table>
                    <hr>
                    <h3 style="text-align:right">TOTAL : {f['tot']:,} FG</h3>
                    <center><p style="font-size:10px">Merci de votre confiance !</p></center>
                </div>
                """, unsafe_allow_html=True)
                st.info("💡 Pour enregistrer : Faire une capture d'écran ou Imprimer (Ctrl+P)")

elif menu == "📦 Stock":
    st.header("📦 Gestion du Stock")
    tab_s1, tab_s2 = st.tabs(["Inventaire", "Ajouter Produit"])
    
    with tab_s2:
        with st.form("add"):
            n = st.text_input("Nom article")
            pv = st.number_input("Prix de vente", min_value=0)
            q = st.number_input("Quantité initiale", min_value=1)
            if st.form_submit_button("Ajouter"):
                db.table("produits").insert({"user_id": user_id, "nom": n, "p_vente": pv, "qte": q}).execute()
                st.rerun()

    with tab_s1:
        res = db.table("produits").select("*").eq("user_id", user_id).execute().data
        if res:
            df = pd.DataFrame(res)
            # Alerte réapprovisionnement
            low_stock = df[df['qte'] <= 5]
            if not low_stock.empty:
                st.warning(f"⚠️ RÉAPPROVISIONNEMENT NÉCESSAIRE pour : {', '.join(low_stock['nom'].tolist())}")
            st.table(df[['nom', 'p_vente', 'qte']])

elif menu == "📊 Bilan":
    st.header("Bilan financier")
    v = db.table("ventes").select("total").eq("user_id", user_id).execute().data
    total = sum([x['total'] for x in v])
    st.metric("Chiffre d'Affaires", f"{total:,} FG")

elif menu == "💸 Dépenses":
    st.header("💸 Dépenses")
    m = st.text_input("Motif")
    mt = st.number_input("Montant", min_value=0)
    if st.button("Enregistrer"):
        db.table("depenses").insert({"user_id": user_id, "motif": m, "montant": mt}).execute()
        st.success("Enregistré")
