import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 1. Configuration de la page
st.set_page_config(page_title="VenteUp Pro", layout="wide")

# --- INITIALISATION DES VARIABLES (Persistence de session) ---
if 'date_installation' not in st.session_state:
    st.session_state.date_installation = datetime.now()
if 'mdp_active' not in st.session_state:
    st.session_state.mdp_active = False  # Par défaut, pas de mot de passe
if 'mdp_secret' not in st.session_state:
    st.session_state.mdp_secret = ""
if 'authentifie' not in st.session_state:
    st.session_state.authentifie = False
if 'licence_payee' not in st.session_state:
    st.session_state.licence_payee = False
if 'stock' not in st.session_state:
    st.session_state.stock = pd.DataFrame(columns=["Produit", "Prix Achat", "Prix Vente", "Quantité"])
if 'ventes' not in st.session_state:
    st.session_state.ventes = pd.DataFrame(columns=["Date", "Produit", "Qte", "Prix Vendu", "Bénéfice"])

# --- CALCUL DE LA PÉRIODE D'ESSAI ---
jours_ecoules = (datetime.now() - st.session_state.date_installation).days
jours_restants = 7 - jours_ecoules

# --- LOGIQUE D'AFFICHAGE ---

# Cas 1 : Période d'essai finie et non payée
if jours_restants <= 0 and not st.session_state.licence_payee:
    st.title("🔒 Activation Requise")
    st.error("Votre période d'essai de 7 jours est terminée.")
    st.write("Pour débloquer votre gestion, envoyez **30 000 GNF** au **610 51 89 73**.")
    cle = st.text_input("Code d'activation", type="password")
    if st.button("Activer"):
        if cle == "VENTEUP2026":
            st.session_state.licence_payee = True
            st.rerun()

# Cas 2 : Mot de passe activé mais utilisateur non connecté
elif st.session_state.mdp_active and not st.session_state.authentifie:
    st.title("🔐 Boutique Verrouillée")
    saisie = st.text_input("Entrez votre mot de passe", type="password")
    if st.button("Se connecter"):
        if saisie == st.session_state.mdp_secret:
            st.session_state.authentifie = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect")

# Cas 3 : L'application normale
else:
    with st.sidebar:
        st.title("🏪 VenteUp")
        if jours_restants > 0 and not st.session_state.licence_payee:
            st.info(f"⏳ Essai : {jours_restants} jours restants")
        
        choix = st.radio("MENU", ["🛒 Vente", "📦 Stock", "📈 Bénéfices", "⚙️ Paramètres"])
        
        if st.session_state.authentifie:
            if st.button("🔒 Verrouiller"):
                st.session_state.authentifie = False
                st.rerun()
        
        st.markdown("---")
        st.write("Support : 610 51 89 73")

    # --- ONGLET VENTE ---
    if choix == "🛒 Vente":
        st.header("🛒 Faire une vente")
        if st.session_state.stock.empty:
            st.warning("Le stock est vide. Allez dans l'onglet 'Stock' pour ajouter des produits.")
        else:
            prod = st.selectbox("Article", st.session_state.stock["Produit"])
            info = st.session_state.stock[st.session_state.stock["Produit"] == prod].iloc[0]
            
            c1, c2 = st.columns(2)
            p_v = c1.number_input("Prix final (GNF)", value=float(info["Prix Vente"]))
            q_v = c2.number_input("Quantité", min_value=1, value=1)
            
            if st.button("✅ Valider la vente"):
                benef = (p_v - float(info["Prix Achat"])) * q_v
                n_v = {"Date": datetime.now().strftime("%H:%M"), "Produit": prod, "Qte": q_v, "Prix Vendu": p_v*q_v, "Bénéfice": benef}
                st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([n_v])], ignore_index=True)
                st.success("Vente enregistrée !")

    # --- ONGLET STOCK ---
    elif choix == "📦 Stock":
        st.header("📦 Gestion du Stock")
        with st.expander("➕ Ajouter un nouveau produit", expanded=True):
            n = st.text_input("Nom de l'article")
            pa = st.number_input("Prix d'Achat (pour le bénéfice)", min_value=0.0)
            pv = st.number_input("Prix de Vente conseillé", min_value=0.0)
            q = st.number_input("Quantité initiale", min_value=1)
            if st.button("Enregistrer le produit"):
                if n:
                    new_p = {"Produit": n, "Prix Achat": pa, "Prix Vente": pv, "Quantité": q}
                    st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([new_p])], ignore_index=True)
                    st.success(f"{n} ajouté !")
                    st.rerun()
        
        st.subheader("📋 Liste des produits")
        if not st.session_state.stock.empty:
            st.dataframe(st.session_state.stock, use_container_width=True)
            if st.button("Effacer tout le stock"):
                st.session_state.stock = pd.DataFrame(columns=["Produit", "Prix Achat", "Prix Vente", "Quantité"])
                st.rerun()

    # --- ONGLET BÉNÉFICES ---
    elif choix == "📈 Bénéfices":
        st.header("📈 Résultats Financiers")
        if not st.session_state.ventes.empty:
            st.metric("Total Ventes", f"{st.session_state.ventes['Prix Vendu'].sum():,.0f} GNF")
            st.metric("Bénéfice Net", f"{st.session_state.ventes['Bénéfice'].sum():,.0f} GNF")
            st.write("### Historique")
            st.dataframe(st.session_state.ventes)
        else:
            st.info("Aucune vente aujourd'hui.")

    # --- ONGLET PARAMÈTRES (Choix du mot de passe) ---
    elif choix == "⚙️ Paramètres":
        st.header("⚙️ Sécurité")
        activer = st.checkbox("Protéger l'application par mot de passe", value=st.session_state.mdp_active)
        
        if activer:
            st.session_state.mdp_active = True
            nouveau_mdp = st.text_input("Définir votre mot de passe", type="password", value=st.session_state.mdp_secret)
            if st.button("Sauvegarder le mot de passe"):
                st.session_state.mdp_secret = nouveau_mdp
                st.success("Mot de passe mis à jour !")
        else:
            st.session_state.mdp_active = False
            st.session_state.authentifie = False
            st.info("Le mot de passe est désactivé. L'accès est libre.")
