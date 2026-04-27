import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="VenteUp Elite Pro", layout="wide", page_icon="💎")

def get_connection():
    # On reste sur v6 pour la stabilité
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

# --- SÉCURITÉ & COORDONNÉES ISSA DIALLO ---
date_inst = datetime.strptime(info_ent['date_installation'], "%Y-%m-%d %H:%M:%S")
jours_restants = 3 - (datetime.now() - date_inst).days
est_active = info_ent['est_active'] == 1

if jours_restants <= 0 and not est_active:
    st.error("🚨 Période d'essai terminée")
    st.title("🔒 Application Verrouillée")
    st.markdown(f"""
    ### Pour continuer, veuillez contacter le développeur :
    
    👨‍💻 **Issa Diallo**
    📞 **WhatsApp & Direct :** [+224 610 51 89 73](https://wa.me/224610518973)
    📧 **Email :** Issatanoudiallo2024@gmail.com
    
    *Demandez votre clé d'activation pour débloquer définitivement votre gestion.*
    """)
    st.divider()
    code = st.text_input("Clé d'activation", type="password")
    if st.button("Activer"):
        if code == info_ent['code_activation']:
            conn = get_connection()
            conn.execute("UPDATE entreprise SET est_active = 1 WHERE id = 1")
            conn.commit()
            st.success("✅ Activé !")
            st.rerun()
    st.stop()

# --- NAVIGATION ---
with st.sidebar:
    st.title(f"🏬 {info_ent['nom']}")
    st.write(f"👤 Gérant : **{info_ent['gerant']}**")
    menu = st.radio("Menu", ["📊 Dashboard", "🛒 Caisse", "📦 Stocks & Appro", "🧾 Factures & Historique", "⚙️ Paramètres"])
    st.divider()
    st.write("🛠️ **Support Issa Diallo**")
    st.caption("📞 +224 610 51 89 73")
    st.caption("📧 Issatanoudiallo2024@gmail.com")

# --- DASHBOARD ---
if menu == "📊 Dashboard":
    st.title(f"Tableau de Bord - {info_ent['nom']} 📊")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes", conn)
    df_p = pd.read_sql("SELECT * FROM produits", conn)
    conn.close()
    c1, c2, c3 = st.columns(3)
    c1.metric("Chiffre d'Affaire", f"{df_v['total'].sum() if not df_v.empty else 0:,.0f} {info_ent['devise']}")
    c2.metric("Bénéfice Net", f"{df_v['benef'].sum() if not df_v.empty else 0:,.0f} {info_ent['devise']}")
    alertes = len(df_p[df_p['qte'] <= df_p['seuil']]) if not df_p.empty else 0
    c3.metric("Alertes Stock", alertes)

# --- CAISSE ---
elif menu == "🛒 Caisse":
    st.title("Vente Directe 🛒")
    conn = get_connection()
    prods = pd.read_sql("SELECT * FROM produits WHERE qte > 0", conn)
    if not prods.empty:
        p_nom = st.selectbox("Produit", prods['nom'].tolist())
        qte_v = st.number_input("Quantité", min_value=1, step=1)
        p_info = prods[prods['nom'] == p_nom].iloc[0]
        st.write(f"### Total : {qte_v * p_info['p_vente']:,.0f} {info_ent['devise']}")
        if st.button("Valider la vente", type="primary"):
            total = qte_v * p_info['p_vente']
            benef = (p_info['p_vente'] - p_info['p_achat']) * qte_v
            c = conn.cursor()
            c.execute("INSERT INTO ventes (produit_id, nom_prod, qte_v, date_v, total, benef) VALUES (?,?,?,?,?,?)",
                      (int(p_info['id']), p_nom, qte_v, datetime.now().strftime("%d/%m/%Y %H:%M"), total, benef))
            c.execute("UPDATE produits SET qte = qte - ? WHERE id = ?", (qte_v, int(p_info['id'])))
            conn.commit()
            st.success(f"Vendu ! {info_ent['message_recu']}")
    conn.close()

# --- STOCKS ---
elif menu == "📦 Stocks & Appro":
    st.title("Gestion Stocks 📦")
    t1, t2, t3 = st.tabs(["Inventaire", "Réapprovisionner", "Nouveau"])
    conn = get_connection()
    with t1:
        df_p = pd.read_sql("SELECT * FROM produits", conn)
        st.dataframe(df_p, use_container_width=True)
        id_del = st.number_input("ID à supprimer", min_value=0)
        if st.button("Supprimer Produit"):
            conn.execute("DELETE FROM produits WHERE id=?", (id_del,))
            conn.commit()
            st.rerun()
    with t2:
        if not df_p.empty:
            p_s = st.selectbox("Produit", df_p['nom'].tolist())
            q_a = st.number_input("Quantité reçue", min_value=1)
            if st.button("Ajouter au stock"):
                conn.execute("UPDATE produits SET qte = qte + ? WHERE nom = ?", (q_a, p_s))
                conn.commit()
                st.success("Stock mis à jour")
    with t3:
        with st.form("new"):
            nom = st.text_input("Nom")
            pa = st.number_input("Prix Achat")
            pv = st.number_input("Prix Vente")
            q = st.number_input("Stock initial", min_value=0)
            if st.form_submit_button("Ajouter"):
                conn.execute("INSERT INTO produits (nom, p_achat, p_vente, qte, seuil) VALUES (?,?,?,?,5)", (nom, pa, pv, q))
                conn.commit()
                st.rerun()
    conn.close()

# --- FACTURES & HISTORIQUE ---
elif menu == "🧾 Factures & Historique":
    st.title("Facturation 🧾")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes ORDER BY id DESC", conn)
    if not df_v.empty:
        st.dataframe(df_v, use_container_width=True)
        st.divider()
        st.subheader("📄 Générer Facture")
        col1, col2 = st.columns(2)
        v_id = col1.selectbox("ID Vente", df_v['id'].tolist())
        v_data = df_v[df_v['id'] == v_id].iloc[0]
        status = col2.radio("Statut", ["PAYÉ ✅", "NON PAYÉ ❌"])
        
        c_nom = st.text_input("Client")
        c_tel = st.text_input("Téléphone Client")
        
        if st.checkbox("Voir la facture"):
            st.markdown(f"""
            <div style="border: 2px solid #333; padding: 20px; background-color: white; color: black; border-radius: 10px;">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <h2>{info_ent['nom']}</h2>
                        <p>📍 {info_ent['adresse']}<br>📞 {info_ent['telephone']}</p>
                    </div>
                    <div style="text-align: right;">
                        <h3>FACTURE #00{v_id}</h3>
                        <p><b>Client :</b> {c_nom}<br>📞 {c_tel}</p>
                    </div>
                </div>
                <hr>
                <p>Produit : <b>{v_data['nom_prod']}</b> | Quantité : {v_data['qte_v']}</p>
                <h3>Total : {v_data['total']:,.0f} {info_ent['devise']}</h3>
                <hr>
                <p>Statut : <b>{status}</b></p>
                <div style="border: 1px dashed #ccc; width: 120px; height: 80px; text-align: center; line-height: 80px; float: right;">CACHET</div>
                <div style="clear: both;"></div>
            </div>
            """, unsafe_allow_html=True)

# --- PARAMÈTRES ---
elif menu == "⚙️ Paramètres":
    st.title("Paramètres ⚙️")
    with st.form("p"):
        n_nom = st.text_input("Nom Boutique", value=info_ent['nom'])
        n_ger = st.text_input("Gérant", value=info_ent['gerant'])
        n_adr = st.text_input("Adresse", value=info_ent['adresse'])
        n_tel = st.text_input("Téléphone", value=info_ent['telephone'])
        n_dev = st.selectbox("Devise", ["FG", "GNF", "$", "CFA"], index=0)
        n_msg = st.text_area("Message Reçu", value=info_ent['message_recu'])
        if st.form_submit_button("Sauvegarder"):
            conn = get_connection()
            conn.execute("UPDATE entreprise SET nom=?, gerant=?, adresse=?, telephone=?, devise=?, message_recu=? WHERE id=1",
                         (n_nom, n_ger, n_adr, n_tel, n_dev, n_msg))
            conn.commit()
            st.rerun()
