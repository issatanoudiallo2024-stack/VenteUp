import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. Configuration
st.set_page_config(page_title="VenteUp Ultimate Pro", layout="wide")

# --- PERSISTANCE ---
def charger_csv(nom_fichier, colonnes):
    if os.path.exists(nom_fichier):
        try: return pd.read_csv(nom_fichier)
        except: return pd.DataFrame(columns=colonnes)
    return pd.DataFrame(columns=colonnes)

def sauver_csv(df, nom_fichier):
    df.to_csv(nom_fichier, index=False)

# --- INITIALISATION ---
if 'stock' not in st.session_state:
    st.session_state.stock = charger_csv("stock_data.csv", ["Produit", "Prix Achat", "Prix Vente", "Quantité"])
if 'ventes' not in st.session_state:
    st.session_state.ventes = charger_csv("ventes_data.csv", ["Date", "Client", "Total", "Bénéfice"])
if 'panier' not in st.session_state:
    st.session_state.panier = []
if 'boutique_info' not in st.session_state:
    st.session_state.boutique_info = {"nom": "MA BOUTIQUE", "adresse": "Conakry", "tel": "6XX XX XX XX"}

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"🏪 {st.session_state.boutique_info['nom']}")
    choix = st.radio("MENU", ["🛒 Caisse", "📦 Stock", "📈 Historique", "⚙️ Paramètres"])

# --- 🛒 CAISSE ---
if choix == "🛒 Caisse":
    st.header("🛒 Caisse & Facturation")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.stock.empty:
            st.warning("Stock vide !")
        else:
            prod = st.selectbox("Article", st.session_state.stock["Produit"])
            info = st.session_state.stock[st.session_state.stock["Produit"] == prod].iloc[0]
            qte = st.number_input("Quantité", min_value=1, value=1)
            px = st.number_input("Prix (GNF)", value=float(info["Prix Vente"]))
            if st.button("🛒 Ajouter"):
                if qte <= info["Quantité"]:
                    st.session_state.panier.append({"Produit": prod, "Qte": qte, "Prix": px, "Total": px*qte, "Bénéfice": (px - info["Prix Achat"])*qte})
                    st.success("Ajouté !")
                else: st.error("Stock insuffisant !")

    with col2:
        if st.session_state.panier:
            st.table(pd.DataFrame(st.session_state.panier)[["Produit", "Qte", "Total"]])
            if st.button("🗑️ Vider"):
                st.session_state.panier = []
                st.rerun()

    if st.session_state.panier:
        st.write("---")
        c1, c2, c3 = st.columns(3)
        nom_cl = c1.text_input("Nom Client")
        tel_cl = c2.text_input("Tel Client")
        adr_cl = c3.text_input("Adresse")

        if st.button("✅ Valider & Générer Facture"):
            total_f = sum(i['Total'] for i in st.session_state.panier)
            # Sauvegardes
            nv = {"Date": datetime.now().strftime("%d/%m/%Y %H:%M"), "Client": nom_cl, "Total": total_f, "Bénéfice": sum(i['Bénéfice'] for i in st.session_state.panier)}
            st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([nv])], ignore_index=True)
            sauver_csv(st.session_state.ventes, "ventes_data.csv")
            for i in st.session_state.panier:
                st.session_state.stock.loc[st.session_state.stock["Produit"] == i["Produit"], "Quantité"] -= i["Qte"]
            sauver_csv(st.session_state.stock, "stock_data.csv")

            # --- LA FACTURE CORRIGÉE ---
            lignes = ""
            for idx, it in enumerate(st.session_state.panier):
                lignes += f"<tr><td border='1'>{idx+1}</td><td>{it['Produit']}</td><td>{it['Qte']}</td><td>{it['Prix']:,}</td><td>{it['Total']:,}</td></tr>"

            facture_html = f"""
            <div style="font-family: sans-serif; border: 2px solid black; padding: 20px; background: white; color: black;">
                <center><h2>{st.session_state.boutique_info['nom']}</h2><p>{st.session_state.boutique_info['adresse']} | Tél: {st.session_state.boutique_info['tel']}</p></center>
                <hr>
                <p><b>Client:</b> {nom_cl} | <b>Tel:</b> {tel_cl} | <b>Date:</b> {datetime.now().strftime("%d/%m/%Y")}</p>
                <table border="1" style="width: 100%; border-collapse: collapse; text-align: center;">
                    <thead style="background: #eee;">
                        <tr><th>N°</th><th>Désignation</th><th>Qté</th><th>P.U</th><th>Total</th></tr>
                    </thead>
                    <tbody>{lignes}</tbody>
                </table>
                <h3 style="text-align: right; color: red;">NET À PAYER : {total_f:,.0f} GNF</h3>
                <center><p>Merci de votre visite !</p></center>
            </div>
            """
            st.markdown(facture_html, unsafe_allow_html=True)
            st.session_state.panier = []

# --- 📦 STOCK ---
elif choix == "📦 Stock":
    st.header("📦 Stock")
    with st.expander("Ajouter"):
        n = st.text_input("Nom")
        pa = st.number_input("Achat", 0.0)
        pv = st.number_input("Vente", 0.0)
        q = st.number_input("Qté", 1)
        if st.button("Sauver"):
            st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([{"Produit":n,"Prix Achat":pa,"Prix Vente":pv,"Quantité":q}])], ignore_index=True)
            sauver_csv(st.session_state.stock, "stock_data.csv")
            st.rerun()
    st.dataframe(st.session_state.stock)
    if st.button("Supprimer tout le stock"):
        st.session_state.stock = pd.DataFrame(columns=["Produit", "Prix Achat", "Prix Vente", "Quantité"])
        sauver_csv(st.session_state.stock, "stock_data.csv")
        st.rerun()

# --- 📈 HISTORIQUE & PARAMÈTRES ---
elif choix == "📈 Historique":
    st.header("📈 Ventes")
    st.dataframe(st.session_state.ventes)
elif choix == "⚙️ Paramètres":
    st.header("⚙️ Config")
    st.session_state.boutique_info['nom'] = st.text_input("Nom boutique", st.session_state.boutique_info['nom'])
    st.session_state.boutique_info['adresse'] = st.text_input("Adresse", st.session_state.boutique_info['adresse'])
    st.session_state.boutique_info['tel'] = st.text_input("Tel", st.session_state.boutique_info['tel'])
    st.success("Enregistré !")
