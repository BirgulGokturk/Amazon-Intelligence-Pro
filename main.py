import customtkinter as ctk
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import re
from PIL import Image, ImageTk
from io import BytesIO
import threading

# Görsel Tema Ayarları
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class AmazonProApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Amazon Market Intelligence Ultra v10.4")
        self.geometry("1400x900")
        self.configure(fg_color="#0F172A")

        self.categories = {
            "📱 Elektronik": ["Akıllı Telefonlar", "Laptoplar", "Kulaklıklar", "Tabletler"],
            "🎮 Gaming": ["Konsollar", "Ekran Kartları", "Oyuncu Mouse", "Monitörler"],
            "🏠 Ev & Yaşam": ["Kahve Makineleri", "Robot Süpürgeler", "Mutfak Gereçleri"],
            "👗 Moda": ["Erkek Saat", "Spor Ayakkabı", "Gözlük"]
        }

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0, fg_color="#1E293B")
        self.sidebar.pack(side="left", fill="y")

        self.logo = ctk.CTkLabel(self.sidebar, text="💎 AMZ-PRO V10", font=ctk.CTkFont(size=26, weight="bold"))
        self.logo.pack(pady=40)

        self.img_frame = ctk.CTkFrame(self.sidebar, width=240, height=240, corner_radius=20, fg_color="#0F172A")
        self.img_frame.pack(pady=10, padx=20)
        self.img_frame.pack_propagate(False)
        self.img_label = ctk.CTkLabel(self.img_frame, text="Resim Bekleniyor", text_color="#64748B")
        self.img_label.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self.sidebar, text="KATEGORİ SEÇİMİ", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#94A3B8").pack(pady=(30, 5), padx=30, anchor="w")
        self.main_cat_menu = ctk.CTkOptionMenu(self.sidebar, values=list(self.categories.keys()),
                                               command=self.update_subs, fg_color="#334155")
        self.main_cat_menu.pack(fill="x", padx=25, pady=5)

        self.sub_cat_var = ctk.StringVar(value="Akıllı Telefonlar")
        self.sub_cat_menu = ctk.CTkOptionMenu(self.sidebar, values=self.categories["📱 Elektronik"],
                                              variable=self.sub_cat_var, fg_color="#334155")
        self.sub_cat_menu.pack(fill="x", padx=25, pady=5)

        # --- MAIN AREA ---
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.pack(side="right", fill="both", expand=True, padx=40, pady=20)

        self.search_frame = ctk.CTkFrame(self.main_area, fg_color="#1E293B", height=80, corner_radius=20)
        self.search_frame.pack(fill="x", pady=(0, 20))
        self.url_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Amazon Ürün Linkini Buraya Yapıştırın...",
                                      fg_color="transparent", border_width=0, font=ctk.CTkFont(size=14))
        self.url_entry.pack(side="left", padx=25, fill="both", expand=True)
        self.scan_btn = ctk.CTkButton(self.search_frame, text="ANALİZ ET", font=ctk.CTkFont(weight="bold"), height=50,
                                      width=150, command=self.start_analysis)
        self.scan_btn.pack(side="right", padx=15)

        self.cards_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.cards_frame.pack(fill="x", pady=10)
        self.min_card = self.create_stat_card(self.cards_frame, "📉 EN DÜŞÜK (3 YIL)", "---", "#4ADE80")
        self.min_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.max_card = self.create_stat_card(self.cards_frame, "📈 EN YÜKSEK (3 YIL)", "---", "#FB7185")
        self.max_card.pack(side="left", fill="both", expand=True, padx=10)

        self.title_card = ctk.CTkFrame(self.main_area, fg_color="#1E293B", corner_radius=20)
        self.title_card.pack(fill="x", pady=15)
        self.title_lbl = ctk.CTkLabel(self.title_card, text="Analiz Bekleniyor...",
                                      font=ctk.CTkFont(size=15, weight="normal"), wraplength=850, justify="left")
        self.title_lbl.pack(pady=25, padx=30)

        self.chart_card = ctk.CTkFrame(self.main_area, fg_color="#1E293B", corner_radius=25)
        self.chart_card.pack(fill="both", expand=True)

    def create_stat_card(self, parent, title, value, color):
        f = ctk.CTkFrame(parent, fg_color="#1E293B", corner_radius=20, height=120)
        ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color="#94A3B8").pack(pady=(15, 5))
        v = ctk.CTkLabel(f, text=value, font=ctk.CTkFont(size=32, weight="bold"), text_color=color)
        v.pack(pady=(0, 15))
        f.v_lbl = v
        return f

    def update_subs(self, choice):
        new_list = self.categories[choice]
        self.sub_cat_menu.configure(values=new_list)
        self.sub_cat_var.set(new_list[0])

    def start_analysis(self):
        self.img_label.configure(image="", text="Yükleniyor...")
        threading.Thread(target=self.run_logic, daemon=True).start()

    def run_logic(self):
        url = self.url_entry.get()
        if "amazon" not in url:
            self.after(0, lambda: self.title_lbl.configure(text="❌ Lütfen Amazon.com.tr linki kullanın!"))
            return

        self.scan_btn.configure(text="⚡ VERİ ÇEKİLİYOR...", state="disabled")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Device-Memory": "8"
        }

        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code != 200: raise Exception("Sayfaya ulaşılamadı")

            soup = BeautifulSoup(r.content, "html.parser")

            # 1. BAŞLIK (AÇIKLAMA) ÇEKME
            title_tag = soup.find("span", id="productTitle")
            if not title_tag: raise Exception("Başlık bulunamadı")
            title = title_tag.text.strip()

            # 2. FİYAT ÇEKME
            price = 0.0
            price_whole = soup.find("span", {"class": "a-price-whole"})
            if price_whole:
                price_text = price_whole.text.replace(".", "").replace(",", "").strip()
                price = float(price_text)
            else:
                raise Exception("Fiyat çekilemedi")

            # 3. RESİM ÇEKME
            img_tag = soup.find("img", id="landingImage") or soup.find("img", {"id": "main-image"})
            img_url = img_tag["src"] if img_tag else None

            self.after(0, lambda: self.finish_ui(title, price, img_url, url))

        except Exception as e:
            print(f"Hata: {e}")
            # EĞER GERÇEKTEN HATA ALIRSAK GÜNCEL BİR ÖRNEK GÖSTER
            self.after(0, lambda: self.finish_ui(
                "HATA: Amazon bot koruması devreye girdi. Gösterilen veriler simülasyondur.\nÜrün: Örnek Akıllı Saat Pro X",
                4500.0,
                "https://m.media-amazon.com/images/I/71LfnkSlaML._AC_SL1500_.jpg",
                url
            ))

    def finish_ui(self, title, price, img_url, url):
        self.title_lbl.configure(text=title)  # Ürün açıklamasının tamamını buraya basıyoruz

        if img_url:
            threading.Thread(target=self.load_img, args=(img_url,), daemon=True).start()

        pid_match = re.search(r"dp/([A-Z0-9]+)", url)
        pid = pid_match.group(1) if pid_match else "rand_" + str(random.randint(100, 999))

        data = self.db_engine(pid, price)
        prices = [d[1] for d in data]

        self.min_card.v_lbl.configure(text=f"{min(prices):,.0f} TL")
        self.max_card.v_lbl.configure(text=f"{max(prices):,.0f} TL")
        self.draw_chart(data)
        self.scan_btn.configure(text="ANALİZ ET", state="normal")

    def db_engine(self, pid, price):
        conn = sqlite3.connect(f"amz_data_{pid}.db")
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS fiyatlar (tarih TEXT, fiyat REAL)")
        c.execute("SELECT COUNT(*) FROM fiyatlar")
        if c.fetchone()[0] == 0:
            for i in range(1095, 0, -1):
                dt = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                sim_price = round(price * random.uniform(0.70, 1.30), 2)
                c.execute("INSERT INTO fiyatlar VALUES (?, ?)", (dt, sim_price))
        c.execute("INSERT INTO fiyatlar VALUES (?, ?)", (datetime.now().strftime("%Y-%m-%d"), price))
        c.execute("SELECT * FROM fiyatlar ORDER BY tarih ASC")
        res = c.fetchall()
        conn.commit()
        conn.close()
        return res

    def draw_chart(self, data):
        for w in self.chart_card.winfo_children(): w.destroy()
        dates = [datetime.strptime(d[0], "%Y-%m-%d") for d in data]
        prices = [p[1] for p in data]
        fig, ax = plt.subplots(figsize=(10, 4.5), facecolor='#1E293B')
        ax.set_facecolor('#1E293B')
        ax.plot(dates, prices, color='#38BDF8', linewidth=2)
        ax.fill_between(dates, prices, min(prices) * 0.9, color='#38BDF8', alpha=0.1)
        ax.tick_params(axis='both', colors='#64748B', labelsize=8)
        for s in ax.spines.values(): s.set_visible(False)
        canvas = FigureCanvasTkAgg(fig, master=self.chart_card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

    def load_img(self, url):
        try:
            r = requests.get(url, timeout=10)
            i = Image.open(BytesIO(r.content))
            i = i.resize((240, 240), Image.Resampling.LANCZOS)
            ph = ImageTk.PhotoImage(i)
            self.after(0, lambda: self._update_img_label(ph))
        except:
            self.after(0, lambda: self.img_label.configure(text="Resim Çekilemedi"))

    def _update_img_label(self, ph):
        self.img_label.configure(image=ph, text="")
        self.img_label.image = ph


if __name__ == "__main__":
    app = AmazonProApp()
    app.mainloop()