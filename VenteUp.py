import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
from PIL import Image, ImageDraw
import io

# --- 🛠️ INFOS DU CONCEPTEUR (FIXES - NE CHANGENT JAMAIS) ---
CONCEPTEUR_NOM = "Issa Diallo"
CONCEPTEUR_TEL = "610 51 89 73"
CONCEPTEUR_MAIL = "issatanoudiallo2024@gmail.com"

st.set_page_config(page_title="VenteUp Pro", page_icon="🏢", layout="wide")

# --- 🗄️ GESTION DE LA BASE DE DONNÉES ---
def get_connection():
    return sqlite3.connect('venteup_v7_final.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Table Utilisateurs
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)')
    # Table Produits
    c.execute('CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nom TEXT, p_achat REAL, p_vente REAL, stock INTEGER)')
    # Table Ventes
    c.execute('CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, client_nom TEXT, client_tel TEXT, client_adr TEXT, details TEXT, total REAL, date TEXT)')
    # Table Dépenses
    c.execute('CREATE TABLE IF NOT EXISTS depenses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, motif TEXT, montant REAL, date TEXT)')
    # Table Config Boutique (Remplie par l'utilisateur)
    c.execute('CREATE TABLE IF NOT EXISTS config (user_id INTEGER PRIMARY KEY, boutique TEXT, gérant TEXT, tel TEXT, mail TEXT, adresse TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- 🔐 SÉCURITÉ ---
def hash_p(p): return hashlib.sha256(str.encode(p)).hexdigest()

if 'user_id' not in st.session_state:
    st.title("🔐 Accès à VenteUp Pro")
    
    conn = get_connection()
    user_count = conn.execute("SELECT count(*) FROM users").fetchone()[0]
    conn.close()

    if user_count == 0:
        st.info("👋 Bienvenue ! Créez votre compte de gérant pour commencer.")
        with st.form("Inscription"):
            u = st.text_input("Identifiant choisi")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Activer mon application"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO users (username, password) VALUES (?,?)", (u, hash_p(p)))
                uid = cur.lastrowid
                # On crée une config vide que l'utilisateur remplira dans l'onglet Paramètres
                cur.execute("INSERT INTO config VALUES (?, 'Ma Boutique', 'Gérant', '000', 'email@exemple.com', 'Ville')", (uid,))
                conn.commit()
                conn.close()
                st.success("Compte créé ! Connectez-vous.")
                st.rerun()
    else:
        with st.form("Login"):
            u = st.text_input("Identifiant")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter"):
                conn = get_connection()
                res = conn.execute("SELECT id FROM users WHERE username=? AND password=?", (u, hash_p(p))).fetchone()
                conn.close()
                if res:
                    st.session_state.user_id = res[0]
                    st.rerun()
                else: st.error("Identifiants incorrects.")
    st.stop()

# --- 🏢 INTERFACE UTILISATEUR ---
UID = st.session_state.user_id

# Récupérer la config de l'utilisateur
conn = get_connection()
c_data = conn.execute("SELECT boutique, gérant, tel, mail, adresse FROM config WHERE user_id=?", (UID,)).fetchone()
conn.close()
conf = {"nom": c_data[0], "gérant": c_data[1], "tel": c_data[2], "mail": c_data[3], "adr": c_data[4]}

# Barre latérale
st.sidebar.title(f"🏢 {conf['nom']}")
st.sidebar.markdown(f"**Gérant :** {conf['gérant']}")
st.sidebar.divider()

menu = ["🛒 Ventes", "📦 Stock", "💸 Dépenses", "📊 Historique", "⚙️ Paramètres"]
choix = st.sidebar.radio("Navigation", menu)

# --- 1. VENTES ---
if choix == "🛒 Ventes":
    st.header("🛒 Terminal de Vente")
    # Vérifier si le stock est vide
    conn = get_connection()
    prods = conn.execute("SELECT nom, p_vente, stock FROM produits WHERE user_id=? AND stock > 0", (UID,)).fetchall()
    conn.close()

    if not prods:
        st.warning("⚠️ Votre stock est vide. Allez dans l'onglet **📦 Stock** pour ajouter des produits avant de vendre.")
    else:
        st.write("Enregistrez une nouvelle vente ici.")
        # (Code du panier...)

# --- 2. STOCK ---
elif choix == "📦 Stock":
    st.header("📦 Gestion du Stock")
    st.info("Ajoutez ici vos articles. Ils apparaîtront ensuite dans l'onglet Ventes.")
    with st.form("add_stock"):
        n = st.text_input("Nom du produit").upper()
        pa = st.number_input("Prix d'achat", min_value=0.0)
        pv = st.number_input("Prix de vente", min_value=0.0)
        q = st.number_input("Quantité en stock", min_value=0)
        if st.form_submit_button("Enregistrer le produit"):
            conn = get_connection()
            conn.execute("INSERT INTO produits (user_id, nom, p_achat, p_vente, stock) VALUES (?,?,?,?,?)", (UID, n, pa, pv, q))
            conn.commit()
            conn.close()
            st.success(f"Produit {n} ajouté !")

# --- 3. DÉPENSES ---
elif choix == "💸 Dépenses":
    st.header("💸 Gestion des Dépenses")
    with st.form("add_dep"):
        m = st.text_input("Motif de la dépense")
        mt = st.number_input("Montant", min_value=0.0)
        if st.form_submit_button("Enregistrer la dépense"):
            conn = get_connection()
            conn.execute("INSERT INTO depenses (user_id, motif, montant, date) VALUES (?,?,?,?)", (UID, m, mt, datetime.now().strftime("%d/%m/%Y")))
            conn.commit()
            conn.close()
            st.success("Dépense enregistrée.")

# --- 4. PARAMÈTRES (Remplis par l'utilisateur) ---
elif choix == "⚙️ Paramètres":
    st.header("⚙️ Configuration de votre Boutique")
    st.write("Ces informations apparaîtront sur vos factures.")
    with st.form("cfg"):
        b_n = st.text_input("Nom de la Boutique", conf['nom'])
        b_g = st.text_input("Nom du Gérant", conf['gérant'])
        b_t = st.text_input("Téléphone", conf['tel'])
        b_m = st.text_input("Email", conf['mail'])
        b_a = st.text_input("Adresse", conf['adr'])
        if st.form_submit_button("Mettre à jour mes informations"):
            conn = get_connection()
            conn.execute("UPDATE config SET boutique=?, gérant=?, tel=?, mail=?, adresse=? WHERE user_id=?", (b_n, b_g, b_t, b_m, b_a, UID))
            conn.commit()
            conn.close()
            st.success("Informations boutique mises à jour !")
            st.rerun()

# --- 👤 SIGNATURE CONCEPTEUR (FIXE) ---
st.sidebar.divider()
st.sidebar.markdown(f"""
<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px;">
    <p style="margin: 0; font-size: 0.8em; color: #555;"><b>👨‍💻 Concepteur :</b></p>
    <p style="margin: 0; font-weight: bold; color: #2ecc71;">{CONCEPTEUR_NOM}</p>
    <p style="margin: 0; font-size: 0.8em;">📞 {CONCEPTEUR_TEL}</p>
    <p style="margin: 0; font-size: 0.8em;">📧 {CONCEPTEUR_MAIL}</p>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("Se déconnecter"):
    del st.session_state.user_id
    st.rerun()
