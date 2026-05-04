import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
from PIL import Image, ImageDraw
import io

# --- 🛠️ INFOS DU CONCEPTEUR (SCELLÉES) ---
CONCEPTEUR_NOM = "Issa Diallo"
CONCEPTEUR_TEL = "610 51 89 73"
CONCEPTEUR_MAIL = "issatanoudiallo2024@gmail.com"

st.set_page_config(page_title="VenteUp Pro", page_icon="🏢", layout="wide")

# --- 🗄️ BASE DE DONNÉES (AUTO-RÉPARATRICE) ---
def get_connection():
    return sqlite3.connect('venteup_cloud_v14.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Table Utilisateurs (Multi-comptes autorisés)
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)')
    # Table Produits
    c.execute('CREATE TABLE IF NOT EXISTS produits (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nom TEXT, p_achat REAL, p_vente REAL, stock INTEGER)')
    # Table Ventes
    c.execute('CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, client_nom TEXT, client_tel TEXT, client_adr TEXT, details TEXT, total REAL, date TEXT)')
    # Table Dépenses
    c.execute('CREATE TABLE IF NOT EXISTS depenses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, motif TEXT, montant REAL, date TEXT)')
    # Table Configuration Boutique
    c.execute('CREATE TABLE IF NOT EXISTS config (user_id INTEGER PRIMARY KEY, boutique TEXT, gerant TEXT, tel TEXT, mail TEXT, adresse TEXT)')
    conn.commit()
    conn.close()

init_db()

def hash_p(p): return hashlib.sha256(str.encode(p)).hexdigest()

# --- 📄 GÉNÉRATEUR DE FACTURE PRO (ATTEND LA FIN DES ACHATS) ---
def generer_facture_pro(conf, client, panier, total):
    img = Image.new('RGB', (800, 1100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 800, 90], fill=(44, 62, 80)) 
    d.text((300, 35), "FACTURE COMMERCIALE", fill=(255, 255, 255))
    
    y_info = 120
    # Bloc Boutique (Émetteur)
    d.text((40, y_info), "ÉMETTEUR :", fill=(44, 62, 80))
    d.text((40, y_info+25), conf['nom'].upper(), fill=(0,0,0))
    d.text((40, y_info+50), f"Gérant : {conf['gerant']}", fill=(80,80,80))
    d.text((40, y_info+75), f"Tél : {conf['tel']}", fill=(80,80,80))
    d.text((40, y_info+100), f"Email : {conf['mail']}", fill=(80,80,80))
    
    # Bloc Client (Destinataire)
    d.text((450, y_info), "DESTINATAIRE :", fill=(44, 62, 80))
    d.text((450, y_info+25), client['nom'].upper(), fill=(0,0,0))
    d.text((450, y_info+50), f"Tél : {client['tel']}", fill=(80,80,80))
    d.text((450, y_info+75), f"Adresse : {client['adr']}", fill=(80,80,80))
    
    # Tableau : N°, Désignation, Qté, P.U, Total
    y_tab = 350
    d.rectangle([40, y_tab, 760, y_tab+35], fill=(236, 240, 241))
    d.text((45, y_tab+10), "N°   DÉSIGNATION          QTÉ      P. UNITAIRE      TOTAL GNF", fill=(0,0,0))
    
    y_row = y_tab + 45
    for i, item in enumerate(panier, 1):
        d.text((45, y_row), f"{i}    {item['nom'][:20]}         {item['qte']}       {item['pu']:,}       {item['tot']:,}", fill=(50,50,50))
        y_row += 30
        
    # Total en bas à droite
    d.rectangle([450, y_row+30, 760, y_row+75], fill=(44, 62, 80))
    d.text((470, y_row+45), f"NET À PAYER : {total:,} GNF", fill=(255,255,255))
    
    # Pied de page Concepteur
    d.text((40, 1050), f"Produit par {CONCEPTEUR_NOM} | {CONCEPTEUR_TEL} | {CONCEPTEUR_MAIL}", fill=(150,150,150))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# --- 🔐 ACCÈS (MULTI-COMPTES STYLE FACEBOOK) ---
if 'user_id' not in st.session_state:
    st.title("🔐 VenteUp Pro - Connexion")
    
    tab_log, tab_reg = st.tabs(["Se Connecter", "Créer un Compte Boutique"])
    
    with tab_log:
        with st.form("Login"):
            u = st.text_input("Identifiant")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Entrer dans ma boutique"):
                conn = get_connection()
                res = conn.execute("SELECT id FROM users WHERE username=? AND password=?", (u, hash_p(p))).fetchone()
                conn.close()
                if res:
                    st.session_state.user_id = res[0]
                    st.rerun()
                else: st.error("Identifiants incorrects.")
                
    with tab_reg:
        with st.form("Register"):
            new_u = st.text_input("Choisir un Identifiant unique")
            new_p = st.text_input("Choisir un Mot de passe", type="password")
            if st.form_submit_button("Créer ma nouvelle boutique"):
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("INSERT INTO users (username, password) VALUES (?,?)", (new_u, hash_p(new_p)))
                    uid = cur.lastrowid
                    cur.execute("INSERT INTO config VALUES (?, 'MA BOUTIQUE', 'GÉRANT', '000', 'contact@mail.com', 'ADRESSE')", (uid,))
                    conn.commit()
                    conn.close()
                    st.success("Boutique créée ! Connectez-vous maintenant.")
                except:
                    st.error("Cet identifiant existe déjà.")
    st.stop()

# --- 🏢 INTERFACE PRINCIPALE ---
UID = st.session_state.user_id
if 'panier' not in st.session_state: st.session_state.panier = []

# Récupération config
conn = get_connection()
c_data = conn.execute("SELECT boutique, gerant, tel, mail, adresse FROM config WHERE user_id=?", (UID,)).fetchone()
conn.close()
conf = {"nom": c_data[0], "gerant": c_data[1], "tel": c_data[2], "mail": c_data[3], "adr": c_data[4]}

st.sidebar.title(f"🏢 {conf['nom']}")
menu = ["🛒 Ventes", "📦 Stock & Réappro", "💸 Dépenses", "📊 Historique", "⚙️ Paramètres"]
choix = st.sidebar.radio("Navigation", menu)

# --- 🛒 ONGLET VENTES (LOGIQUE ATTENTE PANIER) ---
if choix == "🛒 Ventes":
    st.header("🛒 Terminal de Vente")
    col1, col2 = st.columns(2)
    cn = col1.text_input("Nom Client *")
    ct = col2.text_input("Tél Client *")
    ca = col1.text_input("Adresse Client")
    
    conn = get_connection()
    prods = conn.execute("SELECT nom, p_vente, stock FROM produits WHERE user_id=? AND stock > 0", (UID,)).fetchall()
    conn.close()
    
    if prods:
        sel = st.selectbox("Sélectionner les articles (ajoutez-les un par un)", [""] + [p[0] for p in prods])
        if sel:
            inf = next(p for p in prods if p[0] == sel)
            q = st.number_input(f"Quantité pour {sel} (Max: {inf[2]})", 1, inf[2], 1)
            if st.button("➕ Ajouter au Panier"):
                st.session_state.panier.append({"nom": sel, "qte": q, "pu": inf[1], "tot": inf[1]*q})
                st.rerun()

    if st.session_state.panier:
        st.subheader("Panier actuel")
        st.table(st.session_state.panier)
        total_v = sum(i['tot'] for i in st.session_state.panier)
        
        c_v1, c_v2 = st.columns(2)
        if c_v1.button("🗑️ Vider le panier"):
            st.session_state.panier = []
            st.rerun()
            
        if c_v2.button(f"🧾 Terminer les achats et Générer la facture ({total_v:,} GNF)"):
            if cn and ct:
                img = generer_facture_pro(conf, {"nom":cn,"tel":ct,"adr":ca}, st.session_state.panier, total_v)
                st.image(img)
                st.download_button("📥 Télécharger Facture (PNG)", img, f"Facture_{cn}.png")
                
                # Validation en BDD et mise à jour stock
                with get_connection() as conn:
                    conn.execute("INSERT INTO ventes (user_id, client_nom, client_tel, details, total, date) VALUES (?,?,?,?,?,?)",
                                 (UID, cn, ct, str(st.session_state.panier), total_v, datetime.now().strftime("%d/%m/%Y")))
                    for item in st.session_state.panier:
                        conn.execute("UPDATE produits SET stock = stock - ? WHERE nom=? AND user_id=?", (item['qte'], item['nom'], UID))
                
                st.session_state.panier = [] # On vide après facturation
                st.success("Vente enregistrée avec succès !")
            else: st.error("Veuillez saisir le nom et le numéro du client.")

# --- LES AUTRES ONGLETS (RESTENT IDENTIQUES ET SÉCURISÉS) ---
elif choix == "📦 Stock & Réappro":
    st.header("📦 Gestion des Stocks")
    with st.form("stk"):
        n = st.text_input("Nom Article").upper()
        pa, pv, q = st.number_input("P. Achat"), st.number_input("P. Vente"), st.number_input("Quantité", min_value=1)
        if st.form_submit_button("Enregistrer"):
            with get_connection() as conn:
                conn.execute("INSERT INTO produits (user_id, nom, p_achat, p_vente, stock) VALUES (?,?,?,?,?)", (UID, n, pa, pv, q))
            st.success("Article ajouté au stock.")

elif choix == "💸 Dépenses":
    st.header("💸 Dépenses")
    with st.form("dep"):
        m, mt = st.text_input("Motif"), st.number_input("Montant")
        if st.form_submit_button("Enregistrer"):
            with get_connection() as conn:
                conn.execute("INSERT INTO depenses (user_id, motif, montant, date) VALUES (?,?,?,?)", (UID, m, mt, datetime.now().strftime("%d/%m/%Y")))
            st.success("Dépense enregistrée.")

elif choix == "📊 Historique":
    st.header("📊 Historique")
    conn = get_connection()
    data = conn.execute("SELECT date, client_nom, total FROM ventes WHERE user_id=? ORDER BY id DESC", (UID,)).fetchall()
    conn.close()
    if data: st.table(data)
    else: st.info("Aucune vente.")

elif choix == "⚙️ Paramètres":
    st.header("⚙️ Paramètres Boutique")
    with st.form("cfg"):
        bn, bg, bt, bm, ba = st.text_input("Nom Boutique", conf['nom']), st.text_input("Nom Gérant", conf['gerant']), st.text_input("Tél", conf['tel']), st.text_input("Mail", conf['mail']), st.text_input("Adresse", conf['adr'])
        if st.form_submit_button("Sauvegarder"):
            with get_connection() as conn:
                conn.execute("UPDATE config SET boutique=?, gerant=?, tel=?, mail=?, adresse=? WHERE user_id=?", (bn, bg, bt, bm, ba, UID))
            st.success("Paramètres sauvegardés !")
            st.rerun()

# --- 👤 SIGNATURE CONCEPTEUR (VERROUILLÉE) ---
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
