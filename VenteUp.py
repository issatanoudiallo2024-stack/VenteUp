import streamlit as st
import pandas as pd
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="VenteUp - Gestion de Stock", layout="wide")

# --- BARRE LATÉRALE (SIDEBAR) POUR LE PAIEMENT ---
st.sidebar.title("🏪 VenteUp")
st.sidebar.markdown("---")
st.sidebar.subheader("🚀 Activation & Support")
st.sidebar.write("Pour activer la version illimitée ou obtenir de l'aide :")
st.sidebar.success("📞 **Contact : +224 610 51 89 73**")
st.sidebar.info("Paiements acceptés : **Orange Money / Mobile Money**")
st.sidebar.markdown("---")

# --- LOGIQUE DE L'APPLICATION ---
st.title("📦 Ma Boutique - Gestion des Ventes")

# Initialisation du stock en mémoire (pour l'exemple)
if 'stock' not in st.session_state:
    st.session_state.stock = pd.DataFrame(columns=["Produit", "Prix Unitaire", "Quantité"])

if 'ventes' not in st.session_state:
    st.session_state.ventes = pd.DataFrame(columns=["Date", "Produit", "Quantité", "Total"])

# Menu principal
menu = ["Réaliser une vente", "Gérer le stock", "Historique des gains"]
choix = st.sidebar.selectbox("Menu", menu)

if choix == "Réaliser une vente":
    st.header("🛒 Nouvelle Vente")
    if st.session_state.stock.empty:
        st.warning("Le stock est vide. Ajoutez des produits d'abord.")
    else:
        produit = st.selectbox("Choisir le produit", st.session_state.stock["Produit"])
        quantite = st.number_input("Quantité", min_value=1, step=1)
        
        if st.button("Valider la vente"):
            prix = st.session_state.stock.loc[st.session_state.stock["Produit"] == produit, "Prix Unitaire"].values[0]
            total = prix * quantite
            nouvelle_vente = {"Date": datetime.now().strftime("%d/%m/%Y %H:%M"), "Produit": produit, "Quantité": quantite, "Total": total}
            st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([nouvelle_vente])], ignore_index=True)
            st.success(f"Vente validée : {total} GNF")

elif choix == "Gérer le stock":
    st.header("➕ Ajouter au Stock")
    nom = st.text_input("Nom du produit")
    prix_u = st.number_input("Prix de vente (GNF)", min_value=0)
    qte = st.number_input("Quantité initiale", min_value=1)
    
    if st.button("Ajouter le produit"):
        nouveau_p = {"Produit": nom, "Prix Unitaire": prix_u, "Quantité": qte}
        st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([nouveau_p])], ignore_index=True)
        st.success("Produit ajouté !")
    
    st.write("### Stock actuel")
    st.table(st.session_state.stock)

elif choix == "Historique des gains":
    st.header("📈 Mes Revenus")
    if st.session_state.ventes.empty:
        st.write("Aucune vente pour le moment.")
    else:
        total_gains = st.session_state.ventes["Total"].sum()
        st.metric("Total des gains", f"{total_gains} GNF")
        st.dataframe(st.session_state.ventes)
