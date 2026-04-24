import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image
import io

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

licence = charger_licence()
date_debut = datetime.strptime(licence["date_debut"], "%Y-%m-%d")
jours_restants = 7 - (datetime.now() - date_debut).days
if licence["statut"] == "essai" and jours_restants < 0:
    st.error(f"🚫 ESSAI TERMINÉ. Contactez Issa Diallo au 610 51 89 73.")
    st.stop()

# --- 2. INITIALISATION SESSION (ANTI-F5) ---
if 'c_nom' not in st.session_state: st.session_state.c_nom = ""
if 'c_tel' not in st.session_state: st.session_state.c_tel = ""
if 'c_adr' not in st.session_state: st.session_state.c_adr = ""
if 'panier' not in st.session_state: st.session_state.panier = []
if 'cachet_base64' not in st.session_state: st.session_state.cachet_base64 = None

# --- 3. CONFIGURATION & CHARGEMENT ---
st.set_page_config(page_title="VenteUp Pro", layout="wide", page_icon="🛍️")

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

# Encodage image pour HTML
import base64
def get_image_base64(image_file):
    return base64.b64encode(image_file.getvalue()).decode()

if 'stock' not in st.session_state:
    st.session_state.stock = charger_csv("stock_data.csv", ["Produit", "Prix Achat", "Prix Vente", "Quantité"])
if 'ventes' not in st.session_state:
    st.session_state.ventes = charger_csv("ventes_data.csv", ["Date", "Client", "Total", "Bénéfice", "Statut"])
if 'boutique_info' not in st.session_state:
    st.session_state.boutique_info = {"nom": "Ma Boutique", "adresse": "Conakry", "tel": "610"}

# --- 4. NAVIGATION ---
with st.sidebar:
    st.title("🚀 VenteUp Pro")
    choix = st.radio("MENU", ["🛒 Caisse", "📦 Stock", "📈 Historique", "⚙️ Paramètres"])
    st.write(f"⏳ Essai : {max(0, jours_restants)}j" if licence["statut"]=="essai" else "✅ Version Activée")
    st.write("---")
    st.write("Dév: Issa Diallo | 610 51 89 73")

# --- 5. MODULE CAISSE & FACTURE DESIGN ---
if choix == "🛒 Caisse":
    st.header("🛒 Terminal de Vente")
    
    # Zone d'alerte stock bas
    alerte = st.session_state.stock[st.session_state.stock["Quantité"] <= 5]
    if not alerte.empty:
        st.warning(f"⚠️ {len(alerte)} articles sont presque épuisés !")

    col1, col2 = st.columns([1, 1.3])
    
    with col1:
        if not st.session_state.stock.empty:
            p_sel = st.selectbox("Article", st.session_state.stock["Produit"])
            info = st.session_state.stock[st.session_state.stock["Produit"] == p_sel].iloc[0]
            st.caption(f"Disponible: {info['Quantité']} PU: {info['Prix Vente']:,}")
            q = st.number_input("Quantité", min_value=1, value=1)
            if st.button("🛒 Ajouter", use_container_width=True):
                if q <= info["Quantité"]:
                    st.session_state.panier.append({"Produit":p_sel,"Qte":q,"Prix":info["Prix Vente"],"Total":info["Prix Vente"]*q,"Ben":(info["Prix Vente"]-info["Prix Achat"])*q})
                    st.rerun()
                else: st.error("Stock insuffisant !")

    with col2:
        if st.session_state.panier:
            st.subheader("🛒 Panier")
            df_p = pd.DataFrame(st.session_state.panier)
            st.dataframe(df_p[["Produit", "Qte", "Total"]], use_container_width=True)
            st.write(f"**Total temporaire : {df_p['Total'].sum():,} GNF**")
            if st.button("🗑️ Vider"): st.session_state.panier = []; st.rerun()

    if st.session_state.panier:
        st.write("---")
        st.subheader("📝 Renseignements Client")
        c1, c2, c3 = st.columns(3)
        st.session_state.c_nom = c1.text_input("Nom Client", value=st.session_state.c_nom, placeholder="Ex: Adama Doumbouya")
        st.session_state.c_tel = c2.text_input("Téléphone", value=st.session_state.c_tel, placeholder="Ex: 620...")
        st.session_state.c_adr = c3.text_input("Adresse", value=st.session_state.c_adr, placeholder="Ex: Kaloum")
        
        col_pay, col_val = st.columns([2, 1])
        statut = col_pay.radio("État du paiement", ["Payé ✅", "Dette 🔴"], horizontal=True)
        
        if col_val.button("✅ VALIDER & IMPRIMER", use_container_width=True):
            if not st.session_state.c_nom: st.error("Le nom du client est obligatoire.")
            else:
                total_v = sum(i['Total'] for i in st.session_state.panier)
                date_v = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                # --- ENREGISTREMENT DONNÉES ---
                new_v = {"Date":date_v, "Client":st.session_state.c_nom, "Total":total_v, "Bénéfice":sum(i['Ben'] for i in st.session_state.panier), "Statut":statut}
                st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([new_v])], ignore_index=True)
                sauver_csv(st.session_state.ventes, "ventes_data.csv")
                
                for i in st.session_state.panier:
                    st.session_state.stock.loc[st.session_state.stock["Produit"]==i["Produit"], "Quantité"] -= i["Qte"]
                sauver_csv(st.session_state.stock, "stock_data.csv")

                # --- DESIGN FACTURE FINALE ---
                st.success("Vente enregistrée !")
                
                # Couleur statut
                col_statut = "#28a745" if "Payé" in statut else "#dc3545" # Vert si payé, Rouge si Dette

                html_facture = f"""
                <div id="facture" style="font-family:'Helvetica Neue', Helvetica, Arial, sans-serif; padding:40px; border:1px solid #eee; background:#fff; color:#333; max-width:850px; margin:auto; border-radius:10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                    
                    # --- EN-TÊTE ---
                    <div style="display:flex; justify-content:space-between; border-bottom:2px solid #333; padding-bottom:15px;">
                        # GAUCHE : INFOS BOUTIQUE (UTILISATEUR)
                        <div style="text-align:left;">
                            <h2 style="margin:0; color:#000;">{st.session_state.boutique_info['nom'].upper()}</h2>
                            <p style="margin:5px 0;">📍 {st.session_state.boutique_info['adresse']}</p>
                            <p style="margin:5px 0;">📞 {st.session_state.boutique_info['tel']}</p>
                        </div>
                        # DROITE : INFOS CLIENT
                        <div style="text-align:right;">
                            <h3 style="margin:0; color:#555;">FACTURE POUR :</h3>
                            <p style="margin:5px 0;"><b>{st.session_state.c_nom}</b></p>
                            <p style="margin:5px 0;">🗺️ {st.session_state.c_adr}</p>
                            <p style="margin:5px 0;">📞 {st.session_state.c_tel}</p>
                        </div>
                    </div>

                    # --- DÉTAILS DATE/N° ---
                    <div style="margin-top:20px; text-align:right;">
                        <p style="margin:0;">Date: <b>{date_v}</b></p>
                    </div>

                    # --- TABLEAU ARTICLES ---
                    <table style="width:100%; border-collapse:collapse; margin-top:25px; border:1px solid #ddd;">
                        <thead>
                            <tr style="background:#f8f9fa; border-bottom:2px solid #ddd;">
                                <th style="padding:12px; text-align:left; border:1px solid #ddd;">Désignation</th>
                                <th style="padding:12px; border:1px solid #ddd;">Prix Unitaire</th>
                                <th style="padding:12px; border:1px solid #ddd;">Qté</th>
                                <th style="padding:12px; text-align:right; border:1px solid #ddd;">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                for item in st.session_state.panier:
                    html_facture += f"""
                        <tr style="border-bottom:1px solid #eee;">
                            <td style="padding:12px; border:1px solid #ddd;">{item['Produit']}</td>
                            <td style="padding:12px; text-align:center; border:1px solid #ddd;">{item['Prix']:,}</td>
                            <td style="padding:12px; text-align:center; border:1px solid #ddd;">{item['Qte']}</td>
                            <td style="padding:12px; text-align:right; font-weight:bold; border:1px solid #ddd;">{item['Total']:,} GNF</td>
                        </tr>
                    """
                
                # --- TOTAL & CACHET & STATUT ---
                html_facture += f"""
                        </tbody>
                    </table>
                    
                    <div style="margin-top:25px; display:flex; justify-content:space-between; align-items:center;">
                        # GAUCHE : CACHET (si existe)
                        <div style="text-align:left; flex:1;">
                            {f'<img src="data:image/png;base64,{st.session_state.cachet_base64}" style="max-width:150px; max-height:150px; opacity:0.8; margin-top:10px;">' if st.session_state.cachet_base64 else '<p style="font-style:italic; color:#999; margin-top:50px;">(Signature & Cachet)</p>'}
                        </div>
                        
                        # DROITE : TOTAL & STATUT
                        <div style="text-align:right; flex:1; padding:15px; background:#f9f9f9; border-radius:10px; border:1px solid #ddd;">
                            <h1 style="margin:0 0 10px 0; color:#000;">TOTAL NET :</h1>
                            <h1 style="margin:0; color:#000; font-size:36px;">{total_v:,.0f} GNF</h1>
                        </div>
                    </div>

                    # --- STATUT TOUT EN BAS ---
                    <div style="margin-top:30px; text-align:center; padding:15px; background:{col_statut}; color:white; border-radius:5px; font-weight:bold; font-size:20px; text-transform:uppercase;">
                        ÉTAT DU PAIEMENT : {statut}
                    </div>

                    <div style="margin-top:20px; text-align:center; font-size:11px; color:#aaa; border-top:1px solid #eee; padding-top:10px;">
                        Merci de votre confiance. Facture générée par VenteUp Pro.
                    </div>
                </div>

                # --- BOUTON IMPRESSION ---
                <br>
                <button onclick="window.print()" style="width:100%; padding:18px; background:#000; color:#fff; border:none; border-radius:10px; cursor:pointer; font-weight:bold; font-size:16px; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                    🖨️ IMPRIMER / SAUVEGARDER EN PDF
                </button>
                """
                st.markdown(html_facture, unsafe_allow_html=True)
                
                # Nettoyage
                st.session_state.panier = []
                st.session_state.c_nom = ""; st.session_state.c_tel = ""; st.session_state.c_adr = ""

# --- 6. AUTRES MODULES (STOCK, HISTORIQUE) ---
elif choix == "📦 Stock":
    st.header("📦 Inventaire")
    tab1, tab2 = st.tabs(["🔄 Ajout/Nouveau", "🗑️ Suppression"])
    with tab1:
        with st.form("add_stock"):
            st.subheader("Ajouter ou Réapprovisionner")
            n = st.text_input("Désignation Produit")
            pa = st.number_input("Prix Achat Unitaire", min_value=0, value=0)
            pv = st.number_input("Prix Vente Unitaire", min_value=0, value=0)
            q = st.number_input("Quantité", min_value=1, value=1)
            if st.form_submit_button("✅ Valider le stock"):
                if n:
                    if n in st.session_state.stock["Produit"].values:
                        st.session_state.stock.loc[st.session_state.stock["Produit"]==n, "Quantité"] += q
                    else:
                        st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([{"Produit":n,"Prix Achat":pa,"Prix Vente":pv,"Quantité":q}])], ignore_index=True)
                    sauver_csv(st.session_state.stock, "stock_data.csv"); st.success("Stock mis à jour !"); st.rerun()
    with tab2:
        col_del, col_tab = st.columns([1, 2])
        col_tab.dataframe(st.session_state.stock, use_container_width=True)
        if not st.session_state.stock.empty:
            p_del = col_del.selectbox("Article à supprimer", st.session_state.stock["Produit"])
            if col_del.button("⚠️ Supprimer définitivement"):
                st.session_state.stock = st.session_state.stock[st.session_state.stock["Produit"] != p_del].reset_index(drop=True)
                sauver_csv(st.session_state.stock, "stock_data.csv"); st.success("Article supprimé !"); st.rerun()

elif choix == "📈 Historique":
    st.header("📈 Historique des Ventes")
    if not st.session_state.ventes.empty:
        df_v = st.session_state.ventes
        
        c1, c2 = st.columns(2)
        total_ca = df_v["Total"].sum()
        total_ben = df_v["Bénéfice"].sum()
        c1.metric("Chiffre d'Affaires", f"{total_ca:,} GNF")
        c2.metric("Bénéfice Total", f"{total_ben:,} GNF")
        
        st.write("---")
        # Filtre dettes
        dettes = df_v[df_v["Statut"].str.contains("Dette")]
        if not dettes.empty:
            st.error(f"🔴 Total Dettes à récupérer : {dettes['Total'].sum():,} GNF")
            with st.expander("Voir la liste des dettes"):
                st.dataframe(dettes[["Date", "Client", "Total"]], use_container_width=True)
        
        st.write("### Toutes les transactions")
        st.dataframe(df_v, use_container_width=True)
        
        if st.button("🗑️ Vider l'historique"):
            st.session_state.ventes = pd.DataFrame(columns=["Date", "Client", "Total", "Bénéfice", "Statut"])
            sauver_csv(st.session_state.ventes, "ventes_data.csv"); st.rerun()

# --- 7. PARAMÈTRES AVEC UPLOAD CACHET ---
elif choix == "⚙️ Paramètres":
    st.header("⚙️ Configuration")
    
    col_info, col_img = st.columns([2, 1])
    
    with col_info:
        st.subheader("Informations Boutique")
        st.session_state.boutique_info['nom'] = st.text_input("Nom de l'Enseigne", value=st.session_state.boutique_info['nom'])
        st.session_state.boutique_info['adresse'] = st.text_input("Adresse Physique", value=st.session_state.boutique_info['adresse'])
        st.session_state.boutique_info['tel'] = st.text_input("Téléphone", value=st.session_state.boutique_info['tel'])
        if st.button("💾 Enregistrer les informations"): st.success("Paramètres sauvés !")

    with col_img:
        st.subheader("Cachet / Logo")
        st.write("Importez votre cachet numérique ou logo (PNG/JPG) pour personnaliser la facture.")
        # Upload image
        uploaded_file = st.file_uploader("Choisir une image...", type=['png', 'jpg', 'jpeg'])
        
        if uploaded_file is not None:
            # Affichage aperçu
            image = Image.open(uploaded_file)
            st.image(image, caption='Aperçu du cachet', width=150)
            # Conversion Base64 pour HTML
            st.session_state.cachet_base64 = get_image_base64(uploaded_file)
            st.success("Cachet chargé avec succès !")
        elif st.session_state.cachet_base64:
             st.info("Un cachet est actuellement configuré.")
