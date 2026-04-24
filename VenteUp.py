import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 1. Configuration de la page
st.set_page_config(page_title="VenteUp Pro", layout="wide")

# --- CONFIGURATION ISSA DIALLO ---
COMPTE_PAYCARD = "379 705 545"
PRIX = "50 000 GNF"

# --- INITIALISATION ---
if 'date_install' not in st.session_state:
    st.session_state.date_install = datetime.now()
if 'licence_active' not in st.session_state:
    st.session_state.licence_active = False
if 'mdp_secret' not in st.session_state:
    st.session_state.mdp_secret = ""
if 'authentifie' not in st.session_state:
    st.session_state.authentifie = False

# Calcul de l'essai
jours_restants = 7 - (datetime.now() - st.session_state.date_install).days

# --- LOGIQUE D'AFFICHAGE ---

# 1. SI L'ESSAI EST FINI ET NON PAYÉ
if jours_restants <= 0 and not st.session_state.licence_active:
    st.title("🔒 Activation de VenteUp Pro")
    st.error("Votre période d'essai de 7 jours est terminée.")
    
    st.subheader("💳 Comment activer l'application ?")
    st.write(f"### Montant : **{PRIX}**")
    st.warning(f"👉 Effectuez le dépôt sur le compte PayCard : **{COMPTE_PAYCARD}**")
    
    st.write("---")
    ref = st.text_input("Une fois payé, entrez ici la Référence du paiement :")
    if st.button("Vérifier et Débloquer"):
        if len(ref) > 5: # Validation de la référence
            st.session_state.licence_active = True
            st.success("✅ Félicitations ! Votre boutique est activée à vie.")
            st.balloons()
            st.rerun()
        else:
            st.error("Référence invalide ou trop courte.")

# 2. SI UN MOT DE PASSE EST ACTIVÉ
elif st.session_state.mdp_secret != "" and not st.session_state.authentifie:
    st.title("🔐 Connexion Boutique")
    saisie = st.text_input("Entrez votre mot de passe", type="password")
    if st.button("Se connecter"):
        if saisie == st.session_state.mdp_secret:
            st.session_state.authentifie = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect")

# 3. L'INTERFACE DE GESTION NORMALE
else:
    with st.sidebar:
        st.title("🏪 VenteUp Pro")
        if not st.session_state.licence_active:
            st.info(f"⏳ Essai : {max(0, jours_restants)} jours restants")
        else:
            st.success("💎 Version Illimitée")
        
        choix = st.radio("MENU", ["🛒 Vente", "📦 Stock", "📈 Bénéfices", "⚙️ Paramètres"])
        
        if st.session_state.authentifie:
            if st.button("🔒 Déconnexion"):
                st.session_state.authentifie = False
                st.rerun()
        st.markdown("---")
        st.write("Support : 610 51 89 73")

    # --- LOGIQUE DES ONGLETS ---
    if 'stock' not in st.session_state:
        st.session_state.stock = pd.DataFrame(columns=["Produit", "Prix Achat", "Prix Vente", "Quantité"])
    if 'ventes' not in st.session_state:
        st.session_state.ventes = pd.DataFrame(columns=["Date", "Produit", "Qte", "Prix Vendu", "Bénéfice"])

    if choix == "🛒 Vente":
        st.header("🛒 Nouvelle Vente")
        if st.session_state.stock.empty:
            st.warning("Ajoutez d'abord des articles dans l'onglet Stock.")
        else:
            prod = st.selectbox("Sélectionner l'article", st.session_state.stock["Produit"])
            info = st.session_state.stock[st.session_state.stock["Produit"] == prod].iloc[0]
            c1, c2 = st.columns(2)
            p_final = c1.number_input("Prix final (GNF)", value=float(info["Prix Vente"]))
            qte = c2.number_input("Quantité", min_value=1, value=1)
            if st.button("✅ Valider la vente"):
                benef = (p_final - float(info["Prix Achat"])) * qte
                n_v = {"Date": datetime.now().strftime("%H:%M"), "Produit": prod, "Qte": qte, "Prix Vendu": p_final*qte, "Bénéfice": benef}
                st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([n_v])], ignore_index=True)
                st.success("Vente enregistrée !")

    elif choix == "📦 Stock":
        st.header("📦 Gestion du Stock")
        with st.expander("➕ Ajouter un nouveau produit", expanded=True):
            n = st.text_input("Nom de l'article")
            pa = st.number_input("Prix d'Achat", min_value=0.0)
            pv = st.number_input("Prix de Vente conseillé", min_value=0.0)
            q = st.number_input("Quantité", min_value=1)
            if st.button("Enregistrer"):
                if n:
                    new_p = {"Produit": n, "Prix Achat": pa, "Prix Vente": pv, "Quantité": q}
                    st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([new_p])], ignore_index=True)
                    st.rerun()
        st.subheader("📋 Liste des articles")
        st.dataframe(st.session_state.stock, use_container_width=True)

    elif choix == "📈 Bénéfices":
        st.header("📈 Résultats Financiers")
        if not st.session_state.ventes.empty:
            st.metric("Chiffre d'Affaire", f"{st.session_state.ventes['Prix Vendu'].sum():,.0f} GNF")
            st.metric("Bénéfice Net", f"{st.session_state.ventes['Bénéfice'].sum():,.0f} GNF")
            st.write("### Historique des transactions")
            st.dataframe(st.session_state.ventes)
        else:
            st.info("Aucune vente enregistrée aujourd'hui.")

    elif choix == "⚙️ Paramètres":
        st.header("⚙️ Sécurité")
        mdp = st.text_input("Choisir un mot de passe (laisser vide si vous n'en voulez pas)", type="password", value=st.session_state.mdp_secret)
        if st.button("Enregistrer les réglages"):
            st.session_state.mdp_secret = mdp
            st.success("Paramètres mis à jour !")
