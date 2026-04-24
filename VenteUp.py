import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Configuration de la page
st.set_page_config(page_title="VenteUp Pro", layout="wide")

# --- INITIALISATION ---
if 'code_active' not in st.session_state:
    st.session_state.code_active = False
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

# Logique d'affichage
if st.session_state.code_active and not st.session_state.authentifie:
    ecran_verrouillage()
else:
    # --- BARRE LATÉRALE ---
    with st.sidebar:
        st.title("🏪 VenteUp Pro")
        choix = st.radio("MENU", ["🛒 Vente", "📦 Stock", "📈 Bénéfices", "⚙️ Paramètres"])
        st.markdown("---")
        if st.session_state.authentifie:
            if st.button("🔒 Verrouiller"):
                st.session_state.authentifie = False
                st.rerun()
        st.success("📞 Support : 610 51 89 73")

    # --- 1. VENTE ---
    if choix == "🛒 Vente":
        st.header("🛒 Réaliser une vente")
        if st.session_state.stock.empty:
            st.warning("Le stock est vide.")
        else:
            c1, c2 = st.columns(2)
            prod = c1.selectbox("Article", st.session_state.stock["Produit"])
            info = st.session_state.stock[st.session_state.stock["Produit"] == prod].iloc[0]
            prix_f = c2.number_input("Prix final (GNF)", value=float(info["Prix Vente"]))
            qte = st.number_input("Quantité", min_value=1, value=1)
            
            if st.button("✅ Valider"):
                benef = (prix_f - float(info["Prix Achat"])) * qte
                nouvelle_v = {"Date": datetime.now().strftime("%H:%M"), "Produit": prod, "Qte": qte, "Prix Vendu": prix_f*qte, "Bénéfice": benef}
                st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([nouvelle_v])], ignore_index=True)
                st.success("Vente réussie !")

    # --- 2. STOCK ---
    elif choix == "📦 Stock":
        st.header("📦 Gestion du Stock")
        with st.expander("➕ Ajouter un produit"):
            c1, c2, c3, c4 = st.columns(4)
            n = c1.text_input("Nom")
            pa = c2.number_input("Prix Achat", min_value=0.0)
            pv = c3.number_input("Prix Vente", min_value=0.0)
            q = c4.number_input("Quantité", min_value=1)
            if st.button("Enregistrer"):
                if n:
                    new_p = {"Produit": n, "Prix Achat": pa, "Prix Vente": pv, "Quantité": q}
                    st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([new_p])], ignore_index=True)
                    st.rerun()

        st.subheader("📋 Liste")
        for i, row in st.session_state.stock.iterrows():
            col1, col2 = st.columns([4, 1])
            col1.write(f"**{row['Produit']}** - {row['Prix Vente']:,} GNF")
            if col2.button("Supprimer", key=f"p_{i}"):
                st.session_state.stock = st.session_state.stock.drop(i).reset_index(drop=True)
                st.rerun()

    # --- 3. BÉNÉFICES ---
    elif choix == "📈 Bénéfices":
        st.header("📈 Résultats")
        if not st.session_state.ventes.empty:
            ca = st.session_state.ventes["Prix Vendu"].sum()
            be = st.session_state.ventes["Bénéfice"].sum()
            st.metric("Chiffre d'Affaire", f"{ca:,.0f} GNF")
            st.metric("Bénéfice Net", f"{be:,.0f} GNF")
            
            for i, row in st.session_state.ventes.iterrows():
                cv1, cv2 = st.columns([4, 1])
                cv1.write(f"{row['Date']} - {row['Produit']} : {row['Prix Vendu']:,} GNF")
                if cv2.button("Annuler", key=f"v_{i}"):
                    st.session_state.ventes = st.session_state.ventes.drop(i).reset_index(drop=True)
                    st.rerun()
        else:
            st.info("Aucune vente.")

    # --- 4. PARAMÈTRES ---
    elif choix == "⚙️ Paramètres":
        st.header("⚙️ Réglages")
        if st.button("Activer/Désactiver le mot de passe"):
            st.session_state.code_active = not st.session_state.code_active
            st.session_state.authentifie = False
            st.rerun()
        st.info("Le code par défaut est : 1234")
