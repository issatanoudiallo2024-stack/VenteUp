import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="VenteUp Pro", layout="wide", page_icon="🧾")

def get_connection():
    return sqlite3.connect('venteup_v11.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS produits
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, p_achat REAL, p_vente REAL, qte INTEGER, seuil INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ventes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, produit_id INTEGER, nom_prod TEXT, qte_v INTEGER, date_v TIMESTAMP, total REAL, benef REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS entreprise
                 (id INTEGER PRIMARY KEY, nom TEXT, adresse TEXT, telephone TEXT, email TEXT, gerant TEXT, devise TEXT, 
                  date_installation TIMESTAMP, est_active INTEGER, code_activation TEXT, message_recu TEXT)''')
    
    if c.execute("SELECT count(*) FROM entreprise").fetchone()[0] == 0:
        maintenant = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""INSERT INTO entreprise VALUES (1, 'Ma Boutique', 'Conakry', '+224', 'contact@boutique.com', 'Gérant', 'FG', ?, 0, 'VENTEUP-2026', 'Merci de votre confiance !')""", (maintenant,))
    conn.commit()
    conn.close()

init_db()

# --- CHARGEMENT DES INFOS ---
conn = get_connection()
info_ent = pd.read_sql("SELECT * FROM entreprise WHERE id = 1", conn).iloc[0]
conn.close()

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title(f"🏬 {info_ent['nom']}")
    menu = st.radio("Menu", ["📊 Dashboard", "🛒 Caisse", "📦 Stocks & Appro", "🧾 Factures & Historique", "⚙️ Paramètres"])
    st.divider()
    st.caption("Gestion Commerciale v11.0")

# --- DASHBOARD & STOCKS (Codes inchangés pour gagner de la place) ---
if menu == "📊 Dashboard":
    st.title("Performance 📊")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes", conn)
    c1, c2 = st.columns(2)
    c1.metric("CA Total", f"{df_v['total'].sum():,.0f} {info_ent['devise']}")
    c2.metric("Bénéfice", f"{df_v['benef'].sum():,.0f} {info_ent['devise']}")
    conn.close()

elif menu == "🛒 Caisse":
    st.title("Vente 🛒")
    conn = get_connection()
    prods = pd.read_sql("SELECT * FROM produits WHERE qte > 0", conn)
    if not prods.empty:
        with st.form("v"):
            p_nom = st.selectbox("Produit", prods['nom'].tolist())
            qte_v = st.number_input("Quantité", min_value=1)
            if st.form_submit_button("Ajouter"):
                p_info = prods[prods['nom'] == p_nom].iloc[0]
                total = qte_v * p_info['p_vente']
                benef = (p_info['p_vente'] - p_info['p_achat']) * qte_v
                c = conn.cursor()
                c.execute("INSERT INTO ventes (produit_id, nom_prod, qte_v, date_v, total, benef) VALUES (?,?,?,?,?,?)",
                          (int(p_info['id']), p_nom, qte_v, datetime.now().strftime("%d/%m/%Y %H:%M"), total, benef))
                c.execute("UPDATE produits SET qte = qte - ? WHERE id = ?", (qte_v, int(p_info['id'])))
                conn.commit()
                st.success("Vendu !")
    conn.close()

elif menu == "📦 Stocks & Appro":
    st.title("Stocks 📦")
    conn = get_connection()
    df_p = pd.read_sql("SELECT * FROM produits", conn)
    st.dataframe(df_p, use_container_width=True)
    with st.expander("Réapprovisionner ou Nouveau"):
        # Logique de réappro ici...
        pass
    conn.close()

# --- FACTURATION (MISE À JOUR) ---
elif menu == "🧾 Factures & Historique":
    st.title("Édition de Factures Professionnelles 🧾")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes ORDER BY id DESC", conn)
    
    if not df_v.empty:
        selected_ids = st.multiselect("Sélectionner les articles", df_v['id'].tolist())
        
        if selected_ids:
            items = df_v[df_v['id'].isin(selected_ids)]
            st.divider()
            
            c1, c2 = st.columns(2)
            c_nom = c1.text_input("Nom Client")
            c_tel = c2.text_input("Téléphone Client")
            c_adr = c1.text_input("Adresse Client")
            c_eml = c2.text_input("Email Client")
            status = st.radio("Paiement", ["PAYÉ ✅", "NON PAYÉ ❌"], horizontal=True)
            
            # OPTION CACHET IMAGE
            st.subheader("🛠️ Option Cachet")
            cachet_file = st.file_uploader("Importer l'image de votre cachet (PNG transparent conseillé)", type=['png', 'jpg', 'jpeg'])
            
            if st.button("Générer la Facture"):
                total_f = items['total'].sum()
                
                # Conversion du cachet en base64 pour affichage HTML
                cachet_html = ""
                if cachet_file:
                    bin_str = base64.b64encode(cachet_file.getvalue()).decode()
                    cachet_html = f'<img src="data:image/png;base64,{bin_str}" style="width:120px; height:auto; position:absolute; bottom:10px; right:10px; opacity:0.8;">'
                
                # DESIGN DE LA FACTURE (Sans infos développeur)
                facture_html = f"""
                <div id="facture-area" style="border: 2px solid #000; padding: 30px; background: white; color: black; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; position: relative;">
                    <div style="display: flex; justify-content: space-between; border-bottom: 3px solid #1a73e8; padding-bottom: 10px;">
                        <div>
                            <h2 style="margin:0; color:#1a73e8;">{info_ent['nom']}</h2>
                            <p style="margin:2px;">📍 {info_ent['adresse']}</p>
                            <p style="margin:2px;">📞 {info_ent['telephone']}</p>
                            <p style="margin:2px;">📧 {info_ent['email']}</p>
                        </div>
                        <div style="text-align: right;">
                            <h1 style="margin:0; color: #333;">FACTURE</h1>
                            <p style="margin:2px;"><b>CLIENT :</b> {c_nom}</p>
                            <p style="margin:2px;">📍 {c_adr} | 📞 {c_tel}</p>
                            <p style="margin:2px;">Date : {datetime.now().strftime('%d/%m/%Y')}</p>
                        </div>
                    </div>

                    <table style="width: 100%; border-collapse: collapse; margin-top: 25px;">
                        <tr style="background: #1a73e8; color: white;">
                            <th style="padding: 12px; border: 1px solid #000;">N°</th>
                            <th style="padding: 12px; border: 1px solid #000; text-align:left;">Désignation</th>
                            <th style="padding: 12px; border: 1px solid #000;">Qté</th>
                            <th style="padding: 12px; border: 1px solid #000;">P. Unitaire</th>
                            <th style="padding: 12px; border: 1px solid #000;">Total</th>
                        </tr>
                """
                for i, row in enumerate(items.itertuples(), 1):
                    facture_html += f"""
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align:center;">{i}</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{row.nom_prod}</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align:center;">{row.qte_v}</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align:right;">{row.total/row.qte_v:,.0f}</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align:right;"><b>{row.total:,.0f}</b></td>
                        </tr>
                    """
                
                facture_html += f"""
                    </table>
                    
                    <div style="margin-top: 20px; text-align: right;">
                        <h2 style="margin:0;">TOTAL NET : {total_f:,.0f} {info_ent['devise']}</h2>
                        <p style="font-size: 1.2em;">Statut : <span style="color: green;">{status}</span></p>
                    </div>

                    <div style="margin-top: 50px; display: flex; justify-content: space-between; align-items: flex-end;">
                        <div style="font-style: italic;">
                            <p>{info_ent['message_recu']}</p>
                        </div>
                        <div style="width: 200px; height: 120px; border: 1px dashed #ccc; text-align: center; position: relative;">
                            <p style="color: #ccc; margin-top: 40px;">Signature & Cachet</p>
                            {cachet_html}
                        </div>
                    </div>
                </div>
                """
                st.markdown(facture_html, unsafe_allow_html=True)
                
                st.info("💡 Pour enregistrer en image : Faites un clic droit sur la facture -> 'Enregistrer l'image sous' ou utilisez une capture d'écran.")
    conn.close()

# --- PARAMÈTRES ---
elif menu == "⚙️ Paramètres":
    st.title("Configuration ⚙️")
    with st.form("p"):
        n_nom = st.text_input("Nom Boutique", value=info_ent['nom'])
        n_adr = st.text_input("Adresse", value=info_ent['adresse'])
        n_tel = st.text_input("Téléphone", value=info_ent['telephone'])
        n_eml = st.text_input("Email", value=info_ent['email'])
        n_msg = st.text_area("Message bas de facture", value=info_ent['message_recu'])
        if st.form_submit_button("Sauvegarder"):
            conn = get_connection()
            conn.execute("UPDATE entreprise SET nom=?, adresse=?, telephone=?, email=?, message_recu=? WHERE id=1",
                         (n_nom, n_adr, n_tel, n_eml, n_msg))
            conn.commit()
            st.rerun()
