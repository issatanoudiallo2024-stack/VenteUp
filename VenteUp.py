import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Configuration de la page
st.set_page_config(page_title="VenteUp - Gestion Boutique", layout="wide", initial_sidebar_state="expanded")

# --- INITIALISATION DES DONNÉES ---
if 'stock' not in st.session_state:
    st.session_state.stock = pd.DataFrame(columns=["Produit", "Prix Unitaire", "Quantité"])

if 'ventes' not in st.session_state:
    st.session_state.ventes = pd.DataFrame(columns=["Date", "Produit", "Quantité", "Total"])

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title("🏪 VenteUp")
    st.markdown("---")
    choix = st.radio(
        "QUE VOULEZ-VOUS FAIRE ?",
        ["🛒 Faire une Vente", "📦 Ajouter des Articles", "📊 Voir mes Revenus"]
    )
    st.markdown("---")
    st.success(f"📞 **Support & Activation :**\n**610 51 89 73**")

# --- 1. ONGLET : FAIRE UNE VENTE ---
if choix == "🛒 Faire une Vente":
    st.header("🛒 Réaliser une vente")
    if st.session_state.stock.empty:
        st.error("🚨 Votre stock est vide ! Allez dans 'Ajouter des Articles'.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            produit_choisi = st.selectbox("Choisir l'article", st.session_state.stock["Produit"])
        with col2:
            qte_vendre = st.number_input("Quantité", min_value=1, value=1)
        
        if st.button("✅ Valider la vente"):
            prix_u = st.session_state.stock.loc[st.session_state.stock["Produit"] == produit_choisi, "Prix Unitaire"].values[0]
            total = prix_u * qte_vendre
            nouvelle_vente = {"Date": datetime.now().strftime("%H:%M"), "Produit": produit_choisi, "Quantité": qte_vendre, "Total": total}
            st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([nouvelle_vente])], ignore_index=True)
            st.balloons()
            st.success(f"Vendu ! Total : {total:,} GNF")

# --- 2. ONGLET : AJOUTER DES ARTICLES ---
elif choix == "📦 Ajouter des Articles":
    st.header("📦 Gestion du Stock")
    with st.expander("➕ Ajouter un nouvel article", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            nom_p = st.text_input("Nom de l'article")
        with c2:
            prix_p = st.number_input("Prix de vente (GNF)", min_value=0, step=500)
        with c3:
            qte_p = st.number_input("Quantité initiale", min_value=1, value=10)
        
        if st.button("📥 Enregistrer"):
            if nom_p:
                nouvel_art = {"Produit": nom_p, "Prix Unitaire": prix_p, "Quantité": qte_p}
                st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([nouvel_art])], ignore_index=True)
                st.success(f"{nom_p} ajouté !")

    st.subheader("📋 Stock actuel")
    st.table(st.session_state.stock)

# --- 3. ONGLET : REVENUS ---
elif choix == "📊 Voir mes Revenus":
    st.header("📊 Bilan")
    if st.session_state.ventes.empty:
        st.info("Aucune vente.")
    else:
        total_argent = st.session_state.ventes["Total"].sum()
        st.metric("TOTAL GAGNÉ", f"{total_argent:,} GNF")
        st.dataframe(st.session_state.ventes)
