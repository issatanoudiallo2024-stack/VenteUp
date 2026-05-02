import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
from PIL import Image, ImageDraw
import io

# --- INFOS DÉVELOPPEUR ---
MY_NAME = "Issa Diallo"
MY_TEL = "610 51 89 73"
MY_MAIL = "issatanoudiallo2024@gmail.com"

st.set_page_config(page_title="VenteUp Pro", page_icon="🏢", layout="wide")

# --- CONNEXION BDD SÉCURISÉE ---
def get_connection():
    return sqlite3.connect('venteup_v5.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nom TEXT, p_achat REAL, p_vente REAL, stock INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, client_nom TEXT, client_tel TEXT, client_adr TEXT, details TEXT, total REAL, date TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS depenses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, motif TEXT, montant REAL, date TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS config (user_id INTEGER PRIMARY KEY, boutique TEXT, gerant TEXT, tel TEXT, mail TEXT, adresse TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- SÉCURITÉ ---
def hash_pass(p): return hashlib.sha256(str.encode(p)).hexdigest()

# Vérifier s'il y a déjà un utilisateur enregistré
def count_users():
    conn = get_connection()
    res = conn.execute("SELECT count(*) FROM users").fetchone()[0]
    conn.close()
    return res

# --- GESTION ACCÈS ---
if 'user_id' not in st.session_state:
    st.title("🚀 VenteUp - Accès Sécurisé")
    
    # On vérifie si un compte existe
    nb_utilisateurs = count_users()
    
    if nb_utilisateurs == 0:
        st.warning("⚠️ Aucun compte détecté. Créez votre compte unique de gérant.")
        with st.form("Inscription Unique"):
            nu = st.text_input("Nom d'utilisateur souhaité")
            np = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Créer mon compte définitif"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO users (username, password) VALUES (?,?)", (nu, hash_pass(np)))
                uid = cur.lastrowid
                cur.execute("INSERT INTO config VALUES (?,?,?,?,?,?)", (uid, "MA BOUTIQUE", "GÉRANT", "000", "mail@pro.com", "CONAKRY"))
                conn.commit()
                conn.close()
                st.success("Compte créé avec succès ! Connectez-vous maintenant.")
                st.rerun()
    else:
        with st.form("Connexion"):
            st.info("Saisissez vos identifiants pour accéder à votre gestion.")
            u = st.text_input("Utilisateur")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter"):
                conn = get_connection()
                res = conn.execute("SELECT id FROM users WHERE username=? AND password=?", (u, hash_pass(p))).fetchone()
                conn.close()
                if res:
                    st.session_state.user_id = res[0]
                    st.rerun()
                else:
                    st.error("Identifiants incorrects.")

    st.stop()

# --- LE RESTE DU CODE (VENTE, STOCK, etc.) RESTE IDENTIQUE ---
# (Pense à utiliser get_connection() pour chaque interaction SQL)
