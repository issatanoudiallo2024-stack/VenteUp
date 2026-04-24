import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Configuration pour que le menu soit visible
st.set_page_config(page_title="VenteUp - Guinée", layout="wide", initial_sidebar_state="expanded")

# --- STYLE PERSONNALISÉ ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- BARRE LATÉRALE TOUJOURS VISIBLE ---
with st.sidebar:
    st.title("🏪 VenteUp")
    st.success(f"📱 Service Client :\n**610 51 89 73**")
    st.info("Paiement Orange/MoMo accepté")
    st.markdown("---")
    menu = st.radio("TABLEAU DE BORD", ["🛒 Faire une Vente", "📦 Gérer le Stock", "📊 Voir mes Gains"])

# --- LOGIQUE PRINCIPALE ---
if menu == "🛒 Faire une Vente":
    st.header("🛒 Nouvelle Vente")
    # (Le reste du code de vente ici...)
    st.write("Sélectionnez un produit et validez la vente.")

elif menu == "📦 Gérer le Stock":
    st.header("📦 Gestion du Stock")
    st.write("Ajoutez vos articles ici (Riz, Sucre, Huile, etc.)")

elif menu == "📊 Voir mes Gains":
    st.header("📊 Historique des Revenus")
    st.write("Ici s'affiche l'argent gagné aujourd'hui.")
