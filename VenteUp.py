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

# --- AUTHENTIFICATION ---
if st.session_state['user_id'] is None:
    st.title("🚀 VenteUp Pro")
    t1, t2 = st.tabs(["Connexion", "S'inscrire"])
    with t1:
        with st.form("login_f"):
            u_l = st.text_input("Pseudo").strip()
            p_l = st.text_input("Mot de passe", type="password").strip()
            if st.form_submit_button("Se connecter", use_container_width=True):
                res = db.table("users").select("*").eq("username", u_l).eq("password", p_l).execute()
                if res.data:
                    st.session_state['user_id'] = res.data[0]['id']
                    st.rerun()
                else: st.error("Identifiants incorrects.")
    with t2:
        with st.form("reg_f"):
            nu, ne, np = st.text_input("Pseudo"), st.text_input("Nom Boutique"), st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Créer le compte", use_container_width=True):
                db.table("users").insert({"username":nu, "nom_ent":ne, "password":np}).execute()
                st.success("Compte créé !")
    st.stop()

# --- INFOS BOUTIQUE ---
user_id = st.session_state['user_id']
user_info = db.table("users").select("*").eq("id", user_id).execute().data[0]
devise = user_info.get('devise', 'FG')

with st.sidebar:
    st.header(f"🏪 {user_info['nom_ent']}")
    menu = st.radio("Navigation", ["📊 Bilan", "🛒 Vendre", "📦 Stock", "💸 Dépenses", "⚙️ Paramètres"])
    st.divider()
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state['user_id'] = None
        st.rerun()
    
    # --- TA SIGNATURE (VISIBLE PARTOUT) ---
    st.markdown("---")
    st.caption("✍️ Dev: ISSA DIALLO")
    st.caption(f"📧 {user_info.get('email_boutique', 'issatanoudiallo2024@gmail.com')}")
    st.caption(f"📞 {user_info.get('telephone', '610 51 89 73')}")

# --- 1. BILAN (SOLDES VISIBLES) ---
if menu == "📊 Bilan":
    st.header("📊 État de la Caisse")
    v = db.table("ventes").select("total").eq("user_id", user_id).execute().data
    d = db.table("depenses").select("montant").eq("user_id", user_id).execute().data
    tot_v, tot_d = sum([x['total'] for x in v]), sum([x['montant'] for x in d])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Ventes", f"{tot_v:,} {devise}")
    c2.metric("Total Dépenses", f"{tot_d:,} {devise}", delta_color="inverse")
    c3.metric("Solde Net (Bénéfice)", f"{tot_v - tot_d:,} {devise}")

# --- 2. VENDRE & FACTURE ---
elif menu == "🛒 Vendre":
    st.header("🛒 Terminal de Vente")
    prods = db.table("produits").select("*").eq("user_id", user_id).gt("qte", 0).execute().data
    if prods:
        c1, c2 = st.columns([1, 1.2])
        with c1:
            with st.form("vente_pro"):
                p_n = st.selectbox("Article", [x['nom'] for x in prods])
                q = st.number_input("Quantité", min_value=1, value=1)
                rabais = st.number_input("Rabais accordé", min_value=0, value=0)
                nom_c = st.text_input("Nom du Client")
                if st.form_submit_button("Valider la vente", use_container_width=True):
                    sel = [x for x in prods if x['nom'] == p_n][0]
                    t_net = (q * sel['p_vente']) - rabais
                    db.table("ventes").insert({"user_id":user_id, "nom_prod":p_n, "qte_v":q, "total":t_net, "client_nom":nom_c, "rabais":rabais}).execute()
                    db.table("produits").update({"qte": sel['qte'] - q}).eq("id", sel['id']).execute()
                    st.session_state['last_f'] = {"n":nom_c,"p":p_n,"q":q,"net":t_net,"r":rabais, "pv":sel['p_vente']}
                    st.rerun()
        
        if 'last_f' in st.session_state:
            f = st.session_state['last_f']
            with c2:
                st.markdown(f"""
                <div style="background:white; color:black; padding:20px; border:1px solid #ddd; border-radius:10px; font-family:monospace;">
                    <center><h3>{user_info['nom_ent']}</h3><small>{user_info.get('adresse','')}</small></center>
                    <hr>
                    <b>Client:</b> {f['n']}<br>
                    <b>Article:</b> {f['p']} (x{f['q']})<br>
                    <b>Prix Unit:</b> {f['pv']:,} {devise}<br>
                    <b>Rabais:</b> -{f['r']:,} {devise}
                    <h3 style="text-align:right; color:#2E7D32;">TOTAL: {f['net']:,} {devise}</h3>
                    <center><small>--- MERCI ---</small></center>
                </div>
                """, unsafe_allow_html=True)

# --- 3. STOCK & RÉAPPROVISIONNEMENT ---
elif menu == "📦 Stock":
    st.header("📦 Gestion Stock")
    res = db.table("produits").select("*").eq("user_id", user_id).execute().data
    if res:
        st.dataframe(pd.DataFrame(res)[['nom', 'p_vente', 'qte']], use_container_width=True)
    
    col_add, col_reup = st.columns(2)
    with col_add:
        with st.expander("➕ Nouveau Produit"):
            with st.form("new_p"):
                n, pv, q = st.text_input("Nom"), st.number_input("Prix"), st.number_input("Qté", min_value=1)
                if st.form_submit_button("Ajouter"):
                    db.table("produits").insert({"user_id":user_id, "nom":n, "p_vente":pv, "qte":q}).execute()
                    st.rerun()
    with col_reup:
        with st.expander("🔄 Réapprovisionnement"):
            if res:
                with st.form("reup_p"):
                    p_re = st.selectbox("Article à recharger", [x['nom'] for x in res])
                    q_re = st.number_input("Qté ajoutée", min_value=1)
                    if st.form_submit_button("Mettre à jour le stock"):
                        old_q = [x for x in res if x['nom'] == p_re][0]['qte']
                        db.table("produits").update({"qte": old_q + q_re}).eq("nom", p_re).eq("user_id", user_id).execute()
                        st.success("Stock mis à jour !")
                        st.rerun()

# --- 4. DÉPENSES ---
elif menu == "💸 Dépenses":
    st.header("💸 Sorties de caisse")
    with st.form("dp_f"):
        m, mt = st.text_input("Motif"), st.number_input("Montant", min_value=0)
        if st.form_submit_button("Enregistrer"):
            db.table("depenses").insert({"user_id":user_id, "motif":m, "montant":mt}).execute()
            st.success("Dépense enregistrée")

# --- 5. PARAMÈTRES (EMAIL, ADRESSE, DEVISE) ---
elif menu == "⚙️ Paramètres":
    st.header("⚙️ Configuration")
    with st.form("conf_f"):
        ne = st.text_input("Nom Boutique", value=user_info['nom_ent'])
        eb = st.text_input("Email Professionnel", value=user_info.get('email_boutique',''))
        ad = st.text_input("Adresse Physique", value=user_info.get('adresse',''))
        te = st.text_input("Téléphone", value=user_info.get('telephone',''))
        dv = st.selectbox("Devise (Cachet)", ["FG", "GNF", "FCFA", "USD", "EUR"], index=0)
        if st.form_submit_button("Sauvegarder les modifications", use_container_width=True):
            db.table("users").update({"nom_ent":ne, "email_boutique":eb, "adresse":ad, "telephone":te, "devise":dv}).eq("id", user_id).execute()
            st.success("Paramètres mis à jour !")
            st.rerun()
