# -*- coding: utf-8 -*-
"""Math Course AI — 🖥 AI Terminali.

Kod ve işleri seçilen yapay zekâya yazdırma penceresi. İki sağlayıcı:
  • Yerel (LM Studio) — VARSAYILAN. Ücretsiz, veri bilgisayardan çıkmaz.
  • NVIDIA NIM — İSTEĞE BAĞLI bulut. Makinede anahtar bulunsa BİLE kendi
    kendine seçilmez; her oturumda ayrı ve açık onay ister (cloud_consent.py).
    Onay verilmeden tek bayt gitmez. İstek/yanıtlar NVIDIA'ca loglanır.

Güvenlik sözleşmesi — üretilen kodun çalıştırılması:
  1) ÜRETİLEN KOD ASLA OTOMATİK ÇALIŞTIRILMAZ.
  2) BU SÜRÜMDE ÖZELLİK VARSAYILAN OLARAK KAPALIDIR. Gerçek bir işletim
     sistemi kum havuzu (sandbox) bu sürüme yetiştirilemedi; kapalı gelir ve
     riski açıkça yazılıdır (docs/known-limitations.md).
  3) Açıldığında sıra: statik politika denetimi (ai_code_guard.analyze) →
     insan onay penceresi (denetim raporuyla birlikte) → her koşuya ÖZEL boş
     çalışma klasörü → temizlenmiş ortam değişkenleri → python -I -B →
     Windows Job Object ile bellek/süreç tavanı → 180 sn zaman aşımı.
  4) Statik denetim bir güvenlik SINIRI DEĞİLDİR; atlatılabilir. Job Object
     KAYNAK sınırlar, YETKİ sınırlamaz: onaylanan kod hâlâ kullanıcının
     erişebildiği dosyalara ve ağa erişebilir. Onay penceresi bunu yazar.

Pencere içindeki konuşma geçmişi (AI'ya gönderilen bağlam) pencere kapanınca
silinir. Tamamlanan her İŞ ise ayrıca kalıcı **çalışma tutanağına** yazılır
(terminal_tutanak.py → %APPDATA%\\MathCourseAI\\terminal_tutanak.jsonl):
soru + yanıt + çalıştırılan kod + çıktısı + sağlayıcı/model/süre. Token
defterinin aksine tutanak istek METNİNİ saklar — pencere bunu açıkça yazar.
"""

import json
import re
import sys
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog

from mca_common import (APP_FOLDER, THEME, TOKEN_LOG_PATH, RoundedButton,
                        app_lang, estimate_tokens, now_iso, safe_output_tokens,
                        t2)

import ai_code_guard
import cloud_consent

try:
    import nvidia_provider
except Exception:
    nvidia_provider = None

try:
    import terminal_tutanak
except Exception:      # tutanak yoksa terminal yine tam çalışır (kayıt kapalı)
    terminal_tutanak = None

YEREL = "Yerel (LM Studio)"
NVIDIA = "NVIDIA NIM"

CALISMA_KLASORU = APP_FOLDER / "terminal_calismalari"

SISTEM_PROMPT_EN = (
    "You are the terminal assistant of Math Course AI. You write code and do "
    "small jobs for the user's maths studies: sympy solutions and plots, "
    "calculations, data processing, small helper scripts. Answer in English. "
    "When code is requested give ONE ```python block; it must be a single "
    "self-contained file (sympy, matplotlib, numpy are available; plt.show() "
    "is fine). Do NOT write anything dangerous (deleting files, network "
    "access, system settings); if asked, say why and refuse."
)

SISTEM_PROMPT = (
    "Sen Math Course AI'ın terminal asistanısın. Kullanıcının matematik "
    "öğrenimiyle ilgili kod ve işlerini yaparsın: sympy/matplotlib ile çözüm ve "
    "grafik, hesap, veri işleme, küçük yardımcı skriptler. Türkçe cevap ver. "
    "Kod istendiğinde TEK bir ```python bloğu ver; kod tek dosyalık, bağımsız "
    "çalışır olsun (sympy, matplotlib, numpy kullanılabilir; grafik için "
    "plt.show() serbest). Tehlikeli işlem (dosya silme, ağ, sistem ayarı) "
    "YAZMA; istenirse nedenini söyleyip reddet."
)


def extract_python_blocks(text):
    """Metindeki ```python ... ``` bloklarını sırayla döndürür (saf, test edilir).

    Dil etiketi esnek okunur: ```python, ```py ve etiketsiz ``` blokları
    (içeriği koda benziyorsa cagiran karar versin diye) ayrı tutulmaz —
    yalnız python/py/etiketsiz bloklar döner, bash vb. DÖNMEZ.
    """
    blocks = []
    for m in re.finditer(r"```([A-Za-z0-9_+-]*)[ \t]*\r?\n(.*?)```", text or "", re.DOTALL):
        lang = (m.group(1) or "").strip().lower()
        if lang in ("python", "py", ""):
            code = m.group(2).strip("\r\n")
            if code.strip():
                blocks.append(code)
    return blocks


def log_terminal_usage(provider, model, usage, prompt, response, finish, seconds):
    """Terminal isteğini token defterine yazar (yerel istemcininkiyle aynı şema).

    NVIDIA yolu LMStudioClient'tan geçmediği için kendi kaydını yazmalı;
    yoksa defter yalnız yerel isteklerin yarısını gösterirdi."""
    kayit = {
        "time": now_iso(),
        "provider": provider,
        "profile": "terminal",
        "model": model,
        "prompt_tokens": (usage or {}).get("prompt_tokens") or estimate_tokens(prompt),
        "completion_tokens": (usage or {}).get("completion_tokens") or estimate_tokens(response),
        "total_tokens": (usage or {}).get("total_tokens") or 0,
        "finish_reason": finish,
        "seconds": round(float(seconds or 0), 2),
    }
    if not kayit["total_tokens"]:
        kayit["total_tokens"] = kayit["prompt_tokens"] + kayit["completion_tokens"]
    try:
        with TOKEN_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(kayit, ensure_ascii=False) + "\n")
    except Exception:
        pass


class AITerminalWindow(tk.Toplevel):
    """Tek pencerelik sohbet terminali; app = MathCourseApp (client + t)."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.lang = app_lang(app)
        self.title("🖥 AI Terminali / AI Terminal")
        self.geometry("1000x760")
        self.configure(bg=THEME["bg"])
        self._history = []            # [{"role","content"}] — pencereyle yasar
        # _history'deki asistan mesajinin INDEKSI -> tutanak kayit kimligi.
        # Kimligi mesajin icine koymuyoruz: _history oldugu gibi saglayiciya
        # gonderiliyor, fazladan alan API tarafinda reddedilebilir.
        self._tutanak_ids = {}
        self._tutanak_win = None
        self._busy = False
        self._cancel = False
        self._build()

    # ---------------------------------------------------------------- UI --
    def _build(self):
        tk.Label(self, text="🖥 AI Terminali", bg=THEME["bg"], fg=THEME["text"],
                 font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=14, pady=(12, 0))
        self.aciklama_lbl = tk.Label(
            self, text=self._t(
                "Kod ve işlerini seçtiğin yapay zekâya yazdır. Yerel = LM Studio "
                "(veri çıkmaz). NVIDIA NIM = ücretsiz deneme ucu — istek ve "
                "yanıtlar NVIDIA tarafından loglanır, kişisel veri gönderme. "
                "Üretilen kod OTOMATİK ÇALIŞTIRILMAZ; ▶ düğmesi onay penceresi açar. "
                "📜 Tamamlanan her iş kalıcı tutanağa yazılır — token defterinin "
                "aksine tutanak istek ve yanıt METNİNİ saklar (bilgisayarında kalır).",
                "Have the AI of your choice write code and do jobs for you. Local = "
                "LM Studio, the default - your data stays on this machine. "
                "NVIDIA NIM = optional, free trial "
                "endpoint — requests and answers are logged by NVIDIA, so send no "
                "personal data. Generated code is NEVER RUN AUTOMATICALLY; the ▶ "
                "button opens an approval window. 📜 Every finished job goes into a "
                "permanent work record — unlike the token ledger it keeps the TEXT "
                "of your request and the answer (on your machine only)."),
            bg=THEME["bg"], fg=THEME["muted"], font=("Segoe UI", 9),
            wraplength=960, justify="left")
        self.aciklama_lbl.pack(anchor="w", padx=14, pady=(2, 8))
        # Sabit wraplength pencere daraltilinca metni SAGDAN KESIYORDU (ekran
        # dogrulamasinda yakalandi — karsilama kartindaki ayni desen).
        self.bind("<Configure>", self._sarmayi_esitle)

        ust = tk.Frame(self, bg=THEME["bg"])
        ust.pack(fill="x", padx=14)
        tk.Label(ust, text=self._t("Sağlayıcı:", "Provider:"),
                 bg=THEME["bg"], fg=THEME["text"],
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        saglayicilar = [YEREL] + ([NVIDIA] if nvidia_provider is not None else [])
        # VARSAYILAN HER ZAMAN YEREL. Makinede (ya da ortam değişkeninde) bir
        # bulut anahtarı bulunması ONAY DEĞİLDİR: bulut yalnızca kullanıcı bu
        # oturumda listeden açıkça seçip onay penceresini kabul ederse açılır.
        self.sag_var = tk.StringVar(value=YEREL)
        self._son_saglayici = YEREL
        self.sag_cb = ttk.Combobox(ust, textvariable=self.sag_var, values=saglayicilar,
                                   width=18, state="readonly")
        self.sag_cb.pack(side="left", padx=6)
        self.sag_cb.bind("<<ComboboxSelected>>", self._saglayici_degisti)
        tk.Label(ust, text="Model:", bg=THEME["bg"], fg=THEME["text"],
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(10, 2))
        self.model_var = tk.StringVar(value="")
        self.model_cb = ttk.Combobox(ust, textvariable=self.model_var, values=[],
                                     width=40, state="readonly")
        self.model_cb.pack(side="left", padx=4)
        RoundedButton(ust, text=self._t("🔑 Anahtar", "🔑 API key"), parent_bg=THEME["bg"],
                      command=self._anahtar_penceresi).pack(side="right")
        self.durum_lbl = tk.Label(ust, text="", bg=THEME["bg"], fg=THEME["muted"],
                                  font=("Segoe UI", 9))
        self.durum_lbl.pack(side="right", padx=8)

        self.out = tk.Text(self, wrap="word", bg=THEME["surface"], fg=THEME["text"],
                           insertbackground=THEME["text"], relief="flat",
                           font=("Consolas", 10), state="disabled")
        self.out.pack(fill="both", expand=True, padx=14, pady=(8, 4))
        self.out.tag_configure("sen", foreground=THEME["accent"],
                               font=("Consolas", 10, "bold"))
        self.out.tag_configure("ai", foreground=THEME["green"],
                               font=("Consolas", 10, "bold"))
        self.out.tag_configure("sistem", foreground=THEME["muted"])
        self.out.tag_configure("hata", foreground=THEME["danger"])

        alt = tk.Frame(self, bg=THEME["bg"])
        alt.pack(fill="x", padx=14, pady=(0, 12))
        self.inp = tk.Text(alt, height=3, wrap="word", bg=THEME["surface"],
                           fg=THEME["text"], insertbackground=THEME["text"],
                           relief="flat", font=("Segoe UI", 10))
        self.inp.pack(side="left", fill="both", expand=True)
        self.inp.bind("<Control-Return>", lambda e: (self._gonder(), "break")[1])
        sag = tk.Frame(alt, bg=THEME["bg"])
        sag.pack(side="right", padx=(8, 0))
        self.gonder_btn = RoundedButton(sag, text=self._t("Gönder (Ctrl+Enter)", "Send (Ctrl+Enter)"),
                                        parent_bg=THEME["bg"], bg=THEME["accent"],
                                        fg="#FFFFFF", hover="#EC8A4B",
                                        command=self._gonder)
        self.gonder_btn.pack(fill="x", pady=(0, 4))
        RoundedButton(sag, text=self._t("▶ Python bloğunu çalıştır", "▶ Run the Python block"), parent_bg=THEME["bg"],
                      command=self._blok_calistir).pack(fill="x", pady=2)
        RoundedButton(sag, text=self._t("⏹ Durdur (Esc)", "⏹ Stop (Esc)"), parent_bg=THEME["bg"],
                      command=self._durdur).pack(fill="x", pady=2)
        RoundedButton(sag, text=self._t("📜 Tutanak", "📜 Work Record"), parent_bg=THEME["bg"],
                      command=self._tutanak_ac).pack(fill="x", pady=2)
        RoundedButton(sag, text=self._t("Temizle (Ctrl+L)", "Clear (Ctrl+L)"), parent_bg=THEME["bg"],
                      command=self._temizle).pack(fill="x", pady=2)

        # Kisayollar: Ctrl+L temizle, Esc durdur. bind_all DEGIL — pencere
        # duzeyinde baglanir ki ana uygulamanin kisayollarina karismasin.
        self.bind("<Control-l>", lambda e: (self._temizle(), "break")[1])
        self.bind("<Control-L>", lambda e: (self._temizle(), "break")[1])
        self.bind("<Escape>", lambda e: (self._durdur(), "break")[1])
        self.inp.bind("<Control-l>", lambda e: (self._temizle(), "break")[1])
        self.inp.bind("<Escape>", lambda e: (self._durdur(), "break")[1])
        self._modelleri_tazele()
        self._yaz("sistem", self._t(
            "Hazır. Örnek: 'x^3-6x^2+11x-6=0 köklerini sympy ile bulan kod yaz' "
            "→ ▶ ile onaylayıp çalıştır.\n",
            "Ready. Example: 'write code that finds the roots of x^3-6x^2+11x-6=0 "
            "with sympy' → approve with ▶ and run.\n"))

    # ------------------------------------------------------------ yardımcı --
    def _t(self, tr, en):
        """Pencere metni: dil, pencere kurulurken sahibinden okunur."""
        return t2(tr, en, self.lang)

    def _sarmayi_esitle(self, event=None):
        if event is not None and event.widget is not self:
            return
        genislik = max(280, (event.width if event else self.winfo_width()) - 34)
        try:
            self.aciklama_lbl.config(wraplength=genislik)
        except Exception:
            pass

    def _yaz(self, etiket, metin):
        self.out.configure(state="normal")
        if etiket == "sen":
            self.out.insert("end", "\n► SEN\n", "sen")
        elif etiket == "ai":
            self.out.insert("end", "\n◄ AI\n", "ai")
        self.out.insert("end", metin, "hata" if etiket == "hata" else
                        ("sistem" if etiket == "sistem" else None))
        self.out.see("end")
        self.out.configure(state="disabled")

    def _ek(self, parca):
        """Akış parçasını ana thread'de ekler (after ile çağrılır)."""
        self.out.configure(state="normal")
        self.out.insert("end", parca)
        self.out.see("end")
        self.out.configure(state="disabled")

    def _saglayici_degisti(self, *_a):
        """Combobox seçimi: buluta geçiş OTURUMLUK açık onay ister."""
        secilen = self.sag_var.get()
        if secilen == NVIDIA and nvidia_provider is not None:
            if not cloud_consent.is_granted():
                if not self._bulut_onayi_al():
                    self.sag_var.set(YEREL)          # onay yok → yerelde kal
                    self._son_saglayici = YEREL
                    self._yaz("sistem", self._t(
                        "Bulut onayı verilmedi — yerel modelde kalındı, "
                        "hiçbir veri gönderilmedi.\n",
                        "Cloud consent not given — staying on the local model, "
                        "nothing was sent.\n"))
                    self._modelleri_tazele()
                    return
        elif secilen == YEREL and cloud_consent.is_granted():
            cloud_consent.revoke()                    # yerele dönmek izni geri alır
            self._yaz("sistem", self._t(
                "Yerel modele dönüldü — bulut izni geri alındı.\n",
                "Back on the local model — cloud consent revoked.\n"))
        self._son_saglayici = secilen
        self._modelleri_tazele()

    def _bulut_onayi_al(self):
        """Modal açıklama + açık kabul. Dönen değer: izin verildi mi."""
        win = tk.Toplevel(self)
        win.title(self._t("Bulut sağlayıcıya izin ver (bu oturum)",
                          "Allow the cloud provider (this session)"))
        win.geometry("720x460")
        win.configure(bg=THEME["bg"])
        win.transient(self)
        win.grab_set()
        tk.Label(win, text=self._t("Bu seçim verini bilgisayarından ÇIKARIR",
                                   "This choice SENDS DATA OFF YOUR COMPUTER"),
                 bg=THEME["bg"], fg=THEME["danger"],
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 6))
        kutu = tk.Text(win, wrap="word", bg=THEME["surface"], fg=THEME["text"],
                       relief="flat", font=("Segoe UI", 10), height=14)
        kutu.pack(fill="both", expand=True, padx=14)
        kutu.insert("1.0", self._t(cloud_consent.DISCLOSURE_TR,
                                   cloud_consent.DISCLOSURE_EN))
        kutu.configure(state="disabled")
        karar = {"ok": False}
        alt = tk.Frame(win, bg=THEME["bg"])
        alt.pack(fill="x", padx=14, pady=12)
        RoundedButton(alt, text=self._t("Vazgeç — yerel kal", "Cancel — stay local"),
                      parent_bg=THEME["bg"], command=win.destroy).pack(side="right", padx=4)

        def kabul():
            cloud_consent.grant_for_session(NVIDIA)
            karar["ok"] = True
            win.destroy()

        RoundedButton(alt, text=self._t("Anladım, bu oturumda buluta izin ver",
                                        "I understand — allow the cloud this session"),
                      parent_bg=THEME["bg"], bg=THEME["danger"], fg="#FFFFFF",
                      hover="#C4453A", command=kabul).pack(side="right", padx=4)
        win.wait_window()
        return karar["ok"]

    def _modelleri_tazele(self, *_a):
        if self.sag_var.get() == NVIDIA and nvidia_provider is not None:
            modeller = list(nvidia_provider.MODELLER)
            self.durum_lbl.config(text="🔑 " + nvidia_provider.anahtar_maskeli())
        else:
            try:
                modeller = self.app.client.get_models()
            except Exception:
                modeller = []
            aktif = ""
            try:
                aktif = self.app.client.model_profiles.get("math") or ""
            except Exception:
                pass
            if aktif and aktif not in modeller:
                modeller = [aktif] + modeller
            self.durum_lbl.config(text=self._t("yerel — veri makinende kalır",
                                               "local — data stays on this machine"))
        self.model_cb.configure(values=modeller)
        if modeller:
            self.model_var.set(modeller[0])
        else:
            self.model_var.set("")

    def _durdur(self):
        """Esc / ⏹ — süren isteği keser. Çalışan istek yoksa sessiz kalmaz."""
        if not self._busy:
            self._yaz("sistem", self._t("(durdurulacak istek yok)\n",
                                        "(no request to stop)\n"))
            return
        self._cancel = True

    def _temizle(self):
        self._history = []
        self._tutanak_ids = {}     # indeksler gecersizlesti; tutanak DOSYASI durur
        self.out.configure(state="normal")
        self.out.delete("1.0", "end")
        self.out.configure(state="disabled")
        self._yaz("sistem", self._t("Geçmiş temizlendi.\n", "History cleared.\n"))

    # --------------------------------------------------------------- sohbet --
    def _gonder(self):
        if self._busy:
            self._yaz("sistem", self._t("Önceki istek sürüyor — ⏹ Durdur ile kesebilirsin.\n", "A request is still running — press ⏹ Stop to cancel it.\n"))
            return
        soru = self.inp.get("1.0", "end").strip()
        if not soru:
            return
        self.inp.delete("1.0", "end")
        self._yaz("sen", soru + "\n")
        self._history.append({"role": "user", "content": soru})
        self._busy = True
        self._cancel = False
        saglayici = self.sag_var.get()
        model = self.model_var.get()
        self._yaz("ai", "")
        threading.Thread(target=self._worker, args=(saglayici, model),
                         daemon=True).start()

    def _worker(self, saglayici, model):
        try:
            # Token defteri icin istem metni (son kullanici mesaji yeterli).
            soru_metni = next((m["content"] for m in reversed(self._history)
                               if m["role"] == "user"), "")
            baslangic = time.perf_counter()
            gercek_model = model
            if saglayici == NVIDIA and nvidia_provider is not None:
                payload = {"messages": ([{"role": "system", "content": (SISTEM_PROMPT_EN if self.lang == "en" else SISTEM_PROMPT)}]
                                        + self._history[-12:])}
                sonuc = nvidia_provider.sohbet_akisli(
                    payload, model=model,
                    parca_cb=lambda s: self.after(0, self._ek, s),
                    iptal_mi=lambda: self._cancel)
                metin, hata = sonuc.get("metin", ""), sonuc.get("hata")
                kuyruk = f"  [{sonuc.get('model')}, {sonuc.get('sure')} sn]"
                gercek_model = sonuc.get("model") or model
                sure_sn = sonuc.get("sure")
                log_terminal_usage("nvidia", sonuc.get("model"), sonuc.get("usage"),
                                   soru_metni, metin,
                                   "iptal" if hata == "iptal" else ("error" if hata else "stop"),
                                   sonuc.get("sure"))
            else:
                # LM Studio istemcisi tek turlu (system+user); gecmis metne katlanir.
                dokum = "\n\n".join(
                    ("KULLANICI: " if m["role"] == "user" else "ASISTAN: ") + m["content"]
                    for m in self._history[-8:])
                metin, usage, finish = self.app.client.complete(
                    (SISTEM_PROMPT_EN if self.lang == "en" else SISTEM_PROMPT), dokum,
                    max_tokens=safe_output_tokens(dokum), profile="math")
                hata = metin if finish == "error" else None
                if hata:
                    metin = ""
                self.after(0, self._ek, metin or "")
                kuyruk = f"  [yerel, finish={finish}]"
                # Yerel yolda saglayici sure dondurmuyor; tutanak icin burada
                # olcuyoruz (token defteri bu yolu istemci tarafinda yaziyor).
                sure_sn = time.perf_counter() - baslangic
            def bitir():
                if metin:
                    self._history.append({"role": "assistant", "content": metin})
                    self._yaz("sistem", kuyruk + "\n")
                if hata and hata != "iptal":
                    self._yaz("hata", "\n⚠ " + str(hata) + "\n")
                elif hata == "iptal":
                    self._yaz("sistem", self._t("\n(durduruldu — o ana kadarki yanıt yukarıda)\n", "\n(stopped — the answer so far is above)\n"))
                self._tutanaga_yaz(saglayici, gercek_model, soru_metni, metin,
                                   hata, sure_sn)
            self.after(0, bitir)
        finally:
            self._busy = False

    # ------------------------------------------------------------- tutanak --
    def _tutanaga_yaz(self, saglayici, model, istem, yanit, hata, sure):
        """Tamamlanan işi kalıcı tutanağa yazar; kimliği yanıtın indeksine bağlar.

        Yanıt boşsa (hata/iptal) da yazılır: "şu istek şu hatayla döndü" bilgisi
        tutanağın işine yarar. Kayıt hatası sessizce yutulur (modül sözleşmesi).
        """
        if terminal_tutanak is None:
            return None
        durum = "iptal" if hata == "iptal" else ("hata" if hata else "ok")
        kid = terminal_tutanak.kaydet(
            "nvidia" if saglayici == NVIDIA else "yerel", model,
            istem, yanit or "", sure=sure, durum=durum)
        if kid and yanit:
            # yanit _history'ye eklendi -> son indeks o asistan mesaji
            self._tutanak_ids[len(self._history) - 1] = kid
        return kid

    def _tutanak_ac(self):
        if terminal_tutanak is None:
            self._yaz("hata", self._t("terminal_tutanak modülü yüklenemedi.\n", "The terminal_tutanak module could not be loaded.\n"))
            return
        win = self._tutanak_win
        if win is not None and win.winfo_exists():
            win.deiconify()
            win.lift()
            win.yenile()
            return
        self._tutanak_win = TutanakWindow(self)

    # ---------------------------------------------------------- çalıştırma --
    def _son_python_blogu(self):
        """(kod, asistan_mesaj_indeksi) — yoksa (None, None)."""
        for i in range(len(self._history) - 1, -1, -1):
            m = self._history[i]
            if m["role"] == "assistant":
                bloklar = extract_python_blocks(m["content"])
                if bloklar:
                    return bloklar[-1], i
        return None, None

    def _blok_calistir(self):
        kod, idx = self._son_python_blogu()
        if not kod:
            self._yaz("sistem", self._t("Son AI yanitinda calistirilabilir python blogu yok.\n", "The last AI answer has no runnable python block.\n"))
            return
        # ---- GATE 1: ozellik bu surumde varsayilan olarak KAPALI ----------
        if not ai_code_guard.execution_enabled():
            self._yaz("sistem", self._t(
                "> Kod calistirma bu surumde KAPALI.\n"
                "  Sebep: modelin yazdigi kodu calistirmak icin gercek bir isletim\n"
                "  sistemi kum havuzu bu surume yetistirilemedi. Statik denetim +\n"
                "  insan onayi atlatilabilir; kapali gelmesi durust olanidir.\n"
                "  Bilerek acmak icin: " + ai_code_guard.ENABLE_ENV_VAR + "=1 ortam\n"
                "  degiskenini ayarla ve programi yeniden baslat.\n"
                "  Ayrinti: docs/known-limitations.md\n",
                "> Code execution is DISABLED in this build.\n"
                "  Why: a real OS sandbox for running model-written code could not\n"
                "  be finished for this release. A static check plus human approval\n"
                "  can be bypassed, so shipping it off is the honest default.\n"
                "  To turn it on knowingly: set " + ai_code_guard.ENABLE_ENV_VAR + "=1 and\n"
                "  restart the program.\n"
                "  Details: docs/known-limitations.md\n"))
            self._yaz("sistem", "\n" + ai_code_guard.policy_summary(self.lang) + "\n")
            return
        # ---- GATE 2: statik politika denetimi (onay penceresinden ONCE) ---
        rapor = ai_code_guard.analyze(kod)
        if not rapor.ok:
            self._yaz("hata", self._t(
                "> Statik denetim bu kodu REDDETTI - onay penceresi acilmadi.\n",
                "> The static check REFUSED this code - no approval window was opened.\n"))
            self._yaz("sistem", rapor.summary(self.lang) + "\n")
            for v in rapor.violations[:12]:
                self._yaz("sistem", "   satir %d: %s -> %s\n" % (v.line, v.symbol, v.message))
            if len(rapor.violations) > 12:
                self._yaz("sistem", "   ... +%d\n" % (len(rapor.violations) - 12))
            return
        # ---- GATE 3: insan onayi (denetim raporuyla birlikte) -------------
        self._onay_penceresi(kod, self._tutanak_ids.get(idx), rapor)

    def _onay_penceresi(self, kod, kayit_id=None, rapor=None):
        """Kod ONAYSIZ ASLA calismaz: tam metin + statik denetim raporu gosterilir."""
        win = tk.Toplevel(self)
        win.title(self._t("Kodu calistirmayi onayla", "Approve running this code"))
        win.geometry("820x600")
        win.configure(bg=THEME["bg"])
        win.transient(self)
        win.grab_set()
        tk.Label(win, text=self._t("Bu kod BILGISAYARINDA calistirilacak - once oku:", "This code will run ON YOUR COMPUTER - read it first:"),
                 bg=THEME["bg"], fg=THEME["danger"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        kutu = tk.Text(win, wrap="none", bg=THEME["surface"], fg=THEME["text"],
                       insertbackground=THEME["text"], font=("Consolas", 10))
        kutu.pack(fill="both", expand=True, padx=12)
        kutu.insert("1.0", kod)
        kutu.configure(state="disabled")

        if rapor is not None:
            tk.Label(win, text="OK - " + rapor.summary(self.lang), bg=THEME["bg"],
                     fg=THEME["green"], font=("Segoe UI", 9, "bold"),
                     wraplength=780, justify="left").pack(anchor="w", padx=12, pady=(6, 0))
        tk.Label(win, text=self._t(
                     "Calistirma kosullari: python -I -B - HER KOSUYA OZEL bos klasor - "
                     "temizlenmis ortam degiskenleri (API anahtarlari gecmez) - "
                     "Windows Job Object ile 1 GiB bellek ve tek surec tavani - "
                     "180 sn zaman asimi.\n"
                     "DURUST SINIR: bunlar KAYNAK sinirlaridir, YETKI siniri DEGIL. "
                     "Onaylanan kod hala senin erisebildigin dosyalara ve aga "
                     "erisebilir. Statik denetim atlatilabilir. Okumadan onaylama.",
                     "Run conditions: python -I -B - a FRESH EMPTY folder per run - "
                     "scrubbed environment (no API keys are passed through) - "
                     "1 GiB memory and single-process cap via a Windows Job Object - "
                     "180 s timeout.\n"
                     "HONEST LIMIT: those are RESOURCE limits, not PERMISSION limits. "
                     "Approved code can still reach any file you can reach, and the "
                     "network. The static check is bypassable. Do not approve unread."),
                 bg=THEME["bg"], fg=THEME["muted"], font=("Segoe UI", 9),
                 wraplength=780, justify="left").pack(anchor="w", padx=12, pady=4)
        alt = tk.Frame(win, bg=THEME["bg"])
        alt.pack(fill="x", padx=12, pady=(2, 12))
        RoundedButton(alt, text=self._t("Vazgec", "Cancel"), parent_bg=THEME["bg"],
                      command=win.destroy).pack(side="right", padx=4)

        def onayla():
            win.destroy()
            self._yaz("sistem", self._t("\n[calistiriliyor...]\n", "\n[running...]\n"))
            threading.Thread(target=self._kod_kos, args=(kod, kayit_id),
                             daemon=True).start()

        RoundedButton(alt, text=self._t("Onayla ve calistir", "Approve and run"), parent_bg=THEME["bg"],
                      bg=THEME["green"], fg="#FFFFFF", hover="#23B768",
                      command=onayla).pack(side="right", padx=4)

    def _kod_kos(self, kod, kayit_id=None):
        """Onaylanmis kodu ai_code_guard uzerinden kosar (kapilar orada da var)."""
        try:
            r = ai_code_guard.run_guarded(kod, CALISMA_KLASORU, timeout=180)
            if r.status == "refused_disabled":
                cikti, durum = "", self._t("[kapali - kod calistirma etkin degil]",
                                           "[disabled - code execution is off]")
            elif r.status == "refused_policy":
                cikti = (r.analysis.summary(self.lang) if r.analysis else "")
                durum = self._t("[statik denetim reddetti]", "[refused by the static check]")
            elif r.status == "timeout":
                cikti = (r.stdout or "")
                durum = self._t("[zaman asimi - 180 sn]", "[timed out - 180 s]")
            elif r.status == "error":
                cikti, durum = "", self._t("[calistirilamadi: %s]" % r.stderr,
                                           "[could not run: %s]" % r.stderr)
            else:
                cikti = (r.stdout or "")
                if r.stderr:
                    cikti += ("\n[stderr]\n" + r.stderr)
                cikti = cikti.strip() or self._t("(cikti yok)", "(no output)")
                durum = "[bitti, kod %s]" % r.returncode
            try:
                ai_code_guard.cleanup_old_workspaces(CALISMA_KLASORU, keep=20)
            except Exception:
                pass
        except Exception as e:
            cikti, durum = "", self._t("[calistirilamadi: %s]" % e, "[could not run: %s]" % e)
        # Kod, yanit geldikten SONRA calisiyor: ayni isin tutanak kaydi
        # guncellenir (ikinci bir satir acilmaz).
        if terminal_tutanak is not None and kayit_id:
            try:
                terminal_tutanak.kod_ekle(kayit_id, kod, cikti, durum)
            except Exception:
                pass

        def goster():
            if cikti:
                self._yaz(None, cikti + "\n")
            self._yaz("sistem", durum + "\n")
        self.after(0, goster)

    # ------------------------------------------------------------- anahtar --
    def _anahtar_penceresi(self):
        if nvidia_provider is None:
            self._yaz("hata", self._t("nvidia_provider yüklenemedi.\n", "nvidia_provider could not be loaded.\n"))
            return
        win = tk.Toplevel(self)
        win.title(self._t("NVIDIA API anahtarı", "NVIDIA API key"))
        win.geometry("560x220")
        win.configure(bg=THEME["bg"])
        win.transient(self)
        win.grab_set()
        d = nvidia_provider.durum()
        tk.Label(win, text=self._t(f"Durum: {d['anahtar_maskeli']}  ·  kaynak: {d['anahtar_kaynagi']}", f"Status: {d['anahtar_maskeli']}  ·  source: {d['anahtar_kaynagi']}"),
                 bg=THEME["bg"], fg=THEME["text"], font=("Segoe UI", 10)).pack(
                 anchor="w", padx=12, pady=(12, 4))
        tk.Label(win, text=self._t(
                     "Yeni anahtar build.nvidia.com hesabından alınır ve Windows "
                     "Credential Manager'a kaydedilir — diske düz metin yazılmaz.",
                     "Get a new key from your build.nvidia.com account; it is stored in "
                     "Windows Credential Manager — never written to disk in plain text."),
                 bg=THEME["bg"], fg=THEME["muted"], font=("Segoe UI", 9),
                 wraplength=520, justify="left").pack(anchor="w", padx=12)
        giris = tk.Entry(win, show="•", bg=THEME["surface"], fg=THEME["text"],
                         insertbackground=THEME["text"], font=("Consolas", 10), width=60)
        giris.pack(fill="x", padx=12, pady=8)
        sonuc_lbl = tk.Label(win, text="", bg=THEME["bg"], fg=THEME["muted"],
                             font=("Segoe UI", 9), wraplength=520, justify="left")
        sonuc_lbl.pack(anchor="w", padx=12)

        def kaydet():
            ok, mesaj = nvidia_provider.anahtar_kaydet(giris.get())
            sonuc_lbl.config(text=mesaj, fg=THEME["green"] if ok else THEME["danger"])
            if ok:
                giris.delete(0, "end")
                self._modelleri_tazele()

        RoundedButton(win, text=self._t("Kaydet", "Save"), parent_bg=THEME["bg"], bg=THEME["accent"],
                      fg="#FFFFFF", hover="#EC8A4B", command=kaydet).pack(
                      anchor="e", padx=12, pady=8)


class TutanakWindow(tk.Toplevel):
    """📜 Çalışma tutanağı: geçmiş işler, arama, görüntüleme, metne aktarma.

    Salt okunur bir görüntüleyici — kayıt silme/düzenleme bilerek yok:
    tutanağın değeri "yazılanın orada durması"ndan geliyor.
    """

    SUTUNLAR_TR = (("ts", "Tarih", 140), ("saglayici", "Sağlayıcı", 80),
                   ("model", "Model", 220), ("sure", "Süre", 60),
                   ("durum", "Durum", 60), ("kod", "Kod", 45),
                   ("istem", "İstek", 460))
    SUTUNLAR_EN = (("ts", "Date", 140), ("saglayici", "Provider", 80),
                   ("model", "Model", 220), ("sure", "Time", 60),
                   ("durum", "Status", 60), ("kod", "Code", 45),
                   ("istem", "Request", 460))

    def __init__(self, terminal):
        super().__init__(terminal)
        self.terminal = terminal
        self.lang = getattr(terminal, "lang", "tr")
        self.title(self._t("📜 AI Terminali — Çalışma Tutanağı",
                           "📜 AI Terminal — Work Record"))
        self.geometry("1120x720")
        self.configure(bg=THEME["bg"])
        self._kayitlar = []
        self._build()
        self.yenile()

    def _build(self):
        tk.Label(self, text=self._t("📜 Çalışma Tutanağı", "📜 Work Record"),
                 bg=THEME["bg"], fg=THEME["text"],
                 font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=14, pady=(12, 0))
        self.bilgi_lbl = tk.Label(self, text="", bg=THEME["bg"], fg=THEME["muted"],
                                  font=("Segoe UI", 9), wraplength=1060, justify="left")
        self.bilgi_lbl.pack(anchor="w", padx=14, pady=(2, 2))
        self.gizlilik_lbl = tk.Label(
            self, text=self._t(
                "⚠ Bu tutanak, token defterinin aksine isteğin ve yanıtın TAM "
                "METNİNİ saklar — amacı budur. Dosya yalnızca senin "
                "bilgisayarında (%APPDATA%) durur ve Drive yedeğine dâhildir.",
                "⚠ Unlike the token ledger, this record keeps the FULL TEXT of your "
                "request and the answer — that is its purpose. The file stays on your "
                "machine (%APPDATA%) and is part of the Drive backup."),
            bg=THEME["bg"], fg=THEME["accent"], font=("Segoe UI", 9),
            wraplength=1060, justify="left")
        self.gizlilik_lbl.pack(anchor="w", padx=14, pady=(0, 8))
        self.bind("<Configure>", self._sarmayi_esitle)

        ust = tk.Frame(self, bg=THEME["bg"])
        ust.pack(fill="x", padx=14)
        tk.Label(ust, text=self._t("Ara:", "Search:"), bg=THEME["bg"], fg=THEME["text"],
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        self.ara_var = tk.StringVar()
        # Koyu temada surface (#1B1712) ile bg (#201B15) neredeyse ayni ton:
        # cerceve olmadan kutunun NEREDE oldugu gorunmuyordu (ekran
        # dogrulamasinda yakalandi). THEME["border"] tam bu is icin var.
        giris = tk.Entry(ust, textvariable=self.ara_var, bg=THEME["surface"],
                         fg=THEME["text"], insertbackground=THEME["text"],
                         relief="flat", font=("Segoe UI", 10), width=42,
                         highlightthickness=1, highlightbackground=THEME["border"],
                         highlightcolor=THEME["accent"])
        giris.pack(side="left", padx=6, ipady=3)
        giris.bind("<Return>", lambda e: self.yenile())
        self.ara_var.trace_add("write", lambda *_a: self.yenile())
        RoundedButton(ust, text=self._t("🔄 Yenile", "🔄 Refresh"), parent_bg=THEME["bg"],
                      command=self.yenile).pack(side="left", padx=4)
        RoundedButton(ust, text=self._t("💾 Seçili işi metne aktar", "💾 Export selected job"), parent_bg=THEME["bg"],
                      command=self._disa_aktar).pack(side="right", padx=4)
        RoundedButton(ust, text=self._t("📋 Panoya kopyala", "📋 Copy to clipboard"), parent_bg=THEME["bg"],
                      command=self._panoya).pack(side="right", padx=4)

        govde = ttk.Panedwindow(self, orient="vertical")
        govde.pack(fill="both", expand=True, padx=14, pady=8)

        ust_cerceve = tk.Frame(govde, bg=THEME["bg"])
        self.tree = ttk.Treeview(ust_cerceve, columns=[c[0] for c in self.SUTUNLAR_TR],
                                 show="headings", selectmode="browse")
        for anahtar, baslik, genislik in (self.SUTUNLAR_EN if self.lang == "en"
                                           else self.SUTUNLAR_TR):
            self.tree.heading(anahtar, text=baslik)
            self.tree.column(anahtar, width=genislik,
                             anchor="w" if anahtar in ("model", "istem") else "center",
                             stretch=(anahtar == "istem"))
        kaydirma = ttk.Scrollbar(ust_cerceve, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=kaydirma.set)
        self.tree.pack(side="left", fill="both", expand=True)
        kaydirma.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._goster())
        govde.add(ust_cerceve, weight=2)

        alt_cerceve = tk.Frame(govde, bg=THEME["bg"])
        self.detay = tk.Text(alt_cerceve, wrap="word", bg=THEME["surface"],
                             fg=THEME["text"], insertbackground=THEME["text"],
                             relief="flat", font=("Consolas", 10), state="disabled")
        detay_kaydirma = ttk.Scrollbar(alt_cerceve, orient="vertical",
                                       command=self.detay.yview)
        self.detay.configure(yscrollcommand=detay_kaydirma.set)
        self.detay.pack(side="left", fill="both", expand=True)
        detay_kaydirma.pack(side="right", fill="y")
        govde.add(alt_cerceve, weight=3)

    def _t(self, tr, en):
        return t2(tr, en, self.lang)

    def _sarmayi_esitle(self, event=None):
        if event is not None and event.widget is not self:
            return
        genislik = max(320, (event.width if event else self.winfo_width()) - 34)
        for lbl in (getattr(self, "bilgi_lbl", None), getattr(self, "gizlilik_lbl", None)):
            try:
                lbl.config(wraplength=genislik)
            except Exception:
                pass

    # ------------------------------------------------------------ veri --
    def yenile(self, *_a):
        self._kayitlar = terminal_tutanak.ara(self.ara_var.get(), limit=500)
        self.tree.delete(*self.tree.get_children())
        for i, k in enumerate(self._kayitlar):
            istem = " ".join((k["istem"] or "").split())
            self.tree.insert("", "end", iid=str(i), values=(
                k["ts"], k["saglayici"] or "?", k["model"] or "?",
                (f"{k['sure']:.1f}" if k["sure"] is not None else "—"),
                k["durum"], "▶" if k["kod"] else "",
                istem[:160] + ("…" if len(istem) > 160 else "")))
        o = terminal_tutanak.ozet()
        dagilim = ", ".join(f"{ad}: {n}" for ad, n in sorted(o["saglayicilar"].items()))
        self.bilgi_lbl.config(text=(
            self._t(
                f"Toplam {o['toplam']} iş ({dagilim or 'kayıt yok'}) · {o['kodlu']} işte "
                f"kod çalıştırıldı · gösterilen: {len(self._kayitlar)} · dosya: {o['yol']}",
                f"{o['toplam']} jobs ({dagilim or 'no records'}) · code ran in "
                f"{o['kodlu']} · shown: {len(self._kayitlar)} · file: {o['yol']}")))
        if self._kayitlar:
            self.tree.selection_set("0")
            self._goster()
        else:
            self._detay_yaz(self._t(
                "Henüz kayıt yok — terminalden bir iş tamamladığında burada görünür.\n",
                "No records yet — a job finished in the terminal shows up here.\n"))

    def _secili(self):
        sec = self.tree.selection()
        if not sec:
            return None
        try:
            return self._kayitlar[int(sec[0])]
        except Exception:
            return None

    def _detay_yaz(self, metin):
        self.detay.configure(state="normal")
        self.detay.delete("1.0", "end")
        self.detay.insert("1.0", metin)
        self.detay.configure(state="disabled")

    def _goster(self):
        k = self._secili()
        if k:
            self._detay_yaz(terminal_tutanak.metne_cevir(k))

    def _panoya(self):
        k = self._secili()
        if not k:
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(terminal_tutanak.metne_cevir(k))
            self.bilgi_lbl.config(text=self._t("Seçili iş panoya kopyalandı.", "Selected job copied to the clipboard."))
        except Exception as exc:
            self.bilgi_lbl.config(text=self._t(f"Panoya kopyalanamadı: {exc}", f"Could not copy: {exc}"))

    def _disa_aktar(self):
        k = self._secili()
        if not k:
            self.bilgi_lbl.config(text=self._t("Önce listeden bir iş seç.", "Select a job from the list first."))
            return
        varsayilan = "terminal_isi_" + (k["ts"] or "").replace(":", "").replace(" ", "_") + ".txt"
        yol = filedialog.asksaveasfilename(
            parent=self, title=self._t("İşi metne aktar", "Export job as text"), defaultextension=".txt",
            initialfile=varsayilan, filetypes=[(self._t("Metin dosyası", "Text file"), "*.txt")])
        if not yol:
            return
        try:
            with open(yol, "w", encoding="utf-8") as f:
                f.write(terminal_tutanak.metne_cevir(k))
            self.bilgi_lbl.config(text=self._t(f"Yazıldı: {yol}", f"Written: {yol}"))
        except Exception as exc:
            self.bilgi_lbl.config(text=self._t(f"Yazılamadı: {exc}", f"Could not write: {exc}"))


def ai_terminali_ac(app):
    """Ana uygulamadan çağrılır; pencere referansını döndürür."""
    return AITerminalWindow(app)
