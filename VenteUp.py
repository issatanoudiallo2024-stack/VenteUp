import sqlite3
import os
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
from fpdf import FPDF

# ==========================================
# INFOS DÉVELOPPEUR & CRÉDITS
# ==========================================
DEV_NAME = "Issa Diallo"
DEV_TEL = "610 51 89 73"
DEV_MAIL = "issatanoudiallo2024@gmail.com"
APP_VERSION = "VenteUp v1.0"

# ==========================================
# GESTION DE LA BASE DE DONNÉES
# ==========================================
def init_db():
    conn = sqlite3.connect('venteup_data.db')
    cursor = conn.cursor()
    # Table produits : stockage du prix d'achat pour calculer les bénéfices
    cursor.execute('''CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL UNIQUE,
        prix_achat REAL NOT NULL,
        prix_vente REAL NOT NULL,
        stock INTEGER DEFAULT 0)''')
    # Table ventes : historique des transactions
    cursor.execute('''CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client TEXT,
        total REAL,
        benefice REAL,
        date TEXT)''')
    conn.commit()
    conn.close()

# ==========================================
# GÉNÉRATEUR DE FACTURE PDF
# ==========================================
class FacturePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, "FACTURE OFFICIELLE VENTEUP", 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        # Crédits développeur en bas de facture
        credits = f"Logiciel conçu par {DEV_NAME} | Tel: {DEV_TEL} | Mail: {DEV_MAIL}"
        self.cell(0, 10, credits, 0, 1, 'C')
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, f"Signature de {DEV_NAME} (Gérant) : ____________________", 0, 0, 'R')

def generer_document(nom_client, total_vente):
    pdf = FacturePDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.cell(0, 10, f"Client : {nom_client}", ln=True)
    pdf.ln(10)
    
    # Tableau simple
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(100, 10, "Désignation", border=1, fill=True)
    pdf.cell(40, 10, "Total (GNF)", border=1, fill=True, ln=True)
    
    pdf.cell(100, 10, "Vente de marchandises", border=1)
    pdf.cell(40, 10, f"{total_vente}", border=1, ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"TOTAL À PAYER : {total_vente} GNF", ln=True, align='R')
    
    filename = f"Facture_{nom_client}_{datetime.now().strftime('%H%M%S')}.pdf"
    pdf.output(filename)
    return filename

# ==========================================
# INTERFACE PRINCIPALE (GUI)
# ==========================================
class VenteUpApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_VERSION} - Développeur : {DEV_NAME}")
        self.geometry("850x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Layout Principal
        self.grid_columnconfigure(1, weight=1)
        
        # Sidebar (Actions)
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="VENTE UP", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.pack(pady=20)

        # Champs de saisie
        self.ent_nom = ctk.CTkEntry(self.sidebar, placeholder_text="Nom du produit")
        self.ent_nom.pack(pady=10, padx=20)
        
        self.ent_achat = ctk.CTkEntry(self.sidebar, placeholder_text="Prix d'Achat (GNF)")
        self.ent_achat.pack(pady=10, padx=20)
        
        self.ent_vente = ctk.CTkEntry(self.sidebar, placeholder_text="Prix de Vente (GNF)")
        self.ent_vente.pack(pady=10, padx=20)
        
        self.ent_qte = ctk.CTkEntry(self.sidebar, placeholder_text="Quantité")
        self.ent_qte.pack(pady=10, padx=20)

        self.btn_add = ctk.CTkButton(self.sidebar, text="Ajouter / Réappro.", command=self.gestion_stock, fg_color="#2ECC71", hover_color="#27AE60")
        self.btn_add.pack(pady=20, padx=20)

        # Zone Centrale (Vente)
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.lbl_vente = ctk.CTkLabel(self.main_frame, text="FACTURE & CLIENT", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_vente.pack(pady=15)

        self.ent_client = ctk.CTkEntry(self.main_frame, placeholder_text="Nom complet du client", width=300)
        self.ent_client.pack(pady=10)

        self.ent_total = ctk.CTkEntry(self.main_frame, placeholder_text="Montant total de la vente", width=300)
        self.ent_total.pack(pady=10)

        self.btn_pdf = ctk.CTkButton(self.main_frame, text="Générer Facture PDF", command=self.vente_et_pdf, height=40)
        self.btn_pdf.pack(pady=20)

        # Pied de page (Crédits)
        self.footer = ctk.CTkLabel(self, text=f"© 2026 {DEV_NAME} | Contact : {DEV_TEL} | {DEV_MAIL}", font=("Arial", 10, "italic"))
        self.footer.grid(row=3, column=1, pady=10)

    def gestion_stock(self):
        try:
            nom = self.ent_nom.get().upper()
            pa = float(self.ent_achat.get())
            pv = float(self.ent_vente.get())
            qte = int(self.ent_qte.get())
            
            conn = sqlite3.connect('venteup_data.db')
            cursor = conn.cursor()
            
            # Vérification pour réapprovisionnement automatique
            cursor.execute("SELECT stock FROM produits WHERE nom=?", (nom,))
            data = cursor.fetchone()
            
            if data:
                new_stock = data[0] + qte
                cursor.execute("UPDATE produits SET stock=?, prix_achat=?, prix_vente=? WHERE nom=?", (new_stock, pa, pv, nom))
                msg = f"Stock de {nom} mis à jour (+{qte})."
            else:
                cursor.execute("INSERT INTO produits (nom, prix_achat, prix_vente, stock) VALUES (?,?,?,?)", (nom, pa, pv, qte))
                msg = f"Produit {nom} ajouté au catalogue."
            
            conn.commit()
            conn.close()
            messagebox.showinfo("Stock", msg)
        except Exception as e:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs correctement.")

    def vente_et_pdf(self):
        client = self.ent_client.get()
        total = self.ent_total.get()
        
        if not client or not total:
            messagebox.showwarning("Incomplet", "Veuillez saisir le nom du client et le montant.")
            return

        try:
            # Création du fichier PDF
            nom_fichier = generer_document(client, total)
            
            # Enregistrement en BDD (Ici on pourrait automatiser le calcul du bénéfice)
            conn = sqlite3.connect('venteup_data.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO ventes (client, total, date) VALUES (?,?,?)", 
                           (client, float(total), datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Succès", f"Vente enregistrée !\nFacture créée : {nom_fichier}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la vente : {e}")

# ==========================================
# LANCEMENT DU PROGRAMME
# ==========================================
if __name__ == "__main__":
    init_db()
    app = VenteUpApp()
    app.mainloop()
