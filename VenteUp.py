import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# CONFIG
URL = "https://enikglfabczfpahbfzvq.supabase.co"
KEY = "sb_publishable_h169bGdSBk_SpbiXwH0KbQ_JE6Cm7lS"

@st.cache_resource
def init_db():
    return create_client(URL, KEY)

db = init_db()
st.set_page_config(page_title="VenteUp Pro", layout="wide", page_icon="📈")

if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# --- ACCÈS ---
if st.session_state['user_id'] is None:
    st.title("🚀 VenteUp Pro")
    t1, t2 = st.tabs(["Connexion", "S'inscrire"])
    with t1:
        u = st.text_input("Pseudo").strip()
        p = st.text_input("Mot de passe", type="password").strip()
        if st.button("Se connecter", use_container_width=True):
            res = db.table("users").select("*").eq("username", u).eq("password", p).execute()
            if res.data:
                st.session_state['user_id'] = res.data[0]['id']
                st.rerun()
            else: st.error("Identifiants incorrects.")
    with t2:
        nu, ne, np = st.text_input("Nouveau Pseudo"), st.text_input("Nom Boutique"), st.text_input("Mot de passe", type="password")
        if st.button("Créer mon compte"):
            db.table("users").insert({"username":nu, "nom_ent":ne, "password":np}).execute()
            st.success("Compte créé ! Connectez-vous.")
    st.stop()

# --- RÉCUPÉRATION INFOS ---
user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]

with st.sidebar:
    st.header(f"🏪 {user_info['nom_ent']}")
    menu = st.radio("Menu", ["📊 Bilan", "📈 Statistiques", "🛒 Vendre", "📦 Stock", "💸 Dépenses", "⚙️ Paramètres"])
    st.divider()
    if st.button("🚪 Déconnexion"):
        st.session_state['user_id'] = None
        st.rerun()
    st.caption(f"✍️ Dev: ISSA DIALLO")
    st.caption(f"📧 issatanoudiallo2024@gmail.com")
    st.caption(f"📞 610 51 89 73")

# --- PAGES ---

if menu == "📊 Bilan":
    st.header("📊 Bilan Financier Global")
    v = db.table("ventes").select("total").eq("user_id", user_id).execute().data
    d = db.table("depenses").select("montant").eq("user_id", user_id).execute().data
    
    tot_v = sum([x['total'] for x in v])
    tot_d = sum([x['montant'] for x in d])
    benef = tot_v - tot_d
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Ventes Totales", f"{tot_v:,} FG")
    c2.metric("Dépenses Totales", f"{tot_d:,} FG", delta_color="inverse")
    c3.metric("Bénéfice Total", f"{benef:,} FG")

elif menu == "📈 Statistiques":
    st.header("📈 Analyse Graphique")
    
    # Stats Ventes
    v_data = db.table("ventes").select("created_at, total").eq("user_id", user_id).execute().data
    if v_data:
        st.subheader("Évolution des Ventes (Recettes)")
        df_v = pd.DataFrame(v_data)
        df_v['date'] = pd.to_datetime(df_v['created_at']).dt.date
        st.line_chart(df_v.groupby('date')['total'].sum())
    
    # Stats Dépenses
    d_data = db.table("depenses").select("created_at, montant").eq("user_id", user_id).execute().data
    if d_data:
        st.subheader("Évolution des Dépenses")
        df_d = pd.DataFrame(d_data)
        df_d['date'] = pd.to_datetime(df_d['created_at']).dt.date
        st.area_chart(df_d.groupby('date')['montant'].sum(), color="#FF4B4B")
    
    if not v_data and not d_data:
        st.info("Ajoutez des ventes ou des dépenses pour voir les graphiques.")

elif menu == "🛒 Vendre":
    st.header("🛒 Terminal de Vente")
    prods = db.table("produits").select("*").eq("user_id", user_id).gt("qte", 0).execute().data
    if prods:
        col1, col2 = st.columns([1, 1.2])
        with col1:
            with st.form("v_form"):
                p_n = st.selectbox("Article", [x['nom'] for x in prods])
                q = st.number_input("Quantité", min_value=1)
                st.markdown("**👤 Infos Client**")
                cn, ct, cm, ca = st.text_input("Nom"), st.text_input("Tel"), st.text_input("Email"), st.text_input("Adresse")
                if st.form_submit_button("Valider & Facturer"):
                    sel = [x for x in prods if x['nom'] == p_n][0]
                    total = q * sel['p_vente']
                    db.table("ventes").insert({"user_id":user_id, "nom_prod":p_n, "qte_v":q, "total":total}).execute()
                    db.table("produits").update({"qte": sel['qte'] - q}).eq("id", sel['id']).execute()
                    st.session_state['f'] = {"n":cn,"t":ct,"m":cm,"a":ca,"p":p_n,"q":q,"tot":total}
                    st.rerun()
        if 'f' in st.session_state:
            f = st.session_state['f']
            with col2:
                st.markdown(f"""
                <div style="background:white; color:black; padding:25px; border-radius:10px; border:1px solid #ddd;">
                    <div style="display:flex; justify-content:space-between;">
                        <div style="width:45%"><b>{user_info['nom_ent']}</b><br><small>{user_info.get('adresse','')}<br>{user_info.get('telephone','')}</small></div>
                        <div style="width:45%; text-align:right; border-left:1px solid #eee; padding-left:10px;">
                            <b style="color:gray;">CLIENT</b><br><b>{f['n']}</b><br><small>{f['t']}<br>{f['m']}<br>{f['a']}</small>
                        </div>
                    </div>
                    <hr>
                    <table style="width:100%">
                        <tr style="border-bottom:1px solid #eee;"><td><b>{f['p']}</b> x {f['q']}</td><td style="text-align:right;"><b>{f['tot']:,} FG</b></td></tr>
                    </table>
                    <h2 style="text-align:right; color:#2E7D32; margin-top:20px;">TOTAL: {f['tot']:,} FG</h2>
                </div>
                """, unsafe_allow_html=True)

elif menu == "📦 Stock":
    st.header("📦 Stock & Réapprovisionnement")
    res = db.table("produits").select("*").eq("user_id", user_id).execute().data
    if res:
        df = pd.DataFrame(res)
        alerte = df[df['qte'] <= 5]
        if not alerte.empty:
            st.error(f"⚠️ RÉAPPROVISIONNEMENT NÉCESSAIRE : {', '.join(alerte['nom'].tolist())}")
        st.table(df[['nom', 'p_vente', 'qte']])
    with st.expander("Ajouter un article"):
        with st.form("add"):
            n, v, q = st.text_input("Nom"), st.number_input("Prix"), st.number_input("Qté", min_value=1)
            if st.form_submit_button("Enregistrer"):
                db.table("produits").insert({"user_id":user_id,"nom":n,"p_vente":v,"qte":q}).execute()
                st.rerun()

elif menu == "💸 Dépenses":
    st.header("💸 Sorties de caisse")
    with st.form("d"):
        m, mt = st.text_input("Motif de la dépense"), st.number_input("Montant (FG)", min_value=0)
        if st.form_submit_button("Enregistrer"):
            db.table("depenses").insert({"user_id":user_id, "motif":m, "montant":mt}).execute()
            st.success("Dépense enregistrée !")

elif menu == "⚙️ Paramètres":
    st.header("⚙️ Infos de la Boutique")
    with st.form("p"):
        ne, ad, tl = st.text_input("Nom", value=user_info['nom_ent']), st.text_input("Adresse", value=user_info.get('adresse','')), st.text_input("Tel", value=user_info.get('telephone',''))
        if st.form_submit_button("Sauvegarder"):
            db.table("users").update({"nom_ent":ne, "adresse":ad, "telephone":tl}).eq("id", user_id).execute()
            st.rerun()
