import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# --- CONFIGURATION ---
URL = "https://enikglfabczfpahbfzvq.supabase.co"
KEY = "sb_publishable_h169bGdSBk_SpbiXwH0KbQ_JE6Cm7lS"

@st.cache_resource
def init_db(): return create_client(URL, KEY)
db = init_db()

st.set_page_config(page_title="VenteUp Ultimate", layout="wide", page_icon="🏢")

# --- DESIGN CSS CUSTOM ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    [data-testid="stSidebar"] { background-color: #1e293b; color: white; }
    .stMetric { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .bill-container {
        background: white; color: black; padding: 40px; border-radius: 10px;
        border: 1px solid #ddd; box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .signature-box { font-size: 13px; color: #94a3b8; margin-top: 50px; border-top: 1px solid #334155; padding-top: 20px; }
    </style>
""", unsafe_allow_html=True)

if 'user_id' not in st.session_state: st.session_state['user_id'] = None
if 'panier' not in st.session_state: st.session_state['panier'] = []

# --- AUTH ---
if st.session_state['user_id'] is None:
    st.title("🔐 Accès VenteUp")
    u, p = st.text_input("Identifiant"), st.text_input("Mot de passe", type="password")
    if st.button("Se connecter", use_container_width=True):
        res = db.table("users").select("*").eq("username", u).eq("password", p).execute()
        if res.data: 
            st.session_state['user_id'] = res.data[0]['id']
            st.rerun()
    st.stop()

# --- DONNÉES ---
user = db.table("users").select("*").eq("id", st.session_state['user_id']).execute().data[0]
devise = user.get('devise', 'FG')

# --- SIDEBAR AVEC TA SIGNATURE ---
with st.sidebar:
    st.title(f"🏪 {user['nom_ent']}")
    menu = st.radio("MENU", ["📊 Bilan", "🛒 Ventes & Facture", "📦 Stock & Réappro", "💸 Dépenses", "⚙️ Paramètres"])
    
    st.markdown(f"""
    <div class="signature-box">
        <b>DÉVELOPPEUR</b><br>
        👨‍💻 Issa Diallo<br>
        📞 610 51 89 73<br>
        ✉️ {user.get('email_boutique', 'Dev@VenteUp.com')}
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state['user_id'] = None
        st.rerun()

# --- 1. BILAN ---
if menu == "📊 Bilan":
    st.header("📊 Performance de la Boutique")
    v = db.table("ventes").select("total").eq("user_id", user['id']).execute().data
    d = db.table("depenses").select("montant").eq("user_id", user['id']).execute().data
    tot_v, tot_d = sum(x['total'] for x in v), sum(x['montant'] for x in d)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("RECETTES", f"{tot_v:,} {devise}")
    c2.metric("DÉPENSES", f"{tot_d:,} {devise}", delta_color="inverse")
    c3.metric("SOLDE NET", f"{tot_v - tot_d:,} {devise}")

# --- 2. VENTES & FACTURE (DESIGN DEMANDÉ) ---
elif menu == "🛒 Ventes & Facture":
    st.header("🛒 Terminal de Vente")
    prods = db.table("produits").select("*").eq("user_id", user['id']).gt("qte", 0).execute().data
    
    c_vente, c_fact = st.columns([1, 1.4])
    
    with c_vente:
        with st.expander("➕ Ajouter un produit", expanded=True):
            art = st.selectbox("Article", [x['nom'] for x in prods])
            qte = st.number_input("Quantité", min_value=1)
            rab = st.number_input("Rabais sur l'article", min_value=0)
            if st.button("Ajouter au panier"):
                sel = [x for x in prods if x['nom'] == art][0]
                st.session_state['panier'].append({
                    "id": sel['id'], "nom": art, "q": qte, "pv": sel['p_vente'], 
                    "r": rab, "total": (qte * sel['p_vente']) - rab
                })
        
        if st.session_state['panier']:
            st.write("---")
            cli_n = st.text_input("Nom Client")
            cli_t = st.text_input("Téléphone Client")
            cli_a = st.text_input("Adresse Client")
            cli_m = st.text_input("Email Client")
            cachet = st.file_uploader("Image du Cachet", type=['png', 'jpg'])
            
            if st.button("✅ Enregistrer la Vente", use_container_width=True):
                for i in st.session_state['panier']:
                    db.table("ventes").insert({"user_id":user['id'], "nom_prod":i['nom'], "qte_v":i['q'], "total":i['total'], "client_nom":cli_n, "rabais":i['r']}).execute()
                    # Maj Stock
                    old_q = [x for x in prods if x['id'] == i['id']][0]['qte']
                    db.table("produits").update({"qte": old_q - i['q']}).eq("id", i['id']).execute()
                
                st.session_state['last_f'] = {"client": {"n":cli_n,"t":cli_t,"a":cli_a,"m":cli_m}, "items": st.session_state['panier'], "cachet": cachet}
                st.session_state['panier'] = []
                st.rerun()

    with c_fact:
        if 'last_f' in st.session_state:
            f = st.session_state['last_f']
            st.markdown(f"""
            <div class="bill-container">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="width:48%;">
                        <h2 style="color:#0f172a; margin:0;">{user['nom_ent']}</h2>
                        <p style="font-size:13px; line-height:1.5;">
                            <b>Gérant :</b> {user.get('nom_gerant', 'Non défini')}<br>
                            📍 {user.get('adresse', 'Localisation non définie')}<br>
                            📞 {user.get('telephone', 'Numéro non défini')}<br>
                            ✉️ {user.get('email_boutique', 'Email non défini')}
                        </p>
                    </div>
                    <div style="width:48%; text-align:right;">
                        <h4 style="margin:0; color:#475569;">FACTURE POUR :</h4>
                        <p style="font-size:13px; line-height:1.5;">
                            <b>{f['client']['n']}</b><br>
                            {f['client']['t']}<br>
                            {f['client']['a']}<br>
                            {f['client']['m']}
                        </p>
                    </div>
                </div>
                <hr style="margin:20px 0;">
                <table style="width:100%; border-collapse:collapse; font-size:14px;">
                    <tr style="background:#f1f5f9; text-align:left;">
                        <th style="padding:10px;">Désignation</th><th>Qté</th><th>P.U</th><th>Rabais</th><th>Total</th>
                    </tr>
                    {''.join([f"<tr><td style='padding:10px;'>{i['nom']}</td><td>{i['q']}</td><td>{i['pv']:,}</td><td>{i['r']:,}</td><td>{i['total']:,}</td></tr>" for i in f['items']])}
                </table>
                <div style="margin-top:30px; text-align:right;">
                    <span style="font-size:18px; font-weight:bold; color:#1e293b;">NET À PAYER : {sum(i['total'] for i in f['items']):,} {devise}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if f['cachet']: st.image(f['cachet'], width=150)
            st.button("🖼️ Enregistrer en image")

# --- 3. STOCK & RÉAPPRO ---
elif menu == "📦 Stock & Réappro":
    st.header("📦 Inventaire & Réappro")
    res = db.table("produits").select("*").eq("user_id", user['id']).execute().data
    if res:
        df = pd.DataFrame(res)
        st.dataframe(df[['id', 'nom', 'p_achat', 'p_vente', 'qte']], use_container_width=True)
        
        c_up, c_del = st.columns(2)
        with c_up:
            with st.expander("🔄 Réapprovisionnement"):
                t_re = st.selectbox("Article", [x['nom'] for x in res])
                q_re = st.number_input("Ajouter quantité", min_value=1)
                if st.button("Valider"):
                    old = [x for x in res if x['nom'] == t_re][0]
                    db.table("produits").update({"qte": old['qte'] + q_re}).eq("id", old['id']).execute()
                    st.rerun()
        with c_del:
            with st.expander("🗑️ Supprimer un article"):
                t_del = st.selectbox("Article à effacer", [x['nom'] for x in res], key="del")
                if st.button("Confirmer suppression"):
                    db.table("produits").delete().eq("nom", t_del).eq("user_id", user['id']).execute()
                    st.rerun()

# --- 4. DÉPENSES ---
elif menu == "💸 Dépenses":
    st.header("💸 Sorties de caisse")
    with st.form("d_f"):
        mot = st.text_input("Motif")
        mon = st.number_input("Montant", min_value=0)
        if st.form_submit_button("Enregistrer"):
            db.table("depenses").insert({"user_id":user['id'], "motif":mot, "montant":mon}).execute()
            st.rerun()

# --- 5. PARAMÈTRES ---
elif menu == "⚙️ Paramètres":
    st.header("⚙️ Configuration")
    with st.form("p_f"):
        c1, c2 = st.columns(2)
        n_e = c1.text_input("Nom Boutique", value=user['nom_ent'])
        n_g = c2.text_input("Nom du Gérant", value=user.get('nom_gerant',''))
        adr = c1.text_input("Localisation", value=user.get('adresse',''))
        tel = c2.text_input("Téléphone", value=user.get('telephone',''))
        em = c1.text_input("Email", value=user.get('email_boutique',''))
        dv = c2.selectbox("Devise", ["FG", "FCFA", "USD", "EUR"])
        if st.form_submit_button("Sauvegarder les réglages"):
            db.table("users").update({"nom_ent":n_e, "nom_gerant":n_g, "adresse":adr, "telephone":tel, "email_boutique":em, "devise":dv}).eq("id", user['id']).execute()
            st.rerun()
