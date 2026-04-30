import sqlite3
import os
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
from fpdf import FPDF

# ==========================================
# INFOS DÉVELOPPEUR (Issa Diallo)
# ==========================================
DEV_NAME = "Issa Diallo"
DEV_TEL = "610 51 89 73"
DEV_MAIL = "issatanoudiallo2024@gmail.com"

# ==========================================
# LOGIQUE BASE DE DONNÉES
# ==========================================
def init_db():
    conn = sqlite3.connect('venteup_data.db')
    cursor = conn.cursor()
    # Table Produits avec Prix d'Achat pour le bénéfice
    cursor.execute('''CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        prix_achat REAL NOT NULL,
        prix_vente REAL NOT NULL,
        stock INTEGER DEFAULT 0)''')
    # Table Ventes
    cursor.execute('''CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client TEXT,
        total REAL,
        date TEXT)''')
    conn.commit()
    conn.close()

# ==========================================
# GÉNÉRATEUR DE FACTURE PDF
# ==========================================
class FacturePDF(FPDF):
    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'I', 8)
        info = f"Développé par {DEV_NAME} | Tel: {DEV_TEL} | Email: {DEV_MAIL}"
        self.cell(0, 10, info, 0, 0, 'C')

def creer_facture(nom_client, total):
    pdf = FacturePDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "FACTURE VENTEUP", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Client : {nom_client}", ln=True)
    pdf.cell(0, 10, f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.cell(0, 10, f"Total : {total} GNF", ln=True)
    pdf.ln(20)
    pdf.cell(0, 10, f"Signature de {DEV_NAME} : ________________", ln=True, align='R')
    
    filename = f"facture_{nom_client}.pdf"
    pdf.output(filename)
    return filename

# ==========================================
# INTERFACE GRAPHIQUE (GUI)
# ==========================================
class VenteUpApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"VenteUp - Développeur : {DEV_NAME}")
        self.geometry("700x500")
        ctk.set_appearance_mode("dark")

        # Titre
        self.label = ctk.CTkLabel(self, text="GESTION DE VENTE", font=("Arial", 20, "bold"))
        self.label.pack(pady=20)

        # Formulaire
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(pady=10, padx=20, fill="both")

        self.nom_art = ctk.CTkEntry(self.frame, placeholder_text="Nom du produit")
        self.nom_art.grid(row=0, column=0, padx=10, pady=10)

        self.p_achat = ctk.CTkEntry(self.frame, placeholder_text="Prix d'Achat")
        self.p_achat.grid(row=0, column=1, padx=10, pady=10)

        self.p_vente = ctk.CTkEntry(self.frame, placeholder_text="Prix de Vente")
        self.p_vente.grid(row=1, column=0, padx=10, pady=10)

        self.qte = ctk.CTkEntry(self.frame, placeholder_text="Quantité")
        self.qte.grid(row=1, column=1, padx=10, pady=10)

        # Boutons
        self.btn_stock = ctk.CTkButton(self, text="Ajouter au Stock", command=self.action_stock, fg_color="green")
        self.btn_stock.pack(pady=10)

        self.client_name = ctk.CTkEntry(self, placeholder_text="Nom du client (pour facture)")
        self.client_name.pack(pady=10)

        self.btn_vente = ctk.CTkButton(self, text="Vendre & Facture", command=self.action_vente)
        self.btn_vente.pack(pady=10)

    def action_stock(self):
        try:
            conn = sqlite3.connect('venteup_data.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO produits (nom, prix_achat, prix_vente, stock) VALUES (?, ?, ?, ?)",
                           (self.nom_art.get(), float(self.p_achat.get()), float(self.p_vente.get()), int(self.qte.get())))
            conn.commit()
            conn.close()
            messagebox.showinfo("Succès", "Stock mis à jour !")
        except:
            messagebox.showerror("Erreur", "Veuillez remplir correctement les champs.")

    def action_vente(self):
        nom = self.client_name.get()
        if nom:
            fname = creer_facture(nom, "À calculer")
            messagebox.showinfo("Vente", f"Facture générée : {fname}")
        else:
            messagebox.showwarning("Attention", "Entrez le nom du client.")

if __name__ == "__main__":
    init_db()
    app = VenteUpApp()
    app.mainloop()
