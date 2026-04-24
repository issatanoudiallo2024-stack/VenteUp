import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. SYSTÈME DE LICENCE & SÉCURITÉ ---
CODE_DEBLOCAGE_SECRET = "ISSAVUP2026" 
FICHIER_LICENCE = "licence_config.csv"

def charger_licence():
    if os.path.exists(FICHIER_LICENCE):
        try:
            return pd.read_csv(FICHIER_LICENCE).iloc[0].to_dict()
        except:
            pass
    # Initialisation au tout premier lancement
    data = {"date_debut": datetime.now().strftime("%Y-%m-%d"), "statut": "essai"}
    pd.DataFrame([data]).to_csv(FICHIER_LICENCE, index=False)
    return data

def sauver_licence(statut):
    debut = charger_licence()["date_debut"]
    pd.DataFrame([{"date_debut": debut, "statut": statut}]).to_csv(FICHIER_LICENCE, index=False)

# Vérification du temps restant
licence = charger_licence()
date_debut = datetime.strptime(licence["date_debut"], "%Y-%m-%d")
jours_passes = (datetime.now() - date_debut).days
jours_restants = 7 - jours_passes
est_bloque = licence["statut"] == "essai" and jours_restants < 0

# --- 2. ÉCRAN DE BLOCAGE (SI ESSAI FINI) ---
if est_bloque:
    st.set_page_config(page_title="Activation Requise", page_icon="🔒")
    st.error("🚫 PÉRIODE D'ESSAI TERMINÉE")
    st.header("🔓 Activer VenteUp Pro")
    
    st.info(f"""
    Votre période d'essai gratuite est terminée. 
    Pour continuer à utiliser l'application et accéder à vos données, veuillez contacter le développeur.
    
    📞 **Appelez Issa Diallo au : 610 51 89 73**
    
    Une fois l'activation validée, saisissez le code reçu ci-dessous.
    """)
    
    code_saisi = st.text_input("Code d'activation", type="password", placeholder="Entrez le code ici...")
    
    if st.button("Activer l'accès définitif"):
        if code_saisi == CODE_DEBLOCAGE_SECRET:
            sauver_licence("paye")
            st.success("✅ Application activée avec succès !")
            st.rerun()
        else:
            st.error("Code incorrect. Veuillez contacter le 610 51 89 73.")
    st.stop()

# --- 3. CONFIGURATION DE L'APPLICATION ---
st.set_page_config(page_title="VenteUp Pro", layout="wide", page_icon="🛒")

def charger_csv(nom, col):
    if os.path.exists(nom):
        try: return pd.read_csv(nom)
        except: return pd.DataFrame(columns=col)
    return pd.DataFrame(columns=col)

def sauver_csv(df, nom):
    df.to_csv(nom, index=False)

# Initialisation des données
if 'stock' not in st.session_state:
    st.session_state.stock = charger_csv("stock_data.csv", ["Produit", "Prix Achat", "Prix Vente", "Quantité"])
if 'ventes' not in st.session_state:
    st.session_state.ventes = charger_csv("ventes_data.csv", ["Date", "Client", "Total", "Bénéfice", "Statut"])
if 'panier' not in st.session_state:
    st.session_state.panier = []
if 'boutique_info' not in st.session_state:
    st.session_state.boutique_info = {"nom": "", "adresse": "", "tel": ""}

# --- 4. BARRE LATÉRALE ---
with st.sidebar:
    st.title("🚀 VenteUp Pro")
    if licence["statut"] == "essai":
        st.caption(f"⏳ Mode Essai : {max(0, jours_restants)} jours restants")
    else:
        st.success("✅ Version Illimitée")
    
    choix = st.radio("MENU", ["🛒 Caisse", "📦 Stock & Alerte", "📈 Historique", "⚙️ Paramètres"])
    st.markdown("---")
    st.write("**Développeur :** Issa Diallo")
    st.write("📞 **Contact :** 610 51 89 73")

# --- 5. MODULE CAISSE ---
if choix == "🛒 Caisse":
    st.header("🛒 Interface de Vente")
    
    # Alertes de stock bas
    alerte_stock = st.session_state.stock[st.session_state.stock["Quantité"] <= 5]
    if not alerte_stock.empty:
        for _, row in alerte_stock.iterrows():
            st.error(f"⚠️ **Alerte :** {row['Produit']} ({row['Quantité']} restants)")

    if not st.session_state.boutique_info['nom']:
        st.warning("⚠️ Configurez votre boutique dans 'Paramètres' pour imprimer des factures.")

    col1, col2 = st.columns(2)
    with col1:
        if not st.session_state.stock.empty:
            p_sel = st.selectbox("Article", st.session_state.stock["Produit"])
            info = st.session_state.stock[st.session_state.stock["Produit"] == p_sel].iloc[0]
            st.write(f"Stock disponible : **{info['Quantité']}**")
            q = st.number_input("Quantité", min_value=1, value=1)
            if st.button("🛒 Ajouter au panier"):
                if q <= info["Quantité"]:
                    st.session_state.panier.append({
                        "Produit": p_sel, "Qte": q, "Prix": info["Prix Vente"], 
                        "Total": info["Prix Vente"]*q, "Ben": (info["Prix Vente"]-info["Prix Achat"])*q
                    })
                    st.rerun()
                else: st.error("Stock insuffisant")

    with col2:
        if st.session_state.panier:
            st.subheader("Panier actuel")
            st.table(pd.DataFrame(st.session_state.panier)[["Produit", "Qte", "Total"]])
            if st.button("🗑️ Vider le panier"):
                st.session_state.panier = []; st.rerun()

    if st.session_state.panier:
        st.write("---")
        c_n = st.text_input("Nom du Client", "")
        statut = st.radio("Statut du paiement", ["Payé", "Dette"], horizontal=True)
        
        if st.button("✅ Valider & Générer Facture"):
            if not c_n: st.error("Nom client obligatoire")
            else:
                total_v = sum(i['Total'] for i in st.session_state.panier)
                date_v = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                # Sauvegarde Vente
                new_v = {"Date": date_v, "Client": c_n, "Total": total_v, "Bénéfice": sum(i['Ben'] for i in st.session_state.panier), "Statut": statut}
                st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([new_v])], ignore_index=True)
                sauver_csv(st.session_state.ventes, "ventes_data.csv")
                
                # Update Stock
                for i in st.session_state.panier:
                    st.session_state.stock.loc[st.session_state.stock["Produit"] == i["Produit"], "Quantité"] -= i["Qte"]
                sauver_csv(st.session_state.stock, "stock_data.csv")

                # Facture HTML
                html = f"""
                <div style="font-family:sans-serif; border:1px solid #000; padding:15px; background:white; color:black;">
                    <h3>{st.session_state.boutique_info['nom'].upper()}</h3>
                    <p>{st.session_state.boutique_info['adresse']} | {st.session_state.boutique_info['tel']}</p>
                    <hr>
                    <p><b>Client:</b> {c_n} <br> <b>Date:</b> {date_v} <br> <b>Paiement:</b> {statut}</p>
                    <h2 style="color:red;">TOTAL : {total_v:,.0f} GNF</h2>
                </div>
                <br><button onclick="window.print()" style="width:100%; padding:10px; background:black; color:white; cursor:pointer;">🖨️ IMPRIMER / PDF</button>
                """
                st.markdown(html, unsafe_allow_html=True)
                st.session_state.panier = []

# --- 6. MODULE STOCK ---
elif choix == "📦 Stock & Alerte":
    st.header("📦 Gestion des Produits")
    t1, t2 = st.tabs(["➕ Ajouter/Réapprovisionner", "🗑️ Gérer le Stock"])
    
    with t1:
        with st.form("stock_form"):
            n = st.text_input("Nom du produit")
            pa = st.number_input("Prix Achat", value=0)
            pv = st.number_input("Prix Vente", value=0)
            q = st.number_input("Quantité à ajouter", value=0)
            if st.form_submit_button("Enregistrer"):
                if n in st.session_state.stock["Produit"].values:
                    st.session_state.stock.loc[st.session_state.stock["Produit"] == n, "Quantité"] += q
                else:
                    st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([{"Produit":n,"Prix Achat":pa,"Prix Vente":pv,"Quantité":q}])], ignore_index=True)
                sauver_csv(st.session_state.stock, "stock_data.csv")
                st.rerun()

    with t2:
        if not st.session_state.stock.empty:
            for i, row in st.session_state.stock.iterrows():
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.write(f"**{row['Produit']}**")
                c2.write(f"Stock: {row['Quantité']}")
                if c3.button("Supprimer", key=f"del_{i}"):
                    st.session_state.stock = st.session_state.stock.drop(i).reset_index(drop=True)
                    sauver_csv(st.session_state.stock, "stock_data.csv")
                    st.rerun()
            st.markdown("---")
            st.dataframe(st.session_state.stock, use_container_width=True)

# --- 7. MODULE HISTORIQUE ---
elif choix == "📈 Historique":
    st.header("📈 Historique & Dettes")
    if not st.session_state.ventes.empty:
        dettes = st.session_state.ventes[st.session_state.ventes["Statut"] == "Dette"]
        if not dettes.empty:
            st.error(f"Total Dettes à récupérer : **{dettes['Total'].sum():,.0f} GNF**")
        
        for i, row in st.session_state.ventes.iterrows():
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            c1.write(row['Date'])
            c2.write(f"{'🔴' if row['Statut']=='Dette' else '🟢'} {row['Client']}")
            c3.write(f"{row['Total']:,} GNF")
            if c4.button("❌", key=f"vdel_{i}"):
                st.session_state.ventes = st.session_state.ventes.drop(i).reset_index(drop=True)
                sauver_csv(st.session_state.ventes, "ventes_data.csv")
                st.rerun()

# --- 8. MODULE PARAMÈTRES ---
elif choix == "⚙️ Paramètres":
    st.header("⚙️ Configuration")
    st.session_state.boutique_info['nom'] = st.text_input("Nom de la Boutique", st.session_state.boutique_info['nom'])
    st.session_state.boutique_info['adresse'] = st.text_input("Adresse", st.session_state.boutique_info['adresse'])
    st.session_state.boutique_info['tel'] = st.text_input("Téléphone", st.session_state.boutique_info['tel'])
    if st.button("Enregistrer les réglages"):
        st.success("Paramètres mis à jour !")
