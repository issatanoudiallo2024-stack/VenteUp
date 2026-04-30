import streamlit as st
import sqlite3
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="VenteUp Pro - Système Complet", page_icon="🏢", layout="wide")

# --- BASE DE DONNÉES ---
def init_db():
    with sqlite3.connect('venteup_final.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE, 
            p_achat REAL, p_vente REAL, stock INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, client_nom TEXT, client_tel TEXT,
            client_adr TEXT, client_mail TEXT, details TEXT, total REAL, date TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS depenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, date TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY, boutique TEXT, gerant TEXT, tel TEXT, mail TEXT, adresse TEXT)''')
        cursor.execute("INSERT OR IGNORE INTO config (id, boutique, gerant, tel, mail, adresse) VALUES (1, 'Ma Boutique', 'Gérant', '600000000', 'contact@boutique.com', 'Conakry')")
        conn.commit()

init_db()

def get_config():
    conn = sqlite3.connect('venteup_final.db')
    data = conn.execute("SELECT boutique, gerant, tel, mail, adresse FROM config WHERE id=1").fetchone()
    conn.close()
    return {"boutique": data[0], "gerant": data[1], "tel": data[2], "mail": data[3], "adr": data[4]}

# --- GÉNÉRATEUR IMAGE FACTURE ---
def generer_facture_img(conf, client, panier, total):
    img = Image.new('RGB', (600, 850), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    # Style
    d.rectangle([0, 0, 600, 100], fill=(46, 204, 113)) # Bandeau Vert Pro
    d.text((180, 35), conf['boutique'].upper(), fill=(255, 255, 255))
    
    # Infos Entreprise & Client
    y = 120
    d.text((20, y), f"Boutique : {conf['boutique']} | Tel : {conf['tel']}", fill=(0,0,0))
    d.text((20, y+20), f"Client : {client['nom']} | Tel : {client['tel']}", fill=(0,0,0))
    d.text((20, y+40), f"Adresse : {client['adr']}", fill=(0,0,0))
    
    d.line([(20, 190), (580, 190)], fill=(0,0,0), width=2)
    
    # Articles
    y = 210
    d.text((20, y), "DESIGNATION", fill=(0,0,0))
    d.text((450, y), "TOTAL (GNF)", fill=(0,0,0))
    for item in panier:
        y += 30
        d.text((20, y), f"- {item['nom']} (x{item['qte']})", fill=(50,50,50))
        d.text((450, y), f"{item['total']}", fill=(50,50,50))
    
    d.line([(20, y+40), (580, y+40)], fill=(0,0,0), width=2)
    d.text((300, y+60), f"NET A PAYER : {total} GNF", fill=(255,0,0))
    d.text((200, 800), f"Signature Gérant : {conf['gerant']}", fill=(150,150,150))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# --- INTERFACE ---
conf = get_config()
st.sidebar.title(f"🏢 {conf['boutique']}")
menu = ["🛒 Panier de Vente", "📦 Stock & Réappro.", "💸 Dépenses", "📊 Historique", "⚙️ Paramètres"]
choix = st.sidebar.radio("Navigation", menu)

if 'panier' not in st.session_state: st.session_state.panier = []

# --- 1. VENTE ---
if choix == "🛒 Panier de Vente":
    st.header("🛒 Nouvelle Vente Groupée")
    col1, col2 = st.columns(2)
    c_nom = col1.text_input("Nom Client *")
    c_tel = col2.text_input("Téléphone *")
    c_adr = col1.text_input("Adresse Client")
    c_mail = col2.text_input("Email Client")

    st.divider()
    conn = sqlite3.connect('venteup_final.db')
    prods = conn.execute("SELECT nom, p_vente, stock FROM produits WHERE stock > 0").fetchall()
    conn.close()
    
    p_sel = st.selectbox("Choisir un article", [""] + [p[0] for p in prods])
    if p_sel:
        info = next(p for p in prods if p[0] == p_sel)
        qte = st.number_input("Quantité", min_value=1, max_value=info[2], value=1)
        if st.button("➕ Ajouter au Panier"):
            st.session_state.panier.append({"nom": p_sel, "qte": qte, "total": info[1]*qte})

    if st.session_state.panier:
        total_g = sum(item['total'] for item in st.session_state.panier)
        st.table(st.session_state.panier)
        st.write(f"### TOTAL : {total_g} GNF")
        
        if st.button("✅ Valider & Facture Image"):
            if c_nom and c_tel:
                img = generer_facture_img(conf, {"nom": c_nom, "tel": c_tel, "adr": c_adr}, st.session_state.panier, total_g)
                st.image(img)
                st.download_button("📥 Télécharger la Facture (IMAGE)", img, f"Facture_{c_nom}.png", "image/png")
                st.session_state.panier = []
            else: st.error("Renseignez le nom et le numéro du client !")

# --- 2. STOCK ---
elif choix == "📦 Stock & Réappro.":
    st.header("📦 Gestion des Produits")
    with st.form("form_stock"):
        n = st.text_input("Désignation").upper()
        pa = st.number_input("Prix Achat")
        pv = st.number_input("Prix Vente")
        q = st.number_input("Quantité")
        if st.form_submit_button("Enregistrer / Réapprovisionner"):
            with sqlite3.connect('venteup_final.db') as conn:
                conn.execute("INSERT OR REPLACE INTO produits (nom, p_achat, p_vente, stock) VALUES (?,?,?,?)", (n,pa,pv,q))
            st.success("Stock mis à jour !")

# --- 3. DEPENSES ---
elif choix == "💸 Dépenses":
    st.header("💸 Suivi des Frais")
    with st.form("f_dep"):
        motif = st.text_input("Motif (Loyer, Transport...)")
        montant = st.number_input("Montant")
        if st.form_submit_button("Enregistrer Dépense"):
            with sqlite3.connect('venteup_final.db') as conn:
                conn.execute("INSERT INTO depenses (motif, montant, date) VALUES (?,?,?)", (motif, montant, datetime.now().strftime("%d/%m/%Y")))
            st.success("Dépense enregistrée !")

# --- 4. PARAMETRES ---
elif choix == "⚙️ Paramètres":
    st.header("⚙️ Paramètres Boutique")
    with st.form("f_conf"):
        b = st.text_input("Nom Boutique", value=conf['boutique'])
        g = st.text_input("Gérant", value=conf['gerant'])
        t = st.text_input("Téléphone", value=conf['tel'])
        m = st.text_input("Mail", value=conf['mail'])
        a = st.text_input("Adresse", value=conf['adr'])
        if st.form_submit_button("Sauvegarder"):
            with sqlite3.connect('venteup_final.db') as conn:
                conn.execute("UPDATE config SET boutique=?, gerant=?, tel=?, mail=?, adresse=? WHERE id=1", (b,g,t,m,a))
            st.rerun()
