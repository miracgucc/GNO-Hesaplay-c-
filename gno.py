import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc

NOT_KATSAYILARI = {
    'AA': 4.0, 'BA': 3.5, 'BB': 3.0, 'CB': 2.5,
    'CC': 2.0, 'DC': 1.5, 'DD': 1.0, 'FF': 0.0
}

ders_listesi = []  # (id, ders_adi, kredi, harf_notu)
secili_ders_index = None

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
            ders_listesi.append(row)
            tree.insert("", tk.END, values=(row[1], row[2], row[3]))
    except Exception as e:
        messagebox.showerror("SQL Hatası", str(e))

def ders_ekle():
    ders_adi = entry_ders_adi.get().strip()
    kredi = entry_kredi.get().strip()
    harf_notu = combo_not.get()

    if not ders_adi or not kredi or harf_notu not in NOT_KATSAYILARI:
        messagebox.showerror("Hata", "Lütfen tüm alanları doğru doldurun!")
        return
    try:
        kredi = float(kredi)
        if kredi <= 0:
            raise ValueError("Kredi pozitif olmalı!")
    except ValueError as e:
        messagebox.showerror("Hata", f"Kredi sayısal ve pozitif olmalı!\n{e}")
        return

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

    entry_ders_adi.delete(0, tk.END)
    entry_kredi.delete(0, tk.END)
    combo_not.set('')

def secili_dersi_getir(event):
    global secili_ders_index
    secili = tree.focus()
    if not secili:
        return
    values = tree.item(secili, 'values')
    for i, ders in enumerate(ders_listesi):
        if ders[1] == values[0] and str(ders[2]) == str(values[1]) and ders[3] == values[2]:
            secili_ders_index = i
            break
    else:
        secili_ders_index = None
        return

    ders_adi, kredi, harf_notu = values
    entry_ders_adi.delete(0, tk.END)
    entry_ders_adi.insert(0, ders_adi)

    entry_kredi.delete(0, tk.END)
    entry_kredi.insert(0, kredi)

    combo_not.set(harf_notu)

    btn_ekle.pack_forget()
    btn_guncelle.pack(fill='x', pady=5)

def ders_guncelle():
    global secili_ders_index
    if secili_ders_index is None:
        messagebox.showwarning("Uyarı", "Lütfen düzenlemek için bir ders seçin!")
        return

    ders_adi = entry_ders_adi.get().strip()
    kredi = entry_kredi.get().strip()
    harf_notu = combo_not.get()

    if not ders_adi or not kredi or harf_notu not in NOT_KATSAYILARI:
        messagebox.showerror("Hata", "Lütfen tüm alanları doğru doldurun!")
        return
    try:
        kredi = float(kredi)
        if kredi <= 0:
            raise ValueError("Kredi pozitif olmalı!")
    except ValueError as e:
        messagebox.showerror("Hata", f"Kredi sayısal ve pozitif olmalı!\n{e}")
        return

    ders_id = ders_listesi[secili_ders_index][0]

    if conn and ders_id is not None:
        try:
            cursor.execute("UPDATE dersler SET ders_adi=?, kredi=?, harf_notu=? WHERE id=?",
                           (ders_adi, kredi, harf_notu, ders_id))
            conn.commit()
        except Exception as e:
            messagebox.showerror("SQL Hatası", str(e))

    ders_listesi[secili_ders_index] = (ders_id, ders_adi, kredi, harf_notu)

    # Treeview güncelle
    for item in tree.get_children():
        vals = tree.item(item, 'values')
        if vals[0] == ders_listesi[secili_ders_index][1] and str(vals[1]) == str(ders_listesi[secili_ders_index][2]) and vals[2] == ders_listesi[secili_ders_index][3]:
            tree.delete(item)
            break
    tree.insert("", secili_ders_index, values=(ders_adi, kredi, harf_notu))

    entry_ders_adi.delete(0, tk.END)
    entry_kredi.delete(0, tk.END)
    combo_not.set('')

    btn_guncelle.pack_forget()
    btn_ekle.pack(fill='x', pady=5)
    secili_ders_index = None
    label_sonuc.config(text="GNO: -")

def ders_sil():
    global secili_ders_index
    secili = tree.focus()
    if not secili:
        messagebox.showwarning("Uyarı", "Silmek için bir ders seçin!")
        return
    if messagebox.askyesno("Onay", "Seçili dersi silmek istediğinize emin misiniz?"):
        # Bul index
        values = tree.item(secili, 'values')
        for i, ders in enumerate(ders_listesi):
            if ders[1] == values[0] and str(ders[2]) == str(values[1]) and ders[3] == values[2]:
                secili_ders_index = i
                break
        else:
            secili_ders_index = None
            return

        ders_id = ders_listesi[secili_ders_index][0]

        if conn and ders_id is not None:
            try:
                cursor.execute("DELETE FROM dersler WHERE id=?", (ders_id,))
                conn.commit()
            except Exception as e:
                messagebox.showerror("SQL Hatası", str(e))
                return
        del ders_listesi[secili_ders_index]
        tree.delete(secili)

        entry_ders_adi.delete(0, tk.END)
        entry_kredi.delete(0, tk.END)
        combo_not.set('')
        btn_guncelle.pack_forget()
        btn_ekle.pack(fill='x', pady=5)
        label_sonuc.config(text="GNO: -")
        secili_ders_index = None

def gno_hesapla():
    if not ders_listesi:
        messagebox.showwarning("Uyarı", "Ders listesi boş!")
        return

    toplam_kredi = 0
    toplam_puan = 0
    for _, kredi, harf_notu in ders_listesi:
        katsayi = NOT_KATSAYILARI[harf_notu]
        toplam_kredi += kredi
        toplam_puan += kredi * katsayi

    gno = toplam_puan / toplam_kredi if toplam_kredi > 0 else 0
    label_sonuc.config(text=f"GNO: {gno:.2f}")

def temizle():
    global secili_ders_index
    if messagebox.askyesno("Onay", "Tüm dersler silinsin mi?"):
        if conn:
            try:
                cursor.execute("DELETE FROM dersler")
                conn.commit()
            except Exception as e:
                messagebox.showerror("SQL Hatası", str(e))
                return
        ders_listesi.clear()
        for item in tree.get_children():
            tree.delete(item)
        label_sonuc.config(text="GNO: -")
        secili_ders_index = None
        btn_guncelle.pack_forget()
        btn_ekle.pack(fill='x', pady=5)

def on_enter(e):
    e.widget['background'] = '#2196F3'
    e.widget['foreground'] = 'white'

def on_leave(e):
    e.widget['background'] = '#1976D2'
    e.widget['foreground'] = 'white'

# Pencere ayarları
pencere = tk.Tk()
pencere.title("GNO Hesaplayıcı")
pencere.geometry("500x700")
pencere.configure(bg="#121212")  # koyu arka plan
pencere.resizable(True, True)

style = ttk.Style(pencere)
style.theme_use('clam')

# Treeview stil ayarı (alternatif satır rengi)
style.configure("mystyle.Treeview",
                background="#1e1e1e",
                foreground="white",
                fieldbackground="#1e1e1e",
                rowheight=30,
                font=('Segoe UI', 11))
style.map('Treeview', background=[('selected', '#2196F3')])

# Buton renkleri
btn_bg = '#1976D2'
btn_hover_bg = '#2196F3'

# Başlık
baslik = tk.Label(pencere, text="GNO Hesaplayıcı", font=("Segoe UI", 28, "bold"),
                  bg="#121212", fg="#00e5ff")
baslik.pack(pady=20)

# Form Frame
form_frame = tk.Frame(pencere, bg="#121212")
form_frame.pack(pady=10, padx=20, fill='x')

tk.Label(form_frame, text="Ders Adı:", font=("Segoe UI", 13), bg="#121212", fg="white").grid(row=0, column=0, sticky="w", pady=10)
entry_ders_adi = tk.Entry(form_frame, font=("Segoe UI", 13), bg="#1e1e1e", fg="white", insertbackground='white', relief='flat')
entry_ders_adi.grid(row=0, column=1, sticky="ew", padx=15)

tk.Label(form_frame, text="Kredi:", font=("Segoe UI", 13), bg="#121212", fg="white").grid(row=1, column=0, sticky="w", pady=10)
entry_kredi = tk.Entry(form_frame, font=("Segoe UI", 13), bg="#1e1e1e", fg="white", insertbackground='white', relief='flat')
entry_kredi.grid(row=1, column=1, sticky="ew", padx=15)

tk.Label(form_frame, text="Harf Notu:", font=("Segoe UI", 13), bg="#121212", fg="white").grid(row=2, column=0, sticky="w", pady=10)
combo_not = ttk.Combobox(form_frame, values=list(NOT_KATSAYILARI.keys()), font=("Segoe UI", 13))
combo_not.grid(row=2, column=1, sticky="ew", padx=15)

form_frame.columnconfigure(1, weight=1)

# Buton Frame
btn_frame = tk.Frame(pencere, bg="#121212")
btn_frame.pack(pady=15, padx=25, fill='x')

def make_button(text, cmd):
    btn = tk.Button(btn_frame, text=text, command=cmd,
                    font=("Segoe UI", 12, "bold"),
                    bg=btn_bg, fg="white",
                    activebackground=btn_hover_bg,
                    activeforeground="white",
                    relief="flat",
                    padx=15, pady=12,
                    cursor="hand2",
                    borderwidth=0)
    btn.pack(fill='x', pady=7)
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn

btn_ekle = make_button("➕ Ders Ekle", ders_ekle)
btn_guncelle = make_button("✏️ Ders Guncelle", ders_guncelle)
btn_guncelle.pack_forget()
btn_sil = make_button("🗑️ Ders Sil", ders_sil)
btn_hesapla = make_button("🧮 GNO Hesapla", gno_hesapla)
btn_temizle = make_button("🗑️ Temizle", temizle)

# Ders Listesi Treeview
ders_listesi_label = tk.Label(pencere, text="📋 Eklenen Dersler:", font=("Segoe UI", 15),
                              bg="#121212", fg="white")
ders_listesi_label.pack(anchor="w", padx=25, pady=(15, 5))

tree = ttk.Treeview(pencere, columns=("Ders Adı", "Kredi", "Harf Notu"), show='headings', style="mystyle.Treeview", height=12)
tree.pack(padx=25, pady=10, fill='both', expand=True)

tree.heading("Ders Adı", text="Ders Adı")
tree.heading("Kredi", text="Kredi")
tree.heading("Harf Notu", text="Harf Notu")

tree.column("Ders Adı", anchor="w", width=220)
tree.column("Kredi", anchor="center", width=80)
tree.column("Harf Notu", anchor="center", width=80)

tree.bind("<Double-1>", secili_dersi_getir)

# Sonuç Label
label_sonuc = tk.Label(pencere, text="GNO: -", font=("Segoe UI", 26, "bold"),
                       bg="#121212", fg="#00e5ff")
label_sonuc.pack(pady=20)

# Veritabanından yükleme
veritabani_yukle()

pencere.mainloop()
