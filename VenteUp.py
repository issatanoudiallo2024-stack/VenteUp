import streamlit as st
import sqlite3
from datetime import datetime
from fpdf import FPDF

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="VenteUp Pro", page_icon="🏢", layout="wide")

# --- BASE DE DONNÉES ---
def init_db():
    with sqlite3.connect('venteup_v2.db') as conn:
        cursor = conn.cursor()
        # Table Produits
        cursor.execute('''CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE, 
            p_achat REAL, p_vente REAL, stock INTEGER)''')
        # Table Ventes
        cursor.execute('''CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, client_nom TEXT, 
            client_tel TEXT, client_adr TEXT, client_mail TEXT,
            produit TEXT, total REAL, benefice REAL, date TEXT)''')
        # Table Dépenses
        cursor.execute('''CREATE TABLE IF NOT EXISTS depenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, motif TEXT, montant REAL, date TEXT)''')
        # Table Paramètres Entreprise
        cursor.execute('''CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY, boutique TEXT, gerant TEXT, tel TEXT, mail TEXT, adresse TEXT)''')
        # Insertion par défaut si vide
        cursor.execute("INSERT OR IGNORE INTO config (id, boutique, gerant, tel, mail, adresse) VALUES (1, 'Ma Boutique', 'Gérant', '000', 'mail@test.com', 'Adresse')")
        conn.commit()

init_db()

# --- FONCTION RÉCUPÉRATION CONFIG ---
def get_config():
    conn = sqlite3.connect('venteup_v2.db')
    cursor = conn.cursor()
    cursor.execute("SELECT boutique, gerant, tel, mail, adresse FROM config WHERE id=1")
    data = cursor.fetchone()
    conn.close()
    return {"boutique": data[0], "gerant": data[1], "tel": data[2], "mail": data[3], "adr": data[4]}

# --- GÉNÉRATEUR PDF ---
def generer_pdf(c_info, p_nom, total, boutique_info):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, boutique_info['boutique'].upper(), ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, f"Gérant : {boutique_info['gerant']} | Tel : {boutique_info['tel']}", ln=True, align='C')
    pdf.cell(0, 5, f"Adresse : {boutique_info['adr']}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "CLIENT :", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 6, f"Nom : {c_info['nom']} | Tel : {c_info['tel']}", ln=True)
    pdf.cell(0, 6, f"Adresse : {c_info['adr']}", ln=True)
    
    pdf.ln(10)
    pdf.cell(100, 8, "Désignation", border=1)
    pdf.cell(40, 8, "Total (GNF)", border=1, ln=True)
    pdf.cell(100, 8, p_nom, border=1)
    pdf.cell(40, 8, str(total), border=1, ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"TOTAL À PAYER : {total} GNF", ln=True, align='R')
    pdf.output(dest='S').encode('latin-1')
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
conf = get_config()
st.sidebar.title(f"🚀 {conf['boutique']}")
menu = ["🛒 Vente", "📦 Stock", "💸 Dépenses", "📊 Historique", "⚙️ Paramètres"]
choix = st.sidebar.radio("Navigation", menu)

# --- SECTION PARAMÈTRES ---
if choix == "⚙️ Paramètres":
    st.header("⚙️ Configuration de l'Entreprise")
    with st.form("conf_form"):
        new_b = st.text_input("Nom de la boutique", value=conf['boutique'])
        new_g = st.text_input("Nom du Gérant", value=conf['gerant'])
        new_t = st.text_input("Téléphone", value=conf['tel'])
        new_m = st.text_input("Email", value=conf['mail'])
        new_a = st.text_input("Adresse Physique", value=conf['adr'])
        if st.form_submit_button("Sauvegarder les modifications"):
            with sqlite3.connect('venteup_v2.db') as conn:
                conn.execute("UPDATE config SET boutique=?, gerant=?, tel=?, mail=?, adresse=? WHERE id=1", (new_b, new_g, new_t, new_m, new_a))
            st.success("Paramètres mis à jour !")
            st.rerun()

# --- SECTION VENTE ---
elif choix == "🛒 Vente":
    st.header("🛒 Nouvelle Vente")
    # Logique de vente avec client (Nom, Tel, Adresse, Mail)
    c1, c2 = st.columns(2)
    nom_c = c1.text_input("Nom Client")
    tel_c = c2.text_input("Téléphone Client")
    adr_c = c1.text_input("Adresse Client")
    mail_c = c2.text_input("Mail Client")
    
    conn = sqlite3.connect('venteup_v2.db')
    prods = conn.execute("SELECT nom, p_vente, p_achat FROM produits WHERE stock > 0").fetchall()
    conn.close()
    
    dict_p = {p[0]: (p[1], p[2]) for p in prods}
    p_sel = st.selectbox("Produit", [""] + list(dict_p.keys()))
    
    if st.button("Valider la Vente") and p_sel and nom_c:
        pv, pa = dict_p[p_sel]
        bene = pv - pa
        with sqlite3.connect('venteup_v2.db') as conn:
            conn.execute("INSERT INTO ventes (client_nom, client_tel, client_adr, client_mail, produit, total, benefice, date) VALUES (?,?,?,?,?,?,?,?)",
                         (nom_c, tel_c, adr_c, mail_c, p_sel, pv, bene, datetime.now().strftime("%d/%m/%Y %H:%M")))
            conn.execute("UPDATE produits SET stock = stock - 1 WHERE nom=?", (p_sel,))
        st.success("Vente réussie !")

# --- SECTION STOCK (Avec suppression) ---
elif choix == "📦 Stock":
    st.header("📦 Gestion des Produits")
    with st.expander("Ajouter / Réapprovisionner"):
        with st.form("add_p"):
            n = st.text_input("Nom").upper()
            pa = st.number_input("Prix Achat", min_value=0)
            pv = st.number_input("Prix Vente", min_value=0)
            q = st.number_input("Quantité", min_value=0)
            if st.form_submit_button("Enregistrer"):
                with sqlite3.connect('venteup_v2.db') as conn:
                    conn.execute("INSERT OR REPLACE INTO produits (nom, p_achat, p_vente, stock) VALUES (?,?,?,?)", (n, pa, pv, q))
                st.rerun()

    st.subheader("Liste des produits")
    conn = sqlite3.connect('venteup_v2.db')
    df = conn.execute("SELECT id, nom, stock FROM produits").fetchall()
    for row in df:
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.write(f"**{row[1]}** (Stock: {row[2]})")
        if col3.button("Supprimer", key=f"del_p_{row[0]}"):
            conn.execute("DELETE FROM produits WHERE id=?", (row[0],))
            conn.commit()
            st.rerun()
    conn.close()

# --- SECTION DÉPENSES ---
elif choix == "💸 Dépenses":
    st.header("💸 Gestion des Dépenses")
    with st.form("dep_form"):
        motif = st.text_input("Motif de la dépense (Loyer, Transport...)")
        montant = st.number_input("Montant", min_value=0)
        if st.form_submit_button("Ajouter la dépense"):
            with sqlite3.connect('venteup_v2.db') as conn:
                conn.execute("INSERT INTO depenses (motif, montant, date) VALUES (?,?,?)", (motif, montant, datetime.now().strftime("%d/%m/%Y")))
            st.success("Dépense enregistrée")

# --- SECTION HISTORIQUE (Avec suppression) ---
elif choix == "📊 Historique":
    st.header("📊 Historique des Ventes")
    conn = sqlite3.connect('venteup_v2.db')
    vt = conn.execute("SELECT id, client_nom, produit, total, date FROM ventes ORDER BY id DESC").fetchall()
    for v in vt:
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.write(f"{v[4]} - {v[1]} : {v[2]} ({v[3]} GNF)")
        if c3.button("Supprimer", key=f"del_v_{v[0]}"):
            conn.execute("DELETE FROM ventes WHERE id=?", (v[0],))
            conn.commit()
            st.rerun()
    conn.close()
