import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="VenteUp Elite Pro", layout="wide", page_icon="💎")

def get_connection():
    return sqlite3.connect('venteup_v6.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS produits
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, p_achat REAL, p_vente REAL, qte INTEGER, seuil INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ventes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, produit_id INTEGER, nom_prod TEXT, qte_v INTEGER, date_v TIMESTAMP, total REAL, benef REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS entreprise
                 (id INTEGER PRIMARY KEY, nom TEXT, adresse TEXT, telephone TEXT, gerant TEXT, devise TEXT, 
                  date_installation TIMESTAMP, est_active INTEGER, code_activation TEXT, message_recu TEXT)''')
    
    if c.execute("SELECT count(*) FROM entreprise").fetchone()[0] == 0:
        maintenant = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""INSERT INTO entreprise VALUES (1, 'Ma Boutique', 'Conakry', '+224', 'Gérant', 'FG', ?, 0, 'VENTEUP-2026', 'Merci de votre confiance !')""", (maintenant,))
    conn.commit()
    conn.close()

init_db()

# --- CHARGEMENT ---
conn = get_connection()
info_ent = pd.read_sql("SELECT * FROM entreprise WHERE id = 1", conn).iloc[0]
conn.close()

# --- SECURITÉ ISSA DIALLO ---
date_inst = datetime.strptime(info_ent['date_installation'], "%Y-%m-%d %H:%M:%S")
jours_restants = 3 - (datetime.now() - date_inst).days
est_active = info_ent['est_active'] == 1

if jours_restants <= 0 and not est_active:
    st.error("🚨 Période d'essai terminée")
    st.title("🔒 Application Verrouillée")
    st.markdown(f"**Contactez Issa Diallo pour activer :**\n\n📞 WhatsApp: [+224 610 51 89 73](https://wa.me/224610518973)\n📧 {info_ent.get('email', 'Issatanoudiallo2024@gmail.com')}")
    code = st.text_input("Clé d'activation", type="password")
    if st.button("Activer"):
        if code == info_ent['code_activation']:
            conn = get_connection()
            conn.execute("UPDATE entreprise SET est_active = 1 WHERE id = 1")
            conn.commit()
            st.rerun()
    st.stop()

# --- NAVIGATION ---
with st.sidebar:
    st.title(f"🏬 {info_ent['nom']}")
    st.caption(f"Gérant: {info_ent['gerant']}")
    menu = st.radio("Menu", ["📊 Dashboard", "🛒 Caisse", "📦 Stocks & Appro", "🧾 Factures & Historique", "⚙️ Paramètres"])
    st.divider()
    st.caption(f"Dev: Issa Diallo\n📞 610 51 89 73")

# --- FONCTIONS ---
if menu == "📊 Dashboard":
    st.title("Performance 📊")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes", conn)
    df_p = pd.read_sql("SELECT * FROM produits", conn)
    conn.close()
    c1, c2, c3 = st.columns(3)
    c1.metric("Chiffre d'Affaire", f"{df_v['total'].sum() if not df_v.empty else 0:,.0f} {info_ent['devise']}")
    c2.metric("Bénéfice", f"{df_v['benef'].sum() if not df_v.empty else 0:,.0f} {info_ent['devise']}")
    alertes = len(df_p[df_p['qte'] <= df_p['seuil']]) if not df_p.empty else 0
    c3.metric("Alertes Stock", alertes)

elif menu == "🛒 Caisse":
    st.title("Vente Directe 🛒")
    conn = get_connection()
    prods = pd.read_sql("SELECT * FROM produits WHERE qte > 0", conn)
    if not prods.empty:
        p_nom = st.selectbox("Produit", prods['nom'].tolist())
        qte_v = st.number_input("Quantité", min_value=1, step=1)
        p_info = prods[prods['nom'] == p_nom].iloc[0]
        if st.button("Enregistrer la vente", type="primary"):
            total = qte_v * p_info['p_vente']
            benef = (p_info['p_vente'] - p_info['p_achat']) * qte_v
            c = conn.cursor()
            c.execute("INSERT INTO ventes (produit_id, nom_prod, qte_v, date_v, total, benef) VALUES (?,?,?,?,?,?)",
                      (int(p_info['id']), p_nom, qte_v, datetime.now().strftime("%d/%m/%Y %H:%M"), total, benef))
            c.execute("UPDATE produits SET qte = qte - ? WHERE id = ?", (qte_v, int(p_info['id'])))
            conn.commit()
            st.success(f"Vendu ! {info_ent['message_recu']}")
    conn.close()

elif menu == "📦 Stocks & Appro":
    st.title("Stocks 📦")
    t1, t2, t3 = st.tabs(["Inventaire", "Réappro", "Nouveau"])
    conn = get_connection()
    with t1:
        df_p = pd.read_sql("SELECT * FROM produits", conn)
        st.dataframe(df_p, use_container_width=True)
    with t2:
        p_sel = st.selectbox("Produit", df_p['nom'].tolist() if not df_p.empty else [])
        q_p = st.number_input("Quantité à ajouter", min_value=1)
        if st.button("Ajouter"):
            conn.execute("UPDATE produits SET qte = qte + ? WHERE nom = ?", (q_p, p_sel))
            conn.commit()
            st.rerun()
    with t3:
        with st.form("n"):
            nom = st.text_input("Nom")
            pa = st.number_input("Prix Achat")
            pv = st.number_input("Prix Vente")
            q = st.number_input("Initial", min_value=0)
            if st.form_submit_button("Créer"):
                conn.execute("INSERT INTO produits (nom, p_achat, p_vente, qte, seuil) VALUES (?,?,?,?,5)", (nom, pa, pv, q))
                conn.commit()
                st.rerun()
    conn.close()

elif menu == "🧾 Factures & Historique":
    st.title("Facturation & Historique 🧾")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes ORDER BY id DESC", conn)
    
    if not df_v.empty:
        st.subheader("Dernières Ventes")
        st.dataframe(df_v, use_container_width=True)
        
        st.divider()
        st.subheader("📄 Générer une Facture")
        col_v, col_c = st.columns(2)
        
        v_id = col_v.selectbox("Sélectionner la vente (ID)", df_v['id'].tolist())
        v_data = df_v[df_v['id'] == v_id].iloc[0]
        
        status = col_c.radio("Statut du paiement", ["PAYÉ ✅", "NON PAYÉ ❌"])
        client_nom = st.text_input("Nom du Client")
        client_tel = st.text_input("Téléphone Client")
        client_adr = st.text_input("Adresse Client")
        
        if st.checkbox("Prêt pour l'impression ?"):
            # --- DESIGN DE LA FACTURE ---
            st.markdown(f"""
            <div style="border: 2px solid #333; padding: 20px; border-radius: 10px; background-color: white; color: black;">
                <div style="display: flex; justify-content: space-between;">
                    <div style="text-align: left;">
                        <h2 style="margin-bottom:0;">{info_ent['nom']}</h2>
                        <p>📍 {info_ent['adresse']}<br>📞 {info_ent['telephone']}<br>👤 Gérant: {info_ent['gerant']}</p>
                    </div>
                    <div style="text-align: right;">
                        <h3 style="color: grey;">FACTURE #00{v_id}</h3>
                        <p><b>Client :</b> {client_nom}<br>📞 {client_tel}<br>📍 {client_adr}</p>
                    </div>
                </div>
                <hr>
                <table style="width: 100%; text-align: left; border-collapse: collapse;">
                    <tr style="background-color: #eee;">
                        <th style="padding: 10px;">Désignation</th>
                        <th>Quantité</th>
                        <th>Prix Unitaire</th>
                        <th>Total</th>
                    </tr>
                    <tr>
                        <td style="padding: 10px;">{v_data['nom_prod']}</td>
                        <td>{v_data['qte_v']}</td>
                        <td>{v_data['total']/v_data['qte_v'] if v_data['qte_v'] > 0 else 0:,.0f} {info_ent['devise']}</td>
                        <td><b>{v_data['total']:,.0f} {info_ent['devise']}</b></td>
                    </tr>
                </table>
                <hr>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <p style="font-size: 1.2em;">Statut : <b>{status}</b></p>
                        <p><i>{info_ent['message_recu']}</i></p>
                    </div>
                    <div style="text-align: center;">
                        <div style="border: 2px dashed #ccc; width: 150px; height: 100px; line-height: 100px; color: #ccc;">
                            CACHET ICI
                        </div>
                    </div>
                </div>
                <p style="font-size: 0.8em; text-align: center; margin-top: 20px;">Facture générée le {datetime.now().strftime('%d/%m/%Y à %H:%M')} par VenteUp</p>
            </div>
            """, unsafe_allow_html=True)
            st.button("🖨️ Lancer l'impression (Navigateur)")
    conn.close()

elif menu == "⚙️ Paramètres":
    st.title("Paramètres ⚙️")
    with st.form("p"):
        n_nom = st.text_input("Nom Boutique", value=info_ent['nom'])
        n_ger = st.text_input("Gérant", value=info_ent['gerant'])
        n_adr = st.text_input("Adresse", value=info_ent['adresse'])
        n_tel = st.text_input("Téléphone", value=info_ent['telephone'])
        n_dev = st.selectbox("Devise", ["FG", "GNF", "$", "CFA"], index=0)
        n_msg = st.text_area("Message Reçu", value=info_ent['message_recu'])
        if st.form_submit_button("Enregistrer"):
            conn = get_connection()
            conn.execute("UPDATE entreprise SET nom=?, gerant=?, adresse=?, telephone=?, devise=?, message_recu=? WHERE id=1",
                         (n_nom, n_ger, n_adr, n_tel, n_dev, n_msg))
            conn.commit()
            st.rerun()
