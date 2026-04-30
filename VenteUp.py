import streamlit as st
import sqlite3
from datetime import datetime
from fpdf import FPDF

# --- CONFIGURATION ---
DEV_NAME = "Issa Diallo"
DEV_TEL = "610 51 89 73"
DEV_MAIL = "issatanoudiallo2024@gmail.com"

st.set_page_config(page_title="VenteUp - Issa Diallo", layout="centered")

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('venteup_web.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE, 
        p_achat REAL, p_vente REAL, stock INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- INTERFACE ---
st.title("🚀 VenteUp - Gestion Pro")
st.write(f"Développeur : **{DEV_NAME}** | {DEV_TEL}")

menu = ["Vendre", "Gérer le Stock", "Historique"]
choix = st.sidebar.selectbox("Menu", menu)

if choix == "Gérer le Stock":
    st.subheader("📦 Ajouter ou Réapprovisionner")
    nom = st.text_input("Nom du produit").upper()
    pa = st.number_input("Prix d'Achat (GNF)", min_value=0.0)
    pv = st.number_input("Prix de Vente (GNF)", min_value=0.0)
    qte = st.number_input("Quantité", min_value=1)
    
    if st.button("Enregistrer"):
        conn = sqlite3.connect('venteup_web.db')
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO produits (nom, p_achat, p_vente, stock) VALUES (?,?,?,?)", (nom, pa, pv, qte))
        conn.commit()
        st.success(f"Produit {nom} mis à jour !")

elif choix == "Vendre":
    st.subheader("💰 Nouvelle Vente")
    client = st.text_input("Nom du Client")
    # Simulation simplifiée
    montant = st.number_input("Montant Total", min_value=0)
    
    if st.button("Générer Facture"):
        st.info(f"Facture pour {client} créée ! (Fonction PDF prête)")
        # Ici tu peux intégrer ta logique FPDF

st.divider()
st.caption(f"© 2026 {DEV_NAME} - {DEV_MAIL}")
