import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from pathlib import Path

# Az összes modul beimportálása a közvetlen futtatáshoz
from main import process_dataset
from transkribus import flatten_transkribus_for_kraken
from export_kraken import export_for_kraken
from generate_crops import generate_crops
from export_dataset import export_trocr_dataset

# --- Valós idejű terminál átirányítás ---
class IORedirector:
    """Elkapja a print() kimenetet és a Tkinter szövegdobozba irányítja."""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        # A Tkinter GUI frissítése a fő szálon kell történjen
        self.text_widget.after(0, self._write, text)

    def _write(self, text):
        self.text_widget.insert(tk.END, text)
        self.text_widget.see(tk.END) # Automatikus görgetés az aljára

    def flush(self):
        pass

# --- Segédfüggvények ---
def browse_folder(entry_field):
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        entry_field.delete(0, tk.END)
        entry_field.insert(0, folder_selected)

def browse_file(entry_field):
    file_selected = filedialog.askopenfilename(filetypes=[("XSD Séma", "*.xsd"), ("Minden fájl", "*.*")])
    if file_selected:
        entry_field.delete(0, tk.END)
        entry_field.insert(0, file_selected)

def run_in_thread(target_func):
    """Külön szálon indítja a feladatot, hogy a GUI reszponzív maradjon."""
    thread = threading.Thread(target=target_func, daemon=True)
    thread.start()

def clear_console():
    """Törli a beépített terminál tartalmát."""
    console_text.delete(1.0, tk.END)

def confirm_folder_deletion(folder_path, process_name):
    """Figyelmeztet, ha a célmappa nem üres és a folyamat törölné annak tartalmát."""
    target = Path(folder_path)

    if not target.exists() or not target.is_dir():
        return True

    try:
        has_content = any(target.iterdir())
    except Exception as exc:
        messagebox.showerror("Hiba", f"A mappa nem ellenorizheto: {target}\n{exc}")
        return False

    if not has_content:
        return True

    return messagebox.askyesno(
        "Torles megerositese",
        (
            f"A(z) '{target}' mappa nem ures.\n\n"
            f"A '{process_name}' folyamat torolni fogja a benne levo fajlokat.\n"
            "Biztosan folytatod?"
        ),
    )

# --- Futtató funkciók a különböző fülekhez ---
def run_xml_pipeline():
    def task():
        clear_console()
        in_dir = entry_in_main.get()
        out_dir = entry_out_main.get()
        q_dir = entry_quarantine_main.get()
        xsd_dir = entry_xsd_main.get()
        
        if not in_dir:
            messagebox.showwarning("Figyelmeztetés", "Kérlek, add meg a forrás mappát!")
            return
            
        try:
            print(">>> XML Tisztítás és Validáció indítása...\n")
            process_dataset(in_dir, out_dir, xsd_dir, q_dir)
            print("\n>>> FOLYAMAT BEFEJEZŐDÖTT!")
            messagebox.showinfo("Siker", "XML Tisztítás és Validáció befejeződött!")
        except Exception as e:
            print(f"\n[X] KRITIKUS HIBA: {e}")
            messagebox.showerror("Kritikus Hiba", str(e))
    run_in_thread(task)

def run_transkribus():
    def task():
        clear_console()
        src = entry_in_trans.get()
        out = entry_out_trans.get()
        if not src or not out:
            messagebox.showwarning("Figyelmeztetés", "Minden mezőt ki kell tölteni!")
            return
        try:
            print(">>> Transkribus mappák laposítása indítása...\n")
            flatten_transkribus_for_kraken(src, out)
            print("\n>>> FOLYAMAT BEFEJEZŐDÖTT!")
            messagebox.showinfo("Siker", "Transkribus mappák laposítása sikeres!")
        except Exception as e:
            print(f"\n[X] HIBA: {e}")
            messagebox.showerror("Hiba", f"Hiba történt:\n{e}")
    run_in_thread(task)

def run_kraken_export():
    def task():
        clear_console()
        xml_dir = entry_xml_kraken.get()
        img_dir = entry_img_kraken.get()
        out_dir = entry_out_kraken.get()
        do_zip = zip_var_kraken.get()
        
        if not xml_dir or not img_dir or not out_dir:
            messagebox.showwarning("Figyelmeztetés", "Minden mezőt ki kell tölteni!")
            return

        if not confirm_folder_deletion(out_dir, "Kraken Export"):
            print("[MEGSZAKITVA] A felhasznalo nem engedelyezte a kimeneti mappa torleset.")
            return

        try:
            print(">>> Kraken Adathalmaz Export indítása...\n")
            export_for_kraken(xml_dir, img_dir, out_dir, zip_output=do_zip, allow_delete_existing=True)
            print("\n>>> FOLYAMAT BEFEJEZŐDÖTT!")
            messagebox.showinfo("Siker", "Kraken adathalmaz exportálása sikeres!")
        except Exception as e:
            print(f"\n[X] HIBA: {e}")
            messagebox.showerror("Hiba", f"Hiba történt:\n{e}")
    run_in_thread(task)

def run_trocr_export():
    def task():
        clear_console()
        src_dir = entry_src_trocr.get()
        crops_dir = entry_crops_trocr.get()
        out_dir = entry_out_trocr.get()
        do_zip = zip_var.get()
        
        if not src_dir or not crops_dir or not out_dir:
            messagebox.showwarning("Figyelmeztetés", "Minden mezőt ki kell tölteni!")
            return

        if not confirm_folder_deletion(out_dir, "TrOCR Export"):
            print("[MEGSZAKITVA] A felhasznalo nem engedelyezte a kimeneti mappa torleset.")
            return

        try:
            print(">>> TrOCR Képkivágások (Crops) generálása...\n")
            generate_crops(src_dir, crops_dir, padding=5)
            print("\n>>> TrOCR Adathalmaz exportálása...\n")
            export_trocr_dataset(src_dir, crops_dir, out_dir, zip_output=do_zip, allow_delete_existing=True)
            print("\n>>> FOLYAMAT BEFEJEZŐDÖTT!")
            messagebox.showinfo("Siker", "TrOCR adatbázis és képkivágások generálása sikeres!")
        except Exception as e:
            print(f"\n[X] HIBA: {e}")
            messagebox.showerror("Hiba", f"Hiba történt:\n{e}")
    run_in_thread(task)

# --- GUI Felépítése ---
root = tk.Tk()
root.title("HTR Adatelőkészítő Központ")
root.geometry("750x700") # Nagyobb ablak, hogy kiférjen a terminál
root.configure(padx=10, pady=10)

# Felső rész: Fülek
notebook = ttk.Notebook(root)
notebook.pack(expand=False, fill='x', pady=(0, 10))

# --- TAB 1: Eredeti XML Javító ---
tab1 = ttk.Frame(notebook)
notebook.add(tab1, text='1. XML Javító')
tk.Label(tab1, text="Forrás mappa (XML):").grid(row=0, column=0, sticky="e", pady=10, padx=5)
entry_in_main = tk.Entry(tab1, width=45)
entry_in_main.grid(row=0, column=1)
tk.Button(tab1, text="Tallózás", command=lambda: browse_folder(entry_in_main)).grid(row=0, column=2, padx=5)
tk.Label(tab1, text="Kimeneti mappa:").grid(row=1, column=0, sticky="e", pady=10, padx=5)
entry_out_main = tk.Entry(tab1, width=45)
entry_out_main.insert(0, "clean_xml")
entry_out_main.grid(row=1, column=1)
tk.Button(tab1, text="Tallózás", command=lambda: browse_folder(entry_out_main)).grid(row=1, column=2, padx=5)
tk.Label(tab1, text="Karantén mappa:").grid(row=2, column=0, sticky="e", pady=10, padx=5)
entry_quarantine_main = tk.Entry(tab1, width=45)
entry_quarantine_main.insert(0, "quarantine_xml")
entry_quarantine_main.grid(row=2, column=1)
tk.Button(tab1, text="Tallózás", command=lambda: browse_folder(entry_quarantine_main)).grid(row=2, column=2, padx=5)
tk.Label(tab1, text="XSD Séma fájl:").grid(row=3, column=0, sticky="e", pady=10, padx=5)
entry_xsd_main = tk.Entry(tab1, width=45)
entry_xsd_main.insert(0, "pagexml/pagecontent.xsd")
entry_xsd_main.grid(row=3, column=1)
tk.Button(tab1, text="Tallózás", command=lambda: browse_file(entry_xsd_main)).grid(row=3, column=2, padx=5)
tk.Button(tab1, text="XML Tisztítás Indítása", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), command=run_xml_pipeline).grid(row=4, column=0, columnspan=3, pady=15, ipadx=10, ipady=5)

# --- TAB 2: Transkribus ---
tab2 = ttk.Frame(notebook)
notebook.add(tab2, text='2. Transkribus')
tk.Label(tab2, text="Főmappa (amely tartalmazza az alkönyvtárakat):").grid(row=0, column=0, sticky="e", pady=15, padx=5)
entry_in_trans = tk.Entry(tab2, width=45)
entry_in_trans.grid(row=0, column=1)
tk.Button(tab2, text="Tallózás", command=lambda: browse_folder(entry_in_trans)).grid(row=0, column=2, padx=5)
tk.Label(tab2, text="Kimeneti mappa (Laposított):").grid(row=1, column=0, sticky="e", pady=15, padx=5)
entry_out_trans = tk.Entry(tab2, width=45)
entry_out_trans.grid(row=1, column=1)
tk.Button(tab2, text="Tallózás", command=lambda: browse_folder(entry_out_trans)).grid(row=1, column=2, padx=5)
tk.Button(tab2, text="Mappák Laposítása", bg="#2196F3", fg="white", font=("Arial", 10, "bold"), command=run_transkribus).grid(row=2, column=0, columnspan=3, pady=20, ipadx=10, ipady=5)

# --- TAB 3: Kraken Export ---
tab3 = ttk.Frame(notebook)
notebook.add(tab3, text='3. Kraken Export')
tk.Label(tab3, text="Forrás XML mappa:").grid(row=0, column=0, sticky="e", pady=15, padx=5)
entry_xml_kraken = tk.Entry(tab3, width=45)
entry_xml_kraken.grid(row=0, column=1)
tk.Button(tab3, text="Tallózás", command=lambda: browse_folder(entry_xml_kraken)).grid(row=0, column=2, padx=5)
tk.Label(tab3, text="Forrás Képek mappája:").grid(row=1, column=0, sticky="e", pady=15, padx=5)
entry_img_kraken = tk.Entry(tab3, width=45)
entry_img_kraken.grid(row=1, column=1)
tk.Button(tab3, text="Tallózás", command=lambda: browse_folder(entry_img_kraken)).grid(row=1, column=2, padx=5)
tk.Label(tab3, text="Kimeneti (Kraken Ready) mappa:").grid(row=2, column=0, sticky="e", pady=15, padx=5)
entry_out_kraken = tk.Entry(tab3, width=45)
entry_out_kraken.grid(row=2, column=1)
tk.Button(tab3, text="Tallózás", command=lambda: browse_folder(entry_out_kraken)).grid(row=2, column=2, padx=5)
zip_var_kraken = tk.BooleanVar(value=True)
tk.Checkbutton(tab3, text="Csomagolás ZIP fájlba a végén", variable=zip_var_kraken).grid(row=3, column=0, columnspan=3, pady=5)
tk.Button(tab3, text="Kraken Adathalmaz Exportálása", bg="#FF9800", fg="white", font=("Arial", 10, "bold"), command=run_kraken_export).grid(row=4, column=0, columnspan=3, pady=15, ipadx=10, ipady=5)

# --- TAB 4: TrOCR Export ---
tab4 = ttk.Frame(notebook)
notebook.add(tab4, text='4. TrOCR Export')
tk.Label(tab4, text="Forrás mappa (XML + Nagy képek):").grid(row=0, column=0, sticky="e", pady=15, padx=5)
entry_src_trocr = tk.Entry(tab4, width=45)
entry_src_trocr.grid(row=0, column=1)
tk.Button(tab4, text="Tallózás", command=lambda: browse_folder(entry_src_trocr)).grid(row=0, column=2, padx=5)
tk.Label(tab4, text="Kivágások (Crops) mappája:").grid(row=1, column=0, sticky="e", pady=15, padx=5)
entry_crops_trocr = tk.Entry(tab4, width=45)
entry_crops_trocr.insert(0, "output_crops")
entry_crops_trocr.grid(row=1, column=1)
tk.Button(tab4, text="Tallózás", command=lambda: browse_folder(entry_crops_trocr)).grid(row=1, column=2, padx=5)
tk.Label(tab4, text="TrOCR Dataset kimenet:").grid(row=2, column=0, sticky="e", pady=15, padx=5)
entry_out_trocr = tk.Entry(tab4, width=45)
entry_out_trocr.insert(0, "trocr_dataset")
entry_out_trocr.grid(row=2, column=1)
tk.Button(tab4, text="Tallózás", command=lambda: browse_folder(entry_out_trocr)).grid(row=2, column=2, padx=5)
zip_var = tk.BooleanVar(value=True)
tk.Checkbutton(tab4, text="Csomagolás ZIP fájlba a végén", variable=zip_var).grid(row=3, column=0, columnspan=3, pady=5)
tk.Button(tab4, text="TrOCR Pipeline Futtatása", bg="#9C27B0", fg="white", font=("Arial", 10, "bold"), command=run_trocr_export).grid(row=4, column=0, columnspan=3, pady=10, ipadx=10, ipady=5)

# --- Alsó rész: Terminál kimenet ---
console_frame = tk.LabelFrame(root, text=" Rendszerüzenetek (Terminál) ", font=("Arial", 10, "bold"))
console_frame.pack(expand=True, fill='both')

# Gördítősáv és szövegdoboz a terminálnak
scrollbar = tk.Scrollbar(console_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

console_text = tk.Text(console_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
console_text.pack(expand=True, fill='both', padx=5, pady=5)
scrollbar.config(command=console_text.yview)

# Stdout és Stderr átirányítása a Text widgetbe
sys.stdout = IORedirector(console_text)
sys.stderr = IORedirector(console_text)

print("Üdvözöllek a HTR Adatelőkészítő Központban!")
print("A rendszer készen áll a futtatásra. Válassz egy funkciót a fenti fülekből.\n")

root.mainloop()

# Amikor az ablak bezárul, visszaállítjuk a normál kimenetet
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__