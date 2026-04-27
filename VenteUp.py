import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="VenteUp | Smart Management", layout="wide", page_icon="🚀")

# Style CSS personnalisé pour une interface "Premium"
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- GESTION DE LA BASE DE DONNÉES ---
def get_connection():
    return sqlite3.connect('venteup.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Table Produits
    c.execute('''CREATE TABLE IF NOT EXISTS produits
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, p_achat REAL, p_vente REAL, qte INTEGER, seuil INTEGER)''')
    # Table Ventes
    c.execute('''CREATE TABLE IF NOT EXISTS ventes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, produit_id INTEGER, qte_vendue INTEGER, date_v TIMESTAMP, total REAL, benef REAL)''')
    # Table Entreprise & Sécurité (Verrouillage 3 jours)
    c.execute('''CREATE TABLE IF NOT EXISTS entreprise
                 (id INTEGER PRIMARY KEY, nom TEXT, adresse TEXT, telephone TEXT, devise TEXT, 
                  date_installation TIMESTAMP, est_active INTEGER, code_activation TEXT)''')
    
    # Initialisation de la boutique (si vide)
    c.execute("SELECT count(*) FROM entreprise")
    if c.fetchone()[0] == 0:
        maintenant = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Le code d'activation par défaut est 'VENTEUP-2026'
        c.execute("""INSERT INTO entreprise (id, nom, adresse, telephone, devise, date_installation, est_active, code_activation) 
                     VALUES (1, 'Ma Boutique', 'Quartier Nongo', '+224', 'FG', ?, 0, 'VENTEUP-2026')""", (maintenant,))
    conn.commit()
    conn.close()

init_db()

# --- CHARGEMENT DES DONNÉES DE SÉCURITÉ ---
conn = get_connection()
info_ent = pd.read_sql("SELECT * FROM entreprise WHERE id = 1", conn).iloc[0]
conn.close()

# Calcul du délai de 3 jours
date_inst = datetime.strptime(info_ent['date_installation'], "%Y-%m-%d %H:%M:%S")
jours_restants = 3 - (datetime.now() - date_inst).days
essai_expire = jours_restants <= 0
est_active = info_ent['est_active'] == 1

# --- ECRAN DE VERROUILLAGE (SI EXPIRE) ---
if essai_expire and not est_active:
    st.error("🚨 Période d'essai terminée")
    st.title("Application Verrouillée 🔒")
    st.write("Votre période d'utilisation gratuite de 3 jours a pris fin.")
    st.info("Veuillez contacter Issa Diallo pour obtenir votre clé d'activation.")
    
    code_saisi = st.text_input("Clé d'activation", type="password", placeholder="Entrez la clé ici...")
    if st.button("Activer la version complète"):
        if code_saisi == info_ent['code_activation']:
            conn = get_connection()
            c = conn.cursor()
            c.execute("UPDATE entreprise SET est_active = 1 WHERE id = 1")
            conn.commit()
            conn.close()
            st.success("Activation réussie ! Profitez de VenteUp.")
            st.rerun()
        else:
            st.error("Clé invalide. Contactez l'administrateur.")
    st.stop()

# --- INTERFACE PRINCIPALE ---
with st.sidebar:
    st.title(f"🏠 {info_ent['nom']}")
    if not est_active:
        st.warning(f"⏳ Essai : {jours_restants}j restants")
    st.divider()
    menu = st.radio("Navigation", ["📈 Dashboard", "💸 Caisse de Vente", "📦 Inventaire", "⚙️ Paramètres"])
    st.divider()
    st.caption(f"VenteUp v2.0 | {info_ent['telephone']}")

if menu == "📈 Dashboard":
    st.title("Performance de la Boutique 📊")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes", conn)
    df_p = pd.read_sql("SELECT * FROM produits", conn)
    conn.close()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ca = df_v['total'].sum() if not df_v.empty else 0
        st.metric("Chiffre d'Affaires", f"{ca:,.0f} {info_ent['devise']}")
    with c2:
        be = df_v['benef'].sum() if not df_v.empty else 0
        st.metric("Bénéfice Net", f"{be:,.0f} {info_ent['devise']}")
    with c3:
        st.metric("Ventes", len(df_v))
    with c4:
        alertes = len(df_p[df_p['qte'] <= df_p['seuil']])
        st.metric("Stock Bas", alertes, delta_color="inverse" if alertes > 0 else "normal")

    if not df_v.empty:
        st.subheader("Dernières Ventes")
        st.dataframe(df_v.sort_values(by='date_v', ascending=False).head(10), use_container_width=True)

elif menu == "💸 Caisse de Vente":
    st.title("Caisse Rapide 🛒")
    conn = get_connection()
    prods = pd.read_sql("SELECT * FROM produits WHERE qte > 0", conn)
    
    if not prods.empty:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            with st.container(border=True):
                produit_nom = st.selectbox("Produit", prods['nom'].tolist())
                qte_v = st.number_input("Quantité", min_value=1, step=1)
                
                info = prods[prods['nom'] == produit_nom].iloc[0]
                total_p = qte_v * info['p_vente']
                
                st.write(f"## Total : {total_p:,.0f} {info_ent['devise']}")
                if st.button("Valider la Vente", type="primary"):
                    c = conn.cursor()
                    benef = (info['p_vente'] - info['p_achat']) * qte_v
                    c.execute("INSERT INTO ventes (produit_id, qte_vendue, date_v, total, benef) VALUES (?,?,?,?,?)",
                              (int(info['id']), qte_v, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total_p, benef))
                    c.execute("UPDATE produits SET qte = qte - ? WHERE id = ?", (qte_v, int(info['id'])))
                    conn.commit()
                    st.success(f"Vente validée ! ({produit_nom})")
                    st.balloons()
    else:
        st.warning("Aucun produit disponible en stock.")
    conn.close()

elif menu == "📦 Inventaire":
    st.title("Gestion des Stocks 📦")
    tab_list, tab_add = st.tabs(["Liste des Stocks", "Ajouter un Produit"])
    
    with tab_list:
        conn = get_connection()
        df_inv = pd.read_sql("SELECT id, nom, p_achat, p_vente, qte, seuil FROM produits", conn)
        conn.close()
        st.dataframe(df_inv, use_container_width=True)
        
    with tab_add:
        with st.form("new_product", clear_on_submit=True):
            n = st.text_input("Nom du produit")
            c1, c2 = st.columns(2)
            pa = c1.number_input("Prix d'Achat", min_value=0.0)
            pv = c2.number_input("Prix de Vente", min_value=0.0)
            q = st.number_input("Stock Initial", min_value=1)
            s = st.number_input("Seuil d'Alerte", min_value=1, value=5)
            if st.form_submit_button("Enregistrer"):
                conn = get_connection()
                c = conn.cursor()
                c.execute("INSERT INTO produits (nom, p_achat, p_vente, qte, seuil) VALUES (?,?,?,?,?)", (n, pa, pv, q, s))
                conn.commit()
                conn.close()
                st.success("Produit ajouté !")
                st.rerun()

elif menu == "⚙️ Paramètres":
    st.title("Configuration Boutique ⚙️")
    with st.form("shop_settings"):
        new_nom = st.text_input("Nom de l'Enseigne", value=info_ent['nom'])
        new_adr = st.text_input("Adresse de la Boutique", value=info_ent['adresse'])
        new_tel = st.text_input("Contact Téléphonique", value=info_ent['telephone'])
        new_dev = st.selectbox("Devise Monétaire", ["FG", "GNF", "€", "$", "CFA"], index=0)
        
        if st.form_submit_button("Mettre à jour les informations"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("UPDATE entreprise SET nom=?, adresse=?, telephone=?, devise=? WHERE id=1",
                      (new_nom, new_adr, new_tel, new_dev))
            conn.commit()
            conn.close()
            st.success("Paramètres enregistrés !")
            st.rerun()
