import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import base64
import hashlib
from PIL import Image, ImageDraw, ImageFont
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="VenteUp Pro - By Issa Diallo", layout="wide", page_icon="💎")
DB_NAME = 'venteup_pro_v21.db'

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
        u = st.text_input("Identifiant", key="login_u")
        p = st.text_input("Mot de passe", type="password", key="login_p")
        if st.button("Se connecter", key="btn_login"):
            conn = get_connection()
            user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hash_password(p))).fetchone()
            conn.close()
            if user:
                st.session_state['user_id'] = user[0]
                st.rerun()
            else: st.error("Identifiants incorrects.")
    with tab_sign:
        nu = st.text_input("Pseudo", key="sign_u")
        ne = st.text_input("Nom Boutique", key="sign_e")
        np = st.text_input("Mot de passe", type="password", key="sign_p")
        if st.button("S'inscrire", key="btn_signup"):
            conn = get_connection()
            try:
                conn.execute("INSERT INTO users (username, password, nom_ent, devise) VALUES (?,?,?,?)", (nu, hash_password(np), ne, "FG"))
                conn.commit()
                st.success("Compte créé ! Connectez-vous.")
            except: st.error("Pseudo déjà pris.")
            finally: conn.close()
    st.stop()

# --- INTERFACE PRINCIPALE ---
user_id = st.session_state['user_id']
conn = get_connection()
user_info = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

with st.sidebar:
    st.title(f"🏢 {user_info[3]}")
    menu = st.radio("Navigation", ["📊 Dashboard", "🛒 Ventes", "📦 Stock", "🧾 Facturation", "⚙️ Profil"])
    if st.button("Déconnexion"):
        st.session_state['user_id'] = None
        st.rerun()
    st.divider()
    st.success(f"Développeur : **Issa Diallo**")
    st.caption("📞 +224 610 51 89 73")

# --- FONCTION GÉNÉRATION IMAGE FACTURE ---
def generate_invoice_image(user_info, client_info, items):
    # Création d'une image blanche (A4 proportionnelle)
    img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    
    # Texte de base (on utilise le dessin par défaut si les polices personnalisées manquent)
    d.text((50, 50), f"{user_info[3]}", fill=(26, 115, 232))
    d.text((50, 80), f"Adresse: {user_info[4]}\nTel: {user_info[5]}", fill=(0,0,0))
    
    d.text((500, 50), "FACTURE", fill=(0,0,0))
    d.text((500, 80), f"Client: {client_info['nom']}\nTel: {client_info['tel']}\nEmail: {client_info['email']}", fill=(0,0,0))
    
    d.line([(50, 180), (750, 180)], fill=(0,0,0), width=2)
    
    y = 220
    d.text((50, y), "Désignation", fill=(0,0,0))
    d.text((400, y), "Qté", fill=(0,0,0))
    d.text((600, y), "Total", fill=(0,0,0))
    
    y += 40
    total_general = 0
    for r in items.itertuples():
        d.text((50, y), f"{r.nom_prod}", fill=(0,0,0))
        d.text((400, y), f"{r.qte_v}", fill=(0,0,0))
        d.text((600, y), f"{r.total:,.0f} {user_info[7]}", fill=(0,0,0))
        total_general += r.total
        y += 30
        
    d.line([(50, y+20), (750, y+20)], fill=(0,0,0), width=1)
    d.text((500, y+50), f"NET A PAYER: {total_general:,.0f} {user_info[7]}", fill=(26, 115, 232))
    
    d.text((50, 950), "Propulsé par VenteUp - Développé par Issa Diallo", fill=(150,150,150))
    
    # Sauvegarde en mémoire
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- ONGLETS (LOGIQUE) ---
if menu == "📊 Dashboard":
    st.title("Performance 📊")
    df_v = pd.read_sql(f"SELECT * FROM ventes WHERE user_id={user_id}", conn)
    st.metric("Chiffre d'Affaire", f"{df_v['total'].sum():,.0f} {user_info[7]}")

elif menu == "🛒 Ventes":
    st.title("Caisse 🛒")
    prods = pd.read_sql(f"SELECT * FROM produits WHERE user_id={user_id} AND qte > 0", conn)
    if not prods.empty:
        with st.form("v_form"):
            p_sel = st.selectbox("Produit", prods['nom'].tolist())
            q_v = st.number_input("Quantité", min_value=1)
            if st.form_submit_button("Valider"):
                p_i = prods[prods['nom'] == p_sel].iloc[0]
                tot = q_v * p_i['p_vente']
                ben = (p_i['p_vente'] - p_i['p_achat']) * q_v
                conn.execute("INSERT INTO ventes (user_id, nom_prod, qte_v, date_v, total, benef) VALUES (?,?,?,?,?,?)",
                             (user_id, p_sel, q_v, datetime.now().strftime("%d/%m/%Y %H:%M"), tot, ben))
                conn.execute("UPDATE produits SET qte = qte - ? WHERE id = ?", (q_v, int(p_i['id'])))
                conn.commit()
                st.success("Vente réussie !")

elif menu == "📦 Stock":
    st.title("Stocks 📦")
    df_p = pd.read_sql(f"SELECT * FROM produits WHERE user_id={user_id}", conn)
    st.dataframe(df_p, use_container_width=True)
    with st.form("add_s"):
        n = st.text_input("Nom")
        pa = st.number_input("Prix Achat")
        pv = st.number_input("Prix Vente")
        qt = st.number_input("Quantité")
        if st.form_submit_button("Ajouter"):
            conn.execute("INSERT INTO produits (user_id, nom, p_achat, p_vente, qte) VALUES (?,?,?,?,?)", (user_id, n, pa, pv, qt))
            conn.commit()
            st.rerun()

elif menu == "🧾 Facturation":
    st.title("Générateur de Facture Image 🧾")
    df_v = pd.read_sql(f"SELECT * FROM ventes WHERE user_id={user_id} ORDER BY id DESC", conn)
    if not df_v.empty:
        sel = st.multiselect("Ventes à inclure", df_v.index.tolist())
        if sel:
            items = df_v.iloc[sel]
            c_nom = st.text_input("Nom Client")
            c_tel = st.text_input("Tel Client")
            c_eml = st.text_input("Email Client")
            c_adr = st.text_input("Adresse Client")
            
            if st.button("Préparer l'Image de la Facture"):
                client_info = {'nom': c_nom, 'tel': c_tel, 'email': c_eml, 'adr': c_adr}
                img_data = generate_invoice_image(user_info, client_info, items)
                
                st.image(img_data, caption="Aperçu de la facture")
                st.download_button(label="📥 Télécharger la facture (PNG)", 
                                   data=img_data, 
                                   file_name=f"Facture_{c_nom}_{datetime.now().strftime('%d%m%Y')}.png", 
                                   mime="image/png")

elif menu == "⚙️ Profil":
    st.title("Profil ⚙️")
    with st.form("prof"):
        ne = st.text_input("Nom Boutique", value=user_info[3])
        ae = st.text_input("Adresse", value=user_info[4])
        te = st.text_input("Tel", value=user_info[5])
        ee = st.text_input("Email", value=user_info[6])
        if st.form_submit_button("Enregistrer"):
            conn.execute("UPDATE users SET nom_ent=?, adresse=?, telephone=?, email_ent=? WHERE id=?", (ne, ae, te, ee, user_id))
            conn.commit()
            st.rerun()

conn.close()
