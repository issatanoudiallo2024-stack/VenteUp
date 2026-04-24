import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. Configuration de la page
st.set_page_config(page_title="VenteUp Pro - Permanent", layout="wide")

# --- SYSTÈME DE SAUVEGARDE DE FICHIERS ---
def charger_csv(nom_fichier, colonnes):
    if os.path.exists(nom_fichier):
        try:
            return pd.read_csv(nom_fichier)
        except:
            return pd.DataFrame(columns=colonnes)
    return pd.DataFrame(columns=colonnes)

def sauver_csv(df, nom_fichier):
    df.to_csv(nom_fichier, index=False)

# --- INITIALISATION ET CHARGEMENT ---
if 'stock' not in st.session_state:
    st.session_state.stock = charger_csv("stock_data.csv", ["Produit", "Prix Achat", "Prix Vente", "Quantité"])

if 'ventes' not in st.session_state:
    st.session_state.ventes = charger_csv("ventes_data.csv", ["Date", "Client", "Total", "Bénéfice"])

if 'panier' not in st.session_state:
    st.session_state.panier = []

if 'boutique_info' not in st.session_state:
    # On pourrait aussi sauver ça en CSV, mais restons simple pour l'instant
    st.session_state.boutique_info = {"nom": "Ma Boutique", "adresse": "Conakry", "tel": "6XX XX XX XX"}

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title(f"🏪 {st.session_state.boutique_info['nom']}")
    choix = st.radio("MENU", ["🛒 Caisse (Vente)", "📦 Stock", "📈 Historique", "⚙️ Paramètres"])
    st.markdown("---")
    if st.button("♻️ Actualiser les données"):
        st.rerun()
    st.caption("Support : 610 51 89 73")

# --- 1. CAISSE & FACTURATION ---
if choix == "🛒 Caisse (Vente)":
    st.header("🛒 Caisse & Facturation")
    
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.subheader("➕ Ajouter au panier")
        if st.session_state.stock.empty:
            st.warning("Stock vide ! Ajoutez des produits d'abord.")
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
                    st.success(f"Ajouté : {prod_nom}")
                else:
                    st.error("Stock insuffisant !")

    with col_b:
        st.subheader("📋 Panier actuel")
        if st.session_state.panier:
            df_p = pd.DataFrame(st.session_state.panier)
            st.table(df_p[["Produit", "Qte", "Total"]])
            total_panier = df_p["Total"].sum()
            st.write(f"### TOTAL : **{total_panier:,.0f} GNF**")
            if st.button("🗑️ Vider"):
                st.session_state.panier = []
                st.rerun()
        else:
            st.info("Panier vide.")

    # Validation et Facture
    if st.session_state.panier:
        st.markdown("---")
        st.subheader("📄 Infos Acheteur")
        c_c, c_d = st.columns(2)
        n_c = c_c.text_input("Nom de l'acheteur")
        a_c = c_d.text_input("Adresse de l'acheteur")
        
        if st.button("✅ Valider l'Achat"):
            benef_t = sum(i['Bénéfice'] for i in st.session_state.panier)
            nouvelle_v = {
                "Date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Client": n_c if n_c else "Anonyme",
                "Total": total_panier,
                "Bénéfice": benef_t
            }
            # Sauvegarde Vente
            st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([nouvelle_v])], ignore_index=True)
            sauver_csv(st.session_state.ventes, "ventes_data.csv")
            
            # Mise à jour Stock
            for i in st.session_state.panier:
                st.session_state.stock.loc[st.session_state.stock["Produit"] == i["Produit"], "Quantité"] -= i["Qte"]
            sauver_csv(st.session_state.stock, "stock_data.csv")
            
            # Affichage Facture
            st.success("Vente enregistrée en base de données !")
            facture_pro = f"""
=========================================
      {st.session_state.boutique_info['nom'].upper()}
      {st.session_state.boutique_info['adresse']}
      Tél: {st.session_state.boutique_info['tel']}
=========================================
CLIENT : {n_c if n_c else 'Client Passager'}
ADRESSE : {a_c if a_c else 'N/A'}
DATE : {datetime.now().strftime("%d/%m/%Y %H:%M")}
-----------------------------------------
DÉSIGNATION       QTÉ      TOTAL (GNF)
"""
            for i in st.session_state.panier:
                facture_pro += f"{i['Produit'][:15]:<17} {i['Qte']:<8} {i['Total']:,.0f}\n"
            facture_pro += f"-----------------------------------------\nTOTAL : {total_panier:,.0f} GNF\n========================================="
            st.code(facture_pro)
            st.session_state.panier = [] # Vider après succès

# --- 2. STOCK ---
elif choix == "📦 Stock":
    st.header("📦 Gestion Permanente du Stock")
    with st.expander("➕ Ajouter un nouveau produit"):
        n = st.text_input("Nom")
        pa = st.number_input("Prix Achat", min_value=0.0)
        pv = st.number_input("Prix Vente", min_value=0.0)
        q = st.number_input("Quantité", min_value=1)
        if st.button("Sauvegarder en base"):
            new_p = {"Produit": n, "Prix Achat": pa, "Prix Vente": pv, "Quantité": q}
            st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([new_p])], ignore_index=True)
            sauver_csv(st.session_state.stock, "stock_data.csv")
            st.success("Produit sauvé !")
            st.rerun()

    st.subheader("📋 Liste des articles")
    if not st.session_state.stock.empty:
        for i, row in st.session_state.stock.iterrows():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            c1.write(f"**{row['Produit']}**")
            c2.write(f"{row['Prix Vente']:,} GNF")
            c3.write(f"En stock: {row['Quantité']}")
            if c4.button("🗑️", key=f"ds_{i}"):
                st.session_state.stock = st.session_state.stock.drop(i).reset_index(drop=True)
                sauver_csv(st.session_state.stock, "stock_data.csv")
                st.rerun()

# --- 3. HISTORIQUE ---
elif choix == "📈 Historique":
    st.header("📈 Historique des Ventes")
    if not st.session_state.ventes.empty:
        st.metric("Total CA", f"{st.session_state.ventes['Total'].sum():,.0f} GNF")
        st.dataframe(st.session_state.ventes, use_container_width=True)
        if st.button("🔴 Effacer tout l'historique"):
            st.session_state.ventes = pd.DataFrame(columns=["Date", "Client", "Total", "Bénéfice"])
            sauver_csv(st.session_state.ventes, "ventes_data.csv")
            st.rerun()
    else:
        st.info("Aucune donnée enregistrée.")

# --- 4. CONFIGURATION ---
elif choix == "⚙️ Paramètres":
    st.header("⚙️ Boutique")
    st.session_state.boutique_info['nom'] = st.text_input("Nom boutique", value=st.session_state.boutique_info['nom'])
    st.session_state.boutique_info['adresse'] = st.text_input("Adresse", value=st.session_state.boutique_info['adresse'])
    st.session_state.boutique_info['tel'] = st.text_input("Tél", value=st.session_state.boutique_info['tel'])
    if st.button("Valider les infos"):
        st.success("C'est enregistré !")
