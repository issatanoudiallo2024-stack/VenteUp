import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="VenteUp Elite Pro", layout="wide", page_icon="💎")

def get_connection():
    return sqlite3.connect('venteup_v8.db', check_same_thread=False)

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
    ### Contactez le développeur pour débloquer :
    
    👨‍💻 **Issa Diallo**
    📞 **WhatsApp :** [+224 610 51 89 73](https://wa.me/224610518973)
    📧 **Email :** Issatanoudiallo2024@gmail.com
    """)
    code = st.text_input("Clé d'activation", type="password")
    if st.button("Activer"):
        if code == info_ent['code_activation']:
            conn = get_connection()
            conn.execute("UPDATE entreprise SET est_active = 1 WHERE id = 1")
            conn.commit()
            st.rerun()
    st.stop()

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title(f"🏬 {info_ent['nom']}")
    st.write(f"👤 Gérant : **{info_ent['gerant']}**")
    menu = st.radio("Menu", ["📊 Dashboard", "🛒 Caisse", "📦 Stocks", "🧾 Factures & Historique", "⚙️ Paramètres"])
    st.divider()
    st.caption("🛠️ **Support Technique**")
    st.caption("Issa Diallo : 610 51 89 73")
    st.caption("Issatanoudiallo2024@gmail.com")

# --- DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("Performance Commerciale 📊")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes", conn)
    df_p = pd.read_sql("SELECT * FROM produits", conn)
    conn.close()
    c1, c2, c3 = st.columns(3)
    c1.metric("CA Total", f"{df_v['total'].sum() if not df_v.empty else 0:,.0f} {info_ent['devise']}")
    c2.metric("Bénéfice", f"{df_v['benef'].sum() if not df_v.empty else 0:,.0f} {info_ent['devise']}")
    alertes = len(df_p[df_p['qte'] <= df_p['seuil']]) if not df_p.empty else 0
    c3.metric("Alertes Stock", alertes)

# --- CAISSE ---
elif menu == "🛒 Caisse":
    st.title("Vente Rapide 🛒")
    conn = get_connection()
    prods = pd.read_sql("SELECT * FROM produits WHERE qte > 0", conn)
    if not prods.empty:
        with st.form("vente"):
            p_nom = st.selectbox("Produit", prods['nom'].tolist())
            qte_v = st.number_input("Quantité", min_value=1, step=1)
            if st.form_submit_button("Ajouter à la vente"):
                p_info = prods[prods['nom'] == p_nom].iloc[0]
                total = qte_v * p_info['p_vente']
                benef = (p_info['p_vente'] - p_info['p_achat']) * qte_v
                c = conn.cursor()
                c.execute("INSERT INTO ventes (produit_id, nom_prod, qte_v, date_v, total, benef) VALUES (?,?,?,?,?,?)",
                          (int(p_info['id']), p_nom, qte_v, datetime.now().strftime("%d/%m/%Y %H:%M"), total, benef))
                c.execute("UPDATE produits SET qte = qte - ? WHERE id = ?", (qte_v, int(p_info['id'])))
                conn.commit()
                st.success("Vente enregistrée !")
    conn.close()

# --- STOCKS ---
elif menu == "📦 Stocks":
    st.title("Gestion Stocks 📦")
    t1, t2 = st.tabs(["Inventaire", "Nouveau Produit"])
    conn = get_connection()
    with t1:
        df_p = pd.read_sql("SELECT * FROM produits", conn)
        st.dataframe(df_p, use_container_width=True)
    with t2:
        with st.form("n"):
            nom = st.text_input("Nom")
            pa = st.number_input("Prix Achat")
            pv = st.number_input("Prix Vente")
            q = st.number_input("Stock initial")
            if st.form_submit_button("Créer"):
                conn.execute("INSERT INTO produits (nom, p_achat, p_vente, qte, seuil) VALUES (?,?,?,?,5)", (nom, pa, pv, q))
                conn.commit()
                st.rerun()
    conn.close()

# --- FACTURATION ---
elif menu == "🧾 Factures & Historique":
    st.title("Facturation Professionnelle 🧾")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes ORDER BY id DESC", conn)
    
    if not df_v.empty:
        selected_ids = st.multiselect("Sélectionner les articles (ID)", df_v['id'].tolist())
        
        if selected_ids:
            facture_items = df_v[df_v['id'].isin(selected_ids)]
            st.divider()
            
            # Informations Client
            col1, col2 = st.columns(2)
            c_nom = col1.text_input("Nom du Client")
            c_email = col2.text_input("Email du Client")
            c_tel = col1.text_input("Téléphone Client")
            c_adr = col2.text_input("Adresse Client")
            status = st.radio("État du paiement", ["PAYÉ ✅", "NON PAYÉ ❌"], horizontal=True)
            
            if st.button("Générer la Facture"):
                total_gen = facture_items['total'].sum()
                
                html = f"""
                <div style="border: 2px solid #000; padding: 25px; background-color: #fff; color: #000; font-family: sans-serif;">
                    <div style="display: flex; justify-content: space-between; border-bottom: 2px solid #1a73e8; padding-bottom: 10px;">
                        <div>
                            <h2 style="margin:0; color:#1a73e8;">{info_ent['nom']}</h2>
                            <p style="margin:2px;">📍 {info_ent['adresse']}</p>
                            <p style="margin:2px;">📞 {info_ent['telephone']}</p>
                            <p style="margin:2px;">📧 {info_ent['email']}</p>
                        </div>
                        <div style="text-align: right;">
                            <h2 style="margin:0;">FACTURE</h2>
                            <p style="margin:2px;"><b>Client :</b> {c_nom}</p>
                            <p style="margin:2px;">📍 {c_adr}</p>
                            <p style="margin:2px;">📞 {c_tel}</p>
                            <p style="margin:2px;">📧 {c_email}</p>
                        </div>
                    </div>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                        <thead>
                            <tr style="background-color: #f8f9fa;">
                                <th style="border: 1px solid #ddd; padding: 8px;">N°</th>
                                <th style="border: 1px solid #ddd; padding: 8px;">Désignation</th>
                                <th style="border: 1px solid #ddd; padding: 8px;">Qté</th>
                                <th style="border: 1px solid #ddd; padding: 8px;">P. Unit.</th>
                                <th style="border: 1px solid #ddd; padding: 8px;">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                for i, row in enumerate(facture_items.itertuples(), 1):
                    pu = row.total / row.qte_v
                    html += f"""
                            <tr>
                                <td style="border: 1px solid #ddd; padding: 8px; text-align:center;">{i}</td>
                                <td style="border: 1px solid #ddd; padding: 8px;">{row.nom_prod}</td>
                                <td style="border: 1px solid #ddd; padding: 8px; text-align:center;">{row.qte_v}</td>
                                <td style="border: 1px solid #ddd; padding: 8px; text-align:right;">{pu:,.0f}</td>
                                <td style="border: 1px solid #ddd; padding: 8px; text-align:right;">{row.total:,.0f}</td>
                            </tr>
                    """
                html += f"""
                        </tbody>
                    </table>
                    <div style="text-align: right; margin-top: 20px;">
                        <h3>Total Net : {total_gen:,.0f} {info_ent['devise']}</h3>
                        <p>Statut : <b>{status}</b></p>
                    </div>
                    <div style="margin-top: 40px; display: flex; justify-content: space-between;">
                        <p><i>{info_ent['message_recu']}</i></p>
                        <div style="border: 1px solid #000; width: 140px; height: 80px; text-align: center; line-height: 80px;">CACHET</div>
                    </div>
                    <div style="text-align: center; margin-top: 30px; font-size: 11px; color: #666;">
                        Conçu par Issa Diallo | +224 610 51 89 73 | Issatanoudiallo2024@gmail.com
                    </div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)
    conn.close()

# --- PARAMÈTRES ---
elif menu == "⚙️ Paramètres":
    st.title("Paramètres ⚙️")
    with st.form("p"):
        n_nom = st.text_input("Nom Boutique", value=info_ent['nom'])
        n_ger = st.text_input("Gérant", value=info_ent['gerant'])
        n_adr = st.text_input("Adresse Physique", value=info_ent['adresse'])
        n_tel = st.text_input("Téléphone", value=info_ent['telephone'])
        n_eml = st.text_input("Email Boutique", value=info_ent['email'])
        n_dev = st.selectbox("Devise", ["FG", "GNF", "CFA", "$"], index=0)
        n_msg = st.text_area("Message Reçu", value=info_ent['message_recu'])
        if st.form_submit_button("Mettre à jour"):
            conn = get_connection()
            conn.execute("UPDATE entreprise SET nom=?, gerant=?, adresse=?, telephone=?, email=?, devise=?, message_recu=? WHERE id=1",
                         (n_nom, n_ger, n_adr, n_tel, n_eml, n_dev, n_msg))
            conn.commit()
            st.success("Paramètres enregistrés !")
            st.rerun()
