import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64

# --- 1. SYSTÈME DE LICENCE (7 JOURS) ---
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

# --- 2. INITIALISATION SESSION ---
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
    st.session_state.boutique_info = {"nom": "NOM DE VOTRE BOUTIQUE", "adresse": "ADRESSE", "tel": "TELEPHONE"}

# --- 3. MENU ---
with st.sidebar:
    st.title("🚀 VenteUp Pro")
    choix = st.radio("MENU", ["🛒 Caisse", "📦 Stock", "📈 Historique", "⚙️ Paramètres"])
    st.write("---")
    st.write("**Concepteur :** Issa Diallo\n📞 610 51 89 73")

# --- 4. CAISSE & FACTURE EN IMAGE ---
if choix == "🛒 Caisse":
    st.header("🛒 Terminal de Vente")
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        if not st.session_state.stock.empty:
            p_sel = st.selectbox("Article", st.session_state.stock["Produit"])
            info = st.session_state.stock[st.session_state.stock["Produit"] == p_sel].iloc[0]
            q = st.number_input("Quantité", min_value=1, value=1)
            if st.button("🛒 Ajouter", use_container_width=True):
                if q <= info["Quantité"]:
                    st.session_state.panier.append({"Produit":p_sel,"Qte":q,"Prix":info["Prix Vente"],"Total":info["Prix Vente"]*q,"Ben":(info["Prix Vente"]-info["Prix Achat"])*q})
                    st.rerun()
                else: st.error("Stock insuffisant !")

    with col2:
        if st.session_state.panier:
            st.subheader("Panier")
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
        
        if st.button("📸 GÉNÉRER LA FACTURE (IMAGE)", use_container_width=True):
            if not st.session_state.c_nom: st.error("Nom client obligatoire")
            else:
                total_v = sum(i['Total'] for i in st.session_state.panier)
                date_v = datetime.now().strftime("%d/%m/%Y %H:%M")
                col_statut = "#28a745" if "Payé" in statut else "#dc3545"

                # SCRIPT MAGIQUE POUR CAPTURER EN IMAGE
                st.components.v1.html(f"""
                <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
                <div id="facture-zone" style="width:500px; padding:20px; background:white; color:black; border:1px solid #000; font-family:Arial;">
                    <div style="text-align:center; border-bottom:2px solid #000; padding-bottom:10px;">
                        <h2 style="margin:0;">{st.session_state.boutique_info['nom'].upper()}</h2>
                        <p style="font-size:12px;">{st.session_state.boutique_info['adresse']} | {st.session_state.boutique_info['tel']}</p>
                    </div>
                    <div style="margin-top:10px; font-size:13px;">
                        <p><b>Client:</b> {st.session_state.c_nom} | <b>Date:</b> {date_v}</p>
                    </div>
                    <table style="width:100%; border-collapse:collapse; margin-top:10px; font-size:12px;">
                        <tr style="background:#eee;">
                            <th style="border:1px solid #000; padding:5px;">Art.</th>
                            <th style="border:1px solid #000; padding:5px;">Qté</th>
                            <th style="border:1px solid #000; padding:5px;">Total</th>
                        </tr>
                        {"".join([f"<tr><td style='border:1px solid #000; padding:5px;'>{i['Produit']}</td><td style='border:1px solid #000; text-align:center;'>{i['Qte']}</td><td style='border:1px solid #000; text-align:right;'>{i['Total']:,}</td></tr>" for i in st.session_state.panier])}
                    </table>
                    <h3 style="text-align:right;">TOTAL: {total_v:,} GNF</h3>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        {f'<img src="data:image/png;base64,{st.session_state.cachet_base64}" style="width:80px;">' if st.session_state.cachet_base64 else '<p style="font-size:10px;">(Cachet)</p>'}
                        <div style="background:{col_statut}; color:white; padding:5px; border-radius:3px; font-size:12px;">{statut.upper()}</div>
                    </div>
                </div>
                <br>
                <button id="download-btn" style="width:100%; padding:15px; background:green; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">
                    ⬇️ TÉLÉCHARGER DANS LA GALERIE (IMAGE)
                </button>

                <script>
                    document.getElementById('download-btn').onclick = function() {{
                        html2canvas(document.querySelector("#facture-zone")).then(canvas => {{
                            let link = document.createElement('a');
                            link.download = 'facture_{st.session_state.c_nom}_{datetime.now().strftime("%H%M")}.png';
                            link.href = canvas.toDataURL("image/png");
                            link.click();
                        }});
                    }};
                </script>
                """, height=650)
                
                # --- SAUVEGARDE DONNÉES ---
                new_v = {"Date":date_v, "Client":st.session_state.c_nom, "Total":total_v, "Bénéfice":sum(i['Ben'] for i in st.session_state.panier), "Statut":statut}
                st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([new_v])], ignore_index=True)
                sauver_csv(st.session_state.ventes, "ventes_data.csv")
                for i in st.session_state.panier:
                    st.session_state.stock.loc[st.session_state.stock["Produit"]==i["Produit"], "Quantité"] -= i["Qte"]
                sauver_csv(st.session_state.stock, "stock_data.csv")
                # On ne vide pas le panier ici pour que l'utilisateur puisse cliquer sur télécharger

# --- 5. STOCK (RÉAPPRO ET CRÉATION) ---
elif choix == "📦 Stock":
    st.header("📦 Gestion Stock")
    t1, t2, t3 = st.tabs(["🔄 Réappro", "➕ Nouveau", "🗑️ Liste"])
    with t1:
        if not st.session_state.stock.empty:
            p_reap = st.selectbox("Article", st.session_state.stock["Produit"])
            q_plus = st.number_input("Quantité à ajouter", min_value=1)
            if st.button("Valider"):
                st.session_state.stock.loc[st.session_state.stock["Produit"] == p_reap, "Quantité"] += q_plus
                sauver_csv(st.session_state.stock, "stock_data.csv"); st.rerun()
    with t2:
        with st.form("n"):
            n = st.text_input("Nom")
            pa = st.number_input("Prix Achat", 0)
            pv = st.number_input("Prix Vente", 0)
            q = st.number_input("Quantité", 1)
            if st.form_submit_button("Créer"):
                st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([{"Produit":n,"Prix Achat":pa,"Prix Vente":pv,"Quantité":q}])], ignore_index=True)
                sauver_csv(st.session_state.stock, "stock_data.csv"); st.rerun()
    with t3:
        st.dataframe(st.session_state.stock, use_container_width=True)

# --- 6. HISTORIQUE & PARAMÈTRES ---
elif choix == "📈 Historique":
    st.header("📈 Ventes")
    st.dataframe(st.session_state.ventes, use_container_width=True)

elif choix == "⚙️ Paramètres":
    st.header("⚙️ Boutique")
    st.session_state.boutique_info['nom'] = st.text_input("Nom", st.session_state.boutique_info['nom'])
    st.session_state.boutique_info['adresse'] = st.text_input("Adresse", st.session_state.boutique_info['adresse'])
    st.session_state.boutique_info['tel'] = st.text_input("Tél", st.session_state.boutique_info['tel'])
    img = st.file_uploader("Cachet (PNG)", type=['png', 'jpg'])
    if img:
        st.session_state.cachet_base64 = base64.b64encode(img.getvalue()).decode()
        st.success("Ok !")
