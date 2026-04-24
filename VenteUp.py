import streamlit as st
import pandas as pd
import os
from datetime import datetime
import base64

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
    st.error(f"🚫 ESSAI TERMINÉ. Contactez le concepteur au 610 51 89 73.")
    st.stop()

# --- 2. GESTION DES FICHIERS ET SAUVEGARDE ---
def charger_csv(nom, col):
    if os.path.exists(nom):
        try: return pd.read_csv(nom)
        except: return pd.DataFrame(columns=col)
    return pd.DataFrame(columns=col)

def sauver_csv(df, nom):
    df.to_csv(nom, index=False)

# Chargement des données permanentes
if 'stock' not in st.session_state:
    st.session_state.stock = charger_csv("stock_data.csv", ["Produit", "Prix Achat", "Prix Vente", "Quantité"])
if 'ventes' not in st.session_state:
    st.session_state.ventes = charger_csv("ventes_data.csv", ["Date", "Client", "Total", "Bénéfice", "Statut"])

# --- FIX: Mémoire permanente de la boutique ---
FICHIER_INFO = "boutique_config.csv"
if 'boutique_info' not in st.session_state:
    df_info = charger_csv(FICHIER_INFO, ["nom", "adresse", "tel", "cachet"])
    if not df_info.empty:
        st.session_state.boutique_info = df_info.iloc[0].to_dict()
        st.session_state.cachet_base64 = st.session_state.boutique_info.get("cachet")
    else:
        st.session_state.boutique_info = {"nom": "NOM DE LA BOUTIQUE", "adresse": "ADRESSE", "tel": "TELEPHONE"}
        st.session_state.cachet_base64 = None

# Initialisation Panier (Temporel)
if 'panier' not in st.session_state: st.session_state.panier = []

st.set_page_config(page_title="VenteUp Pro", layout="wide")

# --- 3. BARRE LATÉRALE ---
with st.sidebar:
    st.title("🚀 VenteUp Pro")
    choix = st.radio("MENU", ["🛒 Caisse", "📦 Stock", "📈 Historique", "⚙️ Paramètres"])
    st.write("---")
    st.write("**Concepteur :** Issa Diallo\n📞 610 51 89 73")

# --- 4. CAISSE & FACTURE IMAGE ---
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
            if st.button("🗑️ Vider le panier"): st.session_state.panier = []; st.rerun()

    if st.session_state.panier:
        st.write("---")
        st.subheader("📝 Infos Client")
        c1, c2, c3 = st.columns(3)
        nom_c = c1.text_input("Nom Client")
        tel_c = c2.text_input("Téléphone")
        adr_c = c3.text_input("Adresse")
        statut = st.radio("Paiement", ["Payé ✅", "Dette 🔴"], horizontal=True)
        
        if st.button("📸 GÉNÉRER LA FACTURE (IMAGE)", use_container_width=True):
            if not nom_c: st.error("Nom client requis")
            else:
                total_v = sum(i['Total'] for i in st.session_state.panier)
                date_v = datetime.now().strftime("%d/%m/%Y %H:%M")
                col_statut = "#28a745" if "Payé" in statut else "#dc3545"

                st.components.v1.html(f"""
                <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
                <div id="f-zone" style="width:450px; padding:20px; background:white; color:black; border:1px solid #000; font-family:Arial;">
                    <div style="text-align:center; border-bottom:2px solid #000; padding-bottom:10px;">
                        <h2 style="margin:0;">{st.session_state.boutique_info['nom'].upper()}</h2>
                        <p style="font-size:12px;">{st.session_state.boutique_info['adresse']} | {st.session_state.boutique_info['tel']}</p>
                    </div>
                    <p style="font-size:12px;"><b>Client:</b> {nom_c} <br> <b>Date:</b> {date_v}</p>
                    <table style="width:100%; border-collapse:collapse; font-size:12px;">
                        <tr style="background:#eee;"><th>Désign.</th><th>Qté</th><th>Total</th></tr>
                        {"".join([f"<tr><td style='border:1px solid #ddd; padding:5px;'>{i['Produit']}</td><td style='border:1px solid #ddd; text-align:center;'>{i['Qte']}</td><td style='border:1px solid #ddd; text-align:right;'>{i['Total']:,}</td></tr>" for i in st.session_state.panier])}
                    </table>
                    <h3 style="text-align:right; margin-top:10px;">TOTAL: {total_v:,} GNF</h3>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        {f'<img src="data:image/png;base64,{st.session_state.cachet_base64}" style="width:80px;">' if st.session_state.cachet_base64 else '<span></span>'}
                        <div style="background:{col_statut}; color:white; padding:5px; border-radius:3px; font-size:12px;">{statut.upper()}</div>
                    </div>
                </div>
                <button id="dl" style="width:100%; margin-top:10px; padding:15px; background:green; color:white; border:none; border-radius:5px; cursor:pointer;">⬇️ ENREGISTRER DANS LA GALERIE</button>
                <script>
                    document.getElementById('dl').onclick = function() {{
                        html2canvas(document.querySelector("#f-zone")).then(canvas => {{
                            let link = document.createElement('a');
                            link.download = 'facture_{nom_c}.png';
                            link.href = canvas.toDataURL("image/png");
                            link.click();
                        }});
                    }};
                </script>
                """, height=600)
                
                # --- SAUVEGARDE ---
                new_v = {"Date":date_v, "Client":nom_c, "Total":total_v, "Bénéfice":sum(i['Ben'] for i in st.session_state.panier), "Statut":statut}
                st.session_state.ventes = pd.concat([st.session_state.ventes, pd.DataFrame([new_v])], ignore_index=True)
                sauver_csv(st.session_state.ventes, "ventes_data.csv")
                for i in st.session_state.panier:
                    st.session_state.stock.loc[st.session_state.stock["Produit"]==i["Produit"], "Quantité"] -= i["Qte"]
                sauver_csv(st.session_state.stock, "stock_data.csv")

# --- 5. STOCK (AVEC RÉAPPRO ET SUPPRESSION ARTICLE) ---
elif choix == "📦 Stock":
    st.header("📦 Gestion Stock")
    t1, t2, t3 = st.tabs(["🔄 Réappro", "➕ Nouveau", "🗑️ Gérer/Supprimer"])
    with t1:
        if not st.session_state.stock.empty:
            p_reap = st.selectbox("Article", st.session_state.stock["Produit"])
            q_plus = st.number_input("Quantité à ajouter", min_value=1)
            if st.button("Valider l'ajout"):
                st.session_state.stock.loc[st.session_state.stock["Produit"] == p_reap, "Quantité"] += q_plus
                sauver_csv(st.session_state.stock, "stock_data.csv"); st.success("Mis à jour !"); st.rerun()
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
        if not st.session_state.stock.empty:
            p_del = st.selectbox("Supprimer un article", st.session_state.stock["Produit"])
            if st.button("⚠️ Supprimer définitivement"):
                st.session_state.stock = st.session_state.stock[st.session_state.stock["Produit"] != p_del]
                sauver_csv(st.session_state.stock, "stock_data.csv"); st.rerun()

# --- 6. HISTORIQUE (AVEC SUPPRESSION TRANSACTION) ---
elif choix == "📈 Historique":
    st.header("📈 Historique des Ventes")
    if not st.session_state.ventes.empty:
        st.dataframe(st.session_state.ventes, use_container_width=True)
        st.write("---")
        idx_del = st.number_input("Entrez l'index de la vente à supprimer", min_value=0, max_value=len(st.session_state.ventes)-1, step=1)
        if st.button("🗑️ Supprimer cette transaction"):
            st.session_state.ventes = st.session_state.ventes.drop(st.session_state.ventes.index[idx_del])
            sauver_csv(st.session_state.ventes, "ventes_data.csv"); st.rerun()
    else: st.info("Aucune vente enregistrée.")

# --- 7. PARAMÈTRES (SAUVEGARDE PERMANENTE) ---
elif choix == "⚙️ Paramètres":
    st.header("⚙️ Boutique")
    nom_b = st.text_input("Nom de la Boutique", st.session_state.boutique_info['nom'])
    adr_b = st.text_input("Adresse", st.session_state.boutique_info['adresse'])
    tel_b = st.text_input("Tél", st.session_state.boutique_info['tel'])
    img = st.file_uploader("Cachet (PNG)", type=['png', 'jpg'])
    
    if st.button("💾 ENREGISTRER DÉFINITIVEMENT"):
        if img:
            st.session_state.cachet_base64 = base64.b64encode(img.getvalue()).decode()
        st.session_state.boutique_info = {"nom": nom_b, "adresse": adr_b, "tel": tel_b, "cachet": st.session_state.cachet_base64}
        # Sauvegarde physique dans le fichier
        pd.DataFrame([st.session_state.boutique_info]).to_csv(FICHIER_INFO, index=False)
        st.success("Toutes les informations ont été enregistrées sur le disque !")
