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

# --- 🗄️ BASE DE DONNÉES ---
def get_connection():
    return sqlite3.connect('venteup_pro_database.db', check_same_thread=False)

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

# --- 📄 GÉNÉRATEUR DE FACTURE PRO ---
def generer_facture_pro(conf, client, panier, total):
    img = Image.new('RGB', (800, 1100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 800, 90], fill=(44, 62, 80)) 
    d.text((300, 35), "FACTURE COMMERCIALE", fill=(255, 255, 255))
    
    # Infos Boutique (Gauche) / Client (Droite)
    y_info = 120
    d.text((40, y_info), "ÉMETTEUR :", fill=(44, 62, 80))
    d.text((40, y_info+25), conf['nom'].upper(), fill=(0,0,0))
    d.text((40, y_info+50), f"Gérant : {conf['gerant']}", fill=(80,80,80))
    d.text((40, y_info+75), f"Tél : {conf['tel']}", fill=(80,80,80))
    
    d.text((450, y_info), "DESTINATAIRE :", fill=(44, 62, 80))
    d.text((450, y_info+25), client['nom'].upper(), fill=(0,0,0))
    d.text((450, y_info+50), f"Tél : {client['tel']}", fill=(80,80,80))
    d.text((450, y_info+75), f"Adresse : {client['adr']}", fill=(80,80,80))
    
    # Tableau Colonnes : N°, Désignation, Qté, P.U, Total
    y_tab = 350
    d.rectangle([40, y_tab, 760, y_tab+35], fill=(236, 240, 241))
    d.text((45, y_tab+10), "N°   DÉSIGNATION          QTÉ      P. UNITAIRE      TOTAL GNF", fill=(0,0,0))
    
    y_row = y_tab + 45
    for i, item in enumerate(panier, 1):
        d.text((45, y_row), f"{i}    {item['nom'][:20]}         {item['qte']}       {item['pu']:,}       {item['tot']:,}", fill=(50,50,50))
        y_row += 30
        
    d.rectangle([450, y_row+30, 760, y_row+75], fill=(44, 62, 80))
    d.text((470, y_row+45), f"NET À PAYER : {total:,} GNF", fill=(255,255,255))
    d.text((40, 1050), f"Logiciel conçu par {CONCEPTEUR_NOM} | {CONCEPTEUR_TEL}", fill=(150,150,150))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# --- 🔐 ACCÈS (INSCRIPTION UNIQUE) ---
if 'user_id' not in st.session_state:
    st.title("🔐 Accès VenteUp Pro")
    conn = get_connection()
    user_count = conn.execute("SELECT count(*) FROM users").fetchone()[0]
    conn.close()

    if user_count == 0:
        st.info("👋 Bienvenue ! Créez votre compte unique de gérant.")
        with st.form("Inscription"):
            u = st.text_input("Identifiant")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Activer mon application"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO users (username, password) VALUES (?,?)", (u, hash_p(p)))
                uid = cur.lastrowid
                # Initialisation des paramètres par défaut
                cur.execute("INSERT INTO config VALUES (?, 'Ma Boutique', 'Gérant', '000', 'email@boutique.com', 'Adresse')", (uid,))
                conn.commit()
                conn.close()
                st.success("Compte créé avec succès !")
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
                else: st.error("Identifiants incorrects.")
    st.stop()

# --- 🏢 INTERFACE ---
UID = st.session_state.user_id
if 'panier' not in st.session_state: st.session_state.panier = []

conn = get_connection()
c_data = conn.execute("SELECT boutique, gerant, tel, mail, adresse FROM config WHERE user_id=?", (UID,)).fetchone()
conn.close()
conf = {"nom": c_data[0], "gerant": c_data[1], "tel": c_data[2], "mail": c_data[3], "adr": c_data[4]}

st.sidebar.title(f"🏢 {conf['nom']}")
menu = ["🛒 Ventes", "📦 Stock & Réappro", "💸 Dépenses", "📊 Historique", "⚙️ Paramètres"]
choix = st.sidebar.radio("Navigation", menu)

# --- 🛒 VENTES ---
if choix == "🛒 Ventes":
    st.header("🛒 Terminal de Vente")
    c1, c2 = st.columns(2)
    cn = c1.text_input("Nom Client *")
    ct = c2.text_input("Tél Client *")
    ca = c1.text_input("Adresse Client")
    
    conn = get_connection()
    prods = conn.execute("SELECT nom, p_vente, stock FROM produits WHERE user_id=? AND stock > 0", (UID,)).fetchall()
    conn.close()
    
    if not prods:
        st.warning("⚠️ Votre stock est vide. Allez dans '📦 Stock & Réappro' pour ajouter des articles.")
    else:
        sel = st.selectbox("Choisir un article", [""] + [p[0] for p in prods])
        if sel:
            inf = next(p for p in prods if p[0] == sel)
            q = st.number_input("Quantité", 1, inf[2], 1)
            if st.button("➕ Ajouter au Panier"):
                st.session_state.panier.append({"nom": sel, "qte": q, "pu": inf[1], "tot": inf[1]*q})
                st.rerun()

    if st.session_state.panier:
        st.subheader("Articles dans le panier")
        st.table(st.session_state.panier)
        total_v = sum(i['tot'] for i in st.session_state.panier)
        if st.button(f"✅ Valider & Facture ({total_v:,} GNF)"):
            if cn and ct:
                img = generer_facture_pro(conf, {"nom":cn,"tel":ct,"adr":ca}, st.session_state.panier, total_v)
                st.image(img)
                # Enregistrement Vente
                with get_connection() as conn:
                    conn.execute("INSERT INTO ventes (user_id, client_nom, client_tel, details, total, date) VALUES (?,?,?,?,?,?)",
                                 (UID, cn, ct, str(st.session_state.panier), total_v, datetime.now().strftime("%d/%m/%Y")))
                    for item in st.session_state.panier:
                        conn.execute("UPDATE produits SET stock = stock - ? WHERE nom=? AND user_id=?", (item['qte'], item['nom'], UID))
                st.session_state.panier = []
                st.success("Vente réussie !")
            else: st.error("Remplissez le nom et le tél du client.")

# --- 📦 STOCK ---
elif choix == "📦 Stock & Réappro":
    st.header("📦 Gestion des Stocks")
    with st.form("add_stock"):
        n = st.text_input("Nom de l'article").upper()
        pa = st.number_input("Prix d'Achat (GNF)", min_value=0.0)
        pv = st.number_input("Prix de Vente (GNF)", min_value=0.0)
        q = st.number_input("Quantité à ajouter", min_value=1, step=1)
        if st.form_submit_button("Enregistrer l'article"):
            with get_connection() as conn:
                conn.execute("INSERT INTO produits (user_id, nom, p_achat, p_vente, stock) VALUES (?,?,?,?,?)", (UID, n, pa, pv, q))
            st.success(f"L'article {n} a été ajouté au stock !")

# --- 💸 DÉPENSES ---
elif choix == "💸 Dépenses":
    st.header("💸 Suivi des Dépenses")
    with st.form("add_dep"):
        m = st.text_input("Motif de la dépense")
        mt = st.number_input("Montant (GNF)", min_value=0.0)
        if st.form_submit_button("Enregistrer la dépense"):
            with get_connection() as conn:
                conn.execute("INSERT INTO depenses (user_id, motif, montant, date) VALUES (?,?,?,?)", (UID, m, mt, datetime.now().strftime("%d/%m/%Y")))
            st.success("Dépense enregistrée.")

# --- 📊 HISTORIQUE ---
elif choix == "📊 Historique":
    st.header("📊 Historique des Ventes")
    conn = get_connection()
    data = conn.execute("SELECT date, client_nom, total FROM ventes WHERE user_id=? ORDER BY id DESC", (UID,)).fetchall()
    conn.close()
    if data:
        st.table(data)
    else:
        st.info("Aucune vente enregistrée pour le moment.")

# --- ⚙️ PARAMÈTRES ---
elif choix == "⚙️ Paramètres":
    st.header("⚙️ Paramètres de la Boutique")
    with st.form("config_form"):
        b_n = st.text_input("Nom de la boutique", conf['nom'])
        b_g = st.text_input("Nom du Gérant", conf['gerant'])
        b_t = st.text_input("Numéro de téléphone", conf['tel'])
        b_m = st.text_input("Email", conf['mail'])
        b_a = st.text_input("Adresse", conf['adr'])
        if st.form_submit_button("Sauvegarder les modifications"):
            with get_connection() as conn:
                conn.execute("UPDATE config SET boutique=?, gerant=?, tel=?, mail=?, adresse=? WHERE user_id=?", 
                             (b_n, b_g, b_t, b_m, b_a, UID))
            st.success("Informations boutique mises à jour !")
            st.rerun()

# --- 👤 SIGNATURE FIXE (ISSA DIALLO) ---
st.sidebar.divider()
st.sidebar.markdown(f"""
<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border-left: 5px solid #2ecc71;">
    <p style="margin: 0; font-size: 0.8em; color: #555;"><b>👨‍💻 Concepteur :</b></p>
    <p style="margin: 0; font-weight: bold; color: #2ecc71;">{CONCEPTEUR_NOM}</p>
    <p style="margin: 0; font-size: 0.8em;">📞 {CONCEPTEUR_TEL}</p>
    <p style="margin: 0; font-size: 0.8em;">📧 {CONCEPTEUR_MAIL}</p>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("Se déconnecter"):
    del st.session_state.user_id
    st.rerun()
