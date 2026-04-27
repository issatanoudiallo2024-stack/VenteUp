import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# --- CONFIGURATION SUPABASE ---
URL = "https://enikglfabczfpahbfzvq.supabase.co"
KEY = "sb_publishable_h169bGdSBk_SpbiXwH0KbQ_JE6Cm7lS"

@st.cache_resource
def init_db():
    return create_client(URL, KEY)

db = init_db()
st.set_page_config(page_title="VenteUp Pro", layout="wide", page_icon="🚀")

# Initialisation de la session
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# --- ECRAN D'ACCÈS (CONNEXION / INSCRIPTION) ---
if st.session_state['user_id'] is None:
    st.title("🚀 VenteUp Pro")
    t1, t2 = st.tabs(["Connexion", "S'inscrire"])
    
    with t1:
        u_log = st.text_input("Pseudo", key="input_u_login").strip()
        p_log = st.text_input("Mot de passe", type="password", key="input_p_login").strip()
        if st.button("Se connecter", key="btn_login_final", use_container_width=True):
            res = db.table("users").select("*").eq("username", u_log).eq("password", p_log).execute()
            if res.data:
                st.session_state['user_id'] = res.data[0]['id']
                st.rerun()
            else:
                st.error("Pseudo ou mot de passe incorrect.")
            
    with t2:
        nu = st.text_input("Choisir un Pseudo", key="input_u_reg").strip()
        ne = st.text_input("Nom de la Boutique", key="input_e_reg").strip()
        np = st.text_input("Choisir un Mot de passe", type="password", key="input_p_reg").strip()
        if st.button("Créer mon compte", key="btn_reg_final", use_container_width=True):
            try:
                db.table("users").insert({"username":nu, "nom_ent":ne, "password":np}).execute()
                st.success("Compte créé ! Connectez-vous maintenant.")
            except:
                st.error("Erreur : Ce pseudo est déjà utilisé.")
    st.stop()

# --- RÉCUPÉRATION DES DONNÉES UTILISATEUR ---
user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.header(f"🏪 {user_info['nom_ent']}")
    menu = st.radio("Menu", ["📊 Bilan", "📈 Statistiques", "🛒 Vendre", "📦 Stock", "💸 Dépenses", "⚙️ Paramètres"])
    st.divider()
    if st.button("🚪 Déconnexion", key="btn_logout_final"):
        st.session_state['user_id'] = None
        st.rerun()
    st.caption("✍️ Dev: ISSA DIALLO")
    st.caption("📧 issatanoudiallo2024@gmail.com")

# --- 1. PAGE BILAN ---
if menu == "📊 Bilan":
    st.header("📊 Bilan Financier")
    v_bilan = db.table("ventes").select("total").eq("user_id", user_id).execute().data
    d_bilan = db.table("depenses").select("montant").eq("user_id", user_id).execute().data
    
    tot_recettes = sum([x['total'] for x in v_bilan])
    tot_depenses = sum([x['montant'] for x in d_bilan])
    benefice = tot_recettes - tot_depenses
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Ventes Totales", f"{tot_recettes:,} FG")
    c2.metric("Dépenses Totales", f"{tot_depenses:,} FG", delta_color="inverse")
    c3.metric("Bénéfice Net", f"{benefice:,} FG")

# --- 2. PAGE STATISTIQUES ---
elif menu == "📈 Statistiques":
    st.header("📈 Statistiques Graphiques")
    v_data = db.table("ventes").select("created_at, total").eq("user_id", user_id).execute().data
    d_data = db.table("depenses").select("created_at, montant").eq("user_id", user_id).execute().data
    
    if v_data:
        st.subheader("Courbe des Recettes")
        df_v = pd.DataFrame(v_data)
        df_v['date'] = pd.to_datetime(df_v['created_at']).dt.date
        st.line_chart(df_v.groupby('date')['total'].sum())
    
    if d_data:
        st.subheader("Courbe des Dépenses")
        df_d = pd.DataFrame(d_data)
        df_d['date'] = pd.to_datetime(df_d['created_at']).dt.date
        st.area_chart(df_d.groupby('date')['montant'].sum(), color="#FF4B4B")

# --- 3. PAGE VENDRE (TERMINAL & FACTURE) ---
elif menu == "🛒 Vendre":
    st.header("🛒 Terminal de Vente")
    prods = db.table("produits").select("*").eq("user_id", user_id).gt("qte", 0).execute().data
    if prods:
        col_form, col_fact = st.columns([1, 1.2])
        with col_form:
            with st.form("form_vente_final"):
                article_nom = st.selectbox("Sélectionner l'article", [x['nom'] for x in prods])
                quantite_v = st.number_input("Quantité", min_value=1, value=1)
                st.markdown("**👤 Information Client**")
                c_nom = st.text_input("Nom Client")
                c_tel = st.text_input("Téléphone")
                c_mail = st.text_input("Email")
                c_adr = st.text_input("Adresse")
                if st.form_submit_button("Valider la Vente"):
                    sel_prod = [x for x in prods if x['nom'] == article_nom][0]
                    total_v = quantite_v * sel_prod['p_vente']
                    # Enregistrement
                    db.table("ventes").insert({"user_id":user_id, "nom_prod":article_nom, "qte_v":quantite_v, "total":total_v}).execute()
                    db.table("produits").update({"qte": sel_prod['qte'] - quantite_v}).eq("id", sel_prod['id']).execute()
                    # Sauvegarde pour facture
                    st.session_state['last_facture'] = {"n":c_nom, "t":c_tel, "m":c_mail, "a":c_adr, "p":article_nom, "q":quantite_v, "tot":total_v}
                    st.rerun()
        
        if 'last_facture' in st.session_state:
            f = st.session_state['last_facture']
            with col_fact:
                st.markdown(f"""
                <div style="background:white; color:black; padding:20px; border-radius:10px; border:1px solid #ddd;">
                    <div style="display:flex; justify-content:space-between;">
                        <div style="width:48%"><b>{user_info['nom_ent']}</b><br><small>{user_info.get('adresse','')}<br>{user_info.get('telephone','')}</small></div>
                        <div style="width:48%; text-align:right; border-left:1px solid #eee; padding-left:10px;">
                            <b style="color:gray;">FACTURÉ À</b><br><b>{f['n']}</b><br><small>{f['t']}<br>{f['m']}<br>{f['a']}</small>
                        </div>
                    </div>
                    <hr>
                    <table style="width:100%">
                        <tr style="border-bottom:1px solid #eee;"><td><b>{f['p']}</b> x {f['q']}</td><td style="text-align:right;"><b>{f['tot']:,} FG</b></td></tr>
                    </table>
                    <h2 style="text-align:right; color:#2E7D32; margin-top:20px;">TOTAL: {f['tot']:,} FG</h2>
                    <center><small>Généré par VenteUp Pro</small></center>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("Aucun produit en stock.")

# --- 4. PAGE STOCK ---
elif menu == "📦 Stock":
    st.header("📦 Gestion du Stock")
    res_stock = db.table("produits").select("*").eq("user_id", user_id).execute().data
    if res_stock:
        df_stock = pd.DataFrame(res_stock)
        low_items = df_stock[df_stock['qte'] <= 5]
        if not low_items.empty:
            st.error(f"⚠️ RÉAPPROVISIONNEMENT NÉCESSAIRE : {', '.join(low_items['nom'].tolist())}")
        st.table(df_stock[['nom', 'p_vente', 'qte']])
    
    with st.expander("Ajouter un article au stock"):
        with st.form("form_add_stock"):
            nom_art = st.text_input("Nom de l'article")
            prix_art = st.number_input("Prix de vente (FG)", min_value=0)
            qte_art = st.number_input("Quantité en stock", min_value=1)
            if st.form_submit_button("Enregistrer le produit"):
                db.table("produits").insert({"user_id":user_id, "nom":nom_art, "p_vente":prix_art, "qte":qte_art}).execute()
                st.rerun()

# --- 5. PAGE DÉPENSES ---
elif menu == "💸 Dépenses":
    st.header("💸 Sorties de caisse")
    with st.form("form_depense"):
        motif_d = st.text_input("Motif de la dépense")
        montant_d = st.number_input("Montant (FG)", min_value=0)
        if st.form_submit_button("Enregistrer la dépense"):
            db.table("depenses").insert({"user_id":user_id, "motif":motif_d, "montant":montant_d}).execute()
            st.success("Dépense enregistrée.")

# --- 6. PAGE PARAMÈTRES ---
elif menu == "⚙️ Paramètres":
    st.header("⚙️ Paramètres Boutique")
    with st.form("form_params"):
        up_nom = st.text_input("Nom de l'entreprise", value=user_info['nom_ent'])
        up_adr = st.text_input("Adresse", value=user_info.get('adresse',''))
        up_tel = st.text_input("Téléphone", value=user_info.get('telephone',''))
        if st.form_submit_button("Mettre à jour les informations"):
            db.table("users").update({"nom_ent":up_nom, "adresse":up_adr, "telephone":up_tel}).eq("id", user_id).execute()
            st.success("Paramètres sauvegardés !")
            st.rerun()
