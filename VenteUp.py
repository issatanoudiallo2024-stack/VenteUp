import streamlit as st
import sqlite3
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="VenteUp Pro - Panier", page_icon="🛒", layout="wide")

def init_db():
    with sqlite3.connect('venteup_v3.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE, 
            p_achat REAL, p_vente REAL, stock INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, client_nom TEXT, client_tel TEXT,
            details_achat TEXT, total REAL, date TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY, boutique TEXT, gerant TEXT, tel TEXT, adresse TEXT)''')
        cursor.execute("INSERT OR IGNORE INTO config (id, boutique, gerant, tel, adresse) VALUES (1, 'Ma Boutique', 'Gérant', '000', 'Conakry')")
        conn.commit()

init_db()

def get_config():
    conn = sqlite3.connect('venteup_v3.db')
    data = conn.execute("SELECT boutique, gerant, tel, adresse FROM config WHERE id=1").fetchone()
    conn.close()
    return {"boutique": data[0], "gerant": data[1], "tel": data[2], "adr": data[3]}

# --- GÉNÉRATEUR DE FACTURE EN IMAGE ---
def generer_facture_image(conf, client, panier, total):
    # Création d'une image blanche
    img = Image.new('RGB', (600, 800), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    
    # Couleurs et Styles
    d.rectangle([0, 0, 600, 100], fill=(0, 123, 255)) # Bandeau bleu
    
    # Texte de l'en-tête
    d.text((200, 30), conf['boutique'].upper(), fill=(255, 255, 255))
    d.text((20, 120), f"Client : {client['nom']}", fill=(0, 0, 0))
    d.text((20, 140), f"Tel : {client['tel']}", fill=(0, 0, 0))
    d.text((400, 120), f"Date : {datetime.now().strftime('%d/%m/%Y')}", fill=(0, 0, 0))
    
    d.line([(20, 170), (580, 170)], fill=(200, 200, 200), width=2)
    
    # Liste des produits
    y_offset = 200
    d.text((20, y_offset), "PRODUIT", fill=(0, 0, 0))
    d.text((450, y_offset), "PRIX (GNF)", fill=(0, 0, 0))
    
    for item in panier:
        y_offset += 30
        d.text((20, y_offset), f"- {item['nom']} (x{item['qte']})", fill=(50, 50, 50))
        d.text((450, y_offset), f"{item['total']}", fill=(50, 50, 50))
    
    d.line([(20, y_offset + 40), (580, y_offset + 40)], fill=(0, 0, 0), width=2)
    d.text((350, y_offset + 60), f"TOTAL : {total} GNF", fill=(255, 0, 0))
    
    d.text((200, 750), f"Merci de votre confiance ! - {conf['gerant']}", fill=(100, 100, 100))
    
    # Sauvegarde en mémoire
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

# --- INTERFACE ---
conf = get_config()
st.sidebar.title(f"🚀 {conf['boutique']}")
choix = st.sidebar.radio("Navigation", ["🛒 Vente & Panier", "📦 Stock", "⚙️ Paramètres"])

# Initialisation du panier dans la session Streamlit
if 'panier' not in st.session_state:
    st.session_state.panier = []

if choix == "🛒 Vente & Panier":
    st.header("🛒 Nouveau Panier d'Achats")
    
    col1, col2 = st.columns(2)
    nom_c = col1.text_input("Nom Client")
    tel_c = col2.text_input("Téléphone Client")
    
    st.divider()
    
    # Sélection des produits
    conn = sqlite3.connect('venteup_v3.db')
    prods = conn.execute("SELECT nom, p_vente, stock FROM produits WHERE stock > 0").fetchall()
    conn.close()
    
    p_noms = [p[0] for p in prods]
    p_sel = st.selectbox("Choisir un produit à ajouter", [""] + p_noms)
    
    if p_sel:
        p_info = next(p for p in prods if p[0] == p_sel)
        qte_v = st.number_input("Quantité", min_value=1, max_value=p_info[2], value=1)
        if st.button("➕ Ajouter au panier"):
            st.session_state.panier.append({
                "nom": p_sel,
                "prix_unitaire": p_info[1],
                "qte": qte_v,
                "total": p_info[1] * qte_v
            })
            st.success(f"{p_sel} ajouté !")

    # Affichage du Panier
    if st.session_state.panier:
        st.subheader("📝 Contenu du panier")
        total_global = 0
        for i, item in enumerate(st.session_state.panier):
            st.write(f"**{item['nom']}** | Quantité: {item['qte']} | Total: {item['total']} GNF")
            total_global += item['total']
        
        st.write(f"### TOTAL GÉNÉRAL : {total_global} GNF")
        
        if st.button("✅ Valider la vente et générer la facture Image"):
            if nom_c:
                # Génération de l'image
                client_info = {"nom": nom_c, "tel": tel_c}
                img_data = generer_facture_image(conf, client_info, st.session_state.panier, total_global)
                
                st.image(img_data, caption="Facture générée")
                st.download_button("📥 Télécharger la facture (IMAGE)", img_data, f"Facture_{nom_c}.png", "image/png")
                
                # Vider le panier après vente
                st.session_state.panier = []
                st.success("Vente enregistrée !")
            else:
                st.error("Entrez le nom du client !")

elif choix == "📦 Stock":
    st.header("📦 Gestion du Stock")
    with st.form("add_p"):
        n = st.text_input("Nom du produit").upper()
        pa = st.number_input("Prix Achat")
        pv = st.number_input("Prix Vente")
        q = st.number_input("Quantité", min_value=1)
        if st.form_submit_button("Enregistrer"):
            with sqlite3.connect('venteup_v3.db') as conn:
                conn.execute("INSERT OR REPLACE INTO produits (nom, p_achat, p_vente, stock) VALUES (?,?,?,?)", (n, pa, pv, q))
            st.success("Produit ajouté !")

elif choix == "⚙️ Paramètres":
    st.header("⚙️ Paramètres Boutique")
    # Formulaire de mise à jour (comme vu précédemment)
