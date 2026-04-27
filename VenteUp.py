import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="VenteUp Pro v3", layout="wide", page_icon="💎")

def get_connection():
    return sqlite3.connect('venteup_v2.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS produits
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, p_achat REAL, p_vente REAL, qte INTEGER, seuil INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ventes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, produit_id INTEGER, nom_prod TEXT, qte_v INTEGER, date_v TIMESTAMP, total REAL, benef REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS entreprise
                 (id INTEGER PRIMARY KEY, nom TEXT, adresse TEXT, telephone TEXT, devise TEXT, 
                  date_installation TIMESTAMP, est_active INTEGER, code_activation TEXT)''')
    
    if c.execute("SELECT count(*) FROM entreprise").fetchone()[0] == 0:
        maintenant = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO entreprise VALUES (1, 'Ma Boutique', 'Nongo', '+224', 'FG', ?, 0, 'VENTEUP-2026')", (maintenant,))
    conn.commit()
    conn.close()

init_db()

# --- INFOS ENTREPRISE & SECURITE ---
conn = get_connection()
info_ent = pd.read_sql("SELECT * FROM entreprise WHERE id = 1", conn).iloc[0]
conn.close()

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title(f"💎 {info_ent['nom']}")
    menu = st.radio("Navigation", ["📊 Dashboard", "🛒 Caisse", "📦 Stocks & Appro", "🧾 Historique Ventes", "⚙️ Paramètres"])
    st.divider()
    st.caption("Développé par Issa Diallo")

# --- DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("Tableau de Bord")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes", conn)
    df_p = pd.read_sql("SELECT * FROM produits", conn)
    conn.close()

    col1, col2, col3 = st.columns(3)
    ca = df_v['total'].sum() if not df_v.empty else 0
    be = df_v['benef'].sum() if not df_v.empty else 0
    col1.metric("Chiffre d'Affaire", f"{ca:,.0f} {info_ent['devise']}")
    col2.metric("Bénéfice Net", f"{be:,.0f} {info_ent['devise']}")
    
    alertes = df_p[df_p['qte'] <= df_p['seuil']] if not df_p.empty else pd.DataFrame()
    col3.metric("Alertes Stock", len(alertes), delta=f"{len(alertes)} à racheter" if len(alertes)>0 else None, delta_color="inverse")

# --- CAISSE (VENTE) ---
elif menu == "🛒 Caisse":
    st.title("Nouvelle Vente")
    conn = get_connection()
    prods = pd.read_sql("SELECT * FROM produits WHERE qte > 0", conn)
    if not prods.empty:
        with st.form("vente"):
            p_nom = st.selectbox("Sélectionner le produit", prods['nom'].tolist())
            qte_v = st.number_input("Quantité", min_value=1, step=1)
            if st.form_submit_button("Valider la vente", type="primary"):
                p_info = prods[prods['nom'] == p_nom].iloc[0]
                total = qte_v * p_info['p_vente']
                benef = (p_info['p_vente'] - p_info['p_achat']) * qte_v
                c = conn.cursor()
                c.execute("INSERT INTO ventes (produit_id, nom_prod, qte_v, date_v, total, benef) VALUES (?,?,?,?,?,?)",
                          (int(p_info['id']), p_nom, qte_v, datetime.now().strftime("%d/%m %H:%M"), total, benef))
                c.execute("UPDATE produits SET qte = qte - ? WHERE id = ?", (qte_v, int(p_info['id'])))
                conn.commit()
                st.success("Vente enregistrée !")
                st.rerun()
    else:
        st.warning("Stock vide.")
    conn.close()

# --- STOCKS & APPROVISIONNEMENT ---
elif menu == "📦 Stocks & Appro":
    st.title("Gestion des Stocks")
    t1, t2, t3 = st.tabs(["Inventaire", "Réapprovisionner", "Nouveau Produit"])

    with t1: # Liste et Suppression
        conn = get_connection()
        df_p = pd.read_sql("SELECT * FROM produits", conn)
        st.dataframe(df_p, use_container_width=True)
        st.subheader("Supprimer un produit")
        id_del = st.selectbox("ID du produit à retirer", df_p['id'].tolist() if not df_p.empty else [])
        if st.button("Supprimer définitivement", type="secondary"):
            conn.execute("DELETE FROM produits WHERE id = ?", (id_del,))
            conn.commit()
            st.rerun()
        conn.close()

    with t2: # Réappro
        st.subheader("Ajouter du stock à un produit existant")
        conn = get_connection()
        p_list = pd.read_sql("SELECT id, nom FROM produits", conn)
        if not p_list.empty:
            with st.form("appro"):
                p_choice = st.selectbox("Produit", p_list['nom'].tolist())
                plus_qte = st.number_input("Quantité reçue", min_value=1)
                if st.form_submit_button("Mettre à jour le stock"):
                    conn.execute("UPDATE produits SET qte = qte + ? WHERE nom = ?", (plus_qte, p_choice))
                    conn.commit()
                    st.success(f"Stock de {p_choice} mis à jour !")
        conn.close()

    with t3: # Création
        with st.form("new"):
            n = st.text_input("Désignation")
            c1, c2 = st.columns(2)
            pa = c1.number_input("Prix Achat")
            pv = c2.number_input("Prix Vente")
            q = st.number_input("Stock Initial", min_value=0)
            s = st.number_input("Seuil Alerte", value=5)
            if st.form_submit_button("Créer le produit"):
                conn = get_connection()
                conn.execute("INSERT INTO produits (nom, p_achat, p_vente, qte, seuil) VALUES (?,?,?,?,?)", (n, pa, pv, q, s))
                conn.commit()
                conn.close()
                st.rerun()

# --- HISTORIQUE & ANNULATION ---
elif menu == "🧾 Historique Ventes":
    st.title("Historique des Ventes")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes ORDER BY id DESC", conn)
    if not df_v.empty:
        st.dataframe(df_v, use_container_width=True)
        st.subheader("Annuler une vente (Erreur de caisse)")
        v_id = st.number_input("Entrez l'ID de la vente à supprimer", min_value=1, step=1)
        if st.button("Annuler cette vente"):
            # On récupère les infos pour remettre en stock
            v_info = conn.execute("SELECT produit_id, qte_v FROM ventes WHERE id = ?", (int(v_id),)).fetchone()
            if v_info:
                conn.execute("UPDATE produits SET qte = qte + ? WHERE id = ?", (v_info[1], v_info[0]))
                conn.execute("DELETE FROM ventes WHERE id = ?", (int(v_id),))
                conn.commit()
                st.success("Vente annulée et stock rétabli !")
                st.rerun()
    conn.close()

# --- PARAMETRES ---
elif menu == "⚙️ Paramètres":
    st.title("Paramètres")
    with st.form("set"):
        new_nom = st.text_input("Nom", value=info_ent['nom'])
        new_tel = st.text_input("Contact", value=info_ent['telephone'])
        if st.form_submit_button("Sauvegarder"):
            conn = get_connection()
            conn.execute("UPDATE entreprise SET nom=?, telephone=? WHERE id=1", (new_nom, new_tel))
            conn.commit()
            conn.close()
            st.rerun()
