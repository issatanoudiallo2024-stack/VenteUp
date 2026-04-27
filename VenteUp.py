import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import base64
import hashlib

# --- CONFIGURATION ---
st.set_page_config(page_title="VenteUp Multi-User", layout="wide", page_icon="👤")

# --- FONCTIONS BASE DE DONNÉES ---
def get_connection():
    return sqlite3.connect('venteup_multi.db', check_same_thread=False)

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Table Utilisateurs
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, boutique_name TEXT)''')
    # Table Produits liée à user_id
    c.execute('''CREATE TABLE IF NOT EXISTS produits
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nom TEXT, p_achat REAL, p_vente REAL, qte INTEGER, seuil INTEGER)''')
    # Table Ventes liée à user_id
    c.execute('''CREATE TABLE IF NOT EXISTS ventes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, produit_id INTEGER, nom_prod TEXT, qte_v INTEGER, date_v TIMESTAMP, total REAL, benef REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- GESTION DE LA SESSION ---
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None

# --- AUTHENTIFICATION ---
def login_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, username FROM users WHERE username = ? AND password = ?', (username, hash_password(password)))
    data = c.fetchone()
    conn.close()
    return data

def signup_user(username, password, boutique):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password, boutique_name) VALUES (?,?,?)', (username, hash_password(password), boutique))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

# --- ÉCRAN DE CONNEXION ---
if st.session_state['user_id'] is None:
    st.title("🚀 Bienvenue sur VenteUp")
    choice = st.sidebar.selectbox("Action", ["Connexion", "Inscription"])
    
    if choice == "Inscription":
        st.subheader("Créer un nouveau compte")
        new_user = st.text_input("Nom d'utilisateur")
        new_boutique = st.text_input("Nom de votre boutique")
        new_pass = st.text_input("Mot de passe", type='password')
        if st.button("S'inscrire"):
            if signup_user(new_user, new_pass, new_boutique):
                st.success("Compte créé ! Connectez-vous à gauche.")
            else:
                st.error("Ce nom d'utilisateur existe déjà.")

    else:
        st.subheader("Accéder à votre espace")
        user = st.text_input("Utilisateur")
        pasw = st.text_input("Mot de passe", type='password')
        if st.button("Se connecter"):
            result = login_user(user, pasw)
            if result:
                st.session_state['user_id'] = result[0]
                st.session_state['username'] = result[1]
                st.rerun()
            else:
                st.error("Identifiants incorrects")
    
    st.info("🛠️ Support Technique : Issa Diallo | Issatanoudiallo2024@gmail.com")
    st.stop()

# --- SI CONNECTÉ ---
user_id = st.session_state['user_id']

with st.sidebar:
    st.success(f"Connecté : {st.session_state['username']}")
    if st.button("Déconnexion"):
        st.session_state['user_id'] = None
        st.rerun()
    menu = st.radio("Navigation", ["📊 Dashboard", "🛒 Caisse", "📦 Stocks", "🧾 Factures"])

# --- FILTRAGE DES DONNÉES PAR UTILISATEUR ---
conn = get_connection()

if menu == "📊 Dashboard":
    st.title("Mon Tableau de Bord")
    df_v = pd.read_sql(f"SELECT * FROM ventes WHERE user_id = {user_id}", conn)
    st.metric("Total Ventes", f"{df_v['total'].sum():,.0f} FG")

elif menu == "🛒 Caisse":
    st.title("Faire une Vente")
    prods = pd.read_sql(f"SELECT * FROM produits WHERE user_id = {user_id} AND qte > 0", conn)
    if not prods.empty:
        with st.form("v_form"):
            p_nom = st.selectbox("Produit", prods['nom'].tolist())
            qte_v = st.number_input("Quantité", min_value=1)
            if st.form_submit_button("Vendre"):
                p_info = prods[prods['nom'] == p_nom].iloc[0]
                total = qte_v * p_info['p_vente']
                benef = (p_info['p_vente'] - p_info['p_achat']) * qte_v
                c = conn.cursor()
                c.execute("INSERT INTO ventes (user_id, produit_id, nom_prod, qte_v, date_v, total, benef) VALUES (?,?,?,?,?,?,?)",
                          (user_id, int(p_info['id']), p_nom, qte_v, datetime.now().strftime("%d/%m/%Y %H:%M"), total, benef))
                c.execute("UPDATE produits SET qte = qte - ? WHERE id = ? AND user_id = ?", (qte_v, int(p_info['id']), user_id))
                conn.commit()
                st.success("Vendu !")
    else:
        st.warning("Ajoutez des produits dans votre stock d'abord.")

elif menu == "📦 Stocks":
    st.title("Mon Stock Privé")
    t1, t2 = st.tabs(["Inventaire", "Ajouter"])
    with t1:
        df_p = pd.read_sql(f"SELECT * FROM produits WHERE user_id = {user_id}", conn)
        st.dataframe(df_p, use_container_width=True)
    with t2:
        with st.form("add_p"):
            n = st.text_input("Nom du produit")
            pa = st.number_input("Prix Achat")
            pv = st.number_input("Prix Vente")
            q = st.number_input("Quantité")
            if st.form_submit_button("Enregistrer"):
                conn.execute("INSERT INTO produits (user_id, nom, p_achat, p_vente, qte, seuil) VALUES (?,?,?,?,?,?)",
                             (user_id, n, pa, pv, q, 5))
                conn.commit()
                st.rerun()

elif menu == "🧾 Factures":
    st.title("Mes Factures")
    df_v = pd.read_sql(f"SELECT * FROM ventes WHERE user_id = {user_id} ORDER BY id DESC", conn)
    st.write("Ici, vous ne voyez que vos propres ventes.")
    st.dataframe(df_v)

conn.close()
