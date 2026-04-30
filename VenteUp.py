import streamlit as st
import sqlite3
from datetime import datetime
from fpdf import FPDF

# --- CONFIGURATION DÉVELOPPEUR ---
DEV_NAME = "Issa Diallo"
DEV_TEL = "610 51 89 73"
DEV_MAIL = "issatanoudiallo2024@gmail.com"

# Configuration de la page
st.set_page_config(page_title="VenteUp Pro", page_icon="📈", layout="wide")

# --- STYLE PERSONNALISÉ (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stTextInput>div>div>input { border-radius: 5px; }
    </style>
    """, unsafe_allow_stdio=True)

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('venteup_pro.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE, 
        p_achat REAL, p_vente REAL, stock INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client_nom TEXT, 
        client_tel TEXT, client_adr TEXT, client_mail TEXT,
        total REAL, date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- GÉNÉRATEUR DE FACTURE PDF ---
class FacturePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'FACTURE VENTEUP', 0, 1, 'C')
        self.ln(10)
    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        info = f"Logiciel conçu par {DEV_NAME} | Tel: {DEV_TEL} | {DEV_MAIL}"
        self.cell(0, 10, info, 0, 1, 'C')
        self.cell(0, 10, "Signature du Gérant : ____________________", 0, 0, 'R')

# --- INTERFACE PRINCIPALE ---
st.sidebar.title("🎮 Tableau de Bord")
st.sidebar.info(f"Développeur : **{DEV_NAME}**")
menu = ["🛒 Nouvelle Vente", "📦 Gestion de Stock", "📊 Historique"]
choix = st.sidebar.selectbox("Navigation", menu)

if choix == "🛒 Nouvelle Vente":
    st.title("💰 Créer une Vente")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Informations Client")
        c_nom = st.text_input("Nom complet")
        c_tel = st.text_input("Numéro de téléphone")
        c_adr = st.text_input("Adresse")
        c_mail = st.text_input("Email (Optionnel)")
    
    with col2:
        st.subheader("Détails Transaction")
        produit_selection = st.selectbox("Choisir un produit", ["Selectionner..."]) # À lier avec la BDD
        montant = st.number_input("Montant Total (GNF)", min_value=0)
        
    if st.button("Finaliser la vente et générer le PDF"):
        if c_nom and montant > 0:
            # Enregistrement BDD
            conn = sqlite3.connect('venteup_pro.db')
            c = conn.cursor()
            c.execute("INSERT INTO ventes (client_nom, client_tel, client_adr, client_mail, total, date) VALUES (?,?,?,?,?,?)",
                      (c_nom, c_tel, c_adr, c_mail, montant, datetime.now().strftime("%d/%m/%Y %H:%M")))
            conn.commit()
            st.success(f"Vente enregistrée pour {c_nom} !")
            st.balloons()
        else:
            st.error("Veuillez remplir au moins le nom et le montant.")

elif choix == "📦 Gestion de Stock":
    st.title("🏗️ Inventaire & Réapprovisionnement")
    with st.container():
        nom = st.text_input("Désignation du produit").upper()
        pa = st.number_input("Prix d'Achat", min_value=0.0)
        pv = st.number_input("Prix de Vente", min_value=0.0)
        qte = st.number_input("Quantité à ajouter", min_value=1)
        
        if st.button("Mettre à jour le stock"):
            conn = sqlite3.connect('venteup_pro.db')
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO produits (nom, p_achat, p_vente, stock) VALUES (?,?,?,?)", (nom, pa, pv, qte))
            conn.commit()
            st.success(f"Le stock de {nom} est maintenant à jour.")

# --- FOOTER ---
st.divider()
st.caption(f"© 2026 {APP_VERSION if 'APP_VERSION' in locals() else 'VenteUp'} | {DEV_NAME} - {DEV_TEL}")
