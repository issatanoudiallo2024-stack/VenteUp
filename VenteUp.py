import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Configuration de la page
st.set_page_config(page_title="VenteUp Pro", layout="wide")

# --- INITIALISATION DES PARAMÈTRES ET DONNÉES ---
if 'code_active' not in st.session_state:
    st.session_state.code_active = False # Désactivé par défaut
if 'authentifie' not in st.session_state:
    st.session_state.authentifie = False
if 'stock' not in st.session_state:
    st.session_state.stock = pd.DataFrame(columns=["Produit", "Prix Achat", "Prix Vente", "Quantité"])
if 'ventes' not in st.session_state:
    st.session_state.ventes = pd.DataFrame(columns=["Date", "Produit", "Qte", "Prix Vendu", "Bénéfice"])

# --- GESTION DU VERROUILLAGE ---
def ecran_verrouillage():
    st.title("🔐 Accès Protégé")
    code = st.text_input("Entrez le mot de passe", type="password")
    if st.button("Déverrouiller"):
        if code == "1234":
            st.session_state.authentifie = True
            st.rerun()
        else:
            st.error("Code incorrect")

# Logique d'affichage (Vérification si le code est requis)
if st.session_state.code_active and not st.session_state.authentifie:
    ecran_verrouillage()
else:
    # --- BARRE LATÉRALE ---
    with st.sidebar:
        st.title("🏪 VenteUp Pro")
        choix = st.radio("MENU", ["🛒 Vente", "📦 Stock", "📈 Bénéfices", "⚙️ Paramètres"])
        st.markdown("---")
        if st.session_state.authentifie:
            if st.button("🔒 Verrouiller l'appli"):
                st.session_state.authentifie = False
                st.rerun()
        st.success("📞 Support : 610 51 89 73")

    # --- 1. ONGLET VENTE ---
    if choix == "🛒 Vente":
        st.header("🛒 Réaliser une vente")
        if st.session_state.stock.empty:
            st.warning("Le stock est vide. Ajoutez des produits d'abord.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                prod = st.selectbox("Choisir l'article", st.session_state.stock["Produit"])
                info = st.session_state.stock[st.session_state.stock["Produit"] == prod].iloc[0]
            with c2:
                prix_f = st.number_input("Prix final négocié (GNF)", value=float(info["Prix Vente"]))
                qte = st.number_input("Quantité", min_value=1, value=1)
            
            if st.button("✅ Valider la vente"):
                benef = (prix_f - float(info["Prix Achat"])) * qte
                nouvelle_v = {
                    "Date": datetime.now().strftime("%H:%M"), 
                    "Produit": prod, 
                    "Qte": qte, 
                    "Prix Vendu": prix_f * qte, 
                    "Bénéfice": benef
                }
                st.session_state.
