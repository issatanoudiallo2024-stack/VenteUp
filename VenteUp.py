import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64

# --- 1. SYSTÈME DE LICENCE (7 JOURS OFFERTS) ---
CODE_DEBLOCAGE_SECRET = "ISSAVUP2026" 
FICHIER_LICENCE = "licence_config.csv"

def charger_licence():
    if os.path.exists(FICHIER_LICENCE):
        try: return pd.read_csv(FICHIER_LICENCE).iloc[0].to_dict()
        except: pass
    data = {"date_debut": datetime.now().strftime("%Y-%m-%d"), "statut": "essai"}
    pd.DataFrame([data]).to_csv(FICHIER_LICENCE, index=False)
    return data

licence = charger_licence()
date_debut = datetime.strptime(licence["date_debut"], "%Y-%m-%d")
jours_restants = 7 - (datetime.now() - date_debut).days
if licence["statut"] == "essai" and jours_restants < 0:
    st.error(f"🚫 ESSAI TERMINÉ. Contactez Issa Diallo au 610 51 89 73.")
    st.stop()

# --- 2. INITIALISATION ET MÉMOIRE ANTI-EFFACEMENT ---
if 'c_nom' not in st.session_state: st.session_state.c_nom = ""
if 'c_tel' not in st.session_state: st.session_state.c_tel = ""
if 'c_adr' not in st.session_state: st.session_state.c_adr = ""
if 'panier' not in st.session_state: st.session_state.panier = []
if 'cachet_base64' not in st.session_state: st.session_state.cachet_base64 = None

st.set_page_config(page_title="VenteUp Pro", layout="wide")

def charger_csv(nom, col):
    if os.path.exists(nom):
        try:
            df = pd.read_csv(nom)
            for c in col:
                if c not in df.columns: df[c] = "Non payé" if c == "Statut" else 0
            return df
        except: return pd.DataFrame(columns=col)
    return pd.DataFrame(columns=col)

def sauver_csv(df, nom):
    df.to_csv(nom, index=False)

if 'stock' not in st.session_state:
    st.session_state.stock = charger_csv("stock_data.csv", ["Produit", "Prix Achat", "Prix Vente", "Quantité"])
if 'ventes' not in st.session_state:
    st.session_state.ventes = charger_csv("ventes_data.csv", ["Date", "Client", "Total", "Bénéfice", "Statut"])
if 'boutique_info' not in st.session_state:
    # Informations vides pour laisser l'utilisateur les remplir en test
    st.session_state.boutique_info = {"nom": "NOM DE VOTRE BOUTIQUE", "adresse": "ADRESSE", "tel": "TELEPHONE"}

# --- 3. MENU ---
with st.sidebar:
    st.title("🚀 VenteUp Pro")
    choix = st.radio("MENU", ["🛒 Caisse", "📦 Stock", "📈 Historique", "⚙️ Paramètres"])
    st.write("---")
    st.write("**Concepteur :** Issa Diallo")
    st.write("📞 610 51 89 73")
    st.info(f"⏳ Essai : {max(0, jours_restants)}j restants")

# --- 4. CAISSE & FACTURE ---
if choix == "🛒 Caisse":
    st.header("🛒 Terminal de Vente")
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        if not st.session_state.stock.empty:
            p_sel = st.selectbox("Article", st.session_state.stock["Produit"])
            info = st.session_state.stock[st.session_state.stock["Produit"] == p_sel].iloc[0]
            q = st.number_input("Quantité", min_value=1, value=1)
            if st.button("🛒 Ajouter au Panier"):
                if q <= info["Quantité"]:
                    st.session_state.panier.append({"Produit":p_sel,"Qte":q,"Prix":info["Prix Vente"],"Total":info["Prix Vente"]*q,"Ben":(info["Prix Vente"]-info["Prix Achat"])*q})
                    st.rerun()
                else: st.error("Stock insuffisant !")

    with col2:
        if st.session_state.panier:
            st.subheader("Articles sélectionnés")
            st.table(pd.DataFrame(st.session_state.panier)[["Produit", "Qte", "Total"]])
            if st.button("🗑️ Vider"): st.session_state.panier = []; st.rerun()

    if st.session_state.panier:
        st.write("---")
        st.subheader("📝 Informations Client")
        c1, c2, c3 = st.columns(3)
        st.session_state.c_nom = c1.text_input("Nom Client", value=st.session_state.c_nom)
        st.session_state.c_tel = c2.text_input("Téléphone", value=st.session_state.c_tel)
        st.session_state.c_adr = c3.text_input("Adresse", value=st.session_state.c_adr)
        statut = st.radio("Paiement", ["Payé ✅", "Dette 🔴"], horizontal=True)
        
        if st.button("📥 ENREGISTRER LA FACTURE (PDF)", use_container_width=True):
            if not st.session_state.c_nom: st.error("Veuillez entrer le nom du client.")
            else:
                total_v = sum(i['Total'] for i in st.session_state.panier)
                date_v = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                # --- GÉNÉRATION HTML ---
                col_statut = "#28a745" if "Payé" in statut else "#dc3545"
                html_facture = f"""
                <div id="facture-print" style="font-family:Arial; padding:30px; border:1px solid #ddd; background:#fff; color:#000;">
                    <div style="display:flex; justify-content:space-between; border-bottom:2px solid #000; padding-bottom:10px;">
                        <div style="text-align:left;">
                            <h2 style="margin:0;">{st.session_state.boutique_info['nom'].upper()}</h2>
                            <p style="margin:2px 0;">📍 {st.session_state.boutique_info['adresse']}</p>
                            <p style="margin:2px 0;">📞 {st.session_state.boutique_info['tel']}</p>
                        </div>
                        <div style="text-align:right;">
                            <h3 style="margin:0; color:#666;">CLIENT :</h3>
                            <p style="margin:2px 0;"><b>{st.session_state.c_nom}</b></p>
                            <p style="margin:2px 0;">🗺️ {st.session_state.c_adr}</p>
                            <p style="margin:2px 0;">📞 {st.session_state.c_tel}</p>
                        </div>
                    </div>
                    <p style="text-align:right; margin-top:10px;">Date : {date_v}</p>
                    <table style="width:100%; border-collapse:collapse; margin-top:15px;">
                        <tr style="background:#f2f2f2; border:1px solid #000;">
                            <th style="padding:10px; border:1px solid #000;">Article</th>
                            <th style="padding:10px; border:1px solid #000;">Qté</th>
                            <th style="padding:10px; border:1px solid #000;">Total</th>
                        </tr>
                """
                for item in st.session_state.panier:
                    html_facture += f"<tr><td style='padding:10px; border:1px solid #000;'>{item['Produit']}</td><td style='padding:10px; text-align:center; border:1px solid #000;'>{item['Qte']}</td><td style='padding:10px; text-align:right; border:1px solid #000;'>{item['Total']:,} GNF</td></tr>"
                
                html_facture += f"""
                    </table>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:20px;">
                        <div>
                            {f'<img src="data:image/png;base64,{st.session_state.cachet_base64}" style="width:150px;">' if st.session_state.cachet_base64 else '<p style="margin-top:40px; font-style:italic;">(Signature & Cachet)</p>'}
                        </div>
                        <div style="text-align:right;">
                            <h2 style="margin:0;">TOTAL : {total_v:,.0f} GNF</h2>
                        </div>
                    </div>
                    <div style="margin-top:25px; text-align:center; padding:10px; background:{col_statut}; color:white; font-weight:bold; border-radius:5px;">
                        STATUT DU PAIEMENT : {statut.upper()}
                    </div>
                </div>
                <br>
                <button onclick="window.print()" style="width:100%; padding:20px; background:#007bff; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">
                    📥 ENREGISTRER LA FACTURE SUR LE TÉLÉPHONE (PDF)
                </button>
                """
                st.markdown(html_facture, unsafe_allow_html=True)
                
                # --- SAUVEGARDE ET VIDAGE ---
                new_v = {"Date":date_v, "Client":st.session_state.c_nom, "Total":total_v, "Bénéfice":sum(i['Ben'] for i in st.session_state.panier), "Statut":statut}
                st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([new_v])], ignore_index=True)
                sauver_csv(st.session_state.ventes, "ventes_data.csv")
                for i in st.session_state.panier:
                    st.session_state.stock.loc[st.session_state.stock["Produit"]==i["Produit"], "Quantité"] -= i["Qte"]
                sauver_csv(st.session_state.stock, "stock_data.csv")
                st.session_state.panier = []
                st.session_state.c_nom = ""; st.session_state.c_tel = ""; st.session_state.c_adr = ""

# --- 5. MODULES SECONDAIRES ---
elif choix == "📦 Stock":
    st.header("📦 Gestion du Stock")
    with st.form("stock"):
        n = st.text_input("Nom de l'article")
        pa = st.number_input("Prix Achat", 0)
        pv = st.number_input("Prix Vente", 0)
        q = st.number_input("Quantité", 1)
        if st.form_submit_button("Ajouter au stock"):
            st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([{"Produit":n,"Prix Achat":pa,"Prix Vente":pv,"Quantité":q}])], ignore_index=True)
            sauver_csv(st.session_state.stock, "stock_data.csv"); st.rerun()
    st.dataframe(st.session_state.stock, use_container_width=True)

elif choix == "📈 Historique":
    st.header("📈 Historique des Ventes")
    st.dataframe(st.session_state.ventes, use_container_width=True)

elif choix == "⚙️ Paramètres":
    st.header("⚙️ Configuration de la Boutique")
    st.session_state.boutique_info['nom'] = st.text_input("Nom de l'Enseigne", st.session_state.boutique_info['nom'])
    st.session_state.boutique_info['adresse'] = st.text_input("Adresse", st.session_state.boutique_info['adresse'])
    st.session_state.boutique_info['tel'] = st.text_input("Téléphone Boutique", st.session_state.boutique_info['tel'])
    
    img = st.file_uploader("Importer une Signature ou un Cachet (PNG/JPG)", type=['png', 'jpg'])
    if img:
        st.session_state.cachet_base64 = base64.b64encode(img.getvalue()).decode()
        st.success("Image chargée !")
    
    if st.button("Sauvegarder les réglages"): st.success("Ok !")
