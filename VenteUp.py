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

if 'stock' not in st.session_state:
    st.session_state.stock = charger_csv("stock_data.csv", ["Produit", "Prix Achat", "Prix Vente", "Quantité"])
if 'ventes' not in st.session_state:
    st.session_state.ventes = charger_csv("ventes_data.csv", ["Date", "Client", "Total", "Bénéfice"])
if 'panier' not in st.session_state:
    st.session_state.panier = []
if 'boutique_info' not in st.session_state:
    st.session_state.boutique_info = {"nom": "DARA BUSINESS", "adresse": "Ratoma, Bantounka 2", "tel": "610 51 89 73"}

with st.sidebar:
    st.title(f"🏪 {st.session_state.boutique_info['nom']}")
    choix = st.radio("MENU", ["🛒 Caisse", "📦 Stock", "📈 Historique", "⚙️ Paramètres"])
    st.write("---")
    st.caption("Développeur : Issa Diallo")

if choix == "🛒 Caisse":
    st.header("🛒 Caisse")
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.stock.empty: st.warning("Stock vide !")
        else:
            p_sel = st.selectbox("Article", st.session_state.stock["Produit"])
            info = st.session_state.stock[st.session_state.stock["Produit"] == p_sel].iloc[0]
            q = st.number_input("Quantité", min_value=1, value=1)
            if st.button("🛒 Ajouter"):
                if q <= info["Quantité"]:
                    st.session_state.panier.append({"Produit": p_sel, "Qte": q, "Prix": info["Prix Vente"], "Total": info["Prix Vente"]*q, "Ben": (info["Prix Vente"]-info["Prix Achat"])*q})
                    st.success("Ajouté !")
                else: st.error("Pas assez de stock !")
    with col2:
        if st.session_state.panier:
            st.table(pd.DataFrame(st.session_state.panier)[["Produit", "Qte", "Total"]])
            if st.button("🗑️ Vider"):
                st.session_state.panier = []; st.rerun()

    if st.session_state.panier:
        st.write("---")
        c_n = st.text_input("Client", "Mr Sow")
        c_t = st.text_input("Tél", "612 41 15 60")
        c_a = st.text_input("Adresse", "Simbayah")
        
        if st.button("✅ Valider & Facture"):
            total = sum(i['Total'] for i in st.session_state.panier)
            # Sauvegarde des ventes
            new_v = {"Date": datetime.now().strftime("%d/%m/%Y"), "Client": c_n, "Total": total, "Bénéfice": sum(i['Ben'] for i in st.session_state.panier)}
            st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([new_v])], ignore_index=True)
            sauver_csv(st.session_state.ventes, "ventes_data.csv")
            
            # Mise à jour du stock
            for i in st.session_state.panier:
                st.session_state.stock.loc[st.session_state.stock["Produit"] == i["Produit"], "Quantité"] -= i["Qte"]
            sauver_csv(st.session_state.stock, "stock_data.csv")

            # FACTURE HTML
            html = f"""
            <div style="font-family:sans-serif; border:1px solid #ddd; padding:20px; background:white; color:black;">
                <table style="width:100%; border-bottom:2px solid #1a73e8; margin-bottom:10px;">
                    <tr>
                        <td style="text-align:left;">
                            <h2 style="color:#1a73e8; margin:0;">{st.session_state.boutique_info['nom']}</h2>
                            <p style="margin:0;">{st.session_state.boutique_info['adresse']}<br>Tél: {st.session_state.boutique_info['tel']}</p>
                        </td>
                        <td style="text-align:right;">
                            <h2 style="margin:0;">FACTURE</h2>
                            <p style="margin:0;"><b>Client:</b> {c_n}<br><b>Tél:</b> {c_t}<br><b>Date:</b> {new_v['Date']}</p>
                        </td>
                    </tr>
                </table>
                <table style="width:100%; border-collapse:collapse;">
                    <tr style="background:#1a73e8; color:white;">
                        <th style="padding:10px; border:1px solid #ddd;">Désignation</th>
                        <th style="padding:10px; border:1px solid #ddd;">Qté</th>
                        <th style="padding:10px; border:1px solid #ddd;">Total</th>
                    </tr>
            """
            for i in st.session_state.panier:
                html += f"<tr><td style='padding:8px; border:1px solid #ddd;'>{i['Produit']}</td><td style='padding:8px; border:1px solid #ddd; text-align:center;'>{i['Qte']}</td><td style='padding:8px; border:1px solid #ddd; text-align:right;'>{i['Total']:,.0f} GNF</td></tr>"
            
            html += f"""
                </table>
                <h2 style="text-align:right; color:red; margin-top:15px;">TOTAL : {total:,.0f} GNF</h2>
            </div>
            <br><button onclick="window.print()" style="width:100%; padding:10px; background:#1a73e8; color:white; border:none; border-radius:5px; cursor:pointer;">🖨️ IMPRIMER / PDF</button>
            """
            st.markdown(html, unsafe_allow_html=True)
            st.session_state.panier = [] # Vider après affichage

elif choix == "📦 Stock":
    st.header("📦 Stock")
    with st.expander("Ajouter un produit"):
        n = st.text_input("Nom"); pa = st.number_input("Prix Achat"); pv = st.number_input("Prix Vente"); q = st.number_input("Qté initiale", min_value=1)
        if st.button("OK"):
            st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([{"Produit":n,"Prix Achat":pa,"Prix Vente":pv,"Quantité":q}])], ignore_index=True)
            sauver_csv(st.session_state.stock, "stock_data.csv"); st.success("Ajouté !"); st.rerun()
    st.dataframe(st.session_state.stock, use_container_width=True)

elif choix == "📈 Historique":
    st.header("📈 Historique")
    if not st.session_state.ventes.empty:
        st.metric("Chiffre d'Affaire", f"{st.session_state.ventes['Total'].sum():,.0f} GNF")
        st.dataframe(st.session_state.ventes, use_container_width=True)

elif choix == "⚙️ Paramètres":
    st.header("⚙️ Paramètres")
    st.session_state.boutique_info['nom'] = st.text_input("Nom", st.session_state.boutique_info['nom'])
    st.session_state.boutique_info['adresse'] = st.text_input("Adresse", st.session_state.boutique_info['adresse'])
    st.session_state.boutique_info['tel'] = st.text_input("Tél", st.session_state.boutique_info['tel'])
    if st.button("Enregistrer"): st.success("Paramètres sauvegardés !")
