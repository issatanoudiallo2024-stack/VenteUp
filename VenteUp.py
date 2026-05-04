import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
from PIL import Image, ImageDraw
import io

# --- TES INFORMATIONS (FIXES) ---
MY_NAME = "Issa Diallo"
MY_TEL = "610 51 89 73"
MY_MAIL = "issatanoudiallo2024@gmail.com"

st.set_page_config(page_title="VenteUp Pro", page_icon="🏢", layout="wide")

# --- CONNEXION & PERSISTENCE ---
def get_connection():
    # On utilise un nom de base de données robuste
    return sqlite3.connect('venteup_master_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    # Table des comptes (comme Facebook)
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)')
    # Table des produits liée à l'utilisateur
    cursor.execute('CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nom TEXT, p_achat REAL, p_vente REAL, stock INTEGER)')
    # Table des ventes avec historique complet
    cursor.execute('CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, client_nom TEXT, client_tel TEXT, client_adr TEXT, details TEXT, total REAL, date TEXT)')
    # Table des dépenses
    cursor.execute('CREATE TABLE IF NOT EXISTS depenses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, motif TEXT, montant REAL, date TEXT)')
    # Table de configuration de la boutique
    cursor.execute('CREATE TABLE IF NOT EXISTS config (user_id INTEGER PRIMARY KEY, boutique TEXT, gerant TEXT, tel TEXT, mail TEXT, adresse TEXT)')
    conn.commit()
    conn.close()

init_db()

def hash_p(p): return hashlib.sha256(str.encode(p)).hexdigest()

# --- SYSTEME DE CONNEXION ---
if 'user_id' not in st.session_state:
    st.title("🔐 Bienvenue sur VenteUp")
    
    tab_login, tab_signup = st.tabs(["Connexion", "Inscription (Compte Unique)"])
    
    with tab_login:
        with st.form("login_form"):
            u = st.text_input("Nom d'utilisateur")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Accéder à ma boutique"):
                conn = get_connection()
                res = conn.execute("SELECT id FROM users WHERE username=? AND password=?", (u, hash_p(p))).fetchone()
                conn.close()
                if res:
                    st.session_state.user_id = res[0]
                    st.rerun()
                else: st.error("Identifiants incorrects.")

    with tab_signup:
        conn = get_connection()
        user_exists = conn.execute("SELECT count(*) FROM users").fetchone()[0]
        conn.close()
        
        if user_exists == 0:
            st.info("C'est la première installation. Créez votre compte administrateur.")
            with st.form("signup_form"):
                new_u = st.text_input("Choisir un identifiant")
                new_p = st.text_input("Choisir un mot de passe", type="password")
                if st.form_submit_button("Activer mon accès"):
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("INSERT INTO users (username, password) VALUES (?,?)", (new_u, hash_p(new_p)))
                    uid = cur.lastrowid
                    cur.execute("INSERT INTO config VALUES (?,?,?,?,?,?)", (uid, "Ma Boutique", MY_NAME, MY_TEL, MY_MAIL, "Conakry"))
                    conn.commit()
                    conn.close()
                    st.success("Compte activé ! Connectez-vous.")
        else:
            st.warning("L'inscription est verrouillée. Un compte gérant existe déjà.")
    st.stop()

# --- INTERFACE APRES CONNEXION ---
UID = st.session_state.user_id

# Récupération des infos boutique
conn = get_connection()
cfg_res = conn.execute("SELECT boutique, gerant, tel, mail, adresse FROM config WHERE user_id=?", (UID,)).fetchone()
conn.close()
conf = {"nom": cfg_res[0], "gerant": cfg_res[1], "tel": cfg_res[2], "mail": cfg_res[3], "adr": cfg_res[4]}

# Barre latérale (Sidebar) - Les onglets sont ici
st.sidebar.title(f"🏢 {conf['nom']}")
st.sidebar.write(f"Utilisateur : **{conf['gerant']}**")

menu = ["🛒 Ventes & Panier", "📦 Stock", "💸 Dépenses", "📊 Historique", "⚙️ Paramètres"]
choix = st.sidebar.radio("Navigation", menu)

if st.sidebar.button("Déconnexion"):
    del st.session_state.user_id
    st.rerun()

# --- 1. GESTION DES VENTES ---
if choix == "🛒 Ventes & Panier":
    st.header("🛒 Terminal de Vente")
    # ... Interface de vente avec panier ...
    st.write("Sélectionnez vos produits dans le stock pour commencer.")

# --- 5. PARAMÈTRES (POUR REMPLIR TES INFOS) ---
elif choix == "⚙️ Paramètres":
    st.header("⚙️ Configuration de votre profil")
    with st.form("update_cfg"):
        b_nom = st.text_input("Nom de l'entreprise", conf['nom'])
        b_gerant = st.text_input("Nom complet du gérant", conf['gerant'])
        b_tel = st.text_input("Téléphone", conf['tel'])
        b_mail = st.text_input("Email de contact", conf['mail'])
        b_adr = st.text_input("Adresse physique", conf['adr'])
        
        if st.form_submit_button("Enregistrer les modifications"):
            conn = get_connection()
            conn.execute("UPDATE config SET boutique=?, gerant=?, tel=?, mail=?, adresse=? WHERE user_id=?", 
                         (b_nom, b_gerant, b_tel, b_mail, b_adr, UID))
            conn.commit()
            conn.close()
            st.success("Informations mises à jour !")
            st.rerun()

# --- FOOTER ---
st.sidebar.divider()
st.sidebar.caption(f"Propulsé par {MY_NAME}")
