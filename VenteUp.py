import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. Configuration de la page
st.set_page_config(page_title="VenteUp Ultimate Pro", layout="wide")

# --- SYSTÈME DE PERSISTANCE (SAUVEGARDE) ---
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
            st.warning("Stock vide !")
        else:
            prod_nom = st.selectbox("Article", st.session_state.stock["Produit"])
            info_p = st.session_state.stock[st.session_state.stock["Produit"] == prod_nom].iloc[0]
            c1, c2 = st.columns(2)
            qte_v = c1.number_input("Quantité", min_value=1, value=1)
            prix_v = c2.number_input("Prix Unitaire (GNF)", value=float(info_p["Prix Vente"]))
            if st.button("🛒 Ajouter au Panier"):
                if qte_v <= info_p["Quantité"]:
                    item = {"Produit": prod_nom, "Qte": qte_v, "Prix": prix_v, "Total": prix_v * qte_v, "Bénéfice": (prix_v - info_p["Prix Achat"]) * qte_v}
                    st.session_state.panier.append(item)
                    st.success(f"Ajouté : {prod_nom}")
                else:
                    st.error("Stock insuffisant !")

    with col_b:
        st.subheader("📋 Panier")
        if st.session_state.panier:
            df_p = pd.DataFrame(st.session_state.panier)
            st.table(df_p[["Produit", "Qte", "Total"]])
            total_actuel = df_p["Total"].sum()
            st.write(f"### TOTAL : **{total_actuel:,.0f} GNF**")
            if st.button("🗑️ Vider le panier"):
                st.session_state.panier = []
                st.rerun()

    if st.session_state.panier:
        st.markdown("---")
        st.subheader("👤 Infos Client")
        c_i1, c_i2, c_i3 = st.columns(3)
        n_cl = c_i1.text_input("Nom du client")
        t_cl = c_i2.text_input("Téléphone")
        a_cl = c_i3.text_input("Adresse")
        
        if st.button("✅ Valider & Générer la Facture"):
            total_f = sum(i['Total'] for i in st.session_state.panier)
            benef_f = sum(i['Bénéfice'] for i in st.session_state.panier)
            
            # Sauvegardes
            nouvelle_v = {"Date": datetime.now().strftime("%d/%m/%Y %H:%M"), "Client": n_cl if n_cl else "Passager", "Total": total_f, "Bénéfice": benef_f}
            st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([nouvelle_v])], ignore_index=True)
            sauver_csv(st.session_state.ventes, "ventes_data.csv")
            for item in st.session_state.panier:
                st.session_state.stock.loc[st.session_state.stock["Produit"] == item["Produit"], "Quantité"] -= item["Qte"]
            sauver_csv(st.session_state.stock, "stock_data.csv")

            # --- DESIGN FACTURE PREMIUM ---
            facture_html = f"""
            <div id="facture-imprimable" style="border: 1px solid #ccc; padding: 30px; background-color: #fff; color: #000; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: auto; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #1a73e8; padding-bottom: 15px;">
                    <div>
                        <h1 style="margin:0; color: #1a73e8; font-size: 28px;">{st.session_state.boutique_info['nom'].upper()}</h1>
                        <p style="margin:2px 0; font-size: 14px;">{st.session_state.boutique_info['adresse']}</p>
                        <p style="margin:2px 0; font-size: 14px;">Tél: {st.session_state.boutique_info['tel']}</p>
                    </div>
                    <div style="text-align: right;">
                        <h2 style="margin:0; color: #555;">FACTURE</h2>
                        <p style="margin:2px 0;">N° {len(st.session_state.ventes):04d}</p>
                        <p style="margin:2px 0;">{datetime.now().strftime("%d/%m/%Y")}</p>
                    </div>
                </div>
                
                <div style="margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
                    <table style="width: 100%; font-size: 14px;">
                        <tr>
                            <td><strong>DOIT À :</strong> {n_cl if n_cl else 'Client Passager'}</td>
                            <td style="text-align: right;"><strong>TEL :</strong> {t_cl if t_cl else 'N/A'}</td>
                        </tr>
                        <tr>
                            <td colspan="2"><strong>ADRESSE :</strong> {a_cl if a_cl else 'N/A'}</td>
                        </tr>
                    </table>
                </div>

                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <thead>
                        <tr style="background-color: #1a73e8; color: white;">
                            <th style="padding: 12px; border: 1px solid #ddd; text-align: center;">N°</th>
                            <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">Description</th>
                            <th style="padding: 12px; border: 1px solid #ddd; text-align: center;">Qté</th>
                            <th style="padding: 12px; border: 1px solid #ddd; text-align: right;">P.U</th>
                            <th style="padding: 12px; border: 1px solid #ddd; text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for idx, item in enumerate(st.session_state.panier):
                facture_html += f"""
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{idx+1}</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{item['Produit']}</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{item['Qte']}</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{item['Prix']:,.0f}</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{item['Total']:,.0f}</td>
                        </tr>
                """
            
            facture_html += f"""
                    </tbody>
                </table>
                <div style="text-align: right; margin-top: 30px;">
                    <div style="display: inline-block; border-top: 2px solid #1a73e8; padding-top: 10px;">
                        <h2 style="margin:0; color: #d93025;">NET À PAYER : {total_f:,.0f} GNF</h2>
                    </div>
                </div>
                <div style="text-align: center; margin-top: 50px; font-size: 12px; color: #888; border-top: 1px solid #eee; padding-top: 10px;">
                    <p>Merci pour votre achat ! Logiciel VenteUp Pro par Issa Diallo.</p>
                </div>
            </div>
            <br>
            <button onclick="window.print()" style="padding: 10px 20px; background-color: #1a73e8; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">
                🖨️ Imprimer ou Enregistrer en PDF
            </button>
            """
            st.markdown(facture_html, unsafe_allow_html=True)
            st.session_state.panier = []

# --- SECTION STOCK, HISTORIQUE ET PARAMÈTRES ---
elif choix == "📦 Stock":
    st.header("📦 Gestion du Stock")
    with st.expander("➕ Ajouter un article"):
        nom = st.text_input("Nom")
        pa = st.number_input("Prix Achat", min_value=0.0)
        pv = st.number_input("Prix Vente", min_value=0.0)
        qt = st.number_input("Quantité", min_value=1)
        if st.button("Enregistrer"):
            if nom:
                new_p = {"Produit": nom, "Prix Achat": pa, "Prix Vente": pv, "Quantité": qt}
                st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([new_p])], ignore_index=True)
                sauver_csv(st.session_state.stock, "stock_data.csv")
                st.rerun()
    if not st.session_state.stock.empty:
        for i, row in st.session_state.stock.iterrows():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            c1.write(f"**{row['Produit']}**")
            c2.write(f"{row['Prix Vente']:,} GNF")
            c3.write(f"Stock: {row['Quantité']}")
            if c4.button("🗑️", key=f"ds_{i}"):
                st.session_state.stock = st.session_state.stock.drop(i).reset_index(drop=True)
                sauver_csv(st.session_state.stock, "stock_data.csv")
                st.rerun()

elif choix == "📈 Historique":
    st.header("📈 Rapport des Ventes")
    if not st.session_state.ventes.empty:
        st.metric("Chiffre d'Affaire Global", f"{st.session_state.ventes['Total'].sum():,.0f} GNF")
        st.dataframe(st.session_state.ventes, use_container_width=True)
    else:
        st.info("Aucune vente enregistrée.")

elif choix == "⚙️ Paramètres":
    st.header("⚙️ Configuration")
    st.session_state.boutique_info['nom'] = st.text_input("Nom boutique", value=st.session_state.boutique_info['nom'])
    st.session_state.boutique_info['adresse'] = st.text_input("Adresse", value=st.session_state.boutique_info['adresse'])
    st.session_state.boutique_info['tel'] = st.text_input("Contact", value=st.session_state.boutique_info['tel'])
    if st.button("Enregistrer"):
        st.success("Mise à jour réussie !")
                        
