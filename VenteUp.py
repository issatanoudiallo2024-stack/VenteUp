import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import base64
import hashlib

# --- CONFIGURATION ---
st.set_page_config(page_title="VenteUp Pro - Solution Business", layout="wide", page_icon="💎")

def get_connection():
    return sqlite3.connect('venteup_pro_saas.db', check_same_thread=False)

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Table des Utilisateurs avec profil complet
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, 
                  nom_ent TEXT, gerant TEXT, adresse TEXT, telephone TEXT, email TEXT, localization TEXT, devise TEXT)''')
    # Table Produits liée à user_id
    c.execute('''CREATE TABLE IF NOT EXISTS produits
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nom TEXT, p_achat REAL, p_vente REAL, qte INTEGER, seuil INTEGER)''')
    # Table Ventes liée à user_id
    c.execute('''CREATE TABLE IF NOT EXISTS ventes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, produit_id INTEGER, nom_prod TEXT, qte_v INTEGER, date_v TIMESTAMP, total REAL, benef REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- GESTION DE SESSION ---
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# --- AUTHENTIFICATION ---
def signup(u, p, ent):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO users (username, password, nom_ent, devise) VALUES (?,?,?,?)", (u, hash_password(p), ent, "FG"))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def login(u, p):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hash_password(p))).fetchone()
    conn.close()
    return user

# --- ÉCRAN D'ACCUEIL / LOGIN ---
if st.session_state['user_id'] is None:
    st.title("💎 VenteUp Elite Pro")
    st.subheader("Solution de gestion commerciale multi-comptes")
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.info("🔌 Connexion")
        u = st.text_input("Identifiant")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            res = login(u, p)
            if res:
                st.session_state['user_id'] = res[0]
                st.session_state['user_data'] = res
                st.rerun()
            else: st.error("Identifiants incorrects")
            
    with col_r:
        st.info("📝 Créer un compte boutique")
        new_u = st.text_input("Nouvel Identifiant")
        new_ent = st.text_input("Nom de l'entreprise")
        new_p = st.text_input("Nouveau mot de passe", type="password")
        if st.button("S'inscrire"):
            if signup(new_u, new_p, new_ent): st.success("Compte créé avec succès !")
            else: st.error("Nom d'utilisateur déjà pris.")

    st.divider()
    st.markdown(f"**Développeur :** Issa Diallo | **Contact :** +224 610 51 89 73 | **Email :** Issatanoudiallo2024@gmail.com")
    st.stop()

# --- INTERFACE UTILISATEUR CONNECTÉ ---
user_id = st.session_state['user_id']
conn = get_connection()
user_info = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

with st.sidebar:
    st.title(f"🏬 {user_info[3]}")
    st.write(f"👤 Admin : **{user_info[4] if user_info[4] else user_info[1]}**")
    menu = st.radio("Menu", ["📊 Dashboard", "🛒 Caisse", "📦 Stocks & Appro", "🧾 Factures", "⚙️ Paramètres"])
    if st.button("Déconnexion"):
        st.session_state['user_id'] = None
        st.rerun()
    st.divider()
    st.caption("🛠️ **Support Technique**")
    st.caption("Issa Diallo : 610 51 89 73")

# --- CONTENU DES ONGLETS ---

if menu == "📊 Dashboard":
    st.title("Performance Commerciale 📊")
    df_v = pd.read_sql(f"SELECT * FROM ventes WHERE user_id={user_id}", conn)
    c1, c2, c3 = st.columns(3)
    c1.metric("Chiffre d'Affaire", f"{df_v['total'].sum():,.0f} {user_info[9]}")
    c2.metric("Bénéfice Net", f"{df_v['benef'].sum():,.0f} {user_info[9]}")
    c3.metric("Ventes Réalisées", len(df_v))

elif menu == "🛒 Caisse":
    st.title("Vente Rapide 🛒")
    prods = pd.read_sql(f"SELECT * FROM produits WHERE user_id={user_id} AND qte > 0", conn)
    if not prods.empty:
        with st.form("vente"):
            p_sel = st.selectbox("Produit", prods['nom'].tolist())
            q_v = st.number_input("Quantité", min_value=1)
            if st.form_submit_button("Ajouter à la vente"):
                p_data = prods[prods['nom'] == p_sel].iloc[0]
                total = q_v * p_data['p_vente']
                benef = (p_data['p_vente'] - p_data['p_achat']) * q_v
                conn.execute("INSERT INTO ventes (user_id, produit_id, nom_prod, qte_v, date_v, total, benef) VALUES (?,?,?,?,?,?,?)",
                             (user_id, int(p_data['id']), p_sel, q_v, datetime.now().strftime("%d/%m/%Y %H:%M"), total, benef))
                conn.execute("UPDATE produits SET qte = qte - ? WHERE id = ?", (q_v, int(p_data['id'])))
                conn.commit()
                st.success("Vente enregistrée !")
    else: st.warning("Stock vide.")

elif menu == "📦 Stocks & Appro":
    st.title("Gestion des Stocks 📦")
    t1, t2, t3 = st.tabs(["Inventaire", "🔄 Réapprovisionnement", "➕ Nouveau Produit"])
    
    with t1:
        df_p = pd.read_sql(f"SELECT * FROM produits WHERE user_id={user_id}", conn)
        st.dataframe(df_p, use_container_width=True)
    
    with t2:
        st.subheader("Réapprovisionner un article")
        if not df_p.empty:
            p_re = st.selectbox("Choisir l'article", df_p['nom'].tolist())
            q_re = st.number_input("Quantité reçue", min_value=1)
            if st.button("Mettre à jour le stock"):
                conn.execute("UPDATE produits SET qte = qte + ? WHERE nom = ? AND user_id = ?", (q_re, p_re, user_id))
                conn.commit()
                st.success("Stock mis à jour !")
                st.rerun()

    with t3:
        with st.form("add"):
            n = st.text_input("Nom")
            pa = st.number_input("Prix Achat")
            pv = st.number_input("Prix Vente")
            q = st.number_input("Initial")
            if st.form_submit_button("Créer"):
                conn.execute("INSERT INTO produits (user_id, nom, p_achat, p_vente, qte, seuil) VALUES (?,?,?,?,?,?)", (user_id, n, pa, pv, q, 5))
                conn.commit()
                st.rerun()

elif menu == "🧾 Factures":
    st.title("Édition de Factures 🧾")
    df_v = pd.read_sql(f"SELECT * FROM ventes WHERE user_id={user_id} ORDER BY id DESC", conn)
    if not df_v.empty:
        sel = st.multiselect("Sélectionner articles", df_v['id'].tolist())
        if sel:
            items = df_v[df_v['id'].isin(sel)]
            c_nom = st.text_input("Nom Client")
            c_tel = st.text_input("Téléphone Client")
            c_adr = st.text_input("Adresse Client")
            c_eml = st.text_input("Email Client")
            cachet = st.file_uploader("Importer Cachet (Image)")

            if st.button("Générer Facture"):
                c_b64 = base64.b64encode(cachet.getvalue()).decode() if cachet else ""
                html = f"""
                <div style="padding:20px; border:1px solid #000; background:white; color:black; font-family:Arial;">
                    <div style="display:flex; justify-content:space-between;">
                        <div>
                            <h2 style="color:#1a73e8;">{user_info[3]}</h2>
                            <p>📍 {user_info[5]}<br>👤 {user_info[4]}<br>📞 {user_info[6]}<br>📧 {user_info[7]}</p>
                        </div>
                        <div style="text-align:right;">
                            <h2>FACTURE</h2>
                            <p><b>CLIENT :</b> {c_nom}<br>📍 {c_adr}<br>📞 {c_tel}<br>📧 {c_eml}</p>
                        </div>
                    </div>
                    <table style="width:100%; border-collapse:collapse; margin-top:20px;">
                        <tr style="background:#eee; border:1px solid #000;"><th>N°</th><th>Désignation</th><th>Qté</th><th>Total</th></tr>
                """
                for i, r in enumerate(items.itertuples(), 1):
                    html += f"<tr><td style='border:1px solid #ddd; padding:8px; text-align:center;'>{i}</td><td style='border:1px solid #ddd; padding:8px;'>{r.nom_prod}</td><td style='border:1px solid #ddd; padding:8px; text-align:center;'>{r.qte_v}</td><td style='border:1px solid #ddd; padding:8px; text-align:right;'>{r.total:,.0f}</td></tr>"
                
                html += f"""
                    </table>
                    <h3 style="text-align:right;">NET À PAYER : {items['total'].sum():,.0f} {user_info[9]}</h3>
                    <div style="display:flex; justify-content:space-between; margin-top:30px;">
                        <p style="font-size:10px;">Développeur : Issa Diallo (+224 610 51 89 73)</p>
                        <div style="width:120px;">{f'<img src="data:image/png;base64,{c_b64}" width="100">' if c_b64 else 'Signature'}</div>
                    </div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)

elif menu == "⚙️ Paramètres":
    st.title("Profil Boutique & Vendeur ⚙️")
    with st.form("p"):
        n_e = st.text_input("Nom Entreprise", value=user_info[3])
        g_e = st.text_input("Nom du Gérant", value=user_info[4])
        a_e = st.text_input("Adresse Physique", value=user_info[5])
        t_e = st.text_input("Téléphone", value=user_info[6])
        e_e = st.text_input("Email Professionnel", value=user_info[7])
        l_e = st.text_input("Localisation / Ville", value=user_info[8])
        d_e = st.selectbox("Devise", ["FG", "GNF", "CFA", "$"], index=0)
        if st.form_submit_button("Sauvegarder les modifications"):
            conn.execute("UPDATE users SET nom_ent=?, gerant=?, adresse=?, telephone=?, email=?, localization=?, devise=? WHERE id=?",
                         (n_e, g_e, a_e, t_e, e_e, l_e, d_e, user_id))
            conn.commit()
            st.success("Paramètres mis à jour !")
            st.rerun()

conn.close()
