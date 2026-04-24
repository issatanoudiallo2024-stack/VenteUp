import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. Configuration de la page
st.set_page_config(page_title="VenteUp Ultimate", layout="wide")

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

# --- INITIALISATION ET CHARGEMENT DES DONNÉES ---
if 'stock' not in st.session_state:
    st.session_state.stock = charger_csv("stock_data.csv", ["Produit", "Prix Achat", "Prix Vente", "Quantité"])

if 'ventes' not in st.session_state:
    st.session_state.ventes = charger_csv("ventes_data.csv", ["Date", "Client", "Total", "Bénéfice"])

if 'panier' not in st.session_state:
    st.session_state.panier = []

if 'boutique_info' not in st.session_state:
    st.session_state.boutique_info = {"nom": "Ma Boutique", "adresse": "Conakry", "tel": "610 51 89 73"}

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title(f"🏪 {st.session_state.boutique_info['nom']}")
    choix = st.radio("MENU", ["🛒 Caisse (Vente)", "📦 Stock", "📈 Historique", "⚙️ Paramètres"])
    st.markdown("---")
    st.write(f"**Propriétaire :** Issa Diallo")
    st.caption("Compte PayCard : 379 705 545")

# --- 1. CAISSE & FACTURATION ---
if choix == "🛒 Caisse (Vente)":
    st.header("🛒 Gestion des Ventes")
    
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.subheader("➕ Ajouter au panier")
        if st.session_state.stock.empty:
            st.warning("Le stock est vide. Ajoutez des produits d'abord.")
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
                    st.success(f"{prod_nom} ajouté !")
                else:
                    st.error(f"Stock insuffisant ! (Reste : {info_p['Quantité']})")

    with col_b:
        st.subheader("📋 Panier en cours")
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

    # --- SECTION CLIENT & FACTURE ---
    if st.session_state.panier:
        st.markdown("---")
        st.subheader("👤 Informations du Client")
        c_c1, c_c2, c_c3 = st.columns(3)
        nom_cl = c_c1.text_input("Nom du client")
        tel_cl = c_c2.text_input("Téléphone client")
        adr_cl = c_c3.text_input("Adresse client")
        
        if st.button("✅ Valider l'Achat & Générer la Facture"):
            # Calculs
            total_panier = sum(item['Total'] for item in st.session_state.panier)
            benef_total = sum(item['Bénéfice'] for item in st.session_state.panier)
            
            # 1. Sauvegarde Vente
            nouvelle_v = {
                "Date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Client": nom_cl if nom_cl else "Passager",
                "Total": total_panier,
                "Bénéfice": benef_total
            }
            st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([nouvelle_v])], ignore_index=True)
            sauver_csv(st.session_state.ventes, "ventes_data.csv")
            
            # 2. Mise à jour Stock
            for item in st.session_state.panier:
                st.session_state.stock.loc[st.session_state.stock["Produit"] == item["Produit"], "Quantité"] -= item["Qte"]
            sauver_csv(st.session_state.stock, "stock_data.csv")

            # 3. Affichage Facture HTML
            st.success("Vente enregistrée avec succès !")
            
            facture_html = f"""
            <div style="border: 2px solid #333; padding: 20px; border-radius: 10px; background-color: white; color: black; font-family: Arial;">
                <div style="text-align: center;">
                    <h1 style="margin: 0;">{st.session_state.boutique_info['nom'].upper()}</h1>
                    <p>{st.session_state.boutique_info['adresse']} | Tél: {st.session_state.boutique_info['tel']}</p>
                </div>
                <hr>
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <p><strong>CLIENT :</strong> {nom_cl if nom_cl else 'Passager'}</p>
                        <p><strong>TEL :</strong> {tel_cl if tel_cl else 'N/A'}</p>
                        <p><strong>ADRESSE :</strong> {adr_cl if adr_cl else 'N/A'}</p>
                    </div>
                    <div style="text-align: right;">
                        <p><strong>DATE :</strong> {datetime.now().strftime("%d/%m/%Y")}</p>
                        <p><strong>HEURE :</strong> {datetime.now().strftime("%H:%M")}</p>
                    </div>
                </div>
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <thead>
                        <tr style="background-color: #f2f2f2; border-bottom: 2px solid #333;">
                            <th style="padding: 10px; text-align: left;">Désignation</th>
                            <th style="padding: 10px; text-align: center;">Qté</th>
                            <th style="padding: 10px; text-align: right;">P.U (GNF)</th>
                            <th style="padding: 10px; text-align: right;">Total (GNF)</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for item in st.session_state.panier:
                facture_html += f"""
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 10px;">{item['Produit']}</td>
                            <td style="padding: 10px; text-align: center;">{item['Qte']}</td>
                            <td style="padding: 10px; text-align: right;">{item['Prix']:,.0f}</td>
                            <td style="padding: 10px; text-align: right;">{item['Total']:,.0f}</td>
                        </tr>
                """
            
            facture_html += f"""
                    </tbody>
                </table>
                <div style="text-align: right; margin-top: 20px;">
                    <h2 style="color: red;">TOTAL À PAYER : {total_panier:,.0f} GNF</h2>
                </div>
                <div style="text-align: center; margin-top: 30px; border-top: 1px solid #333;">
                    <p>Merci de votre confiance !</p>
                </div>
            </div>
            """
            st.markdown(facture_html, unsafe_allow_html=True)
            st.session_state.panier = [] # Vider le panier

# --- 2. STOCK ---
elif choix == "📦 Stock":
    st.header("📦 Gestion du Stock")
    with st.expander("➕ Ajouter / Modifier un article"):
        nom_p = st.text_input("Nom de l'article")
        pa_p = st.number_input("Prix Achat", min_value=0.0)
        pv_p = st.number_input("Prix Vente", min_value=0.0)
        q_p = st.number_input("Quantité initiale", min_value=1)
        if st.button("Enregistrer le produit"):
            if nom_p:
                new_row = {"Produit": nom_p, "Prix Achat": pa_p, "Prix Vente": pv_p, "Quantité": q_p}
                st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([new_row])], ignore_index=True)
                sauver_csv(st.session_state.stock, "stock_data.csv")
                st.success("Stock mis à jour !")
                st.rerun()

    st.subheader("📋 Articles en rayons")
    if not st.session_state.stock.empty:
        for i, row in st.session_state.stock.iterrows():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            alerte = "🔴" if row['Quantité'] <= 5 else "🟢"
            c1.write(f"{alerte} **{row['Produit']}**")
            c2.write(f"{row['Prix Vente']:,} GNF")
            c3.write(f"Stock: {row['Quantité']}")
            if c4.button("🗑️", key=f"del_{i}"):
                st.session_state.stock = st.session_state.stock.drop(i).reset_index(drop=True)
                sauver_csv(st.session_state.stock, "stock_data.csv")
                st.rerun()

# --- 3. HISTORIQUE ---
elif choix == "📈 Historique":
    st.header("📈 Rapport des Ventes")
    if not st.session_state.ventes.empty:
        st.metric("Chiffre d'Affaire Total", f"{st.session_state.ventes['Total'].sum():,.0f} GNF")
        st.dataframe(st.session_state.ventes, use_container_width=True)
        if st.button("❌ Effacer l'historique"):
            st.session_state.ventes = pd.DataFrame(columns=["Date", "Client", "Total", "Bénéfice"])
            sauver_csv(st.session_state.ventes, "ventes_data.csv")
            st.rerun()
    else:
        st.info("Aucune vente enregistrée.")

# --- 4. CONFIGURATION ---
elif choix == "⚙️ Paramètres":
    st.header("⚙️ Ma Boutique")
    st.session_state.boutique_info['nom'] = st.text_input("Nom de l'Etablissement", value=st.session_state.boutique_info['nom'])
    st.session_state.boutique_info['adresse'] = st.text_input("Localisation (Quartier/Ville)", value=st.session_state.boutique_info['adresse'])
    st.session_state.boutique_info['tel'] = st.text_input("Téléphone (Affiché sur facture)", value=st.session_state.boutique_info['tel'])
    if st.button("Enregistrer les réglages"):
        st.success("Informations boutique mises à jour !")
