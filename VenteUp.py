import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
from PIL import Image, ImageDraw
import io

# --- 🛠️ INFOS DU CONCEPTEUR (FIXES) ---
CONCEPTEUR_NOM = "Issa Diallo"
CONCEPTEUR_TEL = "610 51 89 73"
CONCEPTEUR_MAIL = "issatanoudiallo2024@gmail.com"

st.set_page_config(page_title="VenteUp Pro", page_icon="🏢", layout="wide")

# --- 🗄️ BASE DE DONNÉES ---
def get_connection():
    return sqlite3.connect('venteup_final_v12.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nom TEXT, p_achat REAL, p_vente REAL, stock INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, client_nom TEXT, client_tel TEXT, client_adr TEXT, details TEXT, total REAL, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS depenses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, motif TEXT, montant REAL, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS config (user_id INTEGER PRIMARY KEY, boutique TEXT, gerant TEXT, tel TEXT, mail TEXT, adresse TEXT)')
    conn.commit()
    conn.close()

init_db()

def hash_p(p): return hashlib.sha256(str.encode(p)).hexdigest()

# --- 📄 GÉNÉRATEUR DE FACTURE ---
def generer_facture_pro(conf, client, panier, total):
    img = Image.new('RGB', (800, 1100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 800, 90], fill=(44, 62, 80)) 
    d.text((300, 35), "FACTURE COMMERCIALE", fill=(255, 255, 255))
    
    # Infos Boutique (Gauche)
    y_info = 120
    d.text((40, y_info), "ÉMETTEUR :", fill=(44, 62, 80))
    d.text((40, y_info+25), conf['nom'].upper(), fill=(0,0,0))
    d.text((40, y_info+50), f"Gérant : {conf['gerant']}", fill=(80,80,80))
    d.text((40, y_info+75), f"Tél : {conf['tel']}", fill=(80,80,80))
    d.text((40, y_info+100), f"Email : {conf['mail']}", fill=(80,80,80))
    d.text((40, y_info+125), f"Adr : {conf['adr']}", fill=(80,80,80))
    
    # Infos Client (Droite)
    d.text((450, y_info), "CLIENT :", fill=(44, 62, 80))
    d.text((450, y_info+25), client['nom'].upper(), fill=(0,0,0))
    d.text((450, y_info+50), f"Tél : {client['tel']}", fill=(80,80,80))
    d.text((450, y_info+75), f"Adresse : {client['adr']}", fill=(80,80,80))
    
    # Tableau
    y_tab = 350
    d.rectangle([40, y_tab, 760, y_tab+35], fill=(236, 240, 241))
    d.text((45, y_tab+10), "N°   DÉSIGNATION          QTÉ      P. UNITAIRE      TOTAL GNF", fill=(0,0,0))
    
    y_row = y_tab + 40
    for i, item in enumerate(panier, 1):
        d.text((45, y_row), f"{i}    {item['nom'][:20]}         {item['qte']}       {item['pu']:,}       {item['tot']:,}", fill=(50,50,50))
        y_row += 30
        
    d.rectangle([450, y_row+20, 760, y_row+60], fill=(44, 62, 80))
    d.text((470, y_row+35), f"TOTAL : {total:,} GNF", fill=(255,255,255))
    d.text((40, 1050), f"Conçu par {CONCEPTEUR_NOM} | {CONCEPTEUR_TEL}", fill=(150,150,150))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# --- 🔐 ACCÈS ---
if 'user_id' not in st.session_state:
    st.title("🔐 Accès VenteUp")
    conn = get_connection()
    user_exists = conn.execute("SELECT count(*) FROM users").fetchone()[0]
    conn.close()

    if user_exists == 0:
        with st.form("Initialisation"):
            u = st.text_input("Identifiant Gérant")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Créer le compte unique"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO users (username, password) VALUES (?,?)", (u, hash_p(p)))
                uid = cur.lastrowid
                cur.execute("INSERT INTO config VALUES (?, 'MA BOUTIQUE', 'GÉRANT', '000', 'mail@boutique.com', 'ADRESSE')", (uid,))
                conn.commit()
                conn.close()
                st.success("Compte créé ! Connectez-vous.")
                st.rerun()
    else:
        with st.form("Login"):
            u, p = st.text_input("Utilisateur"), st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Connexion"):
                conn = get_connection()
                res = conn.execute("SELECT id FROM users WHERE username=? AND password=?", (u, hash_p(p))).fetchone()
                conn.close()
                if res:
                    st.session_state.user_id = res[0]
                    st.rerun()
                else: st.error("Identifiants incorrects.")
    st.stop()

# --- 🏢 INTERFACE ---
UID = st.session_state.user_id
conn = get_connection()
c_data = conn.execute("SELECT boutique, gerant, tel, mail, adresse FROM config WHERE user_id=?", (UID,)).fetchone()
conn.close()
conf = {"nom": c_data[0], "gerant": c_data[1], "tel": c_data[2], "mail": c_data[3], "adr": c_data[4]}

st.sidebar.title(f"🏢 {conf['nom']}")
menu = ["🛒 Ventes", "📦 Stock & Réappro", "💸 Dépenses", "📊 Historique", "⚙️ Paramètres"]
choix = st.sidebar.radio("Navigation", menu)

if choix == "⚙️ Paramètres":
    st.header("⚙️ Configuration complète de la Boutique")
    with st.form("cfg_complete"):
        new_nom = st.text_input("Nom de la boutique", conf['nom'])
        new_gerant = st.text_input("Nom du Gérant", conf['gerant'])
        new_tel = st.text_input("Numéro de téléphone", conf['tel'])
        new_mail = st.text_input("Adresse Email", conf['mail'])
        new_adr = st.text_input("Adresse Physique", conf['adr'])
        
        if st.form_submit_button("Enregistrer les modifications"):
            with get_connection() as conn:
                conn.execute("UPDATE config SET boutique=?, gerant=?, tel=?, mail=?, adresse=? WHERE user_id=?", 
                             (new_nom, new_gerant, new_tel, new_mail, new_adr, UID))
            st.success("Informations mises à jour !")
            st.rerun()

elif choix == "🛒 Ventes":
    st.header("🛒 Terminal de Vente")
    # ... (Le reste du code reste identique pour les autres onglets)

# --- 👤 SIGNATURE ---
st.sidebar.divider()
st.sidebar.markdown(f"**Concepteur :** {CONCEPTEUR_NOM}  \n📞 {CONCEPTEUR_TEL}  \n📧 {CONCEPTEUR_MAIL}")
