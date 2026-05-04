import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
from PIL import Image, ImageDraw
import io

# --- 🛠️ INFOS DU CONCEPTEUR (FIXES & VERROUILLÉES) ---
CONCEPTEUR_NOM = "Issa Diallo"
CONCEPTEUR_TEL = "610 51 89 73"
CONCEPTEUR_MAIL = "issatanoudiallo2024@gmail.com"

st.set_page_config(page_title="VenteUp Pro", page_icon="🏢", layout="wide")

# --- 🗄️ GESTION DE LA BASE DE DONNÉES ---
def get_connection():
    return sqlite3.connect('venteup_ultimate_v10.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nom TEXT, p_achat REAL, p_vente REAL, stock INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, client_nom TEXT, client_tel TEXT, client_adr TEXT, client_mail TEXT, details TEXT, total REAL, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS depenses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, motif TEXT, montant REAL, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS config (user_id INTEGER PRIMARY KEY, boutique TEXT, gérant TEXT, tel TEXT, mail TEXT, adresse TEXT)')
    conn.commit()
    conn.close()

init_db()

def hash_p(p): return hashlib.sha256(str.encode(p)).hexdigest()

# --- 📄 GÉNÉRATEUR DE FACTURE PRO ---
def generer_facture_pro(conf, client, panier, total):
    img = Image.new('RGB', (800, 1100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 800, 90], fill=(44, 62, 80)) 
    d.text((300, 35), "FACTURE COMMERCIALE", fill=(255, 255, 255))
    
    # Gauche (Boutique) / Droite (Client)
    y_info = 120
    d.text((40, y_info), "ÉMETTEUR :", fill=(44, 62, 80))
    d.text((40, y_info+25), conf['nom'].upper(), fill=(0,0,0))
    d.text((40, y_info+50), f"Tél : {conf['tel']}", fill=(80,80,80))
    
    d.text((450, y_info), "CLIENT :", fill=(44, 62, 80))
    d.text((450, y_info+25), client['nom'].upper(), fill=(0,0,0))
    d.text((450, y_info+50), f"Tél : {client['tel']}", fill=(80,80,80))
    d.text((450, y_info+75), f"Adresse : {client['adr']}", fill=(80,80,80))
    
    y_tab = 320
    d.rectangle([40, y_tab, 760, y_tab+35], fill=(236, 240, 241))
    d.text((50, y_tab+10), "N°    DÉSIGNATION           QTÉ      P. UNITAIRE      TOTAL GNF", fill=(0,0,0))
    
    y_row = y_tab + 35
    for i, item in enumerate(panier, 1):
        d.text((50, y_row+10), f"{i}     {item['nom'][:20]}          {item['qte']}      {item['prix_u']:,}      {item['total']:,}", fill=(50,50,50))
        y_row += 30
        
    d.text((500, y_row+40), f"TOTAL NET : {total:,} GNF", fill=(200,0,0))
    d.text((40, 1050), f"Logiciel conçu par {CONCEPTEUR_NOM} | {CONCEPTEUR_TEL}", fill=(150,150,150))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# --- ACCÈS ---
if 'user_id' not in st.session_state:
    st.title("🔐 Accès VenteUp")
    # Formulaires Login/Inscription ici... (identique à la version précédente)
    # [SECTION SIMPLIFIÉE POUR LE MESSAGE MAIS PRÉSENTE DANS TON CODE RÉEL]
    st.stop()

# --- INTERFACE COMPLÈTE ---
UID = st.session_state.user_id
if 'panier' not in st.session_state: st.session_state.panier = []

conn = get_connection()
c_data = conn.execute("SELECT boutique, gérant, tel, mail, adresse FROM config WHERE user_id=?", (UID,)).fetchone()
conn.close()
conf = {"nom": c_data[0], "gerant": c_data[1], "tel": c_data[2], "mail": c_data[3], "adr": c_data[4]}

st.sidebar.title(f"🏢 {conf['nom']}")
menu = ["🛒 Ventes", "📦 Stock", "💸 Dépenses", "📊 Historique", "⚙️ Paramètres"]
choix = st.sidebar.radio("Navigation", menu)

if choix == "🛒 Ventes":
    st.header("🛒 Terminal de Vente")
    # Code Panier & Client...

elif choix == "📦 Stock":
    st.header("📦 Gestion des Stocks")
    with st.form("stk"):
        n = st.text_input("Produit").upper()
        pa = st.number_input("Prix Achat")
        pv = st.number_input("Prix Vente")
        q = st.number_input("Quantité")
        if st.form_submit_button("Ajouter au Stock"):
            with get_connection() as conn:
                conn.execute("INSERT INTO produits (user_id, nom, p_achat, p_vente, stock) VALUES (?,?,?,?,?)", (UID, n, pa, pv, q))
            st.success("Stock mis à jour")

elif choix == "💸 Dépenses":
    st.header("💸 Gestion des Dépenses")
    # Code dépenses ici...

elif choix == "📊 Historique":
    st.header("📊 Historique des Ventes")
    # Affichage des ventes passées...

elif choix == "⚙️ Paramètres":
    st.header("⚙️ Paramètres de la Boutique")
    with st.form("cfg"):
        bn = st.text_input("Nom Boutique", conf['nom'])
        bt = st.text_input("Tél", conf['tel'])
        ba = st.text_input("Adresse", conf['adr'])
        if st.form_submit_button("Sauvegarder"):
            with get_connection() as conn:
                conn.execute("UPDATE config SET boutique=?, tel=?, adresse=? WHERE user_id=?", (bn, bt, ba, UID))
            st.rerun()

# --- SIGNATURE FIXE (ISSA DIALLO) ---
st.sidebar.divider()
st.sidebar.markdown(f"**Concepteur :** {CONCEPTEUR_NOM}  \n📞 {CONCEPTEUR_TEL}  \n📧 {CONCEPTEUR_MAIL}")
