import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. Configuration
st.set_page_config(page_title="VenteUp Pro", layout="wide")

def charger_csv(nom, col):
    if os.path.exists(nom):
        try: return pd.read_csv(nom)
        except: return pd.DataFrame(columns=col)
    return pd.DataFrame(columns=col)

def sauver_csv(df, nom):
    df.to_csv(nom, index=False)

# --- INITIALISATION ---
if 'stock' not in st.session_state:
    st.session_state.stock = charger_csv("stock_data.csv", ["Produit", "Prix Achat", "Prix Vente", "Quantité"])
if 'ventes' not in st.session_state:
    st.session_state.ventes = charger_csv("ventes_data.csv", ["Date", "Client", "Total", "Bénéfice"])
if 'panier' not in st.session_state:
    st.session_state.panier = []
if 'boutique_info' not in st.session_state:
    st.session_state.boutique_info = {"nom": "", "adresse": "", "tel": ""}

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title("🚀 VenteUp Pro")
    choix = st.radio("MENU", ["🛒 Caisse", "📦 Stock & Alerte", "📈 Historique", "⚙️ Paramètres"])
    st.markdown("---")
    st.write("**Développeur :** Issa Diallo")
    st.write("📞 **Contact :** 610 51 89 73")

# --- 1. CAISSE ---
if choix == "🛒 Caisse":
    st.header("🛒 Interface de Vente")
    
    # Signal d'alerte global en haut de la caisse
    alerte_stock = st.session_state.stock[st.session_state.stock["Quantité"] <= 5]
    if not alerte_stock.empty:
        for _, row in alerte_stock.iterrows():
            st.error(f"⚠️ **Alerte Stock Bas :** Il ne reste que {row['Quantité']} unité(s) de '{row['Produit']}' !")

    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.stock.empty:
            st.info("Stock vide.")
        else:
            p_sel = st.selectbox("Article", st.session_state.stock["Produit"])
            info = st.session_state.stock[st.session_state.stock["Produit"] == p_sel].iloc[0]
            st.write(f"Stock disponible : **{info['Quantité']}**")
            q = st.number_input("Quantité à vendre", min_value=1, value=1)
            if st.button("🛒 Ajouter au panier"):
                if q <= info["Quantité"]:
                    st.session_state.panier.append({
                        "Produit": p_sel, "Qte": q, "Prix": info["Prix Vente"], 
                        "Total": info["Prix Vente"]*q, "Ben": (info["Prix Vente"]-info["Prix Achat"])*q
                    })
                    st.success("Ajouté")
                else:
                    st.error("Quantité insuffisante !")

    with col2:
        if st.session_state.panier:
            st.subheader("Panier")
            st.table(pd.DataFrame(st.session_state.panier)[["Produit", "Qte", "Total"]])
            if st.button("🗑️ Vider"):
                st.session_state.panier = []; st.rerun()

    if st.session_state.panier:
        st.write("---")
        c_n = st.text_input("Nom du Client", "")
        if st.button("✅ Valider & Facture"):
            if not c_n: st.error("Nom client requis")
            else:
                total_v = sum(i['Total'] for i in st.session_state.panier)
                date_v = datetime.now().strftime("%d/%m/%Y %H:%M")
                # Sauvegarde vente
                new_v = {"Date": date_v, "Client": c_n, "Total": total_v, "Bénéfice": sum(i['Ben'] for i in st.session_state.panier)}
                st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([new_v])], ignore_index=True)
                sauver_csv(st.session_state.ventes, "ventes_data.csv")
                # Update Stock
                for i in st.session_state.panier:
                    st.session_state.stock.loc[st.session_state.stock["Produit"] == i["Produit"], "Quantité"] -= i["Qte"]
                sauver_csv(st.session_state.stock, "stock_data.csv")
                
                # Affichage Facture
                fact_html = f"<div style='border:1px solid #000; padding:15px; background:white; color:black;'><h3>{st.session_state.boutique_info['nom']}</h3><p>Client: {c_n}<br>Total: {total_v:,.0f} GNF</p><button onclick='window.print()'>Imprimer</button></div>"
                st.markdown(fact_html, unsafe_allow_html=True)
                st.session_state.panier = []

# --- 2. STOCK & RÉAPPROVISIONNEMENT ---
elif choix == "📦 Stock & Alerte":
    st.header("📦 Gestion du Stock")
    
    tab1, tab2 = st.tabs(["➕ Nouveau Produit", "🔄 Réapprovisionner"])
    
    with tab1:
        with st.form("nouveau"):
            n = st.text_input("Nom Produit")
            pa = st.number_input("Prix Achat", value=0)
            pv = st.number_input("Prix Vente", value=0)
            q = st.number_input("Qté Initiale", value=1)
            if st.form_submit_button("Créer le produit"):
                if n:
                    st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([{"Produit":n,"Prix Achat":pa,"Prix Vente":pv,"Quantité":q}])], ignore_index=True)
                    sauver_csv(st.session_state.stock, "stock_data.csv"); st.success("Produit créé !"); st.rerun()

    with tab2:
        if not st.session_state.stock.empty:
            p_reap = st.selectbox("Choisir l'article à réapprovisionner", st.session_state.stock["Produit"])
            q_aj = st.number_input("Quantité à AJOUTER", min_value=1, value=1)
            if st.button("🔄 Valider l'ajout"):
                st.session_state.stock.loc[st.session_state.stock["Produit"] == p_reap, "Quantité"] += q_aj
                sauver_csv(st.session_state.stock, "stock_data.csv")
                st.success(f"Stock de {p_reap} mis à jour !")
                st.rerun()

    st.write("---")
    st.subheader("État Global du Stock")
    
    # Coloration du tableau pour les alertes
    def color_stock(val):
        color = 'red' if val <= 5 else 'black'
        return f'color: {color}'
    
    if not st.session_state.stock.empty:
        st.dataframe(st.session_state.stock.style.applymap(color_stock, subset=['Quantité']), use_container_width=True)

# --- 3. HISTORIQUE & PARAMÈTRES (Restent identiques) ---
elif choix == "📈 Historique":
    st.header("📈 Historique")
    st.dataframe(st.session_state.ventes, use_container_width=True)
elif choix == "⚙️ Paramètres":
    st.header("⚙️ Paramètres")
    st.session_state.boutique_info['nom'] = st.text_input("Nom Enseigne", st.session_state.boutique_info['nom'])
    st.session_state.boutique_info['adresse'] = st.text_input("Adresse", st.session_state.boutique_info['adresse'])
    st.session_state.boutique_info['tel'] = st.text_input("Téléphone", st.session_state.boutique_info['tel'])
    if st.button("Sauvegarder"): st.success("Enregistré !")
