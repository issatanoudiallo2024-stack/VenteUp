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
    return sqlite3.connect('venteup_final_v9.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nom TEXT, p_achat REAL, p_vente REAL, stock INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, client_nom TEXT, client_tel TEXT, client_adr TEXT, client_mail TEXT, details TEXT, total REAL, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS config (user_id INTEGER PRIMARY KEY, boutique TEXT, gérant TEXT, tel TEXT, mail TEXT, adresse TEXT)')
    conn.commit()
    conn.close()

init_db()

def hash_p(p): return hashlib.sha256(str.encode(p)).hexdigest()

# --- 📄 GÉNÉRATEUR DE FACTURE PRO ---
def generer_facture_pro(conf, client, panier, total):
    img = Image.new('RGB', (800, 1100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    
    # En-tête
    d.rectangle([0, 0, 800, 90], fill=(44, 62, 80)) 
    d.text((300, 35), "FACTURE COMMERCIALE", fill=(255, 255, 255))
    
    # Mise en page Gauche (Boutique) / Droite (Client)
    y_info = 120
    d.text((40, y_info), "ÉMETTEUR :", fill=(44, 62, 80))
    d.text((40, y_info+25), conf['nom'].upper(), fill=(0,0,0))
    d.text((40, y_info+50), f"Tél : {conf['tel']}", fill=(80,80,80))
    d.text((40, y_info+75), f"Email : {conf['mail']}", fill=(80,80,80))
    
    d.text((450, y_info), "CLIENT :", fill=(44, 62, 80))
    d.text((450, y_info+25), client['nom'].upper(), fill=(0,0,0))
    d.text((450, y_info+50), f"Tél : {client['tel']}", fill=(80,80,80))
    d.text((450, y_info+75), f"Adresse : {client['adr']}", fill=(80,80,80))
    
    d.text((40, 260), f"Date : {datetime.now().strftime('%d/%m/%Y')}", fill=(0,0,0))
    
    # --- TABLEAU (N°, Désignation, Quantité, P.U, Total) ---
    y_tab = 300
    d.rectangle([40, y_tab, 760, y_tab+35], fill=(236, 240, 241))
    d.text((50, y_tab+10), "N°", fill=(0,0,0))
    d.text((100, y_tab+10), "DÉSIGNATION", fill=(0,0,0))
    d.text((380, y_tab+10), "QTÉ", fill=(0,0,0))
    d.text((480, y_tab+10), "P. UNITAIRE", fill=(0,0,0))
    d.text((650, y_tab+10), "TOTAL GNF", fill=(0,0,0))
    
    y_row = y_tab + 35
    for i, item in enumerate(panier, 1):
        d.line([(40, y_row+35), (760, y_row+35)], fill=(200,200,200))
        d.text((50, y_row+10), str(i), fill=(50,50,50))
        d.text((100, y_row+10), item['nom'], fill=(50,50,50))
        d.text((380, y_row+10), str(item['qte']), fill=(50,50,50))
        d.text((480, y_row+10), f"{item['prix_u']:,}", fill=(50,50,50))
        d.text((650, y_row+10), f"{item['total']:,}", fill=(50,50,50))
        y_row += 35
        
    # TOTAL
    d.rectangle([500, y_row+20, 760, y_row+60], fill=(44, 62, 80))
    d.text((510, y_row+35), f"NET À PAYER : {total:,} GNF", fill=(255,255,255))
    
    # Signature Concepteur
    d.text((40, 1050), f"Conçu par {CONCEPTEUR_NOM} | {CONCEPTEUR_TEL}", fill=(150,150,150))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# --- ACCÈS ---
if 'user_id' not in st.session_state:
    st.title("🔐 Accès VenteUp")
    conn = get_connection()
    user_count = conn.execute("SELECT count(*) FROM users").fetchone()[0]
    conn.close()

    if user_count == 0:
        with st.form("Inscription Unique"):
            u = st.text_input("Identifiant")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Activer mon application"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO users (username, password) VALUES (?,?)", (u, hash_p(p)))
                uid = cur.lastrowid
                cur.execute("INSERT INTO config VALUES (?, 'Ma Boutique', 'Gérant', '000', 'contact@mail.com', 'Conakry')", (uid,))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        with st.form("Login"):
            u = st.text_input("Utilisateur")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Connexion"):
                conn = get_connection()
                res = conn.execute("SELECT id FROM users WHERE username=? AND password=?", (u, hash_p(p))).fetchone()
                conn.close()
                if res:
                    st.session_state.user_id = res[0]
                    st.rerun()
                else: st.error("Identifiants incorrects.")
    st.stop()

# --- INTERFACE ---
UID = st.session_state.user_id
if 'panier' not in st.session_state: st.session_state.panier = []

conn = get_connection()
c_data = conn.execute("SELECT boutique, gérant, tel, mail, adresse FROM config WHERE user_id=?", (UID,)).fetchone()
conn.close()
conf = {"nom": c_data[0], "tel": c_data[2], "mail": c_data[3], "adr": c_data[4]}

st.sidebar.title(f"🏢 {conf['nom']}")
menu = ["🛒 Ventes", "📦 Stock", "⚙️ Paramètres"]
choix = st.sidebar.radio("Navigation", menu)

if choix == "🛒 Ventes":
    st.header("🛒 Nouvelle Vente")
    col1, col2 = st.columns(2)
    cn = col1.text_input("Nom Client *")
    ct = col2.text_input("Téléphone Client *")
    ca = col1.text_input("Adresse Client")
    
    conn = get_connection()
    prods = conn.execute("SELECT nom, p_vente, stock FROM produits WHERE user_id=? AND stock > 0", (UID,)).fetchall()
    conn.close()
    
    if prods:
        sel = st.selectbox("Article", [""] + [p[0] for p in prods])
        if sel:
            info = next(p for p in prods if p[0] == sel)
            q = st.number_input("Quantité", 1, info[2], 1)
            if st.button("➕ Ajouter au Panier"):
                st.session_state.panier.append({"nom": sel, "qte": q, "prix_u": info[1], "total": info[1]*q})
                st.rerun()

    if st.session_state.panier:
        st.table(st.session_state.panier)
        total_v = sum(i['total'] for i in st.session_state.panier)
        if st.button(f"✅ Générer Facture ({total_v:,} GNF)"):
            if cn and ct:
                img = generer_facture_pro(conf, {"nom":cn,"tel":ct,"adr":ca}, st.session_state.panier, total_v)
                st.image(img)
                st.download_button("📥 Télécharger PNG", img, f"Facture_{cn}.png")
                st.session_state.panier = []
            else: st.error("Informations client manquantes")

elif choix == "⚙️ Paramètres":
    st.header("⚙️ Ma Boutique")
    with st.form("cfg"):
        bn = st.text_input("Nom Boutique", conf['nom'])
        bt = st.text_input("Tél", conf['tel'])
        bm = st.text_input("Email", conf['mail'])
        ba = st.text_input("Adresse", conf['adr'])
        if st.form_submit_button("Sauvegarder"):
            conn = get_connection()
            conn.execute("UPDATE config SET boutique=?, tel=?, mail=?, adresse=? WHERE user_id=?", (bn, bt, bm, ba, UID))
            conn.commit()
            conn.close()
            st.rerun()

# --- SIGNATURE FIXE (ISSA DIALLO) ---
st.sidebar.divider()
st.sidebar.markdown(f"**Concepteur :** {CONCEPTEUR_NOM}  \n📞 {CONCEPTEUR_TEL}  \n📧 {CONCEPTEUR_MAIL}")
