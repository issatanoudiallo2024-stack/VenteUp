import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. Configuration de la page
st.set_page_config(page_title="VenteUp Pro", layout="wide")

def charger_csv(nom, col):
    if os.path.exists(nom):
        try: return pd.read_csv(nom)
        except: return pd.DataFrame(columns=col)
    return pd.DataFrame(columns=col)

def sauver_csv(df, nom):
    df.to_csv(nom, index=False)

# --- INITIALISATION (VIDE POUR L'UTILISATEUR) ---
if 'stock' not in st.session_state:
    st.session_state.stock = charger_csv("stock_data.csv", ["Produit", "Prix Achat", "Prix Vente", "Quantité"])
if 'ventes' not in st.session_state:
    st.session_state.ventes = charger_csv("ventes_data.csv", ["Date", "Client", "Total", "Bénéfice"])
if 'panier' not in st.session_state:
    st.session_state.panier = []

# Dictionnaire vide pour forcer l'utilisateur à remplir ses infos
if 'boutique_info' not in st.session_state:
    st.session_state.boutique_info = {"nom": "", "adresse": "", "tel": ""}

# --- BARRE LATÉRALE (TES INFOS DE DÉVELOPPEUR) ---
with st.sidebar:
    st.title("🚀 VenteUp Pro")
    choix = st.radio("MENU", ["🛒 Caisse", "📦 Stock", "📈 Historique", "⚙️ Paramètres"])
    st.markdown("---")
    # TES INFOS SONT ICI
    st.write("**Développeur :** Issa Diallo") 
    st.write("📞 **Contact :** 610 51 89 73")
    st.caption("Étudiant à l'UGANC")

# --- 1. CAISSE & FACTURATION ---
if choix == "🛒 Caisse":
    st.header("🛒 Interface de Vente")
    
    if not st.session_state.boutique_info['nom']:
        st.warning("⚠️ Allez dans 'Paramètres' pour configurer le nom de votre boutique.")

    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.stock.empty:
            st.info("Le stock est vide.")
        else:
            p_sel = st.selectbox("Article", st.session_state.stock["Produit"])
            info = st.session_state.stock[st.session_state.stock["Produit"] == p_sel].iloc[0]
            q = st.number_input("Quantité", min_value=1, value=1)
            if st.button("🛒 Ajouter"):
                if q <= info["Quantité"]:
                    st.session_state.panier.append({
                        "Produit": p_sel, "Qte": q, "Prix": info["Prix Vente"], 
                        "Total": info["Prix Vente"]*q, "Ben": (info["Prix Vente"]-info["Prix Achat"])*q
                    })
                    st.success("Ajouté")
                else:
                    st.error("Stock insuffisant")

    with col2:
        if st.session_state.panier:
            st.subheader("Panier")
            st.table(pd.DataFrame(st.session_state.panier)[["Produit", "Qte", "Total"]])
            if st.button("🗑️ Vider"):
                st.session_state.panier = []; st.rerun()

    if st.session_state.panier:
        st.write("---")
        st.subheader("Client")
        c1, c2 = st.columns(2)
        c_n = c1.text_input("Nom du Client", "")
        c_t = c2.text_input("Téléphone", "")
        
        if st.button("✅ Valider & Imprimer"):
            if not c_n:
                st.error("Entrez le nom du client")
            else:
                total_v = sum(i['Total'] for i in st.session_state.panier)
                date_v = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                # Sauvegarde
                new_v = {"Date": date_v, "Client": c_n, "Total": total_v, "Bénéfice": sum(i['Ben'] for i in st.session_state.panier)}
                st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([new_v])], ignore_index=True)
                sauver_csv(st.session_state.ventes, "ventes_data.csv")
                
                for i in st.session_state.panier:
                    st.session_state.stock.loc[st.session_state.stock["Produit"] == i["Produit"], "Quantité"] -= i["Qte"]
                sauver_csv(st.session_state.stock, "stock_data.csv")

                # FACTURE NEUTRE (DÉPEND DES PARAMÈTRES UTILISATEUR)
                html = f"""
                <div style="font-family:sans-serif; border:1px solid #000; padding:20px; background:#fff; color:#000;">
                    <div style="display:flex; justify-content:space-between; border-bottom:1px solid #000; padding-bottom:10px;">
                        <div>
                            <h2 style="margin:0;">{st.session_state.boutique_info['nom'].upper()}</h2>
                            <p style="margin:0;">{st.session_state.boutique_info['adresse']}</p>
                            <p style="margin:0;">{st.session_state.boutique_info['tel']}</p>
                        </div>
                        <div style="text-align:right;">
                            <h2 style="margin:0;">FACTURE</h2>
                            <p style="margin:0;"><b>Client:</b> {c_n}</p>
                            <p style="margin:0;"><b>Date:</b> {date_v}</p>
                        </div>
                    </div>
                    <table style="width:100%; border-collapse:collapse; margin-top:20px;">
                        <tr style="border-bottom:1px solid #000;">
                            <th style="text-align:left; padding:5px;">Désignation</th>
                            <th style="padding:5px;">Qté</th>
                            <th style="text-align:right; padding:5px;">Total</th>
                        </tr>
                """
                for i in st.session_state.panier:
                    html += f"<tr><td style='padding:5px;'>{i['Produit']}</td><td style='padding:5px; text-align:center;'>{i['Qte']}</td><td style='padding:5px; text-align:right;'>{i['Total']:,.0f} GNF</td></tr>"
                
                html += f"""
                    </table>
                    <h3 style="text-align:right; margin-top:20px;">TOTAL NET : {total_v:,.0f} GNF</h3>
                </div>
                <br>
                <button onclick="window.print()" style="width:100%; padding:15px; background:#000; color:#fff; font-weight:bold; cursor:pointer;">
                    🖨️ IMPRIMER / ENREGISTRER PDF
                </button>
                """
                st.markdown(html, unsafe_allow_html=True)
                st.session_state.panier = []

# --- 2. STOCK ---
elif choix == "📦 Stock":
    st.header("📦 Gestion Stock")
    with st.expander("Ajouter un produit"):
        n = st.text_input("Nom"); pa = st.number_input("Prix Achat", value=0); pv = st.number_input("Prix Vente", value=0); q = st.number_input("Qté", value=0)
        if st.button("Ajouter"):
            st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([{"Produit":n,"Prix Achat":pa,"Prix Vente":pv,"Quantité":q}])], ignore_index=True)
            sauver_csv(st.session_state.stock, "stock_data.csv"); st.rerun()
    st.dataframe(st.session_state.stock, use_container_width=True)

# --- 3. PARAMÈTRES ---
elif choix == "⚙️ Paramètres":
    st.header("⚙️ Configuration Boutique")
    st.session_state.boutique_info['nom'] = st.text_input("Nom de l'Enseigne (ex: Ma Boutique)", st.session_state.boutique_info['nom'])
    st.session_state.boutique_info['adresse'] = st.text_input("Adresse", st.session_state.boutique_info['adresse'])
    st.session_state.boutique_info['tel'] = st.text_input("Contact", st.session_state.boutique_info['tel'])
    if st.button("Enregistrer"):
        st.success("Paramètres mis à jour !")

# --- 4. HISTORIQUE ---
elif choix == "📈 Historique":
    st.header("📈 Historique des Ventes")
    st.dataframe(st.session_state.ventes, use_container_width=True)
