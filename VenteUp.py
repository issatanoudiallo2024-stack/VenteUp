import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="VenteUp Pro", layout="wide", page_icon="🚀")

# CSS pour l'interface
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetric"] { background-color: #ffffff; border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

def get_connection():
    # On utilise 'venteup_v2.db' pour corriger le bug de colonne (KeyError)
    return sqlite3.connect('venteup_v2.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS produits
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, p_achat REAL, p_vente REAL, qte INTEGER, seuil INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ventes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, produit_id INTEGER, qte_vendue INTEGER, date_v TIMESTAMP, total REAL, benef REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS entreprise
                 (id INTEGER PRIMARY KEY, nom TEXT, adresse TEXT, telephone TEXT, devise TEXT, 
                  date_installation TIMESTAMP, est_active INTEGER, code_activation TEXT)''')
    
    c.execute("SELECT count(*) FROM entreprise")
    if c.fetchone()[0] == 0:
        maintenant = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""INSERT INTO entreprise (id, nom, adresse, telephone, devise, date_installation, est_active, code_activation) 
                     VALUES (1, 'Ma Boutique', 'Nongo, Conakry', '+224', 'FG', ?, 0, 'VENTEUP-2026')""", (maintenant,))
    conn.commit()
    conn.close()

init_db()

# --- SECURITE ET VERROUILLAGE ---
conn = get_connection()
info_ent = pd.read_sql("SELECT * FROM entreprise WHERE id = 1", conn).iloc[0]
conn.close()

date_inst = datetime.strptime(info_ent['date_installation'], "%Y-%m-%d %H:%M:%S")
jours_restants = 3 - (datetime.now() - date_inst).days
essai_expire = jours_restants <= 0
est_active = info_ent['est_active'] == 1

if essai_expire and not est_active:
    st.error("🚨 Essai terminé")
    st.title("Application Verrouillée")
    code = st.text_input("Code d'activation", type="password")
    if st.button("Activer"):
        if code == info_ent['code_activation']:
            conn = get_connection()
            conn.execute("UPDATE entreprise SET est_active = 1 WHERE id = 1")
            conn.commit()
            conn.close()
            st.success("Activé !")
            st.rerun()
    st.stop()

# --- INTERFACE ---
with st.sidebar:
    st.title(f"🏠 {info_ent['nom']}")
    if not est_active:
        st.warning(f"⏳ {jours_restants} jours restants")
    menu = st.radio("Menu", ["📈 Dashboard", "💸 Caisse", "📦 Inventaire", "⚙️ Paramètres"])

if menu == "📈 Dashboard":
    st.title("Performance 📊")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes", conn)
    df_p = pd.read_sql("SELECT * FROM produits", conn)
    conn.close()

    c1, c2, c3 = st.columns(3)
    c1.metric("CA", f"{df_v['total'].sum() if not df_v.empty else 0:,.0f} {info_ent['devise']}")
    c2.metric("Bénéfice", f"{df_v['benef'].sum() if not df_v.empty else 0:,.0f} {info_ent['devise']}")
    alertes = len(df_p[df_p['qte'] <= df_p['seuil']]) if not df_p.empty else 0
    c3.metric("Alertes Stock", alertes)

    if not df_v.empty:
        st.subheader("Ventes récentes")
        st.dataframe(df_v.tail(10), use_container_width=True)

elif menu == "💸 Caisse":
    st.title("Vendre 🛒")
    conn = get_connection()
    prods = pd.read_sql("SELECT * FROM produits WHERE qte > 0", conn)
    if not prods.empty:
        with st.container(border=True):
            choix = st.selectbox("Produit", prods['nom'].tolist())
            qte_v = st.number_input("Quantité", min_value=1)
            info = prods[prods['nom'] == choix].iloc[0]
            if st.button("Valider la vente", type="primary"):
                total = qte_v * info['p_vente']
                benef = (info['p_vente'] - info['p_achat']) * qte_v
                c = conn.cursor()
                c.execute("INSERT INTO ventes (produit_id, qte_vendue, date_v, total, benef) VALUES (?,?,?,?,?)",
                          (int(info['id']), qte_v, datetime.now(), total, benef))
                c.execute("UPDATE produits SET qte = qte - ? WHERE id = ?", (qte_v, int(info['id'])))
                conn.commit()
                st.success("Vendu !")
    conn.close()

elif menu == "📦 Inventaire":
    st.title("Stocks 📦")
    t1, t2 = st.tabs(["Liste", "Ajouter"])
    with t1:
        conn = get_connection()
        st.dataframe(pd.read_sql("SELECT * FROM produits", conn), use_container_width=True)
        conn.close()
    with t2:
        with st.form("add"):
            n = st.text_input("Nom")
            pa = st.number_input("Prix Achat")
            pv = st.number_input("Prix Vente")
            q = st.number_input("Stock", min_value=1)
            if st.form_submit_button("Ajouter"):
                conn = get_connection()
                conn.execute("INSERT INTO produits (nom, p_achat, p_vente, qte, seuil) VALUES (?,?,?,?,5)", (n, pa, pv, q))
                conn.commit()
                conn.close()
                st.rerun()

elif menu == "⚙️ Paramètres":
    st.title("Paramètres ⚙️")
    with st.form("settings"):
        nom = st.text_input("Nom Boutique", value=info_ent['nom'])
        tel = st.text_input("Téléphone", value=info_ent['telephone'])
        dev = st.selectbox("Devise", ["FG", "GNF", "$"], index=0)
        if st.form_submit_button("Sauvegarder"):
            conn = get_connection()
            conn.execute("UPDATE entreprise SET nom=?, telephone=?, devise=? WHERE id=1", (nom, tel, dev))
            conn.commit()
            conn.close()
            st.rerun()
