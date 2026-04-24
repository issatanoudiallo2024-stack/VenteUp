import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. Configuration de la page
st.set_page_config(page_title="VenteUp Ultimate Pro", layout="wide")

# --- SYSTÈME DE PERSISTANCE (SAUVEGARDE) ---
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
    st.session_state.boutique_info = {"nom": "Ma Boutique", "adresse": "Conakry", "tel": "6XX XX XX XX"}

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title(f"🏪 {st.session_state.boutique_info['nom']}")
    choix = st.radio("MENU", ["🛒 Caisse (Vente)", "📦 Stock", "📈 Historique", "⚙️ Paramètres"])
    st.markdown("---")
    st.write(f"**Développeur :** Issa Diallo")
    st.caption("Compte PayCard : 379 705 545")

# --- 1. CAISSE & FACTURATION ---
if choix == "🛒 Caisse (Vente)":
    st.header("🛒 Caisse & Facturation")
    
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.subheader("➕ Ajouter au panier")
        if st.session_state.stock.empty:
            st.warning("Stock vide ! Ajoutez des produits dans l'onglet Stock.")
        else:
            prod_nom = st.selectbox("Article", st.session_state.stock["Produit"])
            info_p = st.session_state.stock[st.session_state.stock["Produit"] == prod_nom].iloc[0]
            
            c1, c2 = st.columns(2)
            qte_v = c1.number_input("Quantité", min_value=1, value=1)
            prix_v = c2.number_input("Prix Unitaire (GNF)", value=float(info_p["Prix Vente"]))
            
            if st.button("🛒 Ajouter au Panier"):
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
                    st.error(f"Stock insuffisant ! (Disponible : {info_p['Quantité']})")

    with col_b:
        st.subheader("📋 Récapitulatif Panier")
        if st.session_state.panier:
            df_p = pd.DataFrame(st.session_state.panier)
            st.table(df_p[["Produit", "Qte", "Total"]])
            total_actuel = df_p["Total"].sum()
            st.write(f"### TOTAL : **{total_actuel:,.0f} GNF**")
            if st.button("🗑️ Vider le panier"):
                st.session_state.panier = []
                st.rerun()
        else:
            st.info("Le panier est vide.")

    # --- GÉNÉRATION DE LA FACTURE ---
    if st.session_state.panier:
        st.markdown("---")
        st.subheader("👤 Coordonnées du Client")
        c_i1, c_i2, c_i3 = st.columns(3)
        n_cl = c_i1.text_input("Nom du client")
        t_cl = c_i2.text_input("Téléphone client")
        a_cl = c_i3.text_input("Adresse client")
        
        if st.button("✅ Valider l'Achat & Afficher la Facture"):
            total_f = sum(i['Total'] for i in st.session_state.panier)
            benef_f = sum(i['Bénéfice'] for i in st.session_state.panier)
            
            # Sauvegardes
            nouvelle_v = {"Date": datetime.now().strftime("%d/%m/%Y %H:%M"), "Client": n_cl if n_cl else "Passager", "Total": total_f, "Bénéfice": benef_f}
            st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([nouvelle_v])], ignore_index=True)
            sauver_csv(st.session_state.ventes, "ventes_data.csv")
            
            for item in st.session_state.panier:
                st.session_state.stock.loc[st.session_state.stock["Produit"] == item["Produit"], "Quantité"] -= item["Qte"]
            sauver_csv(st.session_state.stock, "stock_data.csv")

            # --- DESIGN FACTURE TABLEAU HTML ---
            facture_html = f"""
            <div style="border: 2px solid #000; padding: 25px; background-color: white; color: black; font-family: 'Arial';">
                <div style="text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px;">
                    <h2 style="margin:0;">{st.session_state.boutique_info['nom'].upper()}</h2>
                    <p style="margin:5px 0;">{st.session_state.boutique_info['adresse']} | Tél: {st.session_state.boutique_info['tel']}</p>
                </div>
                <div style="margin-top: 15px; display: flex; justify-content: space-between;">
                    <div>
                        <p><strong>CLIENT :</strong> {n_cl if n_cl else 'Client Passager'}</p>
                        <p><strong>TEL :</strong> {t_cl if t_cl else 'N/A'}</p>
                        <p><strong>ADRESSE :</strong> {a_cl if a_cl else 'N/A'}</p>
                    </div>
                    <div style="text-align: right;">
                        <p><strong>DATE :</strong> {datetime.now().strftime("%d/%m/%Y")}</p>
                        <p><strong>REÇU N° :</strong> {len(st.session_state.ventes)}</p>
                    </div>
                </div>
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px; border: 1px solid black;">
                    <thead>
                        <tr style="background-color: #eee; border: 1px solid black;">
                            <th style="padding: 8px; border: 1px solid black; text-align: center;">N°</th>
                            <th style="padding: 8px; border: 1px solid black; text-align: left;">Désignation Produit</th>
                            <th style="padding: 8px; border: 1px solid black; text-align: center;">Qté</th>
                            <th style="padding: 8px; border: 1px solid black; text-align: right;">Prix Unitaire</th>
                            <th style="padding: 8px; border: 1px solid black; text-align: right;">Prix Total</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for idx, item in enumerate(st.session_state.panier):
                facture_html += f"""
                        <tr>
                            <td style="padding: 8px; border: 1px solid black; text-align: center;">{idx+1}</td>
                            <td style="padding: 8px; border: 1px solid black;">{item['Produit']}</td>
                            <td style="padding: 8px; border: 1px solid black; text-align: center;">{item['Qte']}</td>
                            <td style="padding: 8px; border: 1px solid black; text-align: right;">{item['Prix']:,.0f}</td>
                            <td style="padding: 8px; border: 1px solid black; text-align: right;">{item['Total']:,.0f}</td>
                        </tr>
                """
            
            facture_html += f"""
                    </tbody>
                </table>
                <div style="text-align: right; margin-top: 20px;">
                    <h3 style="margin:0;">TOTAL NET À PAYER : <span style="color: red;">{total_f:,.0f} GNF</span></h3>
                </div>
                <div style="text-align: center; margin-top: 30px; font-style: italic;">
                    <p>Merci de votre visite et à bientôt !</p>
                </div>
            </div>
            """
            st.markdown(facture_html, unsafe_allow_html=True)
            st.session_state.panier = [] # Réinitialisation

# --- 2. STOCK ---
elif choix == "📦 Stock":
    st.header("📦 Gestion du Stock")
    with st.expander("➕ Ajouter un nouvel article"):
        nom = st.text_input("Nom de l'article")
        pa = st.number_input("Prix Achat", min_value=0.0)
        pv = st.number_input("Prix Vente", min_value=0.0)
        qt = st.number_input("Quantité", min_value=1)
        if st.button("Enregistrer en Stock"):
            if nom:
                new_p = {"Produit": nom, "Prix Achat": pa, "Prix Vente": pv, "Quantité": qt}
                st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([new_p])], ignore_index=True)
                sauver_csv(st.session_state.stock, "stock_data.csv")
                st.success("Stock enregistré !")
                st.rerun()

    st.subheader("📋 Liste des Produits")
    if not st.session_state.stock.empty:
        for i, row in st.session_state.stock.iterrows():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            col = "🟢" if row['Quantité'] > 5 else "🔴"
            c1.write(f"{col} **{row['Produit']}**")
            c2.write(f"{row['Prix Vente']:,} GNF")
            c3.write(f"Stock: {row['Quantité']}")
            if c4.button("🗑️", key=f"del_s_{i}"):
                st.session_state.stock = st.session_state.stock.drop(i).reset_index(drop=True)
                sauver_csv(st.session_state.stock, "stock_data.csv")
                st.rerun()

# --- 3. HISTORIQUE ---
elif choix == "📈 Historique":
    st.header("📈 Historique des Ventes")
    if not st.session_state.ventes.empty:
        st.metric("Chiffre d'Affaire Global", f"{st.session_state.ventes['Total'].sum():,.0f} GNF")
        st.dataframe(st.session_state.ventes, use_container_width=True)
        if st.button("❌ Effacer Tout l'Historique"):
            st.session_state.ventes = pd.DataFrame(columns=["Date", "Client", "Total", "Bénéfice"])
            sauver_csv(st.session_state.ventes, "ventes_data.csv")
            st.rerun()
    else:
        st.info("Aucune vente enregistrée.")

# --- 4. CONFIGURATION ---
elif choix == "⚙️ Paramètres":
    st.header("⚙️ Configuration Boutique")
    st.session_state.boutique_info['nom'] = st.text_input("Nom de la boutique", value=st.session_state.boutique_info['nom'])
    st.session_state.boutique_info['adresse'] = st.text_input("Quartier / Adresse", value=st.session_state.boutique_info['adresse'])
    st.session_state.boutique_info['tel'] = st.text_input("Contact Tél", value=st.session_state.boutique_info['tel'])
    if st.button("Enregistrer les Paramètres"):
        st.success("Informations boutique mises à jour !")
