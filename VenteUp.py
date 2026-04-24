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

# --- INITIALISATION VIDE (POUR L'UTILISATEUR) ---
if 'stock' not in st.session_state:
    st.session_state.stock = charger_csv("stock_data.csv", ["Produit", "Prix Achat", "Prix Vente", "Quantité"])
if 'ventes' not in st.session_state:
    st.session_state.ventes = charger_csv("ventes_data.csv", ["Date", "Client", "Total", "Bénéfice"])
if 'panier' not in st.session_state:
    st.session_state.panier = []

# Informations génériques par défaut
if 'boutique_info' not in st.session_state:
    st.session_state.boutique_info = {
        "nom": "NOM DE VOTRE BOUTIQUE", 
        "adresse": "VOTRE ADRESSE", 
        "tel": "VOTRE CONTACT"
    }

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title(f"🏪 {st.session_state.boutique_info['nom']}")
    choix = st.radio("MENU", ["🛒 Caisse", "📦 Stock", "📈 Historique", "⚙️ Paramètres"])
    st.write("---")
    st.write("**Concepteur :** Issa Diallo")
    st.write("📞 **Contact :** 610 51 89 73")

# --- 1. CAISSE ---
if choix == "🛒 Caisse":
    st.header("🛒 Caisse & Vente")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.stock.empty:
            st.warning("Stock vide. Allez dans 'Stock' pour ajouter des produits.")
        else:
            p_sel = st.selectbox("Article", st.session_state.stock["Produit"])
            info = st.session_state.stock[st.session_state.stock["Produit"] == p_sel].iloc[0]
            q = st.number_input("Quantité", min_value=1, value=1)
            if st.button("🛒 Ajouter au panier"):
                if q <= info["Quantité"]:
                    st.session_state.panier.append({
                        "Produit": p_sel, "Qte": q, "Prix": info["Prix Vente"], 
                        "Total": info["Prix Vente"]*q, "Ben": (info["Prix Vente"]-info["Prix Achat"])*q
                    })
                    st.success("Ajouté !")
                else:
                    st.error(f"Stock insuffisant ({info['Quantité']} restants)")

    with col2:
        if st.session_state.panier:
            st.subheader("Panier")
            st.table(pd.DataFrame(st.session_state.panier)[["Produit", "Qte", "Total"]])
            if st.button("🗑️ Vider le panier"):
                st.session_state.panier = []; st.rerun()

    if st.session_state.panier:
        st.write("---")
        st.subheader("Finaliser la vente")
        c1, c2, c3 = st.columns(3)
        c_n = c1.text_input("Nom Client", "Passager")
        c_t = c2.text_input("Tél Client", "-")
        c_a = c3.text_input("Adresse Client", "-")
        
        if st.button("✅ Valider & Imprimer"):
            total_v = sum(i['Total'] for i in st.session_state.panier)
            date_v = datetime.now().strftime("%d/%m/%Y %H:%M")
            
            # Sauvegardes
            new_v = {"Date": date_v, "Client": c_n, "Total": total_v, "Bénéfice": sum(i['Ben'] for i in st.session_state.panier)}
            st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([new_v])], ignore_index=True)
            sauver_csv(st.session_state.ventes, "ventes_data.csv")
            
            for i in st.session_state.panier:
                st.session_state.stock.loc[st.session_state.stock["Produit"] == i["Produit"], "Quantité"] -= i["Qte"]
            sauver_csv(st.session_state.stock, "stock_data.csv")

            # --- GÉNÉRATION HTML POUR IMPRESSION / PDF ---
            html = f"""
            <div id="printArea" style="font-family:sans-serif; border:1px solid #ddd; padding:20px; background:white; color:black;">
                <div style="display:flex; justify-content:space-between; border-bottom:2px solid #1a73e8; padding-bottom:10px;">
                    <div style="text-align:left;">
                        <h2 style="color:#1a73e8; margin:0;">{st.session_state.boutique_info['nom']}</h2>
                        <p style="margin:0;">{st.session_state.boutique_info['adresse']}</p>
                        <p style="margin:0;">{st.session_state.boutique_info['tel']}</p>
                    </div>
                    <div style="text-align:right;">
                        <h2 style="margin:0; color:#444;">FACTURE</h2>
                        <p style="margin:0;"><b>Client:</b> {c_n}</p>
                        <p style="margin:0;"><b>Date:</b> {date_v}</p>
                    </div>
                </div>
                <table style="width:100%; border-collapse:collapse; margin-top:20px;">
                    <tr style="background:#1a73e8; color:white;">
                        <th style="padding:10px; border:1px solid #ddd; text-align:left;">Désignation</th>
                        <th style="padding:10px; border:1px solid #ddd;">Qté</th>
                        <th style="padding:10px; border:1px solid #ddd; text-align:right;">Total</th>
                    </tr>
            """
            for i in st.session_state.panier:
                html += f"<tr><td style='padding:8px; border:1px solid #ddd;'>{i['Produit']}</td><td style='padding:8px; border:1px solid #ddd; text-align:center;'>{i['Qte']}</td><td style='padding:8px; border:1px solid #ddd; text-align:right;'>{i['Total']:,.0f} GNF</td></tr>"
            
            html += f"""
                </table>
                <h2 style="text-align:right; color:red; margin-top:20px;">TOTAL : {total_v:,.0f} GNF</h2>
            </div>
            <br>
            <button onclick="window.print()" style="width:100%; padding:15px; background:#28a745; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold;">
                🖨️ CLIQUEZ ICI POUR IMPRIMER OU ENREGISTRER EN PDF
            </button>
            """
            st.markdown(html, unsafe_allow_html=True)
            st.session_state.panier = [] # Vide après validation

# --- 2. STOCK ---
elif choix == "📦 Stock":
    st.header("📦 Gestion du Stock")
    with st.expander("Ajouter un article"):
        n = st.text_input("Désignation"); pa = st.number_input("Prix Achat"); pv = st.number_input("Prix Vente"); q = st.number_input("Qté initiale", min_value=1)
        if st.button("Enregistrer"):
            if n:
                st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([{"Produit":n,"Prix Achat":pa,"Prix Vente":pv,"Quantité":q}])], ignore_index=True)
                sauver_csv(st.session_state.stock, "stock_data.csv"); st.rerun()
    st.dataframe(st.session_state.stock, use_container_width=True)

# --- 3. HISTORIQUE ---
elif choix == "📈 Historique":
    st.header("📈 Rapport des Ventes")
    if not st.session_state.ventes.empty:
        st.metric("Total des Ventes", f"{st.session_state.ventes['Total'].sum():,.0f} GNF")
        st.dataframe(st.session_state.ventes, use_container_width=True)

# --- 4. PARAMÈTRES ---
elif choix == "⚙️ Paramètres":
    st.header("⚙️ Réglages de la Boutique")
    st.info("Modifiez ces informations pour qu'elles apparaissent sur vos factures.")
    st.session_state.boutique_info['nom'] = st.text_input("Nom de l'Enseigne", st.session_state.boutique_info['nom'])
    st.session_state.boutique_info['adresse'] = st.text_input("Adresse / Quartier", st.session_state.boutique_info['adresse'])
    st.session_state.boutique_info['tel'] = st.text_input("Téléphone", st.session_state.boutique_info['tel'])
    if st.button("Sauvegarder les paramètres"):
        st.success("C'est enregistré !")
