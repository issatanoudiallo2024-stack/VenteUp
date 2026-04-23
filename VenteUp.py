import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Configuration de la page avec une icône de graphique
st.set_page_config(
    page_title="VenteUp Pro", 
    page_icon="💹", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- STYLE CSS POUR MOBILE ---
st.markdown("""
    <style>
    .main { background-color: #fafafa; }
    div.stButton > button:first-child {
        background-color: #007bff;
        color: white;
        border-radius: 10px;
        height: 3em;
        width: 100%;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

def init_db():
    conn = sqlite3.connect("venteup_data.db")
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY, nom TEXT, p_achat INTEGER, p_vente INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY, nom_p TEXT, gain INTEGER, prix_vendu INTEGER, date TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- NAVIGATION ---
with st.sidebar:
    st.title("🚀 VenteUp Menu")
    nom_boutique = st.text_input("Nom de l'établissement", value="Ma Boutique")
    st.divider()
    conn = sqlite3.connect("venteup_data.db")
    res = conn.execute("SELECT SUM(gain) FROM ventes").fetchone()
    total = res[0] if res[0] else 0
    st.metric("Profit Réalisé", f"{total:,} GNF".replace(',', ' '))
    conn.close()
    st.caption("© 2026 VenteUp Pro | V1.2")

st.header(f"💹 {nom_boutique}")

tab1, tab2, tab3 = st.tabs(["💰 VENDRE", "📋 JOURNAL", "📦 STOCK"])

with tab1:
    conn = sqlite3.connect("venteup_data.db")
    produits = pd.read_sql_query("SELECT * FROM stock", conn)
    if produits.empty:
        st.info("Ajoutez des articles dans l'onglet STOCK pour commencer.")
    else:
        for index, row in produits.iterrows():
            with st.expander(f"🛒 {row['nom']} - {row['p_vente']} GNF"):
                p_nego = st.number_input(f"Prix final", value=int(row['p_vente']), key=f"v_{row['id']}")
                if st.button(f"Enregistrer la vente", key=f"btn_{row['id']}"):
                    gain = p_nego - row['p_achat']
                    date = datetime.now().strftime("%d/%m %H:%M")
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO ventes (nom_p, gain, prix_vendu, date) VALUES (?, ?, ?, ?)", 
                                 (row['nom'], gain, p_nego, date))
                    conn.commit()
                    st.success("Vente enregistrée !")
                    st.rerun()
    conn.close()

with tab2:
    conn = sqlite3.connect("venteup_data.db")
    df_h = pd.read_sql_query("SELECT id, nom_p as Art, prix_vendu as Prix, gain as Gain, date FROM ventes ORDER BY id DESC", conn)
    if not df_h.empty:
        st.dataframe(df_h, use_container_width=True, hide_index=True)
        # Option de téléchargement pour le patron
        csv = df_h.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Télécharger le rapport (Excel/CSV)", data=csv, file_name="ventes_venteup.csv", mime="text/csv")
    conn.close()

with tab3:
    with st.form("ajout"):
        st.write("### Nouvel Article")
        n = st.text_input("Désignation")
        pa = st.number_input("Coût d'achat", min_value=0)
        pv = st.number_input("Prix de vente public", min_value=0)
        if st.form_submit_button("AJOUTER AU STOCK"):
            if n and pv:
                conn = sqlite3.connect("venteup_data.db")
                conn.execute("INSERT INTO stock (nom, p_achat, p_vente) VALUES (?, ?, ?)", (n, pa, pv))
                conn.commit()
                conn.close()
                st.success("Article ajouté !")
                st.rerun()