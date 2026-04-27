import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="VenteUp Pro", layout="wide")

# --- INITIALISATION DE LA BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('venteup.db', check_same_thread=False)
    c = conn.cursor()
    # Table des produits
    c.execute('''CREATE TABLE IF NOT EXISTS produits
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nom TEXT, 
                  prix_achat REAL, 
                  prix_vente REAL, 
                  quantite INTEGER, 
                  seuil_alerte INTEGER)''')
    # Table des ventes
    c.execute('''CREATE TABLE IF NOT EXISTS ventes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  produit_id INTEGER, 
                  quantite_vendue INTEGER, 
                  date_vente TIMESTAMP, 
                  total_vente REAL, 
                  benefice_vente REAL,
                  FOREIGN KEY(produit_id) REFERENCES produits(id))''')
    conn.commit()
    conn.close()

# --- FONCTIONS UTILITAIRES ---
def get_db_connection():
    return sqlite3.connect('venteup.db', check_same_thread=False)

# --- LOGIQUE DE L'APPLICATION ---
init_db()

st.sidebar.title("💰 VenteUp Menu")
menu = st.sidebar.radio("Navigation", ["Tableau de Bord", "Ventes", "Stock/Inventaire"])

if menu == "Tableau de Bord":
    st.title("📊 Performance Commerciale")
    conn = get_db_connection()
    df_ventes = pd.read_sql("SELECT * FROM ventes", conn)
    df_produits = pd.read_sql("SELECT * FROM produits", conn)
    conn.close()

    # Indicateurs (KPIs)
    col1, col2, col3 = st.columns(3)
    with col1:
        ca_total = df_ventes['total_vente'].sum() if not df_ventes.empty else 0
        st.metric("Chiffre d'Affaires", f"{ca_total:,.0f} GNf")
    with col2:
        ben_total = df_ventes['benefice_vente'].sum() if not df_ventes.empty else 0
        st.metric("Bénéfice Net", f"{ben_total:,.0f} GNf")
    with col3:
        alertes = len(df_produits[df_produits['quantite'] <= df_produits['seuil_alerte']])
        st.metric("Ruptures de stock", alertes, delta_color="inverse" if alertes > 0 else "normal")

    if not df_ventes.empty:
        st.subheader("Historique des ventes")
        st.dataframe(df_ventes.sort_values(by='date_vente', ascending=False), use_container_width=True)

elif menu == "Ventes":
    st.title("🛒 Enregistrer une Vente")
    conn = get_db_connection()
    df_dispo = pd.read_sql("SELECT id, nom, prix_vente, prix_achat, quantite FROM produits WHERE quantite > 0", conn)
    
    if not df_dispo.empty:
        with st.form("form_vente"):
            choix = st.selectbox("Produit", df_dispo['nom'].tolist())
            qte = st.number_input("Quantité", min_value=1, step=1)
            submit = st.form_submit_button("Valider la vente")

            if submit:
                # Récupérer infos produit sélectionné
                info = df_dispo[df_dispo['nom'] == choix].iloc[0]
                total = qte * info['prix_vente']
                benefice = (info['prix_vente'] - info['prix_achat']) * qte
                
                c = conn.cursor()
                # 1. Enregistrer la vente
                c.execute("INSERT INTO ventes (produit_id, quantite_vendue, date_vente, total_vente, benefice_vente) VALUES (?,?,?,?,?)",
                          (int(info['id']), qte, datetime.now(), total, benefice))
                # 2. Mettre à jour le stock
                c.execute("UPDATE produits SET quantite = quantite - ? WHERE id = ?", (qte, int(info['id'])))
                conn.commit()
                st.success(f"Vente de {choix} enregistrée !")
    else:
        st.warning("L'inventaire est vide. Ajoutez des produits d'abord.")
    conn.close()

elif menu == "Stock/Inventaire":
    st.title("📦 Gestion des Stocks")
    
    # Formulaire d'ajout
    with st.expander("➕ Ajouter un nouveau produit"):
        with st.form("ajout_produit"):
            nom = st.text_input("Désignation")
            c1, c2 = st.columns(2)
            pa = c1.number_input("Prix d'Achat", min_value=0)
            pv = c2.number_input("Prix de Vente", min_value=0)
            qte_init = st.number_input("Quantité initiale", min_value=1)
            seuil = st.number_input("Seuil d'alerte", min_value=1, value=5)
            btn = st.form_submit_button("Enregistrer le produit")
            
            if btn:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("INSERT INTO produits (nom, prix_achat, prix_vente, quantite, seuil_alerte) VALUES (?,?,?,?,?)",
                          (nom, pa, pv, qte_init, seuil))
                conn.commit()
                conn.close()
                st.success("Produit ajouté !")
                st.rerun()

    # Affichage de l'inventaire
    conn = get_db_connection()
    df_inv = pd.read_sql("SELECT * FROM produits", conn)
    conn.close()
    st.subheader("État des stocks")
    st.dataframe(df_inv, use_container_width=True)
