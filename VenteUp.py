import streamlit as st
import sqlite3
from datetime import datetime
from fpdf import FPDF
import base64

# --- INFOS DÉVELOPPEUR ---
DEV_NAME = "Issa Diallo"
DEV_TEL = "610 51 89 73"
DEV_MAIL = "issatanoudiallo2024@gmail.com"

# Configuration de la page
st.set_page_config(page_title="VenteUp Pro", page_icon="🛍️", layout="wide")

# --- BASE DE DONNÉES ---
def init_db():
    with sqlite3.connect('venteup_pro.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE, 
            p_achat REAL, p_vente REAL, stock INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, client_nom TEXT, 
            client_tel TEXT, client_adr TEXT, client_mail TEXT,
            total REAL, date TEXT)''')
        conn.commit()

init_db()

# --- GÉNÉRATEUR PDF ---
def generer_pdf(client_data, total):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "FACTURE VENTEUP", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.cell(0, 10, f"Client: {client_data['nom']}", ln=True)
    pdf.cell(0, 10, f"Tel: {client_data['tel']}", ln=True)
    pdf.cell(0, 10, f"Adresse: {client_data['adr']}", ln=True)
    if client_data['mail']:
        pdf.cell(0, 10, f"Email: {client_data['mail']}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"TOTAL À PAYER : {total} GNF", ln=True)
    
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, f"Logiciel conçu par {DEV_NAME} | {DEV_TEL}", align='C', ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE UTILISATEUR ---
st.sidebar.title("🚀 VenteUp Menu")
menu = ["🛒 Faire une Vente", "📦 Inventaire", "📜 Historique"]
choix = st.sidebar.radio("Navigation", menu)

if choix == "🛒 Faire une Vente":
    st.header("🛒 Nouvelle Transaction")
    
    with st.expander("👤 Informations du Client", expanded=True):
        c1, c2 = st.columns(2)
        nom = c1.text_input("Nom complet *")
        tel = c2.text_input("Numéro de téléphone *")
        adr = c1.text_input("Adresse de livraison *")
        mail = c2.text_input("Email (facultatif)")

    with st.expander("💰 Détails de la Vente", expanded=True):
        montant = st.number_input("Montant Total de la vente (GNF)", min_value=0, step=500)

    if st.button("🔥 Finaliser et Créer Facture"):
        if nom and tel and adr and montant > 0:
            client_data = {"nom": nom, "tel": tel, "adr": adr, "mail": mail}
            
            # Sauvegarde BDD
            with sqlite3.connect('venteup_pro.db') as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO ventes (client_nom, client_tel, client_adr, client_mail, total, date) VALUES (?,?,?,?,?,?)",
                               (nom, tel, adr, mail, montant, datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
            
            # Préparation PDF
            pdf_bytes = generer_pdf(client_data, montant)
            st.success(f"Vente validée pour {nom} !")
            st.download_button(label="📥 Télécharger la Facture PDF", 
                               data=pdf_bytes, 
                               file_name=f"Facture_{nom}.pdf", 
                               mime="application/pdf")
        else:
            st.error("Veuillez remplir tous les champs obligatoires (*)")

elif choix == "📦 Inventaire":
    st.header("📦 Gestion des Produits")
    with st.form("stock_form"):
        p_nom = st.text_input("Nom du produit").upper()
        p_achat = st.number_input("Prix d'achat", min_value=0)
        p_vente = st.number_input("Prix de vente", min_value=0)
        p_stock = st.number_input("Quantité en stock", min_value=0)
        
        if st.form_submit_button("Enregistrer le produit"):
            with sqlite3.connect('venteup_pro.db') as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO produits (nom, p_achat, p_vente, stock) VALUES (?,?,?,?)", 
                               (p_nom, p_achat, p_vente, p_stock))
                conn.commit()
            st.success(f"Produit {p_nom} ajouté/mis à jour !")

# --- FOOTER ---
st.sidebar.divider()
st.sidebar.caption(f"© 2026 {DEV_NAME}")
st.sidebar.caption(f"📞 {DEV_TEL}")
