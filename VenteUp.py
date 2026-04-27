import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="VenteUp Pro", layout="wide", page_icon="💎")

def get_connection():
    return sqlite3.connect('venteup_final_v12.db', check_same_thread=False)

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

# --- SÉCURITÉ & INFOS DÉVELOPPEUR (ISSA DIALLO) ---
date_inst = datetime.strptime(info_ent['date_installation'], "%Y-%m-%d %H:%M:%S")
jours_restants = 3 - (datetime.now() - date_inst).days
est_active = info_ent['est_active'] == 1

if jours_restants <= 0 and not est_active:
    st.error("🚨 Période d'essai terminée")
    st.title("🔒 Application Verrouillée")
    st.markdown(f"""
    ### Contactez le développeur pour débloquer :
    👨‍💻 **Issa Diallo** 📞 **WhatsApp :** +224 610 51 89 73  
    📧 **Email :** Issatanoudiallo2024@gmail.com
    """)
    code = st.text_input("Code d'activation", type="password")
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
    menu = st.radio("Navigation", ["📊 Dashboard", "🛒 Caisse", "📦 Stocks & Appro", "🧾 Factures & Historique", "⚙️ Paramètres"])
    st.divider()
    st.write("🛠️ **Support Technique**")
    st.caption("Issa Diallo : 610 51 89 73")
    st.caption("Issatanoudiallo2024@gmail.com")

# --- DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("Performance 📊")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes", conn)
    df_p = pd.read_sql("SELECT * FROM produits", conn)
    conn.close()
    col1, col2, col3 = st.columns(3)
    col1.metric("CA Total", f"{df_v['total'].sum():,.0f} {info_ent['devise']}")
    col2.metric("Bénéfice", f"{df_v['benef'].sum():,.0f} {info_ent['devise']}")
    alertes = len(df_p[df_p['qte'] <= df_p['seuil']]) if not df_p.empty else 0
    col3.metric("Alertes Stock", alertes)

# --- CAISSE ---
elif menu == "🛒 Caisse":
    st.title("Vente Directe 🛒")
    conn = get_connection()
    prods = pd.read_sql("SELECT * FROM produits WHERE qte > 0", conn)
    if not prods.empty:
        with st.form("vente_form"):
            p_nom = st.selectbox("Produit", prods['nom'].tolist())
            qte_v = st.number_input("Quantité", min_value=1, step=1)
            submit = st.form_submit_button("Enregistrer la vente")
            if submit:
                p_info = prods[prods['nom'] == p_nom].iloc[0]
                total = qte_v * p_info['p_vente']
                benef = (p_info['p_vente'] - p_info['p_achat']) * qte_v
                c = conn.cursor()
                c.execute("INSERT INTO ventes (produit_id, nom_prod, qte_v, date_v, total, benef) VALUES (?,?,?,?,?,?)",
                          (int(p_info['id']), p_nom, qte_v, datetime.now().strftime("%d/%m/%Y %H:%M"), total, benef))
                c.execute("UPDATE produits SET qte = qte - ? WHERE id = ?", (qte_v, int(p_info['id'])))
                conn.commit()
                st.success(f"Vendu : {p_nom} x{qte_v}")
    else:
        st.warning("Aucun produit en stock. Allez dans 'Stocks' pour en ajouter.")
    conn.close()

# --- STOCKS & REAPPRO ---
elif menu == "📦 Stocks & Appro":
    st.title("Gestion des Stocks 📦")
    t1, t2, t3 = st.tabs(["📋 Inventaire", "🔄 Réapprovisionner", "➕ Nouveau Produit"])
    conn = get_connection()
    
    with t1:
        df_p = pd.read_sql("SELECT * FROM produits", conn)
        st.dataframe(df_p, use_container_width=True)
    
    with t2:
        if not df_p.empty:
            p_re = st.selectbox("Produit à recharger", df_p['nom'].tolist())
            q_add = st.number_input("Ajouter quantité", min_value=1)
            if st.button("Confirmer le réapprovisionnement"):
                conn.execute("UPDATE produits SET qte = qte + ? WHERE nom = ?", (q_add, p_re))
                conn.commit()
                st.success("Stock mis à jour !")
                st.rerun()
    
    with t3:
        with st.form("new_prod"):
            n = st.text_input("Désignation")
            pa = st.number_input("Prix Achat")
            pv = st.number_input("Prix Vente")
            q = st.number_input("Stock Initial", min_value=0)
            if st.form_submit_button("Créer le produit"):
                conn.execute("INSERT INTO produits (nom, p_achat, p_vente, qte, seuil) VALUES (?,?,?,?,5)", (n, pa, pv, q))
                conn.commit()
                st.success("Produit ajouté !")
                st.rerun()
    conn.close()

# --- FACTURATION ---
elif menu == "🧾 Factures & Historique":
    st.title("Facturation 🧾")
    conn = get_connection()
    df_v = pd.read_sql("SELECT * FROM ventes ORDER BY id DESC", conn)
    
    if not df_v.empty:
        selected_ids = st.multiselect("Articles pour la facture", df_v['id'].tolist())
        if selected_ids:
            items = df_v[df_v['id'].isin(selected_ids)]
            st.divider()
            c1, c2 = st.columns(2)
            c_nom = c1.text_input("Client")
            c_tel = c2.text_input("Téléphone Client")
            c_adr = c1.text_input("Adresse Client")
            c_eml = c2.text_input("Email Client")
            
            st.subheader("Image du Cachet")
            img_cachet = st.file_uploader("Télécharger votre cachet (PNG/JPG)", type=["png", "jpg", "jpeg"])
            
            if st.button("Afficher la Facture"):
                total_f = items['total'].sum()
                cachet_b64 = ""
                if img_cachet:
                    cachet_b64 = base64.b64encode(img_cachet.getvalue()).decode()
                
                html = f"""
                <div style="border:1px solid #000; padding:20px; background:white; color:black; font-family:Arial;">
                    <div style="display:flex; justify-content:space-between;">
                        <div>
                            <h2 style="color:#1a73e8;">{info_ent['nom']}</h2>
                            <p>{info_ent['adresse']}<br>{info_ent['telephone']}<br>{info_ent['email']}</p>
                        </div>
                        <div style="text-align:right;">
                            <h2>FACTURE</h2>
                            <p><b>Client :</b> {c_nom}<br>{c_adr}<br>{c_tel}</p>
                        </div>
                    </div>
                    <table style="width:100%; border-collapse:collapse; margin-top:10px;">
                        <tr style="background:#f2f2f2; border:1px solid #000;">
                            <th>N°</th><th>Désignation</th><th>Qté</th><th>P.U</th><th>Total</th>
                        </tr>
                """
                for i, r in enumerate(items.itertuples(), 1):
                    html += f"<tr><td style='border:1px solid #ddd; padding:8px; text-align:center;'>{i}</td><td style='border:1px solid #ddd; padding:8px;'>{r.nom_prod}</td><td style='border:1px solid #ddd; padding:8px; text-align:center;'>{r.qte_v}</td><td style='border:1px solid #ddd; padding:8px; text-align:right;'>{r.total/r.qte_v:,.0f}</td><td style='border:1px solid #ddd; padding:8px; text-align:right;'>{r.total:,.0f}</td></tr>"
                
                html += f"""
                    </table>
                    <h3 style="text-align:right;">Total : {total_f:,.0f} {info_ent['devise']}</h3>
                    <div style="margin-top:20px; display:flex; justify-content:space-between;">
                        <p><i>{info_ent['message_recu']}</i></p>
                        <div style="width:150px; height:80px; text-align:center; position:relative;">
                            {f'<img src="data:image/png;base64,{cachet_b64}" style="width:100px;">' if cachet_b64 else 'Signature'}
                        </div>
                    </div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)
    conn.close()

# --- PARAMÈTRES ---
elif menu == "⚙️ Paramètres":
    st.title("Paramètres ⚙️")
    with st.form("p_set"):
        n_nom = st.text_input("Boutique", value=info_ent['nom'])
        n_tel = st.text_input("Téléphone", value=info_ent['telephone'])
        n_eml = st.text_input("Email", value=info_ent['email'])
        n_adr = st.text_input("Adresse", value=info_ent['adresse'])
        n_msg = st.text_area("Message Reçu", value=info_ent['message_recu'])
        if st.form_submit_button("Sauvegarder"):
            conn = get_connection()
            conn.execute("UPDATE entreprise SET nom=?, telephone=?, email=?, adresse=?, message_recu=? WHERE id=1", (n_nom, n_tel, n_eml, n_adr, n_msg))
            conn.commit()
            st.rerun()
