import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
from PIL import Image, ImageDraw
import io

# --- SIGNATURE DÉVELOPPEUR (FIXE) ---
MY_NAME = "Issa Diallo"
MY_TEL = "610 51 89 73"
MY_MAIL = "issatanoudiallo2024@gmail.com"

st.set_page_config(page_title="VenteUp Pro", page_icon="🏢", layout="wide")

# --- BASE DE DONNÉES ---
def init_db():
    with sqlite3.connect('venteup_final_saas.db') as conn:
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nom TEXT, p_achat REAL, p_vente REAL, stock INTEGER)')
        cursor.execute('CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, client_nom TEXT, client_tel TEXT, client_adr TEXT, client_mail TEXT, details TEXT, total REAL, date TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS depenses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, motif TEXT, montant REAL, date TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS config (user_id INTEGER PRIMARY KEY, boutique TEXT, gerant TEXT, tel TEXT, mail TEXT, adresse TEXT)')
        conn.commit()

init_db()

# --- AUTHENTIFICATION ---
def hash_pass(p): return hashlib.sha256(str.encode(p)).hexdigest()

if 'user_id' not in st.session_state:
    st.title("🚀 VenteUp - Connexion")
    t1, t2 = st.tabs(["Se connecter", "Créer un compte"])
    with t1:
        u = st.text_input("Utilisateur")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Connexion"):
            with sqlite3.connect('venteup_final_saas.db') as conn:
                res = conn.execute("SELECT id FROM users WHERE username=? AND password=?", (u, hash_pass(p))).fetchone()
            if res:
                st.session_state.user_id = res[0]
                st.rerun()
            else: st.error("Identifiants incorrects")
    with t2:
        nu = st.text_input("Nouvel Utilisateur")
        np = st.text_input("Nouveau Mot de passe", type="password")
        if st.button("S'inscrire"):
            try:
                with sqlite3.connect('venteup_final_saas.db') as conn:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO users (username, password) VALUES (?,?)", (nu, hash_pass(np)))
                    uid = cur.lastrowid
                    cur.execute("INSERT INTO config VALUES (?,?,?,?,?,?)", (uid, "MA BOUTIQUE", "GÉRANT", "000", "mail@pro.com", "CONAKRY"))
                st.success("Compte créé ! Connectez-vous.")
            except: st.error("Nom déjà pris.")
    st.stop()

# --- SESSION UTILISATEUR ---
UID = st.session_state.user_id

def get_cfg():
    conn = sqlite3.connect('venteup_final_saas.db')
    d = conn.execute("SELECT boutique, gerant, tel, mail, adresse FROM config WHERE user_id=?", (UID,)).fetchone()
    conn.close()
    return {"boutique": d[0], "gerant": d[1], "tel": d[2], "mail": d[3], "adr": d[4]}

# --- GÉNÉRATEUR FACTURE IMAGE ---
def draw_facture(conf, client, panier, total):
    img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 800, 80], fill=(46, 204, 113))
    d.text((320, 30), "FACTURE COMMERCIALE", fill=(255, 255, 255))
    
    # Gauche (Boutique) / Droite (Client)
    d.text((40, 100), f"BOUTIQUE : {conf['boutique']}", fill=(0,0,0))
    d.text((40, 120), f"Gérant : {conf['gerant']} | Tél : {conf['tel']}", fill=(50,50,50))
    d.text((40, 140), f"Adresse : {conf['adr']}", fill=(50,50,50))
    
    d.text((450, 100), f"CLIENT : {client['nom']}", fill=(0,0,0))
    d.text((450, 120), f"Tél : {client['tel']}", fill=(50,50,50))
    d.text((450, 140), f"Adresse : {client['adr']}", fill=(50,50,50))
    
    d.text((40, 180), f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}", fill=(0,0,0))
    
    # Tableau
    y = 230
    d.rectangle([40, y, 760, y+30], outline=(0,0,0))
    d.text((50, y+10), "N°   Désignation             Qté       P.U          Total", fill=(0,0,0))
    for i, item in enumerate(panier, 1):
        y += 30
        d.text((50, y+10), f"{i}    {item['nom'][:15]}          {item['qte']}       {item['pu']}      {item['tot']}", fill=(50,50,50))
    
    d.text((500, y+60), f"TOTAL : {total} GNF", fill=(255,0,0))
    d.text((40, 950), f"Logiciel par {MY_NAME} | {MY_TEL}", fill=(150,150,150))
    
    b = io.BytesIO()
    img.save(b, format='PNG')
    return b.getvalue()

# --- INTERFACE ---
conf = get_cfg()
st.sidebar.title(f"🏢 {conf['boutique']}")
st.sidebar.caption(f"Développeur : {MY_NAME}")
if st.sidebar.button("Se déconnecter"):
    del st.session_state.user_id
    st.rerun()

menu = ["🛒 Vente (Panier)", "📦 Stock & Réappro", "💸 Dépenses", "📊 Historique", "⚙️ Paramètres"]
choix = st.sidebar.radio("Menu", menu)

if 'cart' not in st.session_state: st.session_state.cart = []

if choix == "🛒 Vente (Panier)":
    st.header("🛒 Nouvelle Vente")
    c1, c2 = st.columns(2)
    cn = c1.text_input("Nom Client *")
    ct = c2.text_input("Téléphone *")
    ca = c1.text_input("Adresse")
    cm = c2.text_input("Email")
    
    conn = sqlite3.connect('venteup_final_saas.db')
    prods = conn.execute("SELECT nom, p_vente, stock FROM produits WHERE user_id=? AND stock > 0", (UID,)).fetchall()
    conn.close()
    
    ps = st.selectbox("Produit", [""] + [p[0] for p in prods])
    if ps:
        inf = next(p for p in prods if p[0] == ps)
        q = st.number_input("Quantité", 1, inf[2])
        if st.button("➕ Ajouter"):
            st.session_state.cart.append({"nom": ps, "qte": q, "pu": inf[1], "tot": inf[1]*q})
            st.rerun()

    if st.session_state.cart:
        st.table(st.session_state.cart)
        total = sum(i['tot'] for i in st.session_state.cart)
        if st.button(f"✅ Valider {total} GNF"):
            if cn and ct:
                img = draw_facture(conf, {"nom":cn,"tel":ct,"adr":ca}, st.session_state.cart, total)
                st.image(img)
                st.download_button("📥 Télécharger Facture", img, f"Facture_{cn}.png", "image/png")
                # Sauvegarde Vente & Mise à jour stock ici...
                st.session_state.cart = []
            else: st.error("Nom/Tel obligatoires")

elif choix == "📦 Stock & Réappro":
    st.header("📦 Stock & Réapprovisionnement")
    with st.form("stk"):
        n = st.text_input("Nom").upper()
        pa = st.number_input("Prix Achat")
        pv = st.number_input("Prix Vente")
        q = st.number_input("Quantité")
        if st.form_submit_button("Sauvegarder"):
            with sqlite3.connect('venteup_final_saas.db') as conn:
                conn.execute("INSERT OR REPLACE INTO produits (user_id, nom, p_achat, p_vente, stock) VALUES (?,?,?,?,?)", (UID,n,pa,pv,q))
            st.success("Produit mis à jour")

elif choix == "💸 Dépenses":
    st.header("💸 Dépenses")
    with st.form("dep"):
        m = st.text_input("Motif")
        mt = st.number_input("Montant")
        if st.form_submit_button("Ajouter"):
            with sqlite3.connect('venteup_final_saas.db') as conn:
                conn.execute("INSERT INTO depenses (user_id, motif, montant, date) VALUES (?,?,?,?)", (UID, m, mt, datetime.now().strftime("%d/%m/%Y")))
            st.success("Dépense enregistrée")

elif choix == "⚙️ Paramètres":
    st.header("⚙️ Paramètres Boutique")
    with st.form("p"):
        b = st.text_input("Boutique", conf['boutique'])
        g = st.text_input("Gérant", conf['gerant'])
        t = st.text_input("Tel", conf['tel'])
        m = st.text_input("Mail", conf['mail'])
        a = st.text_input("Adresse", conf['adr'])
        if st.form_submit_button("Mettre à jour"):
            with sqlite3.connect('venteup_final_saas.db') as conn:
                conn.execute("UPDATE config SET boutique=?, gerant=?, tel=?, mail=?, adresse=? WHERE user_id=?", (b,g,t,m,a,UID))
            st.rerun()

st.divider()
st.caption(f"Signature : {MY_NAME} | {MY_TEL} | {MY_MAIL}")
