import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 1. Configuration
st.set_page_config(page_title="VenteUp Pro", layout="wide")

# --- INITIALISATION DES VARIABLES SYSTÈME ---
if 'date_installation' not in st.session_state:
    st.session_state.date_installation = datetime.now()
if 'mdp_utilisateur' not in st.session_state:
    st.session_state.mdp_utilisateur = None
if 'authentifie' not in st.session_state:
    st.session_state.authentifie = False
if 'licence_payee' not in st.session_state:
    st.session_state.licence_payee = False

# --- LOGIQUE DE LA PÉRIODE D'ESSAI (7 JOURS) ---
date_expiration = st.session_state.date_installation + timedelta(days=7)
jours_restants = (date_expiration - datetime.now()).days

# --- 1. ÉCRAN DE PAIEMENT (Si essai fini et non payé) ---
if jours_restants <= 0 and not st.session_state.licence_payee:
    st.title("⚠️ Période d'essai terminée")
    st.error(f"Vos 7 jours d'essai gratuit sont terminés. Pour continuer à gérer votre boutique, activez la version complète.")
    st.write("### Tarif : 30 000 GNF (Accès à vie)")
    st.write("📲 Payez par **Orange Money** au **610 51 89 73** (Issa Diallo)")
    
    cle_activation = st.text_input("Entrez le code d'activation reçu après paiement", type="password")
    if st.button("Activer l'application"):
        if cle_activation == "VENTEUP2026": # Ton code maître pour débloquer
            st.session_state.licence_payee = True
            st.success("Application activée avec succès !")
            st.rerun()
        else:
            st.error("Code incorrect.")

# --- 2. CONFIGURATION DU MOT DE PASSE (Premier lancement) ---
elif st.session_state.mdp_utilisateur is None:
    st.title("🔐 Sécurisez votre boutique")
    st.write("Bienvenue sur VenteUp ! Choisissez un mot de passe pour protéger vos données.")
    nouveau_mdp = st.text_input("Créez votre mot de passe :", type="password")
    confirmer_mdp = st.text_input("Confirmez le mot de passe :", type="password")
    
    if st.button("Enregistrer mon mot de passe"):
        if nouveau_mdp == confirmer_mdp and len(nouveau_mdp) > 0:
            st.session_state.mdp_utilisateur = nouveau_mdp
            st.success("Mot de passe enregistré !")
            st.rerun()
        else:
            st.error("Les mots de passe ne correspondent pas ou sont vides.")

# --- 3. ÉCRAN DE CONNEXION ---
elif not st.session_state.authentifie:
    st.title("🏪 Connexion VenteUp")
    if jours_restants > 0:
        st.info(f"⏳ Il vous reste **{jours_restants} jours** d'essai gratuit.")
        
    saisie_mdp = st.text_input("Entrez votre mot de passe :", type="password")
    if st.button("Ouvrir ma boutique"):
        if saisie_mdp == st.session_state.mdp_utilisateur:
            st.session_state.authentifie = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")

# --- 4. CONTENU DE L'APPLICATION (Si connecté) ---
else:
    # Initialisation des données si vides
    if 'stock' not in st.session_state:
        st.session_state.stock = pd.DataFrame(columns=["Produit", "Prix Achat", "Prix Vente", "Quantité"])
    if 'ventes' not in st.session_state:
        st.session_state.ventes = pd.DataFrame(columns=["Date", "Produit", "Qte", "Prix Vendu", "Bénéfice"])

    with st.sidebar:
        st.title("VenteUp Pro")
        if st.button("🔒 Déconnexion"):
            st.session_state.authentifie = False
            st.rerun()
        st.markdown("---")
        choix = st.radio("MENU", ["🛒 Vente", "📦 Stock", "📈 Bénéfices"])
        st.info(f"Support : 610 51 89 73")

    # --- PARTIE VENTE ---
    if choix == "🛒 Vente":
        st.header("🛒 Faire une vente")
        if st.session_state.stock.empty:
            st.warning("Ajoutez des produits au stock.")
        else:
            prod = st.selectbox("Article", st.session_state.stock["Produit"])
            info = st.session_state.stock[st.session_state.stock["Produit"] == prod].iloc[0]
            p_v = st.number_input("Prix (Négociable)", value=float(info["Prix Vente"]))
            q_v = st.number_input("Quantité", min_value=1, value=1)
            
            if st.button("Valider"):
                benef = (p_v - float(info["Prix Achat"])) * q_v
                n_v = {"Date": datetime.now().strftime("%H:%M"), "Produit": prod, "Qte": q_v, "Prix Vendu": p_v*q_v, "Bénéfice": benef}
                st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([n_v])], ignore_index=True)
                st.success("Vendu !")

    # --- PARTIE
