import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
from PIL import Image, ImageDraw
import io

# --- SIGNATURE DÉVELOPPEUR ---
MY_NAME = "Issa Diallo"
MY_TEL = "610 51 89 73"
MY_MAIL = "issatanoudiallo2024@gmail.com"

st.set_page_config(page_title="VenteUp Pro - Multi-User", page_icon="🔐", layout="wide")

# --- FONCTIONS BASE DE DONNÉES ---
def init_db():
    with sqlite3.connect('venteup_v4.db') as conn:
        cursor = conn.cursor()
        # Table Utilisateurs
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
        # Table Produits (liée à user_id)
        cursor.execute('''CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nom TEXT, 
            p_achat REAL, p_vente REAL, stock INTEGER)''')
        # Table Ventes (liée à user_id)
        cursor.execute('''CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, client_nom TEXT, 
            client_tel TEXT, client_adr TEXT, details TEXT, total REAL, date TEXT)''')
        # Table Config (liée à user_id)
        cursor.execute('''CREATE TABLE IF NOT EXISTS config (
            user_id INTEGER PRIMARY KEY, boutique TEXT, gerant TEXT, tel TEXT, mail TEXT, adresse TEXT)''')
        conn.commit()

init_db()

# --- GESTION AUTHENTIFICATION ---
def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def signup_user(username, password):
    try:
        with sqlite3.connect('venteup_v4.db') as conn:
            curr = conn.cursor()
            curr.execute("INSERT INTO users(username, password) VALUES (?,?)", (username, hash_pass(password)))
            user_id = curr.lastrowid
            # Créer une config par défaut pour le nouvel utilisateur
            curr.execute("INSERT INTO config VALUES (?,?,?,?,?,?)", (user_id, "Ma Boutique", "Gérant", "000", "mail@pro.com", "Conakry"))
            conn.commit()
        return True
    except: return False

def login_user(username, password):
    with sqlite3.connect('venteup_v4.db') as conn:
        curr = conn.cursor()
        curr.execute("SELECT id FROM users WHERE username=? AND password=?", (username, hash_pass(password)))
        return curr.fetchone()

# --- INTERFACE DE CONNEXION ---
if 'user_id' not in st.session_state:
    st.title("🚀 Bienvenue sur VenteUp")
    auth_mode = st.tabs(["Connexion", "Inscription"])
    
    with auth_mode[0]:
        u_log = st.text_input("Nom d'utilisateur", key="u_log")
        p_log = st.text_input("Mot de passe", type="password", key="p_log")
        if st.button("Se connecter"):
            res = login_user(u_log, p_log)
            if res:
                st.session_state.user_id = res[0]
                st.rerun()
            else: st.error("Identifiants incorrects")
            
    with auth_mode[1]:
        u_sign = st.text_input("Choisir un nom d'utilisateur", key="u_sign")
        p_sign = st.text_input("Choisir un mot de passe", type="password", key="p_sign")
        if st.button("Créer mon compte"):
            if signup_user(u_sign, p_sign):
                st.success("Compte créé ! Connectez-vous.")
            else: st.error("Ce nom d'utilisateur existe déjà.")
    st.stop() # Arrête l'exécution ici si pas connecté

# --- SI CONNECTÉ : RÉCUPÉRATION DES DONNÉES DE L'UTILISATEUR ---
USER_ID = st.session_state.user_id

def get_user_config():
    conn = sqlite3.connect('venteup_v4.db')
    data = conn.execute("SELECT boutique, gerant, tel, mail, adresse FROM config WHERE user_id=?", (USER_ID,)).fetchone()
    conn.close()
    return {"boutique": data[0], "gerant": data[1], "tel": data[2], "mail": data[3], "adr": data[4]}

# --- LE RESTE DE TON CODE (VENTES, STOCK, PARAMÈTRES) ---
# (Ici, on ajoute WHERE user_id = USER_ID à chaque requête SQL)

conf = get_user_config()
st.sidebar.success(f"Connecté : {conf['boutique']}")
if st.sidebar.button("Déconnexion"):
    del st.session_state.user_id
    st.rerun()

st.sidebar.divider()
menu = ["🛒 Ventes", "📦 Stock", "⚙️ Paramètres"]
choix = st.sidebar.radio("Menu", menu)

if choix == "⚙️ Paramètres":
    st.header("⚙️ Ma Boutique")
    with st.form("cfg"):
        b = st.text_input("Nom Boutique", value=conf['boutique'])
        g = st.text_input("Gérant", value=conf['gerant'])
        # ... (les autres champs)
        if st.form_submit_button("Sauvegarder"):
            with sqlite3.connect('venteup_v4.db') as conn:
                conn.execute("UPDATE config SET boutique=?, gerant=?, tel=?, mail=?, adresse=? WHERE user_id=?", (b,g,conf['tel'],conf['mail'],conf['adr'], USER_ID))
            st.success("Paramètres mis à jour !")

# PIED DE PAGE SIGNATURE
st.sidebar.divider()
st.sidebar.caption(f"Propulsé par {MY_NAME}")
