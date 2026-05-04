import streamlit as st
import sqlite3
import hashlib

# --- INFOS ISSA DIALLO ---
MY_NAME = "Issa Diallo"
MY_TEL = "610 51 89 73"

st.set_page_config(page_title="VenteUp Pro", layout="wide")

# Connexion stable
def get_connection():
    return sqlite3.connect('venteup_v6.db', check_same_thread=False)

# Création des tables si elles n'existent pas
conn = get_connection()
conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)')
conn.execute('CREATE TABLE IF NOT EXISTS config (user_id INTEGER PRIMARY KEY, boutique TEXT)')
conn.close()

def hash_p(p): return hashlib.sha256(str.encode(p)).hexdigest()

# --- VERIFICATION DE L'ACCÈS ---
if 'user_id' not in st.session_state:
    st.title("🔐 Accès Restreint")
    
    conn = get_connection()
    user_count = conn.execute("SELECT count(*) FROM users").fetchone()[0]
    conn.close()

    if user_count == 0:
        st.subheader("Créez votre compte unique de gestion")
        with st.form("Inscription"):
            u = st.text_input("Identifiant")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Activer l'application"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO users (username, password) VALUES (?,?)", (u, hash_p(p)))
                uid = cur.lastrowid
                cur.execute("INSERT INTO config (user_id, boutique) VALUES (?,?)", (uid, "MA BOUTIQUE"))
                conn.commit()
                conn.close()
                st.success("Compte créé ! Connectez-vous maintenant.")
                st.rerun()
    else:
        with st.form("Login"):
            u = st.text_input("Utilisateur")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter"):
                conn = get_connection()
                res = conn.execute("SELECT id FROM users WHERE username=? AND password=?", (u, hash_p(p))).fetchone()
                conn.close()
                if res:
                    st.session_state.user_id = res[0]
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
    st.stop()

# --- SI CONNECTÉ : L'INTERFACE S'AFFICHE ICI ---
st.sidebar.title("🏢 Menu Principal")
menu = ["🛒 Vente", "📦 Stock", "💸 Dépenses", "⚙️ Paramètres"]
choix = st.sidebar.radio("Navigation", menu)

if choix == "🛒 Vente":
    st.header("Gestion des Ventes")
    st.write("Bienvenue dans votre espace de vente.")
    # Ton code de vente ici...

elif choix == "📦 Stock":
    st.header("Gestion du Stock")
    # Ton code de stock ici...

st.sidebar.divider()
st.sidebar.caption(f"Développé par {MY_NAME}")
