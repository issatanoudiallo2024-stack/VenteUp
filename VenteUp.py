import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Configuration
st.set_page_config(page_title="VenteUp Pro", layout="wide")

# --- INITIALISATION DES VARIABLES ---
if 'panier' not in st.session_state:
    st.session_state.panier = []
if 'stock' not in st.session_state:
    st.session_state.stock = pd.DataFrame(columns=["Produit", "Prix Achat", "Prix Vente", "Quantité"])
if 'ventes' not in st.session_state:
    st.session_state.ventes = pd.DataFrame(columns=["Date", "Client", "Total", "Bénéfice"])
if 'boutique_info' not in st.session_state:
    st.session_state.boutique_info = {"nom": "Ma Boutique", "adresse": "Conakry", "tel": "6XX XX XX XX"}

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title(f"🏪 {st.session_state.boutique_info['nom']}")
    choix = st.radio("MENU", ["🛒 Caisse (Vente)", "📦 Stock", "📈 Historique", "⚙️ Configuration"])
    st.markdown("---")
    st.caption("Support : 610 51 89 73")

# --- 1. CAISSE (GESTION DU PANIER & FACTURE) ---
if choix == "🛒 Caisse (Vente)":
    st.header("🛒 Caisse & Facturation")
    
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.subheader("➕ Ajouter au panier")
        if st.session_state.stock.empty:
            st.warning("Le stock est vide. Ajoutez des produits d'abord.")
        else:
            prod_nom = st.selectbox("Choisir l'article", st.session_state.stock["Produit"])
            info_p = st.session_state.stock[st.session_state.stock["Produit"] == prod_nom].iloc[0]
            
            c1, c2 = st.columns(2)
            qte_v = c1.number_input("Quantité", min_value=1, value=1)
            prix_v = c2.number_input("Prix unitaire (GNF)", value=float(info_p["Prix Vente"]))
            
            if st.button("🛒 Ajouter au panier"):
                if qte_v <= info_p["Quantité"]:
                    item = {
                        "Produit": prod_nom,
                        "Qte": qte_v,
                        "Prix": prix_v,
                        "Total": prix_v * qte_v,
                        "Bénéfice": (prix_v - info_p["Prix Achat"]) * qte_v
                    }
                    st.session_state.panier.append(item)
                    st.success(f"{prod_nom} ajouté !")
                else:
                    st.error("Stock insuffisant !")

    with col_b:
        st.subheader("📋 Panier actuel")
        if st.session_state.panier:
            df_panier = pd.DataFrame(st.session_state.panier)
            st.table(df_panier[["Produit", "Qte", "Total"]])
            total_panier = df_panier["Total"].sum()
            st.write(f"### TOTAL : **{total_panier:,.0f} GNF**")
            
            if st.button("🗑️ Vider le panier"):
                st.session_state.panier = []
                st.rerun()
        else:
            st.info("Le panier est vide.")

    # --- GÉNÉRATION DE LA FACTURE FINALE ---
    if st.session_state.panier:
        st.markdown("---")
        st.subheader("📄 Renseignements de l'Acheteur")
        col_c, col_d = st.columns(2)
        nom_client = col_c.text_input("Nom du Client")
        adr_client = col_d.text_input("Adresse du Client")
        
        if st.button("✅ Valider l'achat et Générer la Facture"):
            # Enregistrement dans l'historique
            benef_total = sum(item['Bénéfice'] for item in st.session_state.panier)
            nouvelle_v = {
                "Date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Client": nom_client if nom_client else "Anonyme",
                "Total": total_panier,
                "Bénéfice": benef_total
            }
            st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([nouvelle_v])], ignore_index=True)
            
            # Mise à jour du stock
            for item in st.session_state.panier:
                st.session_state.stock.loc[st.session_state.stock["Produit"] == item["Produit"], "Quantité"] -= item["Qte"]

            # --- AFFICHAGE DE LA FACTURE PRO ---
            st.success("Vente enregistrée !")
            st.markdown("### 📄 FACTURE OFFICIELLE")
            facture_pro = f"""
=========================================
      {st.session_state.boutique_info['nom'].upper()}
      {st.session_state.boutique_info['adresse']}
      Tél: {st.session_state.boutique_info['tel']}
=========================================
CLIENT : {nom_client if nom_client else 'Client Passager'}
ADRESSE : {adr_client if adr_client else 'N/A'}
DATE : {datetime.now().strftime("%d/%m/%Y %H:%M")}
-----------------------------------------
DÉSIGNATION       QTÉ      TOTAL (GNF)
"""
            for item in st.session_state.panier:
                facture_pro += f"{item['Produit'][:15]:<17} {item['Qte']:<8} {item['Total']:,.0f}\n"
            
            facture_pro += f"""-----------------------------------------
TOTAL À PAYER :      {total_panier:,.0f} GNF
-----------------------------------------
Merci de votre fidélité !
=========================================
            """
            st.code(facture_pro)
            st.session_state.panier = [] # On vide le panier après la facture

# --- 2. STOCK ---
elif choix == "📦 Stock":
    st.header("📦 Gestion du Stock")
    with st.expander("➕ Ajouter / Modifier un produit"):
        n = st.text_input("Nom de l'article")
        pa = st.number_input("Prix Achat", min_value=0.0)
        pv = st.number_input("Prix Vente", min_value=0.0)
        q = st.number_input("Quantité", min_value=1)
        if st.button("Enregistrer"):
            new_p = {"Produit": n, "Prix Achat": pa, "Prix Vente": pv, "Quantité": q}
            st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([new_p])], ignore_index=True)
            st.rerun()

    st.subheader("📋 Liste des produits")
    if not st.session_state.stock.empty:
        for i, row in st.session_state.stock.iterrows():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            c1.write(f"**{row['Produit']}**")
            c2.write(f"{row['Prix Vente']:,} GNF")
            c3.write(f"Stock: {row['Quantité']}")
            if c4.button("🗑️", key=f"del_s_{i}"):
                st.session_state.stock = st.session_state.stock.drop(i).reset_index(drop=True)
                st.rerun()

# --- 3. CONFIGURATION ---
elif choix == "⚙️ Configuration":
    st.header("⚙️ Paramètres de la Boutique")
    with st.form("config"):
        st.session_state.boutique_info['nom'] = st.text_input("Nom de l'Etablissement", value=st.session_state.boutique_info['nom'])
        st.session_state.boutique_info['adresse'] = st.text_input("Adresse complète", value=st.session_state.boutique_info['adresse'])
        st.session_state.boutique_info['tel'] = st.text_input("Téléphone Contact", value=st.session_state.boutique_info['tel'])
        if st.form_submit_button("Enregistrer les réglages"):
            st.success("Informations de la boutique mises à jour !")

