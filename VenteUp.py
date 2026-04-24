import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 1. Configuration
st.set_page_config(page_title="VenteUp Business", layout="wide")

# --- CONFIGURATION ISSA ---
MON_COMPTE_PAYCARD = "379705545"
PRIX_LICENCE = "30 000 GNF"
CODE_MAITRE = "VENTEUP2026" # Code à donner si le client paye par un autre moyen

# --- INITIALISATION ---
if 'licence_active' not in st.session_state:
    st.session_state.licence_active = False
if 'date_install' not in st.session_state:
    st.session_state.date_install = datetime.now()
if 'mdp_utilisateur' not in st.session_state:
    st.session_state.mdp_utilisateur = ""
if 'authentifie' not in st.session_state:
    st.session_state.authentifie = False

# Calcul de l'essai
jours_restants = 7 - (datetime.now() - st.session_state.date_install).days

# --- LOGIQUE D'ACCÈS ---

# CAS 1 : ESSAI FINI -> BLOCAGE ET PAIEMENT
if jours_restants <= 0 and not st.session_state.licence_active:
    st.title("🔒 Activation de votre Licence")
    st.error(f"Votre période d'essai est terminée. Pour continuer, activez la version complète.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💳 Paiement Rapide")
        st.write(f"**Montant : {PRIX_LICENCE}**")
        st.write(f"Compte PayCard : **{MON_COMPTE_PAYCARD}**")
        # Bouton simulé pour PayCard
        st.markdown(f"""
            <a href="https://pro.paycard.co/pay?account={MON_COMPTE_PAYCARD}&amount=30000" target="_blank">
                <button style="background-color: #f04b4b; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">
                    PAYER 30 000 GNF ICI
                </button>
            </a>
        """, unsafe_allow_html=True)
        st.info("Une fois payé, vous recevrez un code de confirmation par SMS.")

    with col2:
        st.subheader("🔑 Déblocage")
        code_saisi = st.text_input("Entrez votre code d'activation ou réf. de paiement", type="password")
        if st.button("Activer l'application"):
            if len(code_saisi) > 5: # Vérification basique de la référence
                st.session_state.licence_active = True
                st.success("✅ Activation réussie ! Profitez de VenteUp.")
                st.balloons()
                st.rerun()
            else:
                st.error("Référence de paiement invalide.")

# CAS 2 : MOT DE PASSE (OPTIONNEL)
elif st.session_state.mdp_utilisateur != "" and not st.session_state.authentifie:
    st.title("🔐 Connexion Boutique")
    pwd = st.text_input("Votre mot de passe", type="password")
    if st.button("Entrer"):
        if pwd == st.session_state.mdp_utilisateur:
            st.session_state.authentifie = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect")

# CAS 3 : L'APPLICATION NORMALE
else:
    with st.sidebar:
        st.title("🏪 VenteUp Pro")
        if not st.session_state.licence_active:
            st.warning(f"⏳ Essai : {max(0, jours_restants)} jours restants")
        else:
            st.success("💎 Licence Activée")
        
        choix = st.radio("MENU", ["🛒 Vente", "📦 Stock", "📈 Bénéfices", "⚙️ Paramètres"])
        if st.session_state.authentifie and st.button("🔒 Verrouiller"):
            st.session_state.authentifie = False
            st.rerun()

    # --- FONCTIONNALITÉS ---
    if choix == "🛒 Vente":
        st.header("🛒 Nouvelle Vente")
        if 'stock' not in st.session_state or st.session_state.stock.empty:
            st.info("Allez dans 'Stock' pour ajouter des produits.")
        else:
            prod = st.selectbox("Article", st.session_state.stock["Produit"])
            info = st.session_state.stock[st.session_state.stock["Produit"] == prod].iloc[0]
            c1, c2 = st.columns(2)
            p_final = c1.number_input("Prix final (GNF)", value=float(info["Prix Vente"]))
            qte = c2.number_input("Quantité", min_value=1, value=1)
            if st.button("✅ Valider"):
                benef = (p_final - float(info["Prix Achat"])) * qte
                # Sauvegarde vente...
                st.success("Vente enregistrée !")

    elif choix == "📦 Stock":
        st.header("📦 Gestion Stock")
        with st.expander("➕ Ajouter un produit"):
            n = st.text_input("Nom")
            pa = st.number_input("Prix Achat", min_value=0.0)
            pv = st.number_input("Prix Vente", min_value=0.0)
            q = st.number_input("Quantité", min_value=1)
            if st.button("Enregistrer"):
                if 'stock' not in st.session_state:
                    st.session_state.stock = pd.DataFrame(columns=["Produit", "Prix Achat", "Prix Vente", "Quantité"])
                new_p = {"Produit": n, "Prix Achat": pa, "Prix Vente": pv, "Quantité": q}
                st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([new_p])], ignore_index=True)
                st.rerun()
        if 'stock' in st.session_state:
            st.dataframe(st.session_state.stock, use_container_width=True)

    elif choix == "📈 Bénéfices":
        st.header("📈 Résultats")
        st.info("Connectez votre Google Sheets pour voir l'historique permanent.")

    elif choix == "⚙️ Paramètres":
        st.header("⚙️ Sécurité")
        new_pwd = st.text_input("Définir un mot de passe (laisser vide pour désactiver)", type="password")
        if st.button("Mettre à jour le mot de passe"):
            st.session_state.mdp_utilisateur = new_pwd
            st.success("Paramètres enregistrés !")
