import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import base64
import hashlib

# --- CONFIGURATION ---
st.set_page_config(page_title="VenteUp Pro - By Issa Diallo", layout="wide", page_icon="💎")

# BASE DE DONNÉES FIXE (ZÉRO PERTE)
DB_NAME = 'venteup_pro_final_v19.db'

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
    st.title("🚀 VenteUp Pro : Gestion de Commerce")
    tab_log, tab_sign = st.tabs(["Connexion", "Créer un compte"])
    
    with tab_log:
        u = st.text_input("Identifiant")
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
        nu = st.text_input("Pseudo")
        ne = st.text_input("Nom Boutique")
        np = st.text_input("Mot de passe", type="password")
        if st.button("S'inscrire"):
            conn = get_connection()
            try:
                conn.execute("INSERT INTO users (username, password, nom_ent, devise) VALUES (?,?,?,?)", (nu, hash_password(np), ne, "FG"))
                conn.commit()
                st.success("Compte créé avec succès !")
            except: st.error("Le pseudo est déjà pris.")
            finally: conn.close()

    st.divider()
    st.markdown("### 👨‍💻 Développeur du Logiciel")
    st.write("**Issa Diallo** | +224 610 51 89 73 | Issatanoudiallo2024@gmail.com")
    st.stop()

# --- INTERFACE PRINCIPALE ---
user_id = st.session_state['user_id']
conn = get_connection()
user_info = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

with st.sidebar:
    st.title(f"🏢 {user_info[3]}")
    menu = st.radio("Navigation", ["📊 Dashboard", "🛒 Ventes", "📦 Stock & Appro", "🧾 Facturation", "⚙️ Profil"])
    
    if st.button("Déconnexion"):
        st.session_state['user_id'] = None
        st.rerun()
    
    st.divider()
    st.markdown("### 🛠️ Support Technique")
    st.success("**Issa Diallo**")
    st.caption("📞 +224 610 51 89 73")
    st.caption("📧 Issatanoudiallo2024@gmail.com")

# --- ONGLETS ---
if menu == "📊 Dashboard":
    st.title("Performance 📊")
    df_v = pd.read_sql(f"SELECT * FROM ventes WHERE user_id={user_id}", conn)
    c1, c2 = st.columns(2)
    c1.metric("Chiffre d'Affaire", f"{df_v['total'].sum():,.0f} {user_info[7]}")
    c2.metric("Bénéfice", f"{df_v['benef'].sum():,.0f} {user_info[7]}")

elif menu == "🛒 Ventes":
    st.title("Caisse 🛒")
    prods = pd.read_sql(f"SELECT * FROM produits WHERE user_id={user_id} AND qte > 0", conn)
    if not prods.empty:
        with st.form("v"):
            p_sel = st.selectbox("Produit", prods['nom'].tolist())
            q_v = st.number_input("Quantité", min_value=1)
            if st.form_submit_button("Valider la vente"):
                p_i = prods[prods['nom'] == p_sel].iloc[0]
                tot = q_v * p_i['p_vente']
                ben = (p_i['p_vente'] - p_i['p_achat']) * q_v
                conn.execute("INSERT INTO ventes (user_id, nom_prod, qte_v, date_v, total, benef) VALUES (?,?,?,?,?,?)",
                             (user_id, p_sel, q_v, datetime.now().strftime("%d/%m/%Y %H:%M"), tot, ben))
                conn.execute("UPDATE produits SET qte = qte - ? WHERE id = ?", (q_v, int(p_i['id'])))
                conn.commit()
                st.success("Vente enregistrée !")
    else: st.warning("Stock vide.")

elif menu == "📦 Stock & Appro":
    st.title("Stocks 📦")
    t1, t2 = st.tabs(["Inventaire", "Réappro / Nouveau"])
    with t1:
        df_p = pd.read_sql(f"SELECT * FROM produits WHERE user_id={user_id}", conn)
        st.dataframe(df_p, use_container_width=True)
    with t2:
        with st.form("add"):
            n = st.text_input("Désignation")
            pa = st.number_input("Prix Achat")
            pv = st.number_input("Prix Vente")
            qt = st.number_input("Quantité")
            if st.form_submit_button("Enregistrer"):
                conn.execute("INSERT INTO produits (user_id, nom, p_achat, p_vente, qte) VALUES (?,?,?,?,?)", (user_id, n, pa, pv, qt))
                conn.commit()
                st.rerun()

elif menu == "🧾 Facturation":
    st.title("Éditeur de Facture 🧾")
    df_v = pd.read_sql(f"SELECT * FROM ventes WHERE user_id={user_id} ORDER BY id DESC", conn)
    if not df_v.empty:
        sel = st.multiselect("Sélectionner les articles", df_v.index.tolist())
        if sel:
            items = df_v.iloc[sel]
            st.subheader("Informations du Client")
            c1, c2 = st.columns(2)
            c_nom = c1.text_input("Nom du Client")
            c_adr = c2.text_input("Adresse du Client")
            c_tel = c1.text_input("Numéro de Téléphone")
            c_eml = c2.text_input("Email du Client")
            cachet = st.file_uploader("Importer Image du Cachet")
            
            if st.button("Générer la Facture"):
                c_b64 = base64.b64encode(cachet.getvalue()).decode() if cachet else ""
                html = f"""
                <div style="padding:25px; border:1px solid #000; background:white; color:black; font-family:sans-serif;">
                    <div style="display:flex; justify-content:space-between; border-bottom:2px solid #1a73e8; padding-bottom:10px;">
                        <div>
                            <h2 style="color:#1a73e8; margin:0;">{user_info[3]}</h2>
                            <p>📍 {user_info[4]}<br>📞 {user_info[5]}<br>📧 {user_info[6]}</p>
                        </div>
                        <div style="text-align:right;">
                            <h1 style="margin:0;">FACTURE</h1>
                            <p><b>À l'attention de :</b><br>{c_nom}<br>📍 {c_adr}<br>📞 {c_tel}<br>📧 {c_eml}</p>
                        </div>
                    </div>
                    <table style="width:100%; border-collapse:collapse; margin-top:20px;">
                        <tr style="background:#f1f1f1;">
                            <th style="padding:10px; border:1px solid #ddd;">Article</th>
                            <th style="padding:10px; border:1px solid #ddd;">Qté</th>
                            <th style="padding:10px; border:1px solid #ddd;">Total</th>
                        </tr>
                """
                for r in items.itertuples():
                    html += f"<tr><td style='padding:8px; border:1px solid #ddd;'>{r.nom_prod}</td><td style='padding:8px; border:1px solid #ddd; text-align:center;'>{r.qte_v}</td><td style='padding:8px; border:1px solid #ddd; text-align:right;'>{r.total:,.0f}</td></tr>"
                
                html += f"""
                    </table>
                    <h2 style="text-align:right; margin-top:20px;">TOTAL : {items['total'].sum():,.0f} {user_info[7]}</h2>
                    <div style="margin-top:40px; display:flex; justify-content:space-between;">
                        <p style="font-size:10px; color:#555;">Document généré par VenteUp System</p>
                        <div style="text-align:center;">
                            {f'<img src="data:image/png;base64,{c_b64}" width="120">' if c_b64 else 'Signature & Cachet'}
                        </div>
                    </div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)

elif menu == "⚙️ Profil":
    st.title("Paramètres ⚙️")
    with st.form("p"):
        ne = st.text_input("Nom Boutique", value=user_info[3])
        ae = st.text_input("Adresse Physique", value=user_info[4])
        te = st.text_input("Téléphone", value=user_info[5])
        ee = st.text_input("Email Professionnel", value=user_info[6])
        de = st.selectbox("Devise", ["FG", "GNF", "CFA", "$"], index=0)
        if st.form_submit_button("Sauvegarder"):
            conn.execute("UPDATE users SET nom_ent=?, adresse=?, telephone=?, email_ent=?, devise=? WHERE id=?", (ne, ae, te, ee, de, user_id))
            conn.commit()
            st.success("Profil mis à jour !")
            st.rerun()

conn.close()
