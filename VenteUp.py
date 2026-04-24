import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 1. Configuration
st.set_page_config(page_title="VenteUp Ultimate", layout="wide")

# --- INITIALISATION ---
if 'licence_active' not in st.session_state: st.session_state.licence_active = False
if 'date_install' not in st.session_state: st.session_state.date_install = datetime.now()
if 'boutique_info' not in st.session_state:
    st.session_state.boutique_info = {"nom": "Ma Boutique", "adresse": "Conakry", "tel": "6XX XX XX XX"}
if 'stock' not in st.session_state:
    st.session_state.stock = pd.DataFrame(columns=["Produit", "Prix Achat", "Prix Vente", "Quantité"])
if 'ventes' not in st.session_state:
    st.session_state.ventes = pd.DataFrame(columns=["Date", "Produit", "Qte", "Prix Vendu", "Bénéfice", "Statut"])

# Calcul essai
jours_restants = 7 - (datetime.now() - st.session_state.date_install).days

# --- LOGIQUE D'ACCÈS (PAYCARD 379 705 545) ---
if jours_restants <= 0 and not st.session_state.licence_active:
    st.title("🔒 Activation VenteUp")
    st.error(f"Essai terminé. Payez 30 000 GNF au compte PayCard : 379 705 545")
    ref = st.text_input("Référence du paiement :")
    if st.button("Activer"):
        if len(ref) > 5:
            st.session_state.licence_active = True
            st.rerun()
else:
    with st.sidebar:
        st.title(f"🏪 {st.session_state.boutique_info['nom']}")
        choix = st.radio("MENU", ["🛒 Vente & Facture", "📦 Stock", "📈 Bénéfices & Dettes", "⚙️ Paramètres"])
        st.write("---")
        st.caption(f"Support : 610 51 89 73")

    # --- 1. VENTE & FACTURE ---
    if choix == "🛒 Vente & Facture":
        st.header("🛒 Nouvelle Vente")
        if st.session_state.stock.empty:
            st.warning("Le stock est vide.")
        else:
            with st.form("form_vente"):
                prod = st.selectbox("Article", st.session_state.stock["Produit"])
                info = st.session_state.stock[st.session_state.stock["Produit"] == prod].iloc[0]
                c1, c2, c3 = st.columns(3)
                p_v = c1.number_input("Prix (GNF)", value=float(info["Prix Vente"]))
                q_v = c2.number_input("Quantité", min_value=1, value=1)
                statut = c3.selectbox("Paiement", ["Payé", "Dette"])
                valider = st.form_submit_button("Enregistrer la vente")

                if valider:
                    if q_v <= info["Quantité"]:
                        benef = (p_v - float(info["Prix Achat"])) * q_v
                        n_v = {"Date": datetime.now().strftime("%d/%m %H:%M"), "Produit": prod, "Qte": q_v, "Prix Vendu": p_v*q_v, "Bénéfice": benef, "Statut": statut}
                        st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([n_v])], ignore_index=True)
                        # Soustraire du stock
                        st.session_state.stock.loc[st.session_state.stock["Produit"] == prod, "Quantité"] -= q_v
                        st.success("Vente réussie !")
                    else:
                        st.error("Stock insuffisant !")

        if not st.session_state.ventes.empty:
            st.subheader("Dernière facture")
            derniere = st.session_state.ventes.iloc[-1]
            facture_text = f"""
            *** {st.session_state.boutique_info['nom']} ***
            {st.session_state.boutique_info['adresse']}
            Tel: {st.session_state.boutique_info['tel']}
            ---------------------------
            Date: {derniere['Date']}
            Article: {derniere['Produit']}
            Qté: {derniere['Qte']}
            TOTAL: {derniere['Prix Vendu']} GNF
            Statut: {derniere['Statut']}
            ---------------------------
            Merci de votre confiance !
            """
            st.code(facture_text)
            st.info("💡 Copiez ce texte pour l'envoyer sur WhatsApp.")

    # --- 2. STOCK ---
    elif choix == "📦 Stock":
        st.header("📦 Gestion du Stock")
        with st.expander("➕ Ajouter un article"):
            n = st.text_input("Nom")
            pa = st.number_input("Prix Achat", min_value=0.0)
            pv = st.number_input("Prix Vente", min_value=0.0)
            q = st.number_input("Quantité", min_value=1)
            if st.button("Enregistrer"):
                new_p = {"Produit": n, "Prix Achat": pa, "Prix Vente": pv, "Quantité": q}
                st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([new_p])], ignore_index=True)
                st.rerun()

        st.subheader("📋 Liste des produits")
        for i, row in st.session_state.stock.iterrows():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            color = "🔴" if row['Quantité'] < 5 else "🟢"
            col1.write(f"{color} **{row['Produit']}**")
            col2.write(f"{row['Prix Vente']} GNF")
            col3.write(f"Stock: {row['Quantité']}")
            if col4.button("🗑️", key=f"del_st_{i}"):
                st.session_state.stock = st.session_state.stock.drop(i).reset_index(drop=True)
                st.rerun()

    # --- 3. BÉNÉFICES & DETTES ---
    elif choix == "📈 Bénéfices & Dettes":
        st.header("📈 Rapport d'activité")
        dettes = st.session_state.ventes[st.session_state.ventes["Statut"] == "Dette"]
        st.metric("Total Dettes", f"{dettes['Prix Vendu'].sum():,.0f} GNF")
        st.metric("Bénéfice Réel", f"{st.session_state.ventes['Bénéfice'].sum():,.0f} GNF")
        
        st.subheader("Historique des Ventes")
        for i, row in st.session_state.ventes.iterrows():
            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
            c1.write(f"{row['Date']} - {row['Produit']} (x{row['Qte']})")
            c2.write(f"{row['Prix Vendu']} GNF")
            c3.write(f"**{row['Statut']}**")
            if c4.button("🗑️", key=f"del_v_{i}"):
                st.session_state.ventes = st.session_state.ventes.drop(i).reset_index(drop=True)
                st.rerun()

    # --- 4. PARAMÈTRES (CONFIG BOUTIQUE) ---
    elif choix == "⚙️ Paramètres":
        st.header("⚙️ Configuration Boutique")
        with st.form("info_boutique"):
            nom = st.text_input("Nom de la boutique", value=st.session_state.boutique_info['nom'])
            adr = st.text_input("Adresse / Quartier", value=st.session_state.boutique_info['adresse'])
            tel = st.text_input("Téléphone", value=st.session_state.boutique_info['tel'])
            if st.form_submit_button("Enregistrer les infos"):
                st.session_state.boutique_info = {"nom": nom, "adresse": adr, "tel": tel}
                st.success("Infos mises à jour !")
        
        st.write("---")
        if st.button("🔴 Réinitialiser l'application"):
            st.session_state.clear()
            st.rerun()
