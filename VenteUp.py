
elif import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Configuration de la page (Menu visible dès le début)
st.set_page_config(page_title="VenteUp - Gestion Boutique", layout="wide", initial_sidebar_state="expanded")

# --- INITIALISATION DES DONNÉES (Pour ne pas avoir d'erreurs) ---
if 'stock' not in st.session_state:
    st.session_state.stock = pd.DataFrame(columns=["Produit", "Prix Unitaire", "Quantité"])

if 'ventes' not in st.session_state:
    st.session_state.ventes = pd.DataFrame(columns=["Date", "Produit", "Quantité", "Total"])

# --- BARRE LATÉRALE PROFESSIONNELLE ---
with st.sidebar:
    st.title("🏪 VenteUp")
    st.markdown("---")
    # Menu très simple avec des icônes
    choix = st.radio(
        "QUE VOULEZ-VOUS FAIRE ?",
        ["🛒 Faire une Vente", "📦 Ajouter des Articles", "📊 Voir mes Revenus"]
    )
    st.markdown("---")
    st.success(f"📞 **Support & Activation :**\n**610 51 89 73**")
    st.caption("Développé par Issa Diallo")

# --- 1. ONGLET : FAIRE UNE VENTE ---
if choix == "🛒 Faire une Vente":
    st.header("🛒 Réaliser une vente")
    
    if st.session_state.stock.empty:
        st.error("🚨 Votre stock est vide ! Allez dans 'Ajouter des Articles' pour commencer.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            produit_choisi = st.selectbox("Choisir l'article", st.session_state.stock["Produit"])
        with col2:
            qte_vendre = st.number_input("Quantité à vendre", min_value=1, value=1, step=1)
        
        if st.button("✅ Valider la vente"):
            # Calcul du prix
            prix_u = st.session_state.stock.loc[st.session_state.stock["Produit"] == produit_choisi, "Prix Unitaire"].values[0]
            total = prix_u * qte_vendre
            
            # Enregistrement
            nouvelle_vente = {
                "Date": datetime.now().strftime("%H:%M:%S"),
                "Produit": produit_choisi,
                "Quantité": qte_vendre,
                "Total": total
            }
            st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([nouvelle_vente])], ignore_index=True)
            st.balloons()
            st.success(f"Vendu ! Total : {total:,} GNF")

# --- 2. ONGLET : AJOUTER DES ARTICLES (C'est ici que tu travailles) ---
elif choix == "📦 Ajouter des Articles":
    st.header("📦 Gestion du Stock")
    
    with st.expander("➕ Cliquer ici pour ajouter un nouvel article", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            nom_p = st.text_input("Nom de l'article (ex: Riz)")
        with c2:
            prix_p = st.number_input("Prix de vente (GNF)", min_value=0, step=500)
        with c3:
            qte_p = st.number_input("Quantité en stock", min_value=1, value=10)
        
        if st.button("📥 Enregistrer dans le stock"):
            if nom_p:
                nouvel_art = {"Produit": nom_p, "Prix Unitaire": prix_p, "Quantité": qte_p}
                st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([nouvel_art])], ignore_index=True)
                st.success(f"{nom_p} ajouté au stock !")
            else:
                st.warning("Veuillez donner un nom à l'article.")

    st.subheader("📋 Liste de vos articles")
    st.table(st.session_state.stock)

# --- 3. ONGLET : REVENUS ---
elif choix == "📊 Voir mes Revenus":
    st.header("📊 Bilan de la journée")
    if st.session_state.ventes.empty:
        st.info("Aucune vente enregistrée pour le moment.")
    else:
        total_argent = st.session_state.ventes["Total"].sum()
        st.metric("TOTAL GAGNÉ (GNF)", f"{total_argent:,} GNF")
        st.write("### Détails des ventes")
        st.dataframe(st.session_state.ventes, use_container_width=True)
