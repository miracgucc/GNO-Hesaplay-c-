import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
import pyodbc

# Grafik kütüphanesi kontrolü
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_VAR = True
except ImportError:
    MATPLOTLIB_VAR = False

# --- AYARLAR ---
ctk.set_appearance_mode("Dark")  # Mod: "System" (Standart), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Tema: "blue", "green", "dark-blue"

NOT_KATSAYILARI = {
    'AA': 4.0, 'BA': 3.5, 'BB': 3.0, 'CB': 2.5,
    'CC': 2.0, 'DC': 1.5, 'DD': 1.0, 'FF': 0.0
}

ders_listesi = []  # (id, ders_adi, kredi, harf_notu)
secili_ders_index = None

# --- VERİTABANI BAĞLANTISI ---
try:
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=DESKTOP-6F9TTG4\\SQLEXPRESS;"
        "DATABASE=GNOProjeDB;"
        "Trusted_Connection=yes;"
    )
    cursor = conn.cursor()
    cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='dersler' AND xtype='U')
        CREATE TABLE dersler (
            id INT IDENTITY(1,1) PRIMARY KEY,
            ders_adi NVARCHAR(255) NOT NULL,
            kredi FLOAT NOT NULL,
            harf_notu NVARCHAR(10) NOT NULL
        )
    ''')
    conn.commit()
except Exception as e:
    print("Bağlantı hatası:", e)
    conn = None

# --- FONKSİYONLAR ---

def veritabani_yukle():
    global ders_listesi
    ders_listesi.clear()
    for item in tree.get_children():
        tree.delete(item)
    
    if not conn:
        return

    try:
        cursor.execute("SELECT id, ders_adi, kredi, harf_notu FROM dersler")
        rows = cursor.fetchall()
        for row in rows:
            ders_listesi.append((row[0], row[1], row[2], row[3]))
            tree.insert("", tk.END, values=(row[1], row[2], row[3]))
        
        gno_hesapla()
    except Exception as e:
        messagebox.showerror("SQL Hatası", str(e))

def simulasyon_kontrol():
    """Simülasyon modu kontrolü - Renk değişimi yapar"""
    durum = switch_sim.get()
    if durum:
        app.configure(fg_color="#3E2723") # Koyu kahverengi/turuncu tonu
        lbl_baslik.configure(text="SİMÜLASYON MODU", text_color="#FFAB91")
        btn_temizle.configure(state="disabled")
    else:
        app.configure(fg_color="#2b2b2b") # Orijinal Dark tema rengi
        lbl_baslik.configure(text="GNO Hesaplayıcı", text_color="white")
        btn_temizle.configure(state="normal")
        veritabani_yukle()
        temizle_form()

def ders_ekle():
    ders_adi = entry_ders_adi.get().strip()
    kredi = entry_kredi.get().strip()
    harf_notu = combo_not.get()

    if not ders_adi or not kredi or harf_notu not in NOT_KATSAYILARI:
        messagebox.showerror("Hata", "Lütfen tüm alanları doldurun!")
        return
    try:
        kredi = float(kredi)
        if kredi <= 0: raise ValueError
    except:
        messagebox.showerror("Hata", "Kredi pozitif sayı olmalı!")
        return

    # SİMÜLASYON
    if switch_sim.get():
        ders_listesi.append((None, ders_adi, kredi, harf_notu))
        tree.insert("", tk.END, values=(ders_adi, kredi, harf_notu))
        temizle_form()
        gno_hesapla()
        return

    # NORMAL
    if conn:
        try:
            cursor.execute("INSERT INTO dersler (ders_adi, kredi, harf_notu) VALUES (?, ?, ?)",
                           (ders_adi, kredi, harf_notu))
            conn.commit()
            yeni_id = cursor.execute("SELECT @@IDENTITY").fetchone()[0]
            ders_listesi.append((yeni_id, ders_adi, kredi, harf_notu))
            tree.insert("", tk.END, values=(ders_adi, kredi, harf_notu))
        except Exception as e:
            messagebox.showerror("SQL Hatası", str(e))
    else:
        ders_listesi.append((None, ders_adi, kredi, harf_notu))
        tree.insert("", tk.END, values=(ders_adi, kredi, harf_notu))
    
    temizle_form()
    gno_hesapla()

def ders_guncelle():
    global secili_ders_index
    if secili_ders_index is None: return

    ders_adi = entry_ders_adi.get().strip()
    kredi = entry_kredi.get().strip()
    harf_notu = combo_not.get()
    
    try: kredi = float(kredi)
    except: return

    ders_id = ders_listesi[secili_ders_index][0]

    if switch_sim.get():
        ders_listesi[secili_ders_index] = (ders_id, ders_adi, kredi, harf_notu)
        item = tree.get_children()[secili_ders_index]
        tree.item(item, values=(ders_adi, kredi, harf_notu))
    else:
        if conn and ders_id:
            cursor.execute("UPDATE dersler SET ders_adi=?, kredi=?, harf_notu=? WHERE id=?",
                           (ders_adi, kredi, harf_notu, ders_id))
            conn.commit()
        
        ders_listesi[secili_ders_index] = (ders_id, ders_adi, kredi, harf_notu)
        items = tree.get_children()
        tree.item(items[secili_ders_index], values=(ders_adi, kredi, harf_notu))

    temizle_form()
    gno_hesapla()

def ders_sil():
    global secili_ders_index
    secili = tree.focus()
    if not secili:
        messagebox.showwarning("Uyarı", "Silinecek dersi seçin!")
        return
    
    index = tree.get_children().index(secili)
    ders_id = ders_listesi[index][0]

    if messagebox.askyesno("Onay", "Ders silinsin mi?"):
        if not switch_sim.get() and conn and ders_id:
            cursor.execute("DELETE FROM dersler WHERE id=?", (ders_id,))
            conn.commit()
        
        del ders_listesi[index]
        tree.delete(secili)
        temizle_form()
        gno_hesapla()

def temizle():
    if switch_sim.get(): return
    if messagebox.askyesno("DİKKAT", "Tüm veritabanı silinecek! Emin misiniz?"):
        if conn:
            cursor.execute("DELETE FROM dersler")
            conn.commit()
        veritabani_yukle()
        temizle_form()

def temizle_form():
    global secili_ders_index
    entry_ders_adi.delete(0, tk.END)
    entry_kredi.delete(0, tk.END)
    combo_not.set("AA")
    btn_guncelle.pack_forget()
    btn_ekle.pack(fill='x', pady=5)
    secili_ders_index = None

def secili_dersi_getir(event):
    global secili_ders_index
    secili = tree.focus()
    if not secili: return
    
    secili_ders_index = tree.get_children().index(secili)
    vals = tree.item(secili, 'values')
    
    entry_ders_adi.delete(0, tk.END)
    entry_ders_adi.insert(0, vals[0])
    entry_kredi.delete(0, tk.END)
    entry_kredi.insert(0, vals[1])
    combo_not.set(vals[2])

    btn_ekle.pack_forget()
    btn_guncelle.pack(fill='x', pady=5)

def gno_hesapla():
    if not ders_listesi:
        lbl_sonuc.configure(text="GNO: -")
        return
    
    toplam_kredi = sum(d[2] for d in ders_listesi)
    toplam_puan = sum(d[2] * NOT_KATSAYILARI.get(d[3], 0) for d in ders_listesi)
    
    gno = toplam_puan / toplam_kredi if toplam_kredi > 0 else 0
    
    renk = "#00E676" if gno >= 3.0 else "#FFEA00" if gno >= 2.0 else "#FF1744"
    lbl_sonuc.configure(text=f"GNO: {gno:.2f}", text_color=renk)

# --- YENİ ÖZELLİK: HEDEF HESAPLAMA ---
def hedef_hesapla_penceresi():
    if not ders_listesi:
        messagebox.showwarning("Uyarı", "Önce mevcut derslerinizi ekleyin.")
        return

    dialog = ctk.CTkToplevel(app)
    dialog.title("Hedef Hesaplayıcı")
    dialog.geometry("400x350")
    dialog.attributes("-topmost", True) # Her zaman üstte

    ctk.CTkLabel(dialog, text="Hedef GNO (Örn: 3.00):").pack(pady=10)
    entry_hedef = ctk.CTkEntry(dialog)
    entry_hedef.pack(pady=5)

    ctk.CTkLabel(dialog, text="Kalan Kredi Miktarı:").pack(pady=10)
    entry_kalan_kredi = ctk.CTkEntry(dialog)
    entry_kalan_kredi.pack(pady=5)

    lbl_hedef_sonuc = ctk.CTkLabel(dialog, text="", font=("Segoe UI", 14, "bold"))
    lbl_hedef_sonuc.pack(pady=20)

    def hesapla():
        try:
            hedef = float(entry_hedef.get())
            kalan_kredi = float(entry_kalan_kredi.get())
            
            mevcut_kredi = sum(d[2] for d in ders_listesi)
            mevcut_puan = sum(d[2] * NOT_KATSAYILARI.get(d[3], 0) for d in ders_listesi)
            
            toplam_kredi = mevcut_kredi + kalan_kredi
            istenen_toplam_puan = toplam_kredi * hedef
            
            gereken_puan = istenen_toplam_puan - mevcut_puan
            gereken_ortalama = gereken_puan / kalan_kredi
            
            if gereken_ortalama > 4.0:
                lbl_hedef_sonuc.configure(text=f"İmkansız! Gereken Ort: {gereken_ortalama:.2f}", text_color="red")
            elif gereken_ortalama < 0:
                lbl_hedef_sonuc.configure(text="Zaten hedefin üzerindesiniz!", text_color="green")
            else:
                lbl_hedef_sonuc.configure(text=f"Kalan Ders Ortalaması:\n{gereken_ortalama:.2f} olmalı", text_color="#00E5FF")

        except ValueError:
            lbl_hedef_sonuc.configure(text="Lütfen sayısal değer girin!")

    ctk.CTkButton(dialog, text="Hesapla", command=hesapla, fg_color="#F57F17").pack()

# --- GRAFİK ANALİZ ---
def grafik_goster():
    if not MATPLOTLIB_VAR or not ders_listesi:
        messagebox.showinfo("Bilgi", "Veri yok veya kütüphane eksik.")
        return

    harf_sayilari = {}
    for _, _, _, harf in ders_listesi:
        harf_sayilari[harf] = harf_sayilari.get(harf, 0) + 1

    win = ctk.CTkToplevel(app)
    win.title("Not Analizi")
    win.geometry("600x500")

    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor('#2b2b2b') # Arka plan rengi (Dark moda uyum)
    ax.set_facecolor('#2b2b2b')
    
    wedges, texts, autotexts = ax.pie(
        harf_sayilari.values(), 
        labels=harf_sayilari.keys(), 
        autopct='%1.1f%%',
        textprops={'color':"white"} # Yazı rengi
    )
    ax.set_title("Not Dağılımı", color="white")
    
    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)

# --- MODERN ARAYÜZ TASARIMI ---
app = ctk.CTk()
app.title("GNO PRO v2.0")
app.geometry("500x850")

# 1. Başlık ve Switch
frame_header = ctk.CTkFrame(app, fg_color="transparent")
frame_header.pack(pady=20)

lbl_baslik = ctk.CTkLabel(frame_header, text="GNO Hesaplayıcı", font=("Roboto", 28, "bold"))
lbl_baslik.pack()

switch_sim = ctk.CTkSwitch(app, text="Simülasyon Modu", command=simulasyon_kontrol, font=("Roboto", 12))
switch_sim.pack(pady=5)

# 2. Giriş Formu (Card görünümü)
frame_form = ctk.CTkFrame(app)
frame_form.pack(pady=10, padx=20, fill="x")

ctk.CTkLabel(frame_form, text="Ders Bilgileri", font=("Roboto", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

ctk.CTkLabel(frame_form, text="Ders Adı:").grid(row=1, column=0, padx=10, sticky="w")
entry_ders_adi = ctk.CTkEntry(frame_form, placeholder_text="Örn: Yapay Zeka")
entry_ders_adi.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

ctk.CTkLabel(frame_form, text="Kredi:").grid(row=2, column=0, padx=10, sticky="w")
entry_kredi = ctk.CTkEntry(frame_form, placeholder_text="Örn: 4")
entry_kredi.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

ctk.CTkLabel(frame_form, text="Harf Notu:").grid(row=3, column=0, padx=10, sticky="w")
combo_not = ctk.CTkComboBox(frame_form, values=list(NOT_KATSAYILARI.keys()))
combo_not.set("AA") # Varsayılan
combo_not.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

frame_form.columnconfigure(1, weight=1)

# 3. Aksiyon Butonları
frame_btns = ctk.CTkFrame(app, fg_color="transparent")
frame_btns.pack(pady=10, padx=20, fill="x")

btn_ekle = ctk.CTkButton(frame_btns, text="➕ Ekle", command=ders_ekle, fg_color="#1E88E5")
btn_ekle.pack(fill="x", pady=5)

btn_guncelle = ctk.CTkButton(frame_btns, text="💾 Kaydet", command=ders_guncelle, fg_color="#43A047")
# Güncelle butonu gizli başlar

# Araçlar Satırı (Sil, Hedef, Grafik)
frame_tools = ctk.CTkFrame(frame_btns, fg_color="transparent")
frame_tools.pack(fill="x", pady=5)

ctk.CTkButton(frame_tools, text="🗑️ Sil", command=ders_sil, fg_color="#e53935", width=80).pack(side="left", padx=2)
ctk.CTkButton(frame_tools, text="🎯 Hedef", command=hedef_hesapla_penceresi, fg_color="#FB8C00", width=80).pack(side="left", padx=2, expand=True, fill="x")
ctk.CTkButton(frame_tools, text="📊 Analiz", command=grafik_goster, fg_color="#8E24AA", width=80).pack(side="right", padx=2)

btn_temizle = ctk.CTkButton(frame_btns, text="Sıfırla", command=temizle, fg_color="transparent", border_width=1, text_color="#B0BEC5")
btn_temizle.pack(fill="x", pady=5)

# 4. Liste (Treeview)
# CustomTkinter'da Treeview yok, ttk.Treeview'i dark moda uyarlıyoruz
style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", 
                background="#2b2b2b", 
                foreground="white", 
                fieldbackground="#2b2b2b", 
                rowheight=30,
                borderwidth=0)
style.configure("Treeview.Heading", background="#424242", foreground="white", relief="flat")
style.map("Treeview", background=[('selected', '#1E88E5')])

frame_tree = ctk.CTkFrame(app)
frame_tree.pack(padx=20, pady=10, fill="both", expand=True)

tree = ttk.Treeview(frame_tree, columns=("Ad", "Kredi", "Not"), show="headings", height=8)
tree.heading("Ad", text="Ders Adı")
tree.heading("Kredi", text="Kredi")
tree.heading("Not", text="Harf")
tree.column("Ad", width=200)
tree.column("Kredi", width=60, anchor="center")
tree.column("Not", width=60, anchor="center")
tree.pack(fill="both", expand=True, padx=2, pady=2)

tree.bind("<Double-1>", secili_dersi_getir)

# 5. Sonuç
lbl_sonuc = ctk.CTkLabel(app, text="GNO: -", font=("Roboto", 32, "bold"), text_color="#00E5FF")
lbl_sonuc.pack(pady=20)

# Başlangıç
veritabani_yukle()
app.mainloop()