# -*- coding: utf-8 -*-
import sys
import subprocess
import os
import tkinter as tk
from tkinter import ttk, messagebox
from io import BytesIO
import ctypes

# Desactivation des alertes de deprecation pour Pillow
import warnings
warnings.filterwarnings("ignore")

def install_and_import(package):
    try:
        return __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return __import__(package)

try:
    requests = install_and_import('requests')
    from PIL import Image, ImageTk
except Exception as e:
    root_err = tk.Tk()
    root_err.withdraw()
    messagebox.showerror("Erreur de dependances", f"Impossible de charger les bibliotheques : {e}")
    os._exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv("V1.env")
except Exception:
    pass

WEBHOOK_URL  = os.getenv("WEBHOOK_URL", "")
TMDB_API_KEY = os.getenv("API_KEY", "")

class RebirthApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("REBIRTH - Upload Notifier")
        
        # --- DIMENSIONS DE LA FENETRE ---
        window_width = 1250
        window_height = 980
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        center_x = int(screen_width/2 - window_width/2)
        center_y = 20 
        
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.configure(bg="#1a1a1a")
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
        
        # --- STYLE ---
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.style.configure("Vertical.TScrollbar", 
                             gripcount=0, background="#333333", darkcolor="#1a1a1a", 
                             lightcolor="#1a1a1a", troughcolor="#1a1a1a", 
                             bordercolor="#1a1a1a", arrowcolor="#e67e22")
        
        self.style.layout("Vertical.TScrollbar", 
            [('Vertical.Scrollbar.trough', {'children': [('Vertical.Scrollbar.thumb', {'expand': '1'})], 'sticky': 'ns'})])

        self.style.configure("TFrame", background="#1a1a1a")
        self.style.configure("TLabel", background="#1a1a1a", foreground="white", font=("Arial", 11))
        
        self.current_movie = None
        self.images_cache = []
        self.current_poster_tk = None
        self.active_canvas = None

        self.setup_ui()
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        if self.active_canvas:
            self.active_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_exit(self):
        try:
            self.root.destroy()
        except: pass
        os._exit(0)

    def clear_search(self):
        """Efface le contenu du champ de recherche et remet le focus dessus"""
        self.search_entry.delete(0, tk.END)
        self.search_entry.focus_set()

    def setup_ui(self):
        header = tk.Frame(self.root, bg="#e67e22", height=60)
        header.pack(fill="x")
        tk.Label(header, text="REBIRTH UPLOAD BOT", bg="#e67e22", fg="white", font=("Arial", 16, "bold")).pack(pady=15)

        self.main_container = tk.Frame(self.root, bg="#1a1a1a")
        self.main_container.pack(fill="both", expand=True, padx=25, pady=25)

        search_frame = tk.Frame(self.main_container, bg="#1a1a1a")
        search_frame.pack(fill="x", pady=10)
        
        tk.Label(search_frame, text="RECHERCHE TMDB (NOM OU ID) :", fg="#e67e22", bg="#1a1a1a", font=("Arial", 11, "bold")).pack(side="left")
        
        entry_container = tk.Frame(search_frame, bg="#2c2c2c")
        entry_container.pack(side="left", fill="x", expand=True, padx=15)
        
        self.search_entry = tk.Entry(entry_container, bg="#2c2c2c", fg="white", insertbackground="white", font=("Arial", 12), bd=0)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(10, 0), ipady=8)
        self.search_entry.bind("<Return>", lambda e: self.search_movie())

        self.clear_btn = tk.Label(entry_container, text="✕", bg="#2c2c2c", fg="#7f8c8d", font=("Arial", 12, "bold"), cursor="hand2")
        self.clear_btn.pack(side="right", padx=10)
        self.clear_btn.bind("<Button-1>", lambda e: self.clear_search())
        
        tk.Button(search_frame, text="RECHERCHER", bg="#e67e22", fg="white", font=("Arial", 11, "bold"), 
                  relief="flat", padx=15, command=self.search_movie).pack(side="right", padx=5)

        self.results_canvas = tk.Canvas(self.main_container, bg="#1a1a1a", highlightthickness=0)
        self.results_scroll = ttk.Scrollbar(self.main_container, orient="vertical", command=self.results_canvas.yview, style="Vertical.TScrollbar")
        self.results_frame = tk.Frame(self.results_canvas, bg="#1a1a1a")
        
        self.results_frame.bind("<Configure>", lambda e: self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all")))
        self.results_canvas.create_window((0, 0), window=self.results_frame, anchor="nw", width=1180)
        self.results_canvas.configure(yscrollcommand=self.results_scroll.set)
        self.results_canvas.pack(side="left", fill="both", expand=True)
        self.results_scroll.pack(side="right", fill="y")
        
        self.active_canvas = self.results_canvas
        self.form_outer_frame = tk.Frame(self.root, bg="#2c2c2c")

    def search_movie(self):
        query = self.search_entry.get().strip()
        if not query: return
        for widget in self.results_frame.winfo_children(): widget.destroy()
        self.images_cache = []
        
        try:
            if query.isdigit():
                url = f"https://api.themoviedb.org/3/movie/{query}?api_key={TMDB_API_KEY}&language=fr-FR"
                res_data = requests.get(url, timeout=10).json()
                res = [res_data] if "id" in res_data else []
            else:
                url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=fr-FR&query={query}&include_adult=false"
                res = requests.get(url, timeout=10).json().get("results", [])[:20]
            
            for movie in res: self.add_movie_row(movie)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur TMDB : {e}")

    def add_movie_row(self, movie):
        row = tk.Frame(self.results_frame, bg="#262626", pady=8)
        row.pack(fill="x", pady=4, padx=5)
        
        poster_path = movie.get('poster_path')
        img_tk = None
        if poster_path:
            try:
                img_url = f"https://image.tmdb.org/t/p/w92{poster_path}"
                r = requests.get(img_url, timeout=5)
                img = Image.open(BytesIO(r.content)).resize((70, 105), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                self.images_cache.append(img_tk)
            except: pass
        
        tk.Label(row, image=img_tk, bg="#262626").pack(side="left", padx=15) if img_tk else tk.Label(row, text="N/A", bg="#262626", fg="gray", width=10).pack(side="left", padx=15)
        
        info_frame = tk.Frame(row, bg="#262626")
        info_frame.pack(side="left", padx=10, fill="both", expand=True)
        
        title_year = f"{movie.get('title')} ({(movie.get('release_date') or '0000')[:4]})"
        tk.Label(info_frame, text=title_year, fg="white", bg="#262626", font=("Arial", 12, "bold"), anchor="w").pack(fill="x")
        
        tk.Button(row, text="SELECTIONNER", bg="#e67e22", fg="white", font=("Arial", 10, "bold"), relief="flat", padx=15, 
                  command=lambda m=movie: self.open_details_form(m)).pack(side="right", padx=20)

    def toggle_maj(self, event=None):
        current = self.maj_var.get()
        self.maj_var.set(not current)
        if self.maj_var.get():
            self.maj_box.config(text="▣", fg="#2ecc71")
        else:
            self.maj_box.config(text="▢", fg="#e74c3c")

    def show_context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0, bg="#2c2c2c", fg="white", activebackground="#e67e22")
        menu.add_command(label="Coller", command=self.paste_to_rel)
        menu.tk_popup(event.x_root, event.y_root)

    def paste_to_rel(self):
        try:
            text = self.root.clipboard_get()
            self.rel_entry.insert(tk.INSERT, text)
        except tk.TclError:
            pass

    def open_details_form(self, movie):
        self.current_movie = movie
        self.main_container.pack_forget()
        self.form_outer_frame.pack(fill="both", expand=True)
        
        for w in self.form_outer_frame.winfo_children(): w.destroy()
        
        form_canvas = tk.Canvas(self.form_outer_frame, bg="#2c2c2c", highlightthickness=0)
        form_scroll_bar = ttk.Scrollbar(self.form_outer_frame, orient="vertical", command=form_canvas.yview, style="Vertical.TScrollbar")
        form_content = tk.Frame(form_canvas, bg="#2c2c2c")
        
        form_content.bind("<Configure>", lambda e: form_canvas.configure(scrollregion=form_canvas.bbox("all")))
        form_canvas.create_window((0, 0), window=form_content, anchor="nw", width=1220)
        form_canvas.configure(yscrollcommand=form_scroll_bar.set)
        
        form_canvas.pack(side="left", fill="both", expand=True)
        form_scroll_bar.pack(side="right", fill="y")
        self.active_canvas = form_canvas

        poster_path = movie.get('poster_path')
        if poster_path:
            try:
                img_url = f"https://image.tmdb.org/t/p/w185{poster_path}"
                r = requests.get(img_url, timeout=5)
                img = Image.open(BytesIO(r.content)).resize((120, 180), Image.Resampling.LANCZOS)
                self.current_poster_tk = ImageTk.PhotoImage(img)
                tk.Label(form_content, image=self.current_poster_tk, bg="#2c2c2c").pack(pady=(30, 0))
            except: pass
        
        tk.Label(form_content, text=movie['title'].upper(), bg="#2c2c2c", fg="#e67e22", font=("Arial", 16, "bold")).pack(pady=(15, 30))
        
        tk.Label(form_content, text="NOM DE LA RELEASE :", bg="#2c2c2c", fg="#bdc3c7", font=("Arial", 11, "bold")).pack(anchor="w", padx=50)
        
        self.rel_entry = tk.Entry(form_content, bg="#1a1a1a", fg="#2ecc71", bd=0, font=("Consolas", 13, "bold"), insertbackground="white", justify="center")
        self.rel_entry.pack(fill="x", padx=50, pady=10, ipady=12) 
        
        self.rel_entry.bind("<Button-3>", self.show_context_menu)

        self.maj_var = tk.BooleanVar(value=False)
        maj_frame = tk.Frame(form_content, bg="#2c2c2c", cursor="hand2")
        maj_frame.pack(anchor="w", padx=100, pady=20)

        self.maj_box = tk.Label(maj_frame, text="▢", font=("Arial", 32), bg="#2c2c2c", fg="#e74c3c")
        self.maj_box.pack(side="left")
        
        self.maj_label = tk.Label(maj_frame, text=" MISE À JOUR (O/N)", font=("Arial", 12, "bold"), bg="#2c2c2c", fg="white")
        self.maj_label.pack(side="left", padx=10)

        maj_frame.bind("<Button-1>", self.toggle_maj)
        self.maj_box.bind("<Button-1>", self.toggle_maj)
        self.maj_label.bind("<Button-1>", self.toggle_maj)

        tk.Label(form_content, text="STATUTS DES TRACKERS :", bg="#2c2c2c", fg="#bdc3c7", font=("Arial", 11, "bold")).pack(anchor="w", padx=100, pady=(15, 5))
        self.trackers = ["TOS", "ABN", "Torr9", "C411", "LACALE"]
        self.tracker_vars = {}
        for t in self.trackers:
            row = tk.Frame(form_content, bg="#34495e", padx=15, pady=8)
            row.pack(fill="x", padx=100, pady=6) 
            tk.Label(row, text=t, bg="#34495e", fg="white", font=("Arial", 11, "bold"), width=10).pack(side="left")
            var = tk.StringVar(value="Uploadé")
            cb = ttk.Combobox(row, textvariable=var, values=["Uploadé", "Non uploade", "Pending"], width=15, state="readonly")
            cb.pack(side="left", padx=20)
            reason = tk.Entry(row, bg="#1a1a1a", fg="gray", font=("Arial", 10), bd=0)
            reason.pack(side="left", fill="x", expand=True, padx=5, ipady=5)
            reason.insert(0, "Raison si erreur...")
            reason.bind("<FocusIn>", lambda e, r=reason: self._on_reason_focus_in(r))
            reason.bind("<FocusOut>", lambda e, r=reason: self._on_reason_focus_out(r))
            self.tracker_vars[t] = (var, reason)

        btn_f = tk.Frame(form_content, bg="#2c2c2c")
        btn_f.pack(fill="x", padx=100, pady=40)
        tk.Button(btn_f, text="RETOUR", bg="#7f8c8d", fg="white", font=("Arial", 12, "bold"), width=15, height=2, relief="flat", command=self.cancel_form).pack(side="left")
        tk.Button(btn_f, text="ENVOYER SUR DISCORD", bg="#27ae60", fg="white", font=("Arial", 12, "bold"), height=2, relief="flat", command=self.send_final).pack(side="left", fill="x", expand=True, padx=20)
        tk.Button(btn_f, text="QUITTER", bg="#e74c3c", fg="white", font=("Arial", 12, "bold"), width=15, height=2, relief="flat", command=self.on_exit).pack(side="left")

    def _on_reason_focus_in(self, entry):
        if entry.get() == "Raison si erreur...":
            entry.delete(0, tk.END)
            entry.config(fg="white")

    def _on_reason_focus_out(self, entry):
        if not entry.get().strip():
            entry.insert(0, "Raison si erreur...")
            entry.config(fg="gray")

    def cancel_form(self):
        self.form_outer_frame.pack_forget()
        self.main_container.pack(fill="both", expand=True, padx=25, pady=25)
        self.active_canvas = self.results_canvas

    def send_final(self):
        rel = self.rel_entry.get().strip() or "NOM_INCONNU"
        uploads = {}
        for t in self.trackers:
            status, reason_w = self.tracker_vars[t]
            reason_txt = reason_w.get()
            if reason_txt == "Raison si erreur...": reason_txt = ""
            uploads[t] = {'status': status.get(), 'reason': reason_txt}
        
        m = self.current_movie
        img = f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get('poster_path') else None
        
        try:
            self.post_to_discord(m['title'], (m.get('release_date') or "0000")[:4], rel, img, uploads, self.maj_var.get(), m['id'])
            messagebox.showinfo("REBIRTH", "Notification envoyee !")
            self.cancel_form()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur d envoi : {e}")

    def post_to_discord(self, title, year, rel, img, uploads, is_maj, fid):
        status_lines = []
        for site, data in uploads.items():
            s = data['status']
            icon = ":white_check_mark:" if s == "Uploadé" else (":clock4:" if s == "Pending" else ":x:")
            line = f"**{site} :** {icon}"
            # Modification : On met la raison en gras avec **...**
            if s != "Uploadé" and data['reason']: line += f" **`[`{data['reason']}`]`**"
            status_lines.append(line)
        
        maj_text = "🚨 MISE A JOUR 🚨\n" if is_maj else ""
        
        # Ajout d'un double saut de ligne \n\n entre chaque ligne de tracker pour plus d'espace
        upload_block = "\n\n".join(status_lines)
        
        desc = f"ID TMDB : **{fid}**\n\n" \
               f"**Nom de la Release :**\n" \
               f"```fix\n{rel}```\n" \
               f"**Statut des Uploads :**\n" \
               f"{maj_text}\n" \
               + upload_block
        
        embed = {
            "title": f"🎬 Nom du film : {title} ({year})",
            "description": desc,
            "color": 16776960 if is_maj else 15548997,
            "thumbnail": {"url": img} if img else None,
        }
        requests.post(WEBHOOK_URL, json={"content": "@everyone", "embeds": [embed]}, timeout=10)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = RebirthApp()
        app.run()
    except Exception as fatal:
        os._exit(1)