import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="VenteUp Elite Pro", layout="wide", page_icon="💎")

def get_connection():
    return sqlite3.connect('venteup_v10.db', check_same_thread=False)

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

# --- CHARGEMENT ---
conn = get_connection()
info_ent = pd.read_sql("SELECT * FROM entreprise WHERE id = 1", conn).iloc[0]
conn.close()

# --- SÉCURITÉ & SUPPORT ISSA DIALLO ---
date_inst = datetime.strptime(info_ent['date_installation'], "%Y-%m-%d %H:%M:%S")
jours_restants = 3 - (datetime.now() - date_inst).days
est_active = info_ent['est_active'] == 1

if jours_restants <= 0 and not est_active:
    st.error("🚨 Période d'essai terminée")
    st.title("🔒 Application Verrouillée")
    st.markdown(f"""
    ### Contactez le développeur Issa Diallo pour débloquer :
    📞 **WhatsApp & Direct :** +224 610 51 89 73
    📧 **Email :** Issatanoudiallo2024@gmail.com
    """)
    code = st.text_input("Clé d'activation", type="password")
    if st.button("Activer l'application"):
        if code == info_ent['code_activation']:
            conn = get_connection()
            conn.execute("UPDATE entreprise SET est_active = 1 WHERE id = 1")
            conn.commit()
            st.success("✅ Application activée !")
            st.rerun()
    st.stop()

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title(f"🏬 {info_ent['nom']}")
    st.write(f"👤 Gérant : **{info_ent['gerant']}**")
    menu = st.radio("Menu Principal", ["📊 Dashboard", "🛒 Caisse", "📦 Stocks & Appro", "🧾 Factures & Historique", "⚙️ Paramètres"])
    st.divider()
    st.caption("🛠️ **Support Technique**")
    st.caption("Issa Diallo : 610 51 89 73")
    st.caption("Issatanoudiallo2024@gmail.com")

# --- DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("Performance 📊")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes", conn)
    df_p = pd.read_sql("SELECT * FROM produits", conn)
    conn.close()
    c1, c2, c3 = st.columns(3)
    c1.metric("CA Total", f"{df_v['total'].sum() if not df_v.empty else 0:,.0f} {info_ent['devise']}")
    c2.metric("Bénéfice Net", f"{df_v['benef'].sum() if not df_v.empty else 0:,.0f} {info_ent['devise']}")
    alertes = len(df_p[df_p['qte'] <= df_p['seuil']]) if not df_p.empty else 0
    c3.metric("Alertes Stock", alertes)

# --- CAISSE ---
elif menu == "🛒 Caisse":
    st.title("Vente Rapide 🛒")
    conn = get_connection()
    prods = pd.read_sql("SELECT * FROM produits WHERE qte > 0", conn)
    if not prods.empty:
        with st.form("vente"):
            p_nom = st.selectbox("Sélectionner le produit", prods['nom'].tolist())
            qte_v = st.number_input("Quantité", min_value=1, step=1)
            if st.form_submit_button("Valider l'ajout"):
                p_info = prods[prods['nom'] == p_nom].iloc[0]
                total = qte_v * p_info['p_vente']
                benef = (p_info['p_vente'] - p_info['p_achat']) * qte_v
                c = conn.cursor()
                c.execute("INSERT INTO ventes (produit_id, nom_prod, qte_v, date_v, total, benef) VALUES (?,?,?,?,?,?)",
                          (int(p_info['id']), p_nom, qte_v, datetime.now().strftime("%d/%m/%Y %H:%M"), total, benef))
                c.execute("UPDATE produits SET qte = qte - ? WHERE id = ?", (qte_v, int(p_info['id'])))
                conn.commit()
                st.success("Produit enregistré avec succès !")
    conn.close()

# --- STOCKS & REAPPRO ---
elif menu == "📦 Stocks & Appro":
    st.title("Gestion des Stocks 📦")
    t1, t2, t3 = st.tabs(["📋 Inventaire", "🔄 Réapprovisionnement", "➕ Nouveau Produit"])
    conn = get_connection()
    
    with t1:
        df_p = pd.read_sql("SELECT * FROM produits", conn)
        st.dataframe(df_p, use_container_width=True)
        
    with t2:
        st.subheader("Rajouter des quantités")
        if not df_p.empty:
            p_sel = st.selectbox("Choisir le produit à recharger", df_p['nom'].tolist())
            q_plus = st.number_input("Quantité reçue", min_value=1)
            if st.button("Mettre à jour le stock"):
                conn.execute("UPDATE produits SET qte = qte + ? WHERE nom = ?", (q_plus, p_sel))
                conn.commit()
                st.success(f"Le stock de {p_sel} a été augmenté !")
                st.rerun()

    with t3:
        with st.form("new_p"):
            n = st.text_input("Désignation")
            pa = st.number_input("Prix Achat")
            pv = st.number_input("Prix Vente")
            q = st.number_input("Stock Initial", min_value=0)
            if st.form_submit_button("Créer le produit"):
                conn.execute("INSERT INTO produits (nom, p_achat, p_vente, qte, seuil) VALUES (?,?,?,?,5)", (n, pa, pv, q))
                conn.commit()
                st.rerun()
    conn.close()

# --- FACTURATION ---
elif menu == "🧾 Factures & Historique":
    st.title("Édition de Factures 🧾")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes ORDER BY id DESC", conn)
    if not df_v.empty:
        selected_ids = st.multiselect("Sélectionner les articles pour la facture", df_v['id'].tolist())
        if selected_ids:
            items = df_v[df_v['id'].isin(selected_ids)]
            st.divider()
            col1, col2 = st.columns(2)
            c_nom = col1.text_input("Nom du Client")
            c_eml = col2.text_input("Email du Client")
            c_tel = col1.text_input("Téléphone Client")
            c_adr = col2.text_input("Adresse Client")
            status = st.radio("État du paiement", ["PAYÉ ✅", "NON PAYÉ ❌"], horizontal=True)

            if st.button("Visualiser la Facture"):
                total_f = items['total'].sum()
                html = f"""
                <div style="border: 2px solid #000; padding: 20px; background: white; color: black;">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <h2 style="color:#1a73e8;">{info_ent['nom']}</h2>
                            <p>📍 {info_ent['adresse']}<br>📞 {info_ent['telephone']}<br>📧 {info_ent['email']}</p>
                        </div>
                        <div style="text-align: right;">
                            <h2>FACTURE</h2>
                            <p><b>Client :</b> {c_nom}<br>📍 {c_adr}<br>📞 {c_tel}<br>📧 {c_eml}</p>
                        </div>
                    </div>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                        <tr style="background: #eee; border: 1px solid #000;">
                            <th style="padding: 10px;">N°</th><th style="padding: 10px;">Désignation</th>
                            <th style="padding: 10px;">Qté</th><th style="padding: 10px;">P. Unitaire</th><th style="padding: 10px;">Total</th>
                        </tr>
                """
                for i, row in enumerate(items.itertuples(), 1):
                    html += f"<tr><td style='border:1px solid #ddd; padding:8px; text-align:center;'>{i}</td><td style='border:1px solid #ddd; padding:8px;'>{row.nom_prod}</td><td style='border:1px solid #ddd; padding:8px; text-align:center;'>{row.qte_v}</td><td style='border:1px solid #ddd; padding:8px; text-align:right;'>{row.total/row.qte_v:,.0f}</td><td style='border:1px solid #ddd; padding:8px; text-align:right;'>{row.total:,.0f}</td></tr>"
                
                html += f"""
                    </table>
                    <h3 style="text-align: right;">NET À PAYER : {total_f:,.0f} {info_ent['devise']}</h3>
                    <p>Statut : <b>{status}</b></p>
                    <div style="margin-top: 30px; display: flex; justify-content: space-between;">
                        <p><i>{info_ent['message_recu']}</i></p>
                        <div style="border: 1px solid #000; width: 150px; height: 80px; text-align: center; line-height: 80px;">CACHET</div>
                    </div>
                    <p style="text-align: center; font-size: 10px; margin-top: 30px; border-top: 1px solid #eee;">
                        Développé par Issa Diallo | +224 610 51 89 73 | Issatanoudiallo2024@gmail.com
                    </p>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)
    conn.close()

# --- PARAMÈTRES ---
elif menu == "⚙️ Paramètres":
    st.title("Paramètres ⚙️")
    with st.form("params"):
        n_nom = st.text_input("Nom Boutique", value=info_ent['nom'])
        n_ger = st.text_input("Gérant", value=info_ent['gerant'])
        n_adr = st.text_input("Adresse Physique", value=info_ent['adresse'])
        n_tel = st.text_input("Numéro de téléphone", value=info_ent['telephone'])
        n_eml = st.text_input("Email Boutique", value=info_ent['email'])
        n_dev = st.selectbox("Devise", ["FG", "GNF", "CFA", "$"], index=0)
        n_msg = st.text_area("Message sur reçu", value=info_ent['message_recu'])
        if st.form_submit_button("Sauvegarder"):
            conn = get_connection()
            conn.execute("UPDATE entreprise SET nom=?, gerant=?, adresse=?, telephone=?, email=?, devise=?, message_recu=? WHERE id=1",
                         (n_nom, n_ger, n_adr, n_tel, n_eml, n_dev, n_msg))
            conn.commit()
            st.success("Modifications enregistrées !")
            st.rerun()
