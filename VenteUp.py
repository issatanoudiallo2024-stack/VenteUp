import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import base64
import hashlib

# --- CONFIGURATION ---
st.set_page_config(page_title="VenteUp Pro - By Issa Diallo", layout="wide", page_icon="💎")

# BASE DE DONNÉES FIXE (ZÉRO PERTE)
DB_NAME = 'venteup_final_stable.db'

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, 
                  nom_ent TEXT, adresse TEXT, telephone TEXT, email_ent TEXT, devise TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS produits
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nom TEXT, p_achat REAL, p_vente REAL, qte INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ventes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nom_prod TEXT, qte_v INTEGER, date_v TIMESTAMP, total REAL, benef REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- AUTHENTIFICATION ---
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

if st.session_state['user_id'] is None:
    st.title("🚀 VenteUp Pro : Gestion Multi-Comptes")
    st.info("Plateforme sécurisée de gestion commerciale")
    
    tab_log, tab_sign = st.tabs(["Connexion", "Création de compte"])
    
    with tab_log:
        u = st.text_input("Nom d'utilisateur")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            conn = get_connection()
            user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hash_password(p))).fetchone()
            conn.close()
            if user:
                st.session_state['user_id'] = user[0]
                st.rerun()
            else: st.error("Identifiants incorrects")
            
    with tab_sign:
        nu = st.text_input("Pseudo choisi")
        ne = st.text_input("Nom de l'Entreprise")
        np = st.text_input("Mot de passe secret", type="password")
        if st.button("Valider l'inscription"):
            conn = get_connection()
            try:
                conn.execute("INSERT INTO users (username, password, nom_ent, devise) VALUES (?,?,?,?)", (nu, hash_password(np), ne, "FG"))
                conn.commit()
                st.success("Compte créé ! Connectez-vous.")
            except: st.error("Le pseudo existe déjà.")
            finally: conn.close()

    # SIGNATURE VISIBLE DÈS L'ENTRÉE
    st.divider()
    st.markdown("### 🛠️ Support & Développement")
    st.write("**Développeur :** Issa Diallo")
    st.write("**Contact :** +224 610 51 89 73")
    st.write("**Email :** Issatanoudiallo2024@gmail.com")
    st.stop()

# --- INTERFACE PRINCIPALE ---
user_id = st.session_state['user_id']
conn = get_connection()
user_info = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

with st.sidebar:
    st.title(f"🏬 {user_info[3]}")
    menu = st.radio("Navigation", ["📊 Dashboard", "🛒 Ventes (Caisse)", "📦 Stock & Appro", "🧾 Facturation", "⚙️ Paramètres"])
    
    if st.button("🚪 Déconnexion"):
        st.session_state['user_id'] = None
        st.rerun()
    
    # SIGNATURE TOUJOURS VISIBLE POUR L'UTILISATEUR
    st.divider()
    st.markdown("### 👨‍💻 Développeur")
    st.success("**Issa Diallo**")
    st.caption("📞 +224 610 51 89 73")
    st.caption("📧 Issatanoudiallo2024@gmail.com")
    st.caption("📍 Conakry, Guinée")

# --- ONGLETS ---
if menu == "📊 Dashboard":
    st.title(f"Analyses de {user_info[3]} 📊")
    df_v = pd.read_sql(f"SELECT * FROM ventes WHERE user_id={user_id}", conn)
    c1, c2 = st.columns(2)
    c1.metric("Chiffre d'Affaire", f"{df_v['total'].sum():,.0f} {user_info[7]}")
    c2.metric("Bénéfice Net", f"{df_v['benef'].sum():,.0f} {user_info[7]}")

elif menu == "🛒 Ventes (Caisse)":
    st.title("Caisse Express 🛒")
    prods = pd.read_sql(f"SELECT * FROM produits WHERE user_id={user_id} AND qte > 0", conn)
    if not prods.empty:
        with st.form("v"):
            p = st.selectbox("Choisir le produit", prods['nom'].tolist())
            q = st.number_input("Quantité", min_value=1)
            if st.form_submit_button("Confirmer la vente"):
                p_i = prods[prods['nom'] == p].iloc[0]
                total = q * p_i['p_vente']
                benef = (p_i['p_vente'] - p_i['p_achat']) * q
                conn.execute("INSERT INTO ventes (user_id, nom_prod, qte_v, date_v, total, benef) VALUES (?,?,?,?,?,?)",
                             (user_id, p, q, datetime.now().strftime("%d/%m/%Y %H:%M"), total, benef))
                conn.execute("UPDATE produits SET qte = qte - ? WHERE id = ?", (q, int(p_i['id'])))
                conn.commit()
                st.success("Vente enregistrée avec succès !")
    else: st.warning("Veuillez d'abord ajouter des produits au stock.")

elif menu == "📦 Stock & Appro":
    st.title("Gestion des Stocks 📦")
    t1, t2 = st.tabs(["📋 Inventaire", "🔄 Ajouter/Réapprovisionner"])
    with t1:
        df_p = pd.read_sql(f"SELECT * FROM produits WHERE user_id={user_id}", conn)
        st.dataframe(df_p, use_container_width=True)
    with t2:
        st.subheader("Nouveau Produit ou Recharge")
        with st.form("add_p"):
            n = st.text_input("Nom de l'article")
            pa = st.number_input("Prix d'Achat")
            pv = st.number_input("Prix de Vente")
            qt = st.number_input("Quantité")
            if st.form_submit_button("Enregistrer en Stock"):
                conn.execute("INSERT INTO produits (user_id, nom, p_achat, p_vente, qte) VALUES (?,?,?,?,?)", (user_id, n, pa, pv, qt))
                conn.commit()
                st.success("Produit ajouté !")
                st.rerun()

elif menu == "🧾 Facturation":
    st.title("Éditeur de Facture 🧾")
    df_v = pd.read_sql(f"SELECT * FROM ventes WHERE user_id={user_id} ORDER BY id DESC", conn)
    if not df_v.empty:
        sel = st.multiselect("Ventes à inclure dans la facture", df_v.index.tolist())
        if sel:
            items = df_v.iloc[sel]
            c_nom = st.text_input("Nom du Client")
            cachet = st.file_uploader("Télécharger l'image du cachet (PNG/JPG)")
            if st.button("Générer la Facture"):
                c_b64 = base64.b64encode(cachet.getvalue()).decode() if cachet else ""
                html = f"""
                <div style="padding:30px; border:1px solid #000; background:white; color:black; font-family:Arial;">
                    <div style="display:flex; justify-content:space-between; border-bottom:2px solid #333; padding-bottom:10px;">
                        <div>
                            <h2 style="color:#1a73e8; margin:0;">{user_info[3]}</h2>
                            <p style="margin:2px;">📍 {user_info[4]}<br>📞 {user_info[5]}<br>📧 {user_info[6]}</p>
                        </div>
                        <div style="text-align:right;">
                            <h1 style="margin:0;">FACTURE</h1>
                            <p><b>CLIENT :</b> {c_nom}<br>Date : {datetime.now().strftime('%d/%m/%Y')}</p>
                        </div>
                    </div>
                    <table style="width:100%; border-collapse:collapse; margin-top:20px;">
                        <tr style="background:#eee; border:1px solid #000;">
                            <th style="padding:10px;">Désignation</th>
                            <th style="padding:10px;">Qté</th>
                            <th style="padding:10px;">Total</th>
                        </tr>
                """
                for r in items.itertuples():
                    html += f"<tr><td style='border:1px solid #ddd; padding:8px;'>{r.nom_prod}</td><td style='border:1px solid #ddd; padding:8px; text-align:center;'>{r.qte_v}</td><td style='border:1px solid #ddd; padding:8px; text-align:right;'>{r.total:,.0f}</td></tr>"
                
                html += f"""
                    </table>
                    <h2 style="text-align:right; margin-top:20px;">NET À PAYER : {items['total'].sum():,.0f} {user_info[7]}</h2>
                    <div style="margin-top:50px; display:flex; justify-content:space-between; align-items:flex-end;">
                        <p style="font-size:10px; color:#999;">Généré via VenteUp System</p>
                        <div style="width:150px; height:100px; border:1px dashed #ccc; text-align:center;">
                            {f'<img src="data:image/png;base64,{c_b64}" width="120">' if c_b64 else '<p style="padding-top:30px;">Cachet & Signature</p>'}
                        </div>
                    </div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)

elif menu == "⚙️ Paramètres":
    st.title("Configuration Boutique ⚙️")
    with st.form("p"):
        ne = st.text_input("Nom de l'Entreprise", value=user_info[3])
        ae = st.text_input("Adresse Physique", value=user_info[4])
        te = st.text_input("Téléphone", value=user_info[5])
        ee = st.text_input("Email Boutique", value=user_info[6])
        de = st.selectbox("Devise", ["FG", "GNF", "CFA", "$"], index=0)
        if st.form_submit_button("Enregistrer les réglages"):
            conn.execute("UPDATE users SET nom_ent=?, adresse=?, telephone=?, email_ent=?, devise=? WHERE id=?", (ne, ae, te, ee, de, user_id))
            conn.commit()
            st.success("Boutique mise à jour !")
            st.rerun()

conn.close()
