# -*- coding: utf-8 -*-
"""Math Course AI — 📒 Token Kullanım Defteri.

Yapay zekâya giden her isteğin kaydı: ne zaman, hangi sağlayıcı/model, kaç
token, kaç saniye, nasıl bitti. Eski "ham JSON satırlarını dök" ekranının
yerine geçer: özet kartlar + gruplu tablolar + CSV dışa aktarma sunar.

Tasarım kararları
-----------------
• Mantık katmanı Tk'sız: read_records/normalize/summarize/group_by/to_csv
  saf fonksiyonlardır, headless test edilir (test_token_ledger.py).
• GERİYE UYUM: defterdeki eski satırlarda "profile" ve "provider" alanları
  yoktu. normalize() bunları uydurmaz — eksikse profile="?" ve provider
  "yerel" sayılır (o dönemde tek sağlayıcı LM Studio'ydu; bu bir varsayım
  değil, tarihsel olgudur ve arayüzde de böyle yazar).
• MALİYET: hem yerel LM Studio hem NVIDIA NIM ücretsiz uçlar → 0,00 $.
  Fiyat tablosu yine de vardır (config["token_prices"], 1M token başına USD)
  ki ileride ücretli bir sağlayıcı eklenirse defter hazır olsun. Bilinmeyen
  model = ücretsiz sayılır ve tabloda "?" ile işaretlenir — sessizce sıfır
  yazıp "hiç para harcamadın" demek yanlış olurdu.
"""

import csv
import json
from collections import OrderedDict
from datetime import datetime, timedelta

from mca_common import app_lang, t2, TOKEN_LOG_PATH

__all__ = ["read_records", "normalize", "summarize", "group_by", "to_csv",
           "record_cost", "TokenLedgerWindow", "token_defteri_ac"]

# 1M token basina USD. Iki mevcut saglayici da ucretsiz; tablo ileriye donuk.
DEFAULT_PRICES = {
    "__local__": 0.0,     # LM Studio: kendi bilgisayarinda kosar
    "__nvidia__": 0.0,    # NIM ucretsiz deneme uclari
}


# ══════════════════════════════════════════════════════════════════════════
# MANTIK KATMANI (Tk'siz — test edilebilir)
# ══════════════════════════════════════════════════════════════════════════

def normalize(rec):
    """Ham kaydı defter satırına çevirir; eksik alanları dürüstçe işaretler."""
    if not isinstance(rec, dict):
        return None
    out = {
        "time": str(rec.get("time") or ""),
        "provider": str(rec.get("provider") or "yerel"),
        "profile": str(rec.get("profile") or "?"),
        "model": str(rec.get("model") or "?"),
        "prompt_tokens": int(rec.get("prompt_tokens") or 0),
        "completion_tokens": int(rec.get("completion_tokens") or 0),
        "total_tokens": int(rec.get("total_tokens") or 0),
        "finish_reason": str(rec.get("finish_reason") or ""),
        "seconds": float(rec.get("seconds") or 0.0),
    }
    if not out["total_tokens"]:
        out["total_tokens"] = out["prompt_tokens"] + out["completion_tokens"]
    return out


def read_records(path=None, limit=None):
    """Defteri okur → normalize edilmiş kayıt listesi (bozuk satırlar atlanır).

    limit: son N **kayıt** (satır değil) — bozuk/boş satırlar limiti yemesin.
    """
    p = path or TOKEN_LOG_PATH
    try:
        if not p.exists():
            return []
        satirlar = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return []
    kayitlar = []
    for s in satirlar:
        s = s.strip()
        if not s:
            continue
        try:
            r = normalize(json.loads(s))
        except Exception:
            continue
        if r:
            kayitlar.append(r)
    if limit:
        kayitlar = kayitlar[-int(limit):]
    return kayitlar


def _gun(rec):
    """Kaydın gün damgası (YYYY-MM-DD) — tarih okunamazsa boş string."""
    t = rec.get("time") or ""
    return t[:10] if len(t) >= 10 else ""


def record_cost(rec, prices=None):
    """Tek kaydın maliyeti (USD) → (tutar, bilinen_mi).

    bilinen_mi False ise model fiyat tablosunda yok; tutar 0.0 döner ama
    arayüz bunu "?" ile gösterir (bilinmeyeni ücretsizmiş gibi sunmayız).
    """
    tablo = dict(DEFAULT_PRICES)
    tablo.update(prices or {})
    model = rec.get("model") or ""
    if model in tablo:
        birim = tablo[model]
    elif rec.get("provider") == "nvidia":
        birim = tablo.get("__nvidia__", 0.0)
    elif rec.get("provider") in ("yerel", "local"):
        birim = tablo.get("__local__", 0.0)
    else:
        return 0.0, False
    return (rec.get("total_tokens", 0) / 1_000_000.0) * float(birim), True


def summarize(records, today=None):
    """Özet kartların sayıları — bugün / 7 gün / 30 gün / tüm zamanlar."""
    bugun = today or datetime.now().strftime("%Y-%m-%d")
    try:
        bd = datetime.strptime(bugun, "%Y-%m-%d")
    except Exception:
        bd = datetime.now()
    esik7 = (bd - timedelta(days=6)).strftime("%Y-%m-%d")
    esik30 = (bd - timedelta(days=29)).strftime("%Y-%m-%d")

    def topla(secili):
        return {
            "istek": len(secili),
            "token": sum(r["total_tokens"] for r in secili),
            "giris": sum(r["prompt_tokens"] for r in secili),
            "cikis": sum(r["completion_tokens"] for r in secili),
            "sure": round(sum(r["seconds"] for r in secili), 1),
        }

    hepsi = list(records)
    ozet = {
        "tum": topla(hepsi),
        "bugun": topla([r for r in hepsi if _gun(r) == bugun]),
        "son7": topla([r for r in hepsi if _gun(r) >= esik7]),
        "son30": topla([r for r in hepsi if _gun(r) >= esik30]),
    }
    ozet["ilk_kayit"] = min((r["time"] for r in hepsi if r["time"]), default="")
    ozet["son_kayit"] = max((r["time"] for r in hepsi if r["time"]), default="")
    sureli = [r for r in hepsi if r["seconds"] > 0]
    ozet["ortalama_sure"] = round(sum(r["seconds"] for r in sureli) / len(sureli), 1) if sureli else 0.0
    kesilen = [r for r in hepsi if r["finish_reason"] not in ("stop", "", "eos")]
    ozet["kesilen"] = len(kesilen)
    return ozet


def group_by(records, key):
    """key'e göre gruplu özet → [{anahtar, istek, token, sure}] (token'a göre azalan).

    key: 'model' | 'provider' | 'profile' | 'gun'
    """
    kova = OrderedDict()
    for r in records:
        k = _gun(r) if key == "gun" else (r.get(key) or "?")
        h = kova.setdefault(k, {"anahtar": k, "istek": 0, "token": 0, "sure": 0.0,
                                "giris": 0, "cikis": 0})
        h["istek"] += 1
        h["token"] += r["total_tokens"]
        h["giris"] += r["prompt_tokens"]
        h["cikis"] += r["completion_tokens"]
        h["sure"] += r["seconds"]
    for h in kova.values():
        h["sure"] = round(h["sure"], 1)
    satirlar = list(kova.values())
    if key == "gun":
        satirlar.sort(key=lambda h: h["anahtar"])      # gunler kronolojik
    else:
        satirlar.sort(key=lambda h: h["token"], reverse=True)
    return satirlar


def to_csv(records, path):
    """Defteri CSV'ye yazar → yazılan satır sayısı."""
    alanlar = ["time", "provider", "profile", "model", "prompt_tokens",
               "completion_tokens", "total_tokens", "finish_reason", "seconds"]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=alanlar)
        w.writeheader()
        for r in records:
            w.writerow({a: r.get(a, "") for a in alanlar})
    return len(records)


# ══════════════════════════════════════════════════════════════════════════
# ARAYÜZ
# ══════════════════════════════════════════════════════════════════════════

def token_defteri_ac(app):
    """Ana uygulamadan çağrılır."""
    return TokenLedgerWindow(app)


try:
    import tkinter as tk
    from tkinter import ttk, filedialog
    from mca_common import app_lang, t2, THEME, RoundedButton, APP_FOLDER
except Exception:  # pragma: no cover — headless testte Tk yoksa mantik yine calisir
    tk = None


class TokenLedgerWindow(tk.Toplevel if tk else object):
    """📒 Token Kullanım Defteri penceresi."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.lang = app_lang(app)
        self.title("📒 Token Kullanım Defteri / Token Ledger")
        self.geometry("1040x720")
        self.configure(bg=THEME["bg"])
        self.records = read_records()
        self._build()

    def _t(self, tr, en):
        return t2(tr, en, self.lang)

    def _build(self):
        tk.Label(self, text=self._t("📒 Token Kullanım Defteri", "📒 Token Usage Ledger"), bg=THEME["bg"], fg=THEME["text"],
                 font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=14, pady=(12, 0))
        tk.Label(self, text=("Yapay zekâya giden her isteğin kaydı. Yerel LM Studio kendi "
                             "bilgisayarında çalışır, NVIDIA NIM ücretsiz deneme ucudur — "
                             "ikisi de para harcamaz; defter yine de ne kadar iş yaptığını "
                             "ve nerede yavaşladığını gösterir."),
                 bg=THEME["bg"], fg=THEME["muted"], font=("Segoe UI", 9),
                 wraplength=1000, justify="left").pack(anchor="w", padx=14, pady=(2, 8))

        if not self.records:
            tk.Label(self, text=self._t(
                         "Defter henüz boş — yapay zekâya ilk soruyu sorduğunda "
                         "kayıtlar burada birikmeye başlar.",
                         "The ledger is empty — records start collecting here once you "
                         "ask the AI your first question."),
                     bg=THEME["bg"], fg=THEME["accent"], font=("Segoe UI", 11)).pack(
                     anchor="w", padx=14, pady=20)
            self._alt_dugmeler()
            return

        ozet = summarize(self.records)
        kartlar = tk.Frame(self, bg=THEME["bg"])
        kartlar.pack(fill="x", padx=12)
        for baslik, veri, renk in ((self._t("Bugün", "Today"), ozet["bugun"], THEME["accent"]),
                                   (self._t("Son 7 gün", "Last 7 days"), ozet["son7"], THEME["green"]),
                                   (self._t("Son 30 gün", "Last 30 days"), ozet["son30"], THEME["text"]),
                                   (self._t("Tüm zamanlar", "All time"), ozet["tum"], THEME["muted"])):
            k = tk.Frame(kartlar, bg=THEME["panel"], highlightbackground=THEME["border"],
                         highlightthickness=1)
            k.pack(side="left", fill="both", expand=True, padx=4, pady=4)
            tk.Label(k, text=baslik, bg=THEME["panel"], fg=THEME["muted"],
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(8, 0))
            tk.Label(k, text=f"{veri['token']:,}".replace(",", "."), bg=THEME["panel"],
                     fg=renk, font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=10)
            tk.Label(k, text=f"token · {veri['istek']} istek · {veri['sure']:.0f} sn",
                     bg=THEME["panel"], fg=THEME["muted"],
                     font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(0, 8))

        bilgi = (f"İlk kayıt: {ozet['ilk_kayit'] or '-'}   ·   Son kayıt: {ozet['son_kayit'] or '-'}"
                 f"   ·   Ortalama yanıt: {ozet['ortalama_sure']} sn"
                 + (f"   ·   ⚠ {ozet['kesilen']} istek yarıda kesildi (uzunluk sınırı/hata)"
                    if ozet["kesilen"] else ""))
        tk.Label(self, text=bilgi, bg=THEME["bg"], fg=THEME["muted"],
                 font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(4, 6))

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        self._grup_sekmesi(nb, self._t("Modele göre", "By model"), "model")
        self._grup_sekmesi(nb, self._t("Sağlayıcıya göre", "By provider"), "provider")
        self._grup_sekmesi(nb, self._t("İşe göre (profil)", "By task (profile)"), "profile")
        self._grup_sekmesi(nb, self._t("Güne göre", "By day"), "gun")
        self._kayit_sekmesi(nb)
        self._alt_dugmeler()

    def _grup_sekmesi(self, nb, baslik, anahtar):
        cerceve = ttk.Frame(nb)
        nb.add(cerceve, text=baslik)
        kolonlar = ("anahtar", "istek", "token", "giris", "cikis", "sure")
        basliklar = {"anahtar": baslik.split()[0],
                     "istek": self._t("İstek", "Requests"),
                     "token": self._t("Toplam token", "Total tokens"),
                     "giris": self._t("Giriş", "Input"),
                     "cikis": self._t("Çıkış", "Output"),
                     "sure": self._t("Süre (sn)", "Seconds")}
        if anahtar == "gun":
            # Gunluk kullanim CUBUK GRAFIGI: tablo sayilari verir, grafik
            # ritmi gosterir ("hangi gun yogun calistim").
            self._gun_grafigi(cerceve)
        tree = ttk.Treeview(cerceve, columns=kolonlar, show="headings",
                            height=9 if anahtar == "gun" else 14)
        for k in kolonlar:
            tree.heading(k, text=basliklar[k])
            tree.column(k, width=200 if k == "anahtar" else 110,
                        anchor="w" if k == "anahtar" else "e")
        for h in group_by(self.records, anahtar):
            tree.insert("", "end", values=(h["anahtar"], h["istek"],
                                           f"{h['token']:,}".replace(",", "."),
                                           f"{h['giris']:,}".replace(",", "."),
                                           f"{h['cikis']:,}".replace(",", "."),
                                           f"{h['sure']:.0f}"))
        sb = ttk.Scrollbar(cerceve, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _gun_grafigi(self, parent, gun_sayisi=14):
        """Son N günün token kullanımını çubuk grafikle çizer.

        student_tracker'ın istatistik grafikleriyle AYNI desen: matplotlib
        FigureCanvasTkAgg + THEME renkleri. Veri yoksa GRAFİK ÇİZİLMEZ —
        boş eksen çizmek "veri var ama sıfır" gibi okunurdu.
        """
        satirlar = group_by(self.records, "gun")[-int(gun_sayisi):]
        if not satirlar:
            tk.Label(parent, text=self._t("Grafik için henüz veri yok.",
                                          "Not enough data for a chart yet."),
                     bg=THEME["bg"], fg=THEME["muted"],
                     font=("Segoe UI", 9)).pack(anchor="w", padx=8, pady=6)
            return None
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except Exception:
            return None
        try:
            fig = Figure(figsize=(9.2, 2.4), dpi=100, facecolor=THEME["bg"])
            ax = fig.add_subplot(111)
            ax.set_facecolor(THEME["panel"])
            etiketler = [h["anahtar"][5:] for h in satirlar]     # AA-GG yeter
            degerler = [h["token"] for h in satirlar]
            ax.bar(range(len(degerler)), degerler, color=THEME["accent"], width=0.62)
            ax.set_xticks(range(len(etiketler)))
            ax.set_xticklabels(etiketler, fontsize=8, color=THEME["muted"], rotation=0)
            ax.tick_params(axis="y", labelsize=8, colors=THEME["muted"])
            for kenar in ax.spines.values():
                kenar.set_color(THEME["line"])
            ax.grid(axis="y", color=THEME["line"], linewidth=0.7, alpha=0.6)
            ax.set_axisbelow(True)
            ax.set_title(self._t(f"Son {len(satirlar)} günün token kullanımı",
                                 f"Token usage over the last {len(satirlar)} days"),
                         fontsize=10, color=THEME["text"], loc="left")
            fig.tight_layout(pad=1.1)
            tuval = FigureCanvasTkAgg(fig, master=parent)
            tuval.get_tk_widget().pack(fill="x", padx=6, pady=(6, 2))
            return fig
        except Exception:
            return None

    def _kayit_sekmesi(self, nb):
        cerceve = ttk.Frame(nb)
        nb.add(cerceve, text=self._t("Kayıtlar (son 300)", "Records (last 300)"))
        kolonlar = ("time", "provider", "model", "profile", "total", "sure", "finish")
        basliklar = {"time": "Zaman", "provider": "Sağlayıcı", "model": "Model",
                     "profile": "İş", "total": "Token", "sure": "sn", "finish": "Bitiş"}
        genislik = {"time": 150, "provider": 90, "model": 240, "profile": 80,
                    "total": 90, "sure": 70, "finish": 100}
        tree = ttk.Treeview(cerceve, columns=kolonlar, show="headings", height=14)
        for k in kolonlar:
            tree.heading(k, text=basliklar[k])
            tree.column(k, width=genislik[k],
                        anchor="e" if k in ("total", "sure") else "w")
        for r in list(reversed(self.records))[:300]:
            tree.insert("", "end", values=(r["time"], r["provider"], r["model"],
                                           r["profile"],
                                           f"{r['total_tokens']:,}".replace(",", "."),
                                           f"{r['seconds']:.1f}", r["finish_reason"]))
        sb = ttk.Scrollbar(cerceve, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _alt_dugmeler(self):
        alt = tk.Frame(self, bg=THEME["bg"])
        alt.pack(fill="x", padx=14, pady=(0, 12))
        self.durum = tk.Label(alt, text=self._t(f"Defter: {TOKEN_LOG_PATH}", f"Ledger: {TOKEN_LOG_PATH}"), bg=THEME["bg"],
                              fg=THEME["muted"], font=("Segoe UI", 8))
        self.durum.pack(side="left")
        RoundedButton(alt, text=self._t("Kapat", "Close"), parent_bg=THEME["bg"],
                      command=self.destroy).pack(side="right", padx=4)
        RoundedButton(alt, text=self._t("📤 CSV dışa aktar", "📤 Export CSV"), parent_bg=THEME["bg"],
                      bg=THEME["accent"], fg="#FFFFFF", hover="#EC8A4B",
                      command=self._csv_ver).pack(side="right", padx=4)
        RoundedButton(alt, text=self._t("📁 Klasörü aç", "📁 Open folder"), parent_bg=THEME["bg"],
                      command=lambda: self.app.open_folder(APP_FOLDER)).pack(side="right", padx=4)

    def _csv_ver(self):
        if not self.records:
            return
        p = filedialog.asksaveasfilename(
            parent=self, title="Token defterini CSV kaydet",
            initialfile="token_defteri.csv", defaultextension=".csv",
            filetypes=[("CSV", "*.csv")])
        if not p:
            return
        try:
            n = to_csv(self.records, p)
            self.durum.config(text=self._t(f"{n} kayıt CSV'ye yazıldı: {p}", f"{n} records written to CSV: {p}"), fg=THEME["green"])
        except Exception as exc:
            self.durum.config(text=self._t(f"CSV yazılamadı: {exc}", f"Could not write CSV: {exc}"), fg=THEME["danger"])
