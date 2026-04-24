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
    st.session_state.boutique_info = {"nom": "MA BOUTIQUE", "adresse": "Conakry, Guinée", "tel": "6XX XX XX XX"}

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title(f"🏪 {st.session_state.boutique_info['nom']}")
    choix = st.radio("MENU", ["🛒 Caisse (Vente)", "📦 Stock", "📈 Historique", "⚙️ Paramètres"])
    st.markdown("---")
    st.write(f"**Propriétaire :** Issa Diallo")
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
            prod_nom = st.selectbox("Choisir l'article", st.session_state.stock["Produit"])
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
        n_cl = c_i1.text_input("Nom du client", value="Mr Sow")
        t_cl = c_i2.text_input("Téléphone", value="6XX XX XX XX")
        a_cl = c_i3.text_input("Adresse", value="Bantounka 1")
        
        if st.button("✅ Valider & Générer la Facture"):
            total_f = sum(i['Total'] for i in st.session_state.panier)
            benef_f = sum(i['Bénéfice'] for i in st.session_state.panier)
            
            # Sauvegardes
            nouvelle_v = {"Date": datetime.now().strftime("%d/%m/%Y %H:%M"), "Client": n_cl, "Total": total_f, "Bénéfice": benef_f}
            st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([nouvelle_v])], ignore_index=True)
            sauver_csv(st.session_state.ventes, "ventes_data.csv")
            for item in st.session_state.panier:
                st.session_state.stock.loc[st.session_state.stock["Produit"] == item["Produit"], "Quantité"] -= item["Qte"]
            sauver_csv(st.session_state.stock, "stock_data.csv")

            # --- DESIGN FACTURE (SANS BUG) ---
            facture_html = f"""
            <div style="border: 1px solid #ccc; padding: 25px; background-color: #fff; color: #000; font-family: sans-serif; max-width: 700px; margin: auto;">
                <div style="display: flex; justify-content: space-between; border-bottom: 3px solid #1a73e8; padding-bottom: 10px;">
                    <div>
                        <h2 style="margin:0; color: #1a73e8;">{st.session_state.boutique_info['nom']}</h2>
                        <p style="margin:0;">{st.session_state.boutique_info['adresse']}</p>
                        <p style="margin:0;">Tél: {st.session_state.boutique_info['tel']}</p>
                    </div>
                    <div style="text-align: right;">
                        <h2 style="margin:0;">FACTURE</h2>
                        <p style="margin:0;">N° {len(st.session_state.ventes):04d}</p>
                        <p style="margin:0;">{datetime.now().strftime("%d/%m/%Y")}</p>
                    </div>
                </div>
                
                <div style="margin: 20px 0; padding: 10px; background-color: #f8f9fa;">
                    <p><strong>DOIT À :</strong> {n_cl}</p>
                    <p><strong>TEL :</strong> {t_cl} | <strong>ADRESSE :</strong> {a_cl}</p>
                </div>

                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <thead>
                        <tr style="background-color: #1a73e8; color: white;">
                            <th style="padding: 10px; border: 1px solid #ddd;">N°</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Produit</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Qté</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">P.U</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for idx, item in enumerate(st.session_state.panier):
                facture_html += f"""
                        <tr>
                            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{idx+1}</td>
                            <td style="padding: 8px; border: 1px solid #ddd;">{item['Produit']}</td>
                            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{item['Qte']}</td>
                            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{item['Prix']:,.0f}</td>
                            <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{item['Total']:,.0f}</td>
                        </tr>
                """
            
            facture_html += f"""
                    </tbody>
                </table>
                <h3 style="text-align: right; color: #d93025; margin-top: 20px;">TOTAL : {total_f:,.0f} GNF</h3>
                <p style="text-align: center; font-size: 10px; color: #888; margin-top: 30px;">Généré par VenteUp Pro</p>
            </div>
            <br>
            <button onclick="window.print()" style="width:100%; padding:10px; background:#1a73e8; color:white; border:none; border-radius:5px; cursor:pointer;">
                🖨️ Imprimer la Facture
            </button>
            """
            # CRITIQUE : Utilisation impérative de unsafe_allow_html=True
            st.markdown(facture_html, unsafe_allow_html=True)
            st.session_state.panier = []

# --- LE RESTE DU CODE (STOCK / HISTORIQUE) ---
elif choix == "📦 Stock":
    st.header("📦 Gestion du Stock")
    with st.expander("➕ Ajouter un article"):
        n = st.text_input("Nom")
        pa = st.number_input("Prix Achat", min_value=0.0)
        pv = st.number_input("Prix Vente", min_value=0.0)
        qt = st.number_input("Quantité", min_value=1)
        if st.button("Enregistrer"):
            if n:
                new_p = {"Produit": n, "Prix Achat": pa, "Prix Vente": pv, "Quantité": qt}
                st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([new_p])], ignore_index=True)
                sauver_csv(st.session_state.stock, "stock_data.csv")
                st.rerun()
    if not st.session_state.stock.empty:
        st.dataframe(st.session_state.stock, use_container_width=True)

elif choix == "📈 Historique":
    st.header("📈 Rapport
