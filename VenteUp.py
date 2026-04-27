import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import base64
import hashlib

# --- CONFIGURATION ---
st.set_page_config(page_title="VenteUp Elite Pro", layout="wide", page_icon="📈")

def get_connection():
    return sqlite3.connect('venteup_final_saas.db', check_same_thread=False)

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, 
                  nom_ent TEXT, gerant TEXT, adresse TEXT, telephone TEXT, email TEXT, localization TEXT, 
                  devise TEXT, date_inscription TIMESTAMP, est_actif INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS produits
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nom TEXT, p_achat REAL, p_vente REAL, qte INTEGER, seuil INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ventes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, produit_id INTEGER, nom_prod TEXT, qte_v INTEGER, date_v TIMESTAMP, total REAL, benef REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- GESTION DE SESSION ---
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# --- SECURITÉ ISSA DIALLO (Vérification Licence) ---
def check_license(user_data):
    if user_data[11] == 1: # Si est_actif == 1
        return True
    date_insc = datetime.strptime(user_data[10], "%Y-%m-%d %H:%M:%S")
    if datetime.now() > date_insc + timedelta(days=3):
        return False
    return True

# --- INTERFACE DE CONNEXION ---
if st.session_state['user_id'] is None:
    st.title("🚀 VenteUp : Gestion Commerciale Intégrée")
    tab_log, tab_sign = st.tabs(["Connexion", "Créer un compte"])
    
    with tab_log:
        u = st.text_input("Nom d'utilisateur")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Accéder à mon espace"):
            conn = get_connection()
            user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hash_password(p))).fetchone()
            conn.close()
            if user:
                if check_license(user):
                    st.session_state['user_id'] = user[0]
                    st.rerun()
                else:
                    st.error("🚨 Période d'essai terminée. Contactez Issa Diallo (+224 610 51 89 73).")
            else: st.error("Identifiants incorrects.")

    with tab_sign:
        new_u = st.text_input("Choisir un pseudo")
        new_e = st.text_input("Nom de la Boutique")
        new_p = st.text_input("Choisir un mot de passe", type="password")
        if st.button("Finaliser l'inscription"):
            conn = get_connection()
            try:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute("INSERT INTO users (username, password, nom_ent, date_inscription, est_actif, devise) VALUES (?,?,?,?,?,?)", 
                             (new_u, hash_password(new_p), new_e, now, 0, "FG"))
                conn.commit()
                st.success("Compte créé ! Vous avez 3 jours d'essai gratuit.")
            except: st.error("Pseudo déjà utilisé.")
            finally: conn.close()
    st.stop()

# --- INTERFACE PRINCIPALE ---
user_id = st.session_state['user_id']
conn = get_connection()
user_info = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

with st.sidebar:
    st.header(f"🏢 {user_info[3]}")
    menu = st.radio("Menu", ["📊 Analyse", "🛒 Ventes", "📦 Stock & Appro", "🧾 Facturation", "⚙️ Paramètres"])
    if st.button("Déconnexion"):
        st.session_state['user_id'] = None
        st.rerun()
    st.divider()
    st.caption("👨‍💻 Développeur : Issa Diallo")
    st.caption("📞 +224 610 51 89 73")

# --- ANALYSE (DASHBOARD) ---
if menu == "📊 Analyse":
    st.title("Tableau de Bord 📊")
    df_v = pd.read_sql(f"SELECT * FROM ventes WHERE user_id={user_id}", conn)
    
    col1, col2, col3 = st.columns(3)
    ca = df_v['total'].sum()
    benef = df_v['benef'].sum()
    col1.metric("Chiffre d'Affaire", f"{ca:,.0f} {user_info[9]}")
    col2.metric("Bénéfice Réalisé", f"{benef:,.0f} {user_info[9]}")
    col3.metric("Nombre de Ventes", len(df_v))

    if not df_v.empty:
        st.subheader("Évolution des ventes")
        df_v['date_v'] = pd.to_datetime(df_v['date_v'])
        chart_data = df_v.groupby(df_v['date_v'].dt.date)['total'].sum()
        st.line_chart(chart_data)

# --- VENTES (CAISSE) ---
elif menu == "🛒 Ventes":
    st.title("Nouvelle Vente 🛒")
    prods = pd.read_sql(f"SELECT * FROM produits WHERE user_id={user_id} AND qte > 0", conn)
    if not prods.empty:
        with st.form("caisse"):
            p_nom = st.selectbox("Sélectionner l'article", prods['nom'].tolist())
            qte = st.number_input("Quantité", min_value=1)
            if st.form_submit_button("Valider la vente"):
                p_info = prods[prods['nom'] == p_nom].iloc[0]
                tot = qte * p_info['p_vente']
                ben = (p_info['p_vente'] - p_info['p_achat']) * qte
                conn.execute("INSERT INTO ventes (user_id, produit_id, nom_prod, qte_v, date_v, total, benef) VALUES (?,?,?,?,?,?,?)",
                             (user_id, int(p_info['id']), p_nom, qte, datetime.now().strftime("%Y-%m-%d %H:%M"), tot, ben))
                conn.execute("UPDATE produits SET qte = qte - ? WHERE id = ?", (qte, int(p_info['id'])))
                conn.commit()
                st.success("Vente effectuée !")
    else: st.warning("Stock épuisé.")

# --- STOCK & APPRO ---
elif menu == "📦 Stock & Appro":
    st.title("Gestion de Stock 📦")
    t1, t2, t3 = st.tabs(["Inventaire", "Réapprovisionnement", "Nouveau Produit"])
    
    with t1:
        df_p = pd.read_sql(f"SELECT * FROM produits WHERE user_id={user_id}", conn)
        # Style pour le stock faible
        def highlight_low_stock(s):
            return ['background-color: #ffcccc' if v <= 5 else '' for v in s]
        st.dataframe(df_p.style.apply(highlight_low_stock, subset=['qte']), use_container_width=True)

    with t2:
        if not df_p.empty:
            p_re = st.selectbox("Article à recharger", df_p['nom'].tolist())
            q_re = st.number_input("Quantité ajoutée", min_value=1)
            if st.button("Mettre à jour"):
                conn.execute("UPDATE produits SET qte = qte + ? WHERE nom=? AND user_id=?", (q_re, p_re, user_id))
                conn.commit()
                st.rerun()

    with t3:
        with st.form("new"):
            nom = st.text_input("Désignation")
            pa = st.number_input("Prix Achat")
            pv = st.number_input("Prix Vente")
            qt = st.number_input("Quantité initiale")
            if st.form_submit_button("Ajouter au catalogue"):
                conn.execute("INSERT INTO produits (user_id, nom, p_achat, p_vente, qte, seuil) VALUES (?,?,?,?,?,5)", 
                             (user_id, nom, pa, pv, qt))
                conn.commit()
                st.rerun()

# --- FACTURATION ---
elif menu == "🧾 Facturation":
    st.title("Générer une Facture 🧾")
    df_v = pd.read_sql(f"SELECT * FROM ventes WHERE user_id={user_id} ORDER BY id DESC", conn)
    if not df_v.empty:
        ids = st.multiselect("Sélectionner les articles", df_v['id'].tolist())
        if ids:
            sel_items = df_v[df_v['id'].isin(ids)]
            c_nom = st.text_input("Nom Client")
            c_tel = st.text_input("Téléphone Client")
            c_adr = st.text_input("Adresse Client")
            img = st.file_uploader("Cachet (Image)")
            
            if st.button("Afficher"):
                c_b64 = base64.b64encode(img.getvalue()).decode() if img else ""
                html = f"""
                <div style="padding:20px; border:1px solid #000; background:white; color:black; font-family:Arial;">
                    <div style="display:flex; justify-content:space-between;">
                        <div style="text-align:left;">
                            <h2 style="color:#1a73e8;">{user_info[3]}</h2>
                            <p>📍 {user_info[5]}<br>📞 {user_info[6]}<br>📧 {user_info[7]}</p>
                        </div>
                        <div style="text-align:right;">
                            <h2>FACTURE</h2>
                            <p><b>Client :</b> {c_nom}<br>📍 {c_adr}<br>📞 {c_tel}</p>
                        </div>
                    </div>
                    <table style="width:100%; border-collapse:collapse; margin-top:20px;">
                        <tr style="background:#eee;"><th>N°</th><th>Article</th><th>Qté</th><th>Total</th></tr>
                """
                for i, r in enumerate(sel_items.itertuples(), 1):
                    html += f"<tr><td style='border:1px solid #ddd; padding:8px; text-align:center;'>{i}</td><td style='border:1px solid #ddd; padding:8px;'>{r.nom_prod}</td><td style='border:1px solid #ddd; padding:8px; text-align:center;'>{r.qte_v}</td><td style='border:1px solid #ddd; padding:8px; text-align:right;'>{r.total:,.0f}</td></tr>"
                
                html += f"""
                    </table>
                    <h3 style="text-align:right; margin-top:20px;">TOTAL : {sel_items['total'].sum():,.0f} {user_info[9]}</h3>
                    <div style="display:flex; justify-content:space-between; margin-top:40px;">
                        <p style="font-size:10px;">Propulsé par VenteUp | Développé par Issa Diallo</p>
                        <div style="width:120px;">{f'<img src="data:image/png;base64,{c_b64}" width="100">' if c_b64 else 'Signature'}</div>
                    </div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)

# --- PARAMÈTRES ---
elif menu == "⚙️ Paramètres":
    st.title("Paramètres du Compte ⚙️")
    with st.form("settings"):
        n_ent = st.text_input("Nom Boutique", value=user_info[3])
        n_ger = st.text_input("Gérant", value=user_info[4])
        n_adr = st.text_input("Adresse", value=user_info[5])
        n_tel = st.text_input("Téléphone", value=user_info[6])
        n_eml = st.text_input("Email", value=user_info[7])
        n_loc = st.text_input("Localisation", value=user_info[8])
        n_dev = st.selectbox("Devise", ["FG", "GNF", "CFA", "$"], index=0)
        if st.form_submit_button("Enregistrer"):
            conn.execute("UPDATE users SET nom_ent=?, gerant=?, adresse=?, telephone=?, email=?, localization=?, devise=? WHERE id=?",
                         (n_ent, n_ger, n_adr, n_tel, n_eml, n_loc, n_dev, user_id))
            conn.commit()
            st.success("Modifications enregistrées !")
            st.rerun()

conn.close()
