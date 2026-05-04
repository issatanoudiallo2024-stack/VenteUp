import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
from PIL import Image, ImageDraw
import io

# --- 🛠️ INFOS DU CONCEPTEUR (FIXES & SÉCURISÉES) ---
CONCEPTEUR_NOM = "Issa Diallo"
CONCEPTEUR_TEL = "610 51 89 73"
CONCEPTEUR_MAIL = "issatanoudiallo2024@gmail.com"

st.set_page_config(page_title="VenteUp Pro", page_icon="🏢", layout="wide")

# --- 🗄️ BASE DE DONNÉES ---
def get_connection():
    return sqlite3.connect('venteup_final_final.db', check_same_thread=False)

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

# --- 📄 GÉNÉRATEUR DE FACTURE (MISE EN PAGE EXACTE) ---
def generer_facture_pro(conf, client, panier, total):
    img = Image.new('RGB', (800, 1100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    
    # Header sombre pro
    d.rectangle([0, 0, 800, 90], fill=(44, 62, 80)) 
    d.text((300, 35), "FACTURE COMMERCIALE", fill=(255, 255, 255))
    
    y_info = 120
    # BOUTIQUE (Gauche)
    d.text((40, y_info), "ÉMETTEUR :", fill=(44, 62, 80))
    d.text((40, y_info+25), conf['nom'].upper(), fill=(0,0,0))
    d.text((40, y_info+50), f"Gérant : {conf['gerant']}", fill=(80,80,80))
    d.text((40, y_info+75), f"Tél : {conf['tel']}", fill=(80,80,80))
    d.text((40, y_info+100), f"Email : {conf['mail']}", fill=(80,80,80))
    
    # CLIENT (Droite)
    d.text((450, y_info), "DESTINATAIRE :", fill=(44, 62, 80))
    d.text((450, y_info+25), client['nom'].upper(), fill=(0,0,0))
    d.text((450, y_info+50), f"Tél : {client['tel']}", fill=(80,80,80))
    d.text((450, y_info+75), f"Adresse : {client['adr']}", fill=(80,80,80))
    
    # DATE (En bas des infos)
    date_v = datetime.now().strftime("%d/%m/%Y à %H:%M")
    d.text((40, 260), f"Date de facturation : {date_v}", fill=(0,0,0))
    d.line([(40, 285), (760, 285)], fill=(200,200,200))
    
    # TABLEAU (N°, Désignation, Qté, P.U, Total)
    y_tab = 310
    d.rectangle([40, y_tab, 760, y_tab+35], fill=(236, 240, 241))
    d.text((45, y_tab+10), "N°    DÉSIGNATION              QTÉ      P. UNITAIRE      P. TOTAL", fill=(0,0,0))
    
    y_row = y_tab + 45
    for i, item in enumerate(panier, 1):
        d.text((45, y_row), f"{i}", fill=(50,50,50))
        d.text((90, y_row), f"{item['nom'][:25]}", fill=(50,50,50))
        d.text((340, y_row), f"{item['qte']}", fill=(50,50,50))
        d.text((440, y_row), f"{item['pu']:,}", fill=(50,50,50))
        d.text((630, y_row), f"{item['tot']:,} GNF", fill=(50,50,50))
        y_row += 35
        
    # TOTAL FINAL
    d.rectangle([450, y_row+30, 760, y_row+75], fill=(44, 62, 80))
    d.text((470, y_row+45), f"TOTAL À PAYER : {total:,} GNF", fill=(255,255,255))
    
    # SIGNATURE CONCEPTEUR
    d.text((40, 1050), f"Logiciel conçu par {CONCEPTEUR_NOM} | 📞 {CONCEPTEUR_TEL} | 📧 {CONCEPTEUR_MAIL}", fill=(150,150,150))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# --- 🔐 ACCÈS STYLE FACEBOOK ---
if 'user_id' not in st.session_state:
    st.title("🏢 VenteUp Pro - Accès")
    t1, t2 = st.tabs(["Connexion", "Ouvrir un compte Boutique"])
    with t1:
        with st.form("L"):
            u, p = st.text_input("Identifiant"), st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter"):
                conn = get_connection()
                res = conn.execute("SELECT id FROM users WHERE username=? AND password=?", (u, hash_p(p))).fetchone()
                conn.close()
                if res: st.session_state.user_id = res[0]; st.rerun()
                else: st.error("Identifiants incorrects.")
    with t2:
        with st.form("R"):
            nu, np = st.text_input("Nouvel Identifiant"), st.text_input("Nouveau Mot de passe", type="password")
            if st.form_submit_button("Créer ma boutique"):
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("INSERT INTO users (username, password) VALUES (?,?)", (nu, hash_p(np)))
                    uid = cur.lastrowid
                    cur.execute("INSERT INTO config VALUES (?, 'MA BOUTIQUE', 'GÉRANT', '000', 'contact@mail.com', 'ADRESSE')", (uid,))
                    conn.commit(); conn.close()
                    st.success("Compte créé ! Connectez-vous.")
                except: st.error("Cet identifiant est déjà pris.")
    st.stop()

# --- 🏠 INTERFACE PRINCIPALE ---
UID = st.session_state.user_id
if 'panier' not in st.session_state: st.session_state.panier = []

conn = get_connection()
c_data = conn.execute("SELECT boutique, gerant, tel, mail, adresse FROM config WHERE user_id=?", (UID,)).fetchone()
conn.close()
conf = {"nom": c_data[0], "gerant": c_data[1], "tel": c_data[2], "mail": c_data[3], "adr": c_data[4]}

st.sidebar.title(f"🏢 {conf['nom']}")
menu = ["🛒 Ventes", "📦 Stock", "💸 Dépenses", "📊 Historique", "⚙️ Paramètres"]
choix = st.sidebar.radio("Menu", menu)

if choix == "🛒 Ventes":
    st.header("🛒 Terminal de Vente")
    c1, c2 = st.columns(2)
    cn, ct, ca = c1.text_input("Nom Client *"), c2.text_input("Tél Client *"), c1.text_input("Adresse Client")
    
    conn = get_connection()
    prods = conn.execute("SELECT nom, p_vente, stock FROM produits WHERE user_id=? AND stock > 0", (UID,)).fetchall()
    conn.close()
    
    if prods:
        sel = st.selectbox("Ajouter un article au panier", [""] + [p[0] for p in prods])
        if sel:
            inf = next(p for p in prods if p[0] == sel)
            q = st.number_input(f"Quantité ({inf[2]} dispo)", 1, inf[2], 1)
            if st.button("➕ Ajouter au Panier"):
                st.session_state.panier.append({"nom": sel, "qte": q, "pu": inf[1], "tot": inf[1]*q})
                st.rerun()

    if st.session_state.panier:
        st.subheader("Articles sélectionnés")
        st.table(st.session_state.panier)
        total_v = sum(i['tot'] for i in st.session_state.panier)
        
        col_b1, col_b2 = st.columns(2)
        if col_b1.button("🗑️ Vider tout"): st.session_state.panier = []; st.rerun()
        if col_b2.button(f"🧾 Valider & Générer Facture ({total_v:,} GNF)"):
            if cn and ct:
                img = generer_facture_pro(conf, {"nom":cn,"tel":ct,"adr":ca}, st.session_state.panier, total_v)
                st.image(img)
                st.download_button("📥 Télécharger la Facture (PNG)", img, f"Facture_{cn}.png")
                # Sauvegarde BDD
                with get_connection() as conn:
                    conn.execute("INSERT INTO ventes (user_id, client_nom, client_tel, client_adr, details, total, date) VALUES (?,?,?,?,?,?,?)",
                                 (UID, cn, ct, ca, str(st.session_state.panier), total_v, datetime.now().strftime("%d/%m/%Y")))
                    for i in st.session_state.panier:
                        conn.execute("UPDATE produits SET stock = stock - ? WHERE nom=? AND user_id=?", (i['qte'], i['nom'], UID))
                st.session_state.panier = []
                st.success("Vente enregistrée !")
            else: st.error("Saisissez le nom et le tél du client.")

elif choix == "📦 Stock":
    st.header("📦 Gestion du Stock")
    with st.form("S"):
        n = st.text_input("Nom de l'article").upper()
        pa, pv, q = st.number_input("Prix Achat"), st.number_input("Prix Vente"), st.number_input("Quantité", 1)
        if st.form_submit_button("Enregistrer"):
            with get_connection() as conn:
                conn.execute("INSERT INTO produits (user_id, nom, p_achat, p_vente, stock) VALUES (?,?,?,?,?)", (UID, n, pa, pv, q))
            st.success("Produit ajouté !")

elif choix == "⚙️ Paramètres":
    st.header("⚙️ Paramètres Boutique")
    with st.form("P"):
        bn, bg, bt, bm, ba = st.text_input("Boutique", conf['nom']), st.text_input("Gérant", conf['gerant']), st.text_input("Tél", conf['tel']), st.text_input("Mail", conf['mail']), st.text_input("Adresse", conf['adr'])
        if st.form_submit_button("Sauvegarder"):
            with get_connection() as conn:
                conn.execute("UPDATE config SET boutique=?, gerant=?, tel=?, mail=?, adresse=? WHERE user_id=?", (bn, bg, bt, bm, ba, UID))
            st.rerun()

# --- 👤 SIGNATURE DU CONCEPTEUR ---
st.sidebar.divider()
st.sidebar.markdown(f"""
<div style="background-color: #2c3e50; padding: 15px; border-radius: 8px; color: white;">
    <p style="margin: 0; font-size: 0.7em;">DÉVELOPPÉ PAR :</p>
    <p style="margin: 0; font-weight: bold; font-size: 1.1em; color: #2ecc71;">{CONCEPTEUR_NOM}</p>
    <p style="margin: 5px 0 0 0; font-size: 0.8em;">📞 {CONCEPTEUR_TEL}</p>
    <p style="margin: 0; font-size: 0.8em;">📧 {CONCEPTEUR_MAIL}</p>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("Déconnexion"): del st.session_state.user_id; st.rerun()
