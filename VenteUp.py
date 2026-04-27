import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="VenteUp Elite Pro", layout="wide", page_icon="💎")

def get_connection():
    return sqlite3.connect('venteup_v3.db', check_same_thread=False)

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
        c.execute("""INSERT INTO entreprise VALUES (1, 'Ma Boutique', 'Conakry', '+224', 'Propriétaire', 'FG', ?, 0, 'VENTEUP-2026', 'Merci !')""", (maintenant,))
    conn.commit()
    conn.close()

init_db()

# --- CHARGEMENT DES PARAMÈTRES ---
conn = get_connection()
info_ent = pd.read_sql("SELECT * FROM entreprise WHERE id = 1", conn).iloc[0]
conn.close()

# --- SÉCURITÉ ---
date_inst = datetime.strptime(info_ent['date_installation'], "%Y-%m-%d %H:%M:%S")
jours_restants = 3 - (datetime.now() - date_inst).days
est_active = info_ent['est_active'] == 1

if jours_restants <= 0 and not est_active:
    st.error("🚨 Période d'essai de 3 jours terminée")
    code = st.text_input("Entrez la clé d'activation", type="password")
    if st.button("Activer l'application"):
        if code == info_ent['code_activation']:
            conn = get_connection()
            conn.execute("UPDATE entreprise SET est_active = 1 WHERE id = 1")
            conn.commit()
            st.success("Application activée avec succès !")
            st.rerun()
    st.stop()

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title(f"🏬 {info_ent['nom']}")
    st.write(f"👤 Gérant : **{info_ent['gerant']}**")
    st.write(f"📍 {info_ent['adresse']}")
    st.divider()
    menu = st.radio("Menu Principal", ["📊 Dashboard", "🛒 Caisse", "📦 Stocks & Appro", "🧾 Historique & Export", "⚙️ Paramètres"])
    st.divider()
    if not est_active:
        st.info(f"⏳ Essai : {jours_restants} jours restants")
    st.caption("Solution VenteUp par Issa Diallo")

# --- DASHBOARD ---
if menu == "📊 Dashboard":
    st.title(f"Tableau de Bord - {info_ent['nom']} 📊")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes", conn)
    df_p = pd.read_sql("SELECT * FROM produits", conn)
    conn.close()

    c1, c2, c3 = st.columns(3)
    ca = df_v['total'].sum() if not df_v.empty else 0
    be = df_v['benef'].sum() if not df_v.empty else 0
    c1.metric("Chiffre d'Affaire", f"{ca:,.0f} {info_ent['devise']}")
    c2.metric("Bénéfice Net", f"{be:,.0f} {info_ent['devise']}")
    alertes = len(df_p[df_p['qte'] <= df_p['seuil']]) if not df_p.empty else 0
    c3.metric("Alertes Stock", alertes, delta_color="inverse" if alertes > 0 else "normal")

# --- CAISSE ---
elif menu == "🛒 Caisse":
    st.title("Vente Directe 🛒")
    conn = get_connection()
    prods = pd.read_sql("SELECT * FROM produits WHERE qte > 0", conn)
    if not prods.empty:
        with st.container(border=True):
            p_nom = st.selectbox("Produit", prods['nom'].tolist())
            qte_v = st.number_input("Quantité", min_value=1, step=1)
            p_info = prods[prods['nom'] == p_nom].iloc[0]
            total = qte_v * p_info['p_vente']
            st.write(f"## Total à payer : {total:,.0f} {info_ent['devise']}")
            if st.button("Valider l'encaissement", type="primary", use_container_width=True):
                benef = (p_info['p_vente'] - p_info['p_achat']) * qte_v
                c = conn.cursor()
                c.execute("INSERT INTO ventes (produit_id, nom_prod, qte_v, date_v, total, benef) VALUES (?,?,?,?,?,?)",
                          (int(p_info['id']), p_nom, qte_v, datetime.now().strftime("%d/%m %H:%M"), total, benef))
                c.execute("UPDATE produits SET qte = qte - ? WHERE id = ?", (qte_v, int(p_info['id'])))
                conn.commit()
                st.success(f"Vendu ! {info_ent['message_recu']}")
                st.balloons()
    conn.close()

# --- STOCKS ---
elif menu == "📦 Stocks & Appro":
    st.title("Gestion des Produits 📦")
    t1, t2, t3 = st.tabs(["Inventaire", "Réapprovisionner", "Nouveau Produit"])
    conn = get_connection()
    with t1:
        df_p = pd.read_sql("SELECT * FROM produits", conn)
        st.dataframe(df_p, use_container_width=True)
        id_del = st.number_input("ID à supprimer", min_value=0, step=1)
        if st.button("❌ Supprimer le produit"):
            conn.execute("DELETE FROM produits WHERE id=?", (id_del,))
            conn.commit()
            st.rerun()
    with t2:
        if not df_p.empty:
            p_sel = st.selectbox("Produit à recharger", df_p['nom'].tolist())
            q_plus = st.number_input("Quantité reçue", min_value=1)
            if st.button("Mettre à jour le stock"):
                conn.execute("UPDATE produits SET qte = qte + ? WHERE nom = ?", (q_plus, p_sel))
                conn.commit()
                st.success("Stock augmenté !")
    with t3:
        with st.form("add"):
            n = st.text_input("Désignation")
            pa = st.number_input("Prix d'achat")
            pv = st.number_input("Prix de vente")
            q = st.number_input("Stock initial", min_value=0)
            s = st.number_input("Seuil alerte", value=5)
            if st.form_submit_button("Créer le produit"):
                conn.execute("INSERT INTO produits (nom, p_achat, p_vente, qte, seuil) VALUES (?,?,?,?,?)", (n, pa, pv, q, s))
                conn.commit()
                st.rerun()
    conn.close()

# --- HISTORIQUE ---
elif menu == "🧾 Historique & Export":
    st.title("Historique 🧾")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes ORDER BY id DESC", conn)
    if not df_v.empty:
        st.dataframe(df_v, use_container_width=True)
        # Export Excel
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            df_v.to_excel(writer, index=False)
        st.download_button("📥 Télécharger Rapport Excel", data=out.getvalue(), file_name="ventes.xlsx")
    conn.close()

# --- PARAMÈTRES AMÉLIORÉS ---
elif menu == "⚙️ Paramètres":
    st.title("Centre de Contrôle ⚙️")
    with st.expander("🏢 Profil de l'Entreprise", expanded=True):
        with st.form("entreprise_form"):
            n_nom = st.text_input("Nom de l'entreprise", value=info_ent['nom'])
            n_ger = st.text_input("Nom du Gérant", value=info_ent['gerant'])
            n_adr = st.text_input("Adresse Physique", value=info_ent['adresse'])
            n_tel = st.text_input("Numéro de téléphone", value=info_ent['telephone'])
            n_dev = st.selectbox("Devise", ["FG", "GNF", "CFA", "$", "€"], index=0)
            n_msg = st.text_area("Message de bienvenue/reçu", value=info_ent['message_recu'])
            if st.form_submit_button("Sauvegarder le profil"):
                conn = get_connection()
                conn.execute("UPDATE entreprise SET nom=?, adresse=?, telephone=?, gerant=?, devise=?, message_recu=? WHERE id=1", 
                             (n_nom, n_adr, n_tel, n_ger, n_dev, n_msg))
                conn.commit()
                st.success("Profil mis à jour !")
                st.rerun()
    
    with st.expander("🔐 Sécurité & Réinitialisation"):
        if st.button("Effacer l'historique des ventes"):
            conn = get_connection()
            conn.execute("DELETE FROM ventes")
            conn.commit()
            st.warning("Historique vidé.")
            st.rerun()
