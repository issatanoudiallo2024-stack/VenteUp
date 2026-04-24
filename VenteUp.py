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
if licence["statut"] == "essai" and jours_restants < 0:
    st.error("🚫 PÉRIODE D'ESSAI TERMINÉE. Contactez Issa Diallo au 610 51 89 73.")
    st.stop()

# --- 2. CONFIGURATION & CHARGEMENT ---
st.set_page_config(page_title="VenteUp Pro", layout="wide")

def charger_csv(nom, col):
    if os.path.exists(nom):
        try:
            df = pd.read_csv(nom)
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

# --- 4. CAISSE & FACTURATION ---
if choix == "🛒 Caisse":
    st.header("🛒 Interface de Vente")
    col1, col2 = st.columns(2)
    with col1:
        if not st.session_state.stock.empty:
            p_sel = st.selectbox("Sélectionner l'article", st.session_state.stock["Produit"])
            info = st.session_state.stock[st.session_state.stock["Produit"] == p_sel].iloc[0]
            st.write(f"En stock : **{info['Quantité']}**")
            q = st.number_input("Quantité", min_value=1, value=1)
            if st.button("🛒 Ajouter au panier"):
                if q <= info["Quantité"]:
                    st.session_state.panier.append({"Produit":p_sel,"Qte":q,"Prix":info["Prix Vente"],"Total":info["Prix Vente"]*q,"Ben":(info["Prix Vente"]-info["Prix Achat"])*q})
                    st.rerun()
                else: st.error("Stock insuffisant")
    with col2:
        if st.session_state.panier:
            st.subheader("Panier")
            st.table(pd.DataFrame(st.session_state.panier)[["Produit", "Qte", "Total"]])
            if st.button("🗑️ Vider le panier"): st.session_state.panier = []; st.rerun()

    if st.session_state.panier:
        st.write("---")
        st.subheader("Informations Client & Paiement")
        c1, c2 = st.columns(2)
        c_nom = c1.text_input("Nom du Client")
        c_tel = c2.text_input("Téléphone du Client")
        statut = st.radio("Mode de paiement", ["Payé", "Dette"], horizontal=True)
        
        if st.button("✅ Valider & Imprimer Facture"):
            if not c_nom: st.error("Veuillez saisir le nom du client")
            else:
                total_v = sum(i['Total'] for i in st.session_state.panier)
                date_v = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                # Enregistrement
                new_v = {"Date":date_v, "Client":c_nom, "Total":total_v, "Bénéfice":sum(i['Ben'] for i in st.session_state.panier), "Statut":statut}
                st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([new_v])], ignore_index=True)
                sauver_csv(st.session_state.ventes, "ventes_data.csv")
                
                for i in st.session_state.panier:
                    st.session_state.stock.loc[st.session_state.stock["Produit"]==i["Produit"], "Quantité"] -= i["Qte"]
                sauver_csv(st.session_state.stock, "stock_data.csv")

                # --- AFFICHAGE FACTURE ---
                st.success("Vente validée !")
                html_facture = f"""
                <div style="font-family:sans-serif; border:2px solid #000; padding:20px; background:white; color:black; border-radius:10px;">
                    <div style="text-align:center; border-bottom:1px solid #ddd; padding-bottom:10px;">
                        <h2 style="margin:0;">{st.session_state.boutique_info['nom'].upper()}</h2>
                        <p style="margin:5px 0;">{st.session_state.boutique_info['adresse']} | Tél: {st.session_state.boutique_info['tel']}</p>
                    </div>
                    <div style="margin-top:15px; display:flex; justify-content:space-between;">
                        <div>
                            <p><b>Date:</b> {date_v}</p>
                            <p><b>Client:</b> {c_nom}</p>
                            <p><b>Contact:</b> {c_tel}</p>
                        </div>
                        <div style="text-align:right;">
                            <p><b>Statut:</b> {statut}</p>
                        </div>
                    </div>
                    <table style="width:100%; border-collapse:collapse; margin-top:15px;">
                        <tr style="background:#f2f2f2; border-bottom:1px solid #000;">
                            <th style="text-align:left; padding:8px;">Article</th>
                            <th style="padding:8px;">Qté</th>
                            <th style="text-align:right; padding:8px;">Total</th>
                        </tr>
                """
                for item in st.session_state.panier:
                    html_facture += f"<tr><td style='padding:8px;'>{item['Produit']}</td><td style='padding:8px; text-align:center;'>{item['Qte']}</td><td style='padding:8px; text-align:right;'>{item['Total']:,} GNF</td></tr>"
                
                html_facture += f"""
                    </table>
                    <div style="text-align:right; margin-top:20px; border-top:2px solid #000; padding-top:10px;">
                        <h3 style="margin:0;">TOTAL NET : {total_v:,.0f} GNF</h3>
                    </div>
                </div>
                <br>
                <button onclick="window.print()" style="width:100%; padding:15px; background:black; color:white; font-weight:bold; border-radius:5px; cursor:pointer;">
                    🖨️ IMPRIMER LA FACTURE (PDF)
                </button>
                """
                st.markdown(html_facture, unsafe_allow_html=True)
                st.session_state.panier = []

# --- 5. MODULE STOCK ---
elif choix == "📦 Stock & Alerte":
    st.header("📦 Gestion du Stock")
    t1, t2, t3 = st.tabs(["🔄 Réapprovisionnement", "➕ Nouveau Produit", "🗑️ Liste & Suppression"])
    
    with t1:
        st.subheader("Réapprovisionnement :")
        if not st.session_state.stock.empty:
            p_reap = st.selectbox("Article à recharger", st.session_state.stock["Produit"])
            q_aj = st.number_input("Quantité à ajouter", min_value=1, value=1)
            if st.button("🔄 Valider l'ajout"):
                st.session_state.stock.loc[st.session_state.stock["Produit"] == p_reap, "Quantité"] += q_aj
                sauver_csv(st.session_state.stock, "stock_data.csv")
                st.success(f"Stock mis à jour pour {p_reap} !"); st.rerun()

    with t2:
        st.subheader("Ajouter un nouvel article :")
        with st.form("new_art"):
            n_n = st.text_input("Désignation")
            n_pa = st.number_input("Prix Achat", min_value=0)
            n_pv = st.number_input("Prix Vente", min_value=0)
            n_q = st.number_input("Stock Initial", min_value=1)
            if st.form_submit_button("➕ Créer l'article"):
                if n_n:
                    new_l = {"Produit": n_n, "Prix Achat": n_pa, "Prix Vente": n_pv, "Quantité": n_q}
                    st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([new_l])], ignore_index=True)
                    sauver_csv(st.session_state.stock, "stock_data.csv"); st.rerun()

    with t3:
        st.subheader("Inventaire")
        st.dataframe(st.session_state.stock, use_container_width=True)
        for i, row in st.session_state.stock.iterrows():
            if st.button(f"Supprimer {row['Produit']}", key=f"s_{i}"):
                st.session_state.stock = st.session_state.stock.drop(i).reset_index(drop=True)
                sauver_csv(st.session_state.stock, "stock_data.csv"); st.rerun()

# --- 6. HISTORIQUE & 7. PARAMÈTRES (Inchangés) ---
elif choix == "📈 Historique":
    st.header("📈 Historique des Ventes")
    if not st.session_state.ventes.empty:
        dettes = st.session_state.ventes[st.session_state.ventes["Statut"] == "Dette"]
        if not dettes.empty: st.error(f"Total Dettes : {dettes['Total'].sum():,.0f} GNF")
        st.dataframe(st.session_state.ventes, use_container_width=True)
        if st.button("🗑️ Effacer l'historique"):
            st.session_state.ventes = pd.DataFrame(columns=["Date", "Client", "Total", "Bénéfice", "Statut"])
            sauver_csv(st.session_state.ventes, "ventes_data.csv"); st.rerun()

elif choix == "⚙️ Paramètres":
    st.header("⚙️ Paramètres Boutique")
    st.session_state.boutique_info['nom'] = st.text_input("Nom Boutique", st.session_state.boutique_info['nom'])
    st.session_state.boutique_info['adresse'] = st.text_input("Adresse", st.session_state.boutique_info['adresse'])
    st.session_state.boutique_info['tel'] = st.text_input("Téléphone", st.session_state.boutique_info['tel'])
    if st.button("Enregistrer"): st.success("Ok !")
