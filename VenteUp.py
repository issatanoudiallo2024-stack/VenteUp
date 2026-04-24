import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. SYSTÈME DE LICENCE ---
CODE_DEBLOCAGE_SECRET = "ISSAVUP2026" 
FICHIER_LICENCE = "licence_config.csv"

def charger_licence():
    if os.path.exists(FICHIER_LICENCE):
        try: return pd.read_csv(FICHIER_LICENCE).iloc[0].to_dict()
        except: pass
    data = {"date_debut": datetime.now().strftime("%Y-%m-%d"), "statut": "essai"}
    pd.DataFrame([data]).to_csv(FICHIER_LICENCE, index=False)
    return data

def sauver_licence(statut):
    debut = charger_licence()["date_debut"]
    pd.DataFrame([{"date_debut": debut, "statut": statut}]).to_csv(FICHIER_LICENCE, index=False)

licence = charger_licence()
date_debut = datetime.strptime(licence["date_debut"], "%Y-%m-%d")
jours_restants = 7 - (datetime.now() - date_debut).days
est_bloque = licence["statut"] == "essai" and jours_restants < 0

if est_bloque:
    st.set_page_config(page_title="Activation Requise")
    st.error("🚫 PÉRIODE D'ESSAI TERMINÉE")
    st.info(f"Appelez Issa Diallo au : **610 51 89 73** pour activer l'accès.")
    code_saisi = st.text_input("Code d'activation", type="password")
    if st.button("Activer"):
        if code_saisi == CODE_DEBLOCAGE_SECRET:
            sauver_licence("paye")
            st.success("Activé !")
            st.rerun()
    st.stop()

# --- 2. CONFIGURATION APP ---
st.set_page_config(page_title="VenteUp Pro", layout="wide")

def charger_csv(nom, col):
    if os.path.exists(nom):
        try:
            df = pd.read_csv(nom)
            # SÉCURITÉ : Ajouter les colonnes manquantes si le fichier est ancien
            for c in col:
                if c not in df.columns: df[c] = "Inconnu" if c == "Statut" else 0
            return df
        except: return pd.DataFrame(columns=col)
    return pd.DataFrame(columns=col)

def sauver_csv(df, nom):
    df.to_csv(nom, index=False)

if 'stock' not in st.session_state:
    st.session_state.stock = charger_csv("stock_data.csv", ["Produit", "Prix Achat", "Prix Vente", "Quantité"])
if 'ventes' not in st.session_state:
    st.session_state.ventes = charger_csv("ventes_data.csv", ["Date", "Client", "Total", "Bénéfice", "Statut"])
if 'panier' not in st.session_state:
    st.session_state.panier = []
if 'boutique_info' not in st.session_state:
    st.session_state.boutique_info = {"nom": "", "adresse": "", "tel": ""}

# --- 3. BARRE LATÉRALE ---
with st.sidebar:
    st.title("🚀 VenteUp Pro")
    st.caption(f"⏳ Essai : {max(0, jours_restants)}j" if licence["statut"]=="essai" else "✅ Illimité")
    choix = st.radio("MENU", ["🛒 Caisse", "📦 Stock & Alerte", "📈 Historique", "⚙️ Paramètres"])
    st.write("---")
    st.write("**Développeur :** Issa Diallo\n📞 610 51 89 73")

# --- 4. CAISSE ---
if choix == "🛒 Caisse":
    st.header("🛒 Vente")
    col1, col2 = st.columns(2)
    with col1:
        if not st.session_state.stock.empty:
            p_sel = st.selectbox("Choisir l'article", st.session_state.stock["Produit"])
            info = st.session_state.stock[st.session_state.stock["Produit"] == p_sel].iloc[0]
            q = st.number_input("Quantité", min_value=1, value=1)
            if st.button("🛒 Ajouter"):
                if q <= info["Quantité"]:
                    st.session_state.panier.append({"Produit":p_sel,"Qte":q,"Prix":info["Prix Vente"],"Total":info["Prix Vente"]*q,"Ben":(info["Prix Vente"]-info["Prix Achat"])*q})
                    st.rerun()
                else: st.error("Stock insuffisant")
    with col2:
        if st.session_state.panier:
            st.table(pd.DataFrame(st.session_state.panier)[["Produit", "Qte", "Total"]])
            if st.button("🗑️ Vider"): st.session_state.panier = []; st.rerun()

    if st.session_state.panier:
        st.write("---")
        c_n = st.text_input("Nom Client")
        statut = st.radio("Paiement", ["Payé", "Dette"], horizontal=True)
        if st.button("✅ Valider"):
            if c_n:
                total_v = sum(i['Total'] for i in st.session_state.panier)
                new_v = {"Date":datetime.now().strftime("%d/%m/%Y %H:%M"), "Client":c_n, "Total":total_v, "Bénéfice":sum(i['Ben'] for i in st.session_state.panier), "Statut":statut}
                st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([new_v])], ignore_index=True)
                sauver_csv(st.session_state.ventes, "ventes_data.csv")
                for i in st.session_state.panier:
                    st.session_state.stock.loc[st.session_state.stock["Produit"]==i["Produit"], "Quantité"] -= i["Qte"]
                sauver_csv(st.session_state.stock, "stock_data.csv")
                st.success("Enregistré !"); st.session_state.panier = []; st.rerun()

# --- 5. STOCK ---
elif choix == "📦 Stock & Alerte":
    st.header("📦 Gestion Stock")
    t1, t2 = st.tabs(["➕ Réapprovisionnement", "🗑️ Supprimer"])
    with t1:
        with st.form("reap"):
            # AJOUT DE "Réapprovisionnement :" DEVANT
            n = st.text_input("Réapprovisionnement : Nom du produit")
            pa = st.number_input("Prix Achat", value=0)
            pv = st.number_input("Prix Vente", value=0)
            q = st.number_input("Quantité", value=0)
            if st.form_submit_button("Valider"):
                if n in st.session_state.stock["Produit"].values:
                    st.session_state.stock.loc[st.session_state.stock["Produit"]==n, "Quantité"] += q
                else:
                    st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([{"Produit":n,"Prix Achat":pa,"Prix Vente":pv,"Quantité":q}])], ignore_index=True)
                sauver_csv(st.session_state.stock, "stock_data.csv"); st.rerun()
    with t2:
        for i, row in st.session_state.stock.iterrows():
            c1, c2 = st.columns([4, 1])
            c1.write(f"**{row['Produit']}** ({row['Quantité']})")
            if c2.button("Supprimer", key=f"d_{i}"):
                st.session_state.stock = st.session_state.stock.drop(i).reset_index(drop=True)
                sauver_csv(st.session_state.stock, "stock_data.csv"); st.rerun()

# --- 6. HISTORIQUE ---
elif choix == "📈 Historique":
    st.header("📈 Historique")
    if not st.session_state.ventes.empty:
        # Affichage sécurisé des dettes (correction KeyError)
        if "Statut" in st.session_state.ventes.columns:
            dettes = st.session_state.ventes[st.session_state.ventes["Statut"] == "Dette"]
            if not dettes.empty: st.error(f"Dettes : {dettes['Total'].sum():,.0f} GNF")
        
        st.dataframe(st.session_state.ventes, use_container_width=True)
        if st.button("❌ Effacer tout l'historique"):
            st.session_state.ventes = pd.DataFrame(columns=["Date", "Client", "Total", "Bénéfice", "Statut"])
            sauver_csv(st.session_state.ventes, "ventes_data.csv"); st.rerun()

# --- 7. PARAMÈTRES ---
elif choix == "⚙️ Paramètres":
    st.header("⚙️ Paramètres")
    st.session_state.boutique_info['nom'] = st.text_input("Boutique", st.session_state.boutique_info['nom'])
    st.session_state.boutique_info['adresse'] = st.text_input("Adresse", st.session_state.boutique_info['adresse'])
    st.session_state.boutique_info['tel'] = st.text_input("Tél", st.session_state.boutique_info['tel'])
    if st.button("Sauver"): st.success("Ok !")
