# -*- coding: utf-8 -*-
"""Math Course AI — tanıtım sunumunun İÇERİĞİ (tek kaynak, iki dilli).

Sunumun metni burada durur; `tanitim_uret.py` bunu PPTX/PDF/HTML'e çevirir.
İçerik ile üretimi ayırmanın sebebi: sürüm numarası koddan okunduğu için
kendiliğinden tazelenir ama İÇERİK elle yazılır —
yeni sürüm notu yazarken bu dosyaya da bakılmalı.

Her slayt bir sözlüktür:
    tip     : "kapak" | "madde" | "kart" | "sayi" | "tablo" | "kapanis"
              | "gorsel" | "galeri"
    baslik  : (tr, en)
    alt     : (tr, en)                      — isteğe bağlı alt başlık
    ogeler  : tipe göre içerik (aşağıya bak)
    gorsel  : dosya adı                     — yalnız "gorsel" tipi
    dipnot  : (tr, en)                      — isteğe bağlı

"gorsel"/"galeri" slaytları `tanitim_gorseller/<dil>/` altındaki GERÇEK
ekran görüntülerini kullanır; onları `python tanitim_ekran.py` üretir
(programı başlatır, sekme sekme gezer, fotoğraflar). Görüntüler dil
başına ayrıdır: TR destede Türkçe arayüz, EN destede İngilizce arayüz.

Metin çiftleri YERİNDE durur (anahtar sözlüğü değil): eşleşmeyen anahtar
sessizce boş slayt üretir, çift ise okurken görülür — mca_common.t2 ile aynı
gerekçe.
"""

from mca_common import VERSION

__all__ = ["SLAYTLAR", "BASLIK", "ALTBASLIK"]

BASLIK = ("Math Course AI", "Math Course AI")
ALTBASLIK = (
    f"{VERSION}  ·  yerel öncelikli matematik çalışma masası (bulut isteğe bağlı)",
    f"{VERSION}  ·  a local-first maths study workstation (cloud optional)",
)

SLAYTLAR = [
    # ─────────────────────────────────────────────────────────── kapak ──
    {
        "tip": "kapak",
        "baslik": ("Math Course AI", "Math Course AI"),
        "alt": ("Matematik kursunu takip ederken ihtiyacın olan her şey "
                "tek pencerede — yapay zekâ varsayılan olarak SENİN "
                "bilgisayarında çalışır.",
                "Everything you need while following a maths course in one "
                "window — with the AI running on YOUR machine by default."),
        "dipnot": (f"{VERSION}  ·  Windows · Python 3.11 · kaynak kod MIT "
                   f"(ikili dağıtım yok — bkz. THIRD_PARTY_NOTICES.md)",
                   f"{VERSION}  ·  Windows · Python 3.11 · source MIT "
                   f"(no binary distribution — see THIRD_PARTY_NOTICES.md)"),
    },
    # ──────────────────────────────────────────────────────────── sorun ──
    {
        "tip": "kart",
        "baslik": ("Çözdüğü sorun", "The problem it solves"),
        "alt": ("Kurs takip etmek dağınık bir iştir — program bu dağınıklığı toplar.",
                "Following a course is a scattered job — the program gathers it up."),
        "ogeler": [
            (("Dağınık çalışma", "Scattered studying"),
             ("PDF bir yerde, notlar başka yerde, sorular defterde. Hepsi tek "
              "pencerede ve tek veritabanında; kaldığın yer hatırlanır.",
              "The PDF is in one place, notes in another, questions in a "
              "notebook. All of it in one window and one database; where you "
              "left off is remembered.")),
            (("Ne çalışacağımı bilmiyorum", "I don't know what to study"),
             ("📅 Bugün panosu tekrar vakti geleni, yanlışlarını ve "
              "denenmemişleri gösterir; tek tıkla o konudan sınav başlatır.",
              "The 📅 Today dashboard shows what is due, what you got wrong and "
              "what you never tried; one click starts an exam on it.")),
            (("Unutma", "Forgetting"),
             ("Aralıklı tekrar (Leitner): doğru bildiğin 1 → 3 → 7 → 14 → 30 → "
              "60 gün sonra, yanlış bildiğin hemen karşına gelir.",
              "Spaced repetition (Leitner): correct answers return after 1 → 3 → "
              "7 → 14 → 30 → 60 days; wrong ones come back immediately.")),
            (("Takıldığımı kimseye soramıyorum", "Nobody to ask when I'm stuck"),
             ("Yerel yapay zekâ öğretmen (LM Studio) — varsayılan yol budur; "
              "yerel modelle çalışırken bağlantı gerekmez ve verin makinende kalır.",
              "A local AI tutor through LM Studio — this is the default path; "
              "with the local model no connection is needed and your data stays "
              "on your machine.")),
        ],
    },
    # ─────────────────────────────────────────────────────────── sayılar ──
    {
        "tip": "sayi",
        "baslik": ("Program bir bakışta", "The program at a glance"),
        "ogeler": [
            (("665", "665"), ("konu bilgi bankası girişi\n(AI'sız, anında)",
                              "topic knowledge entries\n(no AI, instant)")),
            (("50 + 90", "50 + 90"), ("gömülü simülasyon\n+ formül kartı",
                                      "embedded simulations\n+ formula cards")),
            (("13", "13"), ("çalışma alanı\n(5 bilim lab'ı dâhil)",
                            "workspaces\n(5 science labs inside)")),
            (("2 471", "2,471"), ("otomatik test kontrolü\n11 pakette",
                                  "automated checks\nacross 11 suites")),
        ],
        "dipnot": ("Her sayı tools/measure_facts.py ile ÖLÇÜLDÜ; elle yazılan "
                   "sayı yok. Test toplamı bu sürümün kayıtlı koşusundan gelir "
                   "ve kurs kitaplığı yokken atlanan kontroller ayrıca yazılır.",
                   "Every number here is MEASURED by tools/measure_facts.py; "
                   "none is hand-written. The test total comes from this "
                   "release's recorded run, which also states how many checks "
                   "are skipped when no course library is present."),
    },
    # ──────────────────────────────────────────────────────── kaynaklar ──
    {
        "tip": "madde",
        "baslik": ("📚 Kurs kaynakları & okuma takibi",
                   "📚 Course resources & reading progress"),
        "alt": ("Sol panel: KENDİ kurs klasörünün ders/bölüm ağacı "
                "(program hiçbir kurs içeriği dağıtmaz).",
                "The left panel: a course/section tree of YOUR OWN course "
                "folder (the program ships no course content)."),
        "ogeler": [
            ("Ağaç iki kök altında toplanır: 📘 Dersler ve 📝 Soru Bankaları.",
             "The tree groups everything under 📘 Lessons and 📝 Question Banks."),
            ("Dosyanın yanındaki ☐ kutusuna tıklamak onu ✅ Bitirdim yapar — "
             "dosya açılmaz, kurs başlığındaki sayaç güncellenir.",
             "Clicking the ☐ box marks a file ✅ Done — it does not open the "
             "file, and the counter in the course header updates."),
            ("PDF açmak dosyayı otomatik 📖 Okunuyor yapar; \"kaldığın yer\" "
             "kartı seni oraya geri götürür.",
             "Opening a PDF marks it 📖 Reading automatically; the \"continue "
             "where you left off\" card takes you back."),
            ("Arama kutusu 300 dosyalık kursta aradığın konuyu saniyede bulur.",
             "The search box finds your topic in a 300-file course in a second."),
        ],
    },
    # ────────────────────────────────────────────────────────────── PDF ──
    {
        "tip": "madde",
        "baslik": ("📄 PDF okuyucu + ✂ soru kırpma",
                   "📄 PDF reader + ✂ question clipping"),
        "ogeler": [
            ("Kalem, işaretleme, metin, silgi — çizimler AYRI bir not dosyasına "
             "kaydedilir, orijinal PDF değişmez.",
             "Pen, highlight, text, eraser — annotations go into a separate "
             "sidecar file; the original PDF is never modified."),
            ("✂ Soru Kırp: sorunun etrafına dikdörtgen çiz, yüksek çözünürlükte "
             "kesilsin ve kurs/konu/zorluk/şıklarla bankana girsin.",
             "✂ Clip Question: drag a rectangle around a question; it is cut at "
             "high resolution and enters your bank with course/topic/difficulty."),
            ("Kaynak PDF ve sayfa numarası otomatik kaydedilir — \"bu soru "
             "nereden geldi?\" sorusunun cevabı hep elinde.",
             "The source PDF and page number are stored automatically — \"where "
             "did this question come from?\" always has an answer."),
            ("İşaretli PDF'i dışa aktarabilir, yazdırabilir ya da paylaşabilirsin.",
             "You can export the annotated PDF, print it or share it."),
        ],
    },
    # ─────────────────────────────────────────────── ekran: ana pencere ──
    {
        "tip": "gorsel",
        "baslik": ("🖥 Ekranda: ana pencere", "🖥 On screen: the main window"),
        "alt": ("Solda kurs ağacı, ortada PDF okuyucu, sağda kurs takibi — "
                "üstte çalışma alanı şeridi ve AI durum ışığı.",
                "Course tree on the left, PDF reader in the middle, course "
                "tracker on the right — workspace strip and AI status on top."),
        "gorsel": "pdf.png",
        "dipnot": ("Bu ve sonraki ekranlar gerçek ekran görüntüsüdür: "
                   "tanitim_ekran.py programı başlatır ve kareleri kendisi çeker.",
                   "This and the following screens are real screenshots: "
                   "tanitim_ekran.py starts the program and takes them itself."),
    },
    # ────────────────────────────────────────────────────── konu bilgisi ──
    {
        "tip": "kart",
        "baslik": ("ℹ Konu bilgisi — yapay zekâ olmadan, anında",
                   "ℹ Topic info — instant, with no AI"),
        "ogeler": [
            (("665 konu girişi", "665 topic entries"),
             ("Elle yazılmış gömülü bir bankadan gelir: hiç AI çağrısı "
              "yapılmadan, çevrimdışı ve anında açılır. Sayı depodan ölçülür; "
              "banka bir müfredat değildir ve tam kapsam iddia etmez.",
              "From a hand-written embedded bank: no AI call at all, offline "
              "and instant. The count is measured from the repository; the "
              "bank is not a curriculum and claims no complete coverage.")),
            (("Günlük hayat benzetmesiyle başlar",
              "Starts with an everyday analogy"),
             ("Benzetme → Nedir? → Ne için kullanılır? → (varsa) 📜 tarih ve "
              "biyografi.",
              "Analogy → What is it? → What is it used for? → 📜 history and "
              "biography where there is any.")),
            (("Uydurma tarihçe yazılmaz", "No invented history"),
             ("Salt işlemsel konularda (yuvarlama, PEMDAS) tarih bölümü "
              "atlanır — bilinmeyen \"bilinmiyor\" kalır.",
              "For purely procedural topics (rounding, PEMDAS) the history "
              "section is simply left out — unknown stays unknown.")),
            (("LaTeX düzgün görünür", "LaTeX renders properly"),
             ("√, üs/alt simge, Yunan harfleri ve semboller okunabilir "
              "Unicode'a çevrilir; ham $\\sqrt{x}$ görünmez.",
              "Roots, super/subscripts, Greek letters and symbols become "
              "readable Unicode; no raw LaTeX on screen.")),
        ],
    },
    # ─────────────────────────────────────────────────────────── AI tutor ──
    {
        "tip": "madde",
        "baslik": ("🤖 Yerel yapay zekâ öğretmen", "🤖 A local AI tutor"),
        "alt": ("Yapay zekâ SENİN bilgisayarında çalışır (LM Studio).",
                "The AI runs on YOUR machine (LM Studio)."),
        "ogeler": [
            ("Program dosyaları yerelde okur ve modele yalnızca SEÇTİĞİN "
             "metni/bağlamı gönderir. VARSAYILAN sağlayıcı yereldir: hesap "
             "ve bağlantı gerektirmez, verin makinende kalır. Bulut sağlayıcı "
             "İSTEĞE BAĞLIDIR ve ancak o oturumda sen seçersen devreye girer.",
             "The program reads your files locally and sends the model only the "
             "text or context YOU selected. The DEFAULT provider is local, so it "
             "needs neither an account nor a connection and your data stays on "
             "your machine. The cloud provider is OPTIONAL and only activates if "
             "you pick it in that session."),
            ("Model profilleri: matematik, bilim, kimya, biyo, görsel ve kod "
             "işleri farklı modellere yönlendirilir.",
             "Model profiles: maths, science, chemistry, biology, vision and "
             "code work are routed to different models."),
            ("Profiller KURULU modellere göre çözümlenir — bir modeli silmek "
             "özelliği bozmaz, yalnızca kaliteyi düşürür.",
             "Profiles resolve against what is actually installed — removing a "
             "model degrades quality instead of breaking the feature."),
            ("🟢/🟡/🔴 durum göstergesi üst çubukta: hazır mı, model yüklü mü, "
             "kapalı mı — 30 saniyede bir gerçekten yoklanır.",
             "A 🟢/🟡/🔴 indicator in the top bar: ready, no model loaded, or "
             "off — genuinely polled every 30 seconds."),
        ],
    },
    # ──────────────────────────────────────────────── ekran: AI öğretmen ──
    {
        "tip": "gorsel",
        "baslik": ("🖥 Ekranda: yapay zekâ öğretmen",
                   "🖥 On screen: the AI tutor"),
        "alt": ("Soru yaz ya da problem görseli ekle; seçili kaynak hakkında "
                "sor — cevap yerel modelden gelir.",
                "Type a question or attach a problem image; ask about the "
                "selected resource — the answer comes from the local model."),
        "gorsel": "ai.png",
    },
    # ────────────────────────────────────────────────────────── terminal ──
    {
        "tip": "kart",
        "baslik": ("🖥 AI Terminali — kodu sen onaylamadan çalışmaz",
                   "🖥 AI Terminal — nothing runs before you approve it"),
        "ogeler": [
            (("İki sağlayıcı", "Two providers"),
             ("Yerel (LM Studio) — varsayılan, verin makinende kalır. NVIDIA "
              "NIM — isteğe bağlı ücretsiz deneme uçları; pencere isteklerin "
              "NVIDIA'da loglandığını açıkça yazar ve oturumluk onay ister.",
              "Local (LM Studio) — the default; your data stays on your machine. "
              "NVIDIA NIM — optional free trial endpoints; the window states "
              "plainly that requests are logged on NVIDIA's side and asks for "
              "consent for that session.")),
            (("Onay kapısı", "The approval gate"),
             ("▶ düğmesi kodun TAMAMINI ayrı bir pencerede gösterir. Onay "
              "vermeden hiçbir şey çalışmaz.",
              "The ▶ button shows the COMPLETE code in a separate window. "
              "Nothing runs until you approve.")),
            (("Bu sürümde KAPALI", "OFF in this release"),
             ("Kod çalıştırma varsayılan olarak kapalıdır: gerçek bir işletim "
              "sistemi kum havuzu yetişmedi. Açıldığında statik politika "
              "denetimi, her koşuya özel boş klasör, temizlenmiş ortam ve "
              "Windows Job Object kaynak tavanı devreye girer — bunlar KAYNAK "
              "sınırıdır, YETKİ sınırı değildir; kum havuzu DEĞİLDİR.",
              "Code execution is off by default: a real OS sandbox was not "
              "finished. When enabled you get a static policy check, a fresh "
              "empty folder per run, a scrubbed environment and Windows Job "
              "Object caps — those are RESOURCE limits, not PERMISSION limits, "
              "and they are NOT a sandbox.")),
            (("Anahtar diske yazılmaz", "The key never touches disk"),
             ("NVIDIA anahtarı ortam değişkeninden ya da bu programın KENDİ "
              "Windows Credential Manager kaydından okunur; başka bir "
              "uygulamanın kimlik deposu okunmaz. Arayüzde yalnız sağlayıcı, "
              "durum ve SON 4 karakter görünür.",
              "The NVIDIA key is read from the environment or from this "
              "program's OWN Windows Credential Manager entry; no other "
              "application's credential store is read. The interface shows only "
              "the provider, the status and the LAST 4 characters.")),
        ],
    },
    # ─────────────────────────────────────────────────────────── tutanak ──
    {
        "tip": "madde",
        "baslik": ("📜 Çalışma tutanağı — yazdırdığın kod kaybolmaz",
                   "📜 Work record — the code you had written is never lost"),
        "ogeler": [
            ("Tamamlanan her iş kalıcı kayda geçer: soru, yanıt, çalıştırılan "
             "kod, çıktısı, sağlayıcı, model ve süre.",
             "Every finished job is recorded: question, answer, executed code, "
             "its output, provider, model and duration."),
            ("📜 Tutanak penceresi tarih sıralı listeler; arama kutusu soru, "
             "yanıt, model ve kod metninde arar.",
             "The 📜 Work Record window lists jobs newest first; the search box "
             "matches question, answer, model and code text."),
            ("Seçili işi tek tıkla metne aktar ya da panoya kopyala.",
             "Export the selected job to text or copy it to the clipboard."),
            ("Token defteri yalnız SAYAÇ tutar; tutanak METİN tutar — ikisi "
             "ayrı, program bunu açıkça söyler.",
             "The token ledger keeps only COUNTERS; the record keeps TEXT — two "
             "different things, and the program says so plainly."),
        ],
    },
    # ──────────────────────────────────────────────────────── bugün panosu ──
    {
        "tip": "kart",
        "baslik": ("🎓 Öğrenci Takip — \"bugün ne çalışayım?\" 10 saniyede",
                   "🎓 Student Tracker — \"what do I study today?\" in ten seconds"),
        "ogeler": [
            (("📅 Bugün panosu", "📅 Today dashboard"),
             ("Dört kart: tekrar vakti gelenler, yanlışlar, denenmemişler, "
              "doğruluk. Her kartta tek tık sınav.",
              "Four cards: due for review, wrong, untried, accuracy. Each card "
              "starts an exam in one click.")),
            (("📌 Bu Hafta önerileri", "📌 This Week suggestions"),
             ("Biriken veriden en fazla 3 gerekçeli öneri — kural tabanlı, "
              "AI çağrısı YOK, pano anında açılır.",
              "At most three reasoned suggestions from your own data — "
              "rule-based, NO AI call, the dashboard opens instantly.")),
            (("Gerekçe hep görünür", "The reason is always visible"),
             ("\"Türev — son 12 denemede %41,7 doğruluk\" · \"Geometri — 21 "
              "gündür hiç soru çözmedin\".",
              "\"Derivatives — 41.7% over the last 12 attempts\" · \"Geometry — "
              "21 days without a single question\".")),
            (("Veri yetersizse susar", "It stays quiet without data"),
             ("Tahmin üretmez: \"öneri için henüz yeterli veri yok\" der. "
              "Zayıflık yoksa bunu da söyler.",
              "It invents nothing: it says \"not enough data yet\". If there is "
              "no weakness, it says that too.")),
        ],
    },
    # ─────────────────────────────────────────────── ekran: Bugün panosu ──
    {
        "tip": "gorsel",
        "baslik": ("🖥 Ekranda: Bugün panosu", "🖥 On screen: the Today dashboard"),
        "alt": ("Dört kart + Bu Hafta önerileri. Veri azken pano tahmin "
                "üretmez — bunu ekranda da açıkça söyler.",
                "Four cards plus This Week suggestions. With little data the "
                "dashboard invents nothing — and says so right on screen."),
        "gorsel": "takip.png",
    },
    # ────────────────────────────────────────────────────────────── SRS ──
    {
        "tip": "tablo",
        "baslik": ("🔁 Aralıklı tekrar (Leitner)", "🔁 Spaced repetition (Leitner)"),
        "alt": ("Her sorunun bir sonraki tekrar tarihi DENEME GEÇMİŞİNDEN "
                "hesaplanır — ayrı bir zamanlayıcı durumu yoktur.",
                "The next review date is computed from each question's attempt "
                "history — there is no separate scheduler state."),
        "ogeler": [
            (("Durum", "State"), ("Bir sonraki tekrar", "Next review")),
            (("Yanlış bildin", "Answered wrong"), ("Hemen — bugünkü listeye düşer",
                                                   "Immediately — into today's list")),
            (("1. kez doğru", "1st correct"), ("1 gün sonra", "1 day later")),
            (("2. kez üst üste", "2nd in a row"), ("3 gün sonra", "3 days")),
            (("3. · 4. kez", "3rd · 4th"), ("7 · 14 gün", "7 · 14 days")),
            (("5. · 6.+ kez", "5th · 6th+"), ("30 · 60 gün", "30 · 60 days")),
        ],
    },
    # ───────────────────────────────────────────────────────────── sınav ──
    {
        "tip": "madde",
        "baslik": ("📝 Sınav, ⏱ süreli mod ve soru dökümü",
                   "📝 Exams, ⏱ timed mode and the question breakdown"),
        "ogeler": [
            ("Havuz seç (Hepsi / Çözülmedi / Yanlış / Tekrar / Tekrar Vakti) ve "
             "başla. Şıklı sorular otomatik puanlanır.",
             "Pick a pool (All / Untried / Wrong / Review / Due) and start. "
             "Multiple-choice questions are graded automatically."),
            ("Açık uçlu sorularda sympy eşdeğerliği anlar (0,5 = 1/2, 2x+2x = 4x) "
             "ve EŞLEŞTİ / EŞDEĞER / FARKLI önerir — son kararı SEN verirsin.",
             "For open questions sympy recognises equivalence (0.5 = 1/2, "
             "2x+2x = 4x) and suggests MATCH / EQUIVALENT / DIFFERENT — but YOU "
             "make the final call."),
            ("⏱ Süre koy: geri sayım işler (son dakika kırmızı), süre bitince "
             "sınav kendini kapatır ve özet bunu açıkça söyler.",
             "Set a duration: a countdown runs (red in the last minute) and the "
             "exam closes itself when time is up, saying so in the summary."),
            ("Sınav bittikten sonra satıra çift tıkla: hangi soruda ne yazdın, "
             "doğru cevap neydi, ne kadar kaldın — soru soru.",
             "Afterwards double-click a row: what you answered, the correct "
             "answer and how long you spent — question by question."),
        ],
    },
    # ────────────────────────────────────────────────────────────── rapor ──
    {
        "tip": "madde",
        "baslik": ("📄 Haftalık özet raporu", "📄 Weekly summary report"),
        "alt": ("Tarayıcıda açılan tek sayfa; renkli ya da gri yazdırılır, A4 PDF olur.",
                "A single page in your browser; prints in colour or grayscale as an A4 PDF."),
        "ogeler": [
            ("Haftanın çalışma günleri, çözülen soru sayısı, doğruluğun GEÇEN "
             "HAFTAYA GÖRE değişimi.",
             "Study days, questions answered, and how your accuracy changed "
             "AGAINST LAST WEEK."),
            ("Haftanın zayıf konuları ve bitirilen sınavlar (süreli miydi bilgisi "
             "dâhil).",
             "This week's weak topics and the exams you finished (including "
             "whether they were timed)."),
            ("Veri yoksa BOŞ GRAFİK ÇİZİLMEZ — \"bu hafta veri yok\" yazar.",
             "With no data it draws NO EMPTY CHART — it says \"no data this week\"."),
            ("Üç denemeden az veri olan konu haftalık yoruma girmez; iki "
             "denemeden hafta çıkarımı yapılmaz.",
             "A topic with fewer than three attempts is left out — no conclusions "
             "are drawn from two attempts."),
        ],
    },
    # ─────────────────────────────────────────────────────────── paketler ──
    {
        "tip": "kart",
        "baslik": ("📦 Soru paketleri — sınırsız, telifsiz, paylaşılabilir",
                   "📦 Question packs — unlimited, licence-free, shareable"),
        "ogeler": [
            (("Yerleşik üreteçler", "Built-in generators"),
             ("Pre-Algebra, Algebra, Geometri, Lineer Cebir, Calculus — soru VE "
              "kesin cevabını üretir, TR/EN, sınırsız.",
              "Pre-Algebra, Algebra, Geometry, Linear Algebra, Calculus — they "
              "produce the question AND its exact answer, TR/EN, unlimited.")),
            (("📤 .mcpack ile paylaş", "📤 Share with .mcpack"),
             ("Sorularını lisans + atıfla tek dosyaya yaz; ✂ ile kırptığın "
              "GÖRSELLİ sorular da taşınır.",
              "Write your questions into one file with licence and attribution; "
              "questions you clipped with ✂ keep their IMAGES.")),
            (("Telif kuralı", "The licence rule"),
             ("Telifli soru bankaları programa GÖMÜLMEZ. Harici pakette lisans "
              "belirtilmemişse UNKNOWN işaretlenir ve uyarı çıkar.",
              "Copyrighted banks are NEVER embedded. An external pack with no "
              "licence is flagged UNKNOWN and warned about before import.")),
            (("Güvenli içe aktarma", "Safe import"),
             ("Paketten gelen görsel yolları doğrulanır: ../ ya da mutlak yol "
              "veren bir paket dosya sistemine taşamaz.",
              "Image paths inside a pack are validated: one containing ../ or an "
              "absolute path cannot escape onto your filesystem.")),
        ],
    },
    # ────────────────────────────────────────────────────── lab + görsel ──
    {
        "tip": "kart",
        "baslik": ("🧪 Laboratuvarlar ve 📐 Görsel Matematik",
                   "🧪 Labs and 📐 Visual Math"),
        "ogeler": [
            (("📐 Görsel Matematik Lab", "📐 Visual Math Lab"),
             ("sympy ile adım adım çözüm + matplotlib grafiği. Cevabı değil, "
              "YOLU görürsün.",
              "Step-by-step solutions with sympy plus a matplotlib plot. You see "
              "the PATH, not just the answer.")),
            (("50 simülasyon · 90 formül kartı", "50 simulations · 90 formula cards"),
             ("Kurs konularının etkileşimli görselleştirmeleri ve formülün ne "
              "dediğini gösteren kartlar.",
              "Interactive visualisations of course topics and cards showing "
              "what a formula actually says.")),
            (("🧪 Beş bilim lab'ı", "🧪 Five science labs"),
             ("Veri, Fizik, Kimya, DNA, Kuantum — hepsinin ortak fikri aynı: "
              "konuyu MATEMATİĞE çevirmek.",
              "Data, Physics, Chemistry, DNA, Quantum — they all share one idea: "
              "turn the subject into MATHS.")),
            (("Ders kartı üretici", "Lesson-card generator"),
             ("Poster kalitesinde, yazdırılabilir PNG ders kartları.",
              "Poster-quality, printable PNG lesson cards.")),
        ],
    },
    # ───────────────────────────────────────────── ekran: Görsel Mat Lab ──
    {
        "tip": "gorsel",
        "baslik": ("🖥 Ekranda: Görsel Matematik Lab",
                   "🖥 On screen: the Visual Math Lab"),
        "alt": ("Soldan örnek yükle: sağda grafik, altta adım adım çözüm ve "
                "\"gerçek hayat açıklaması\" birlikte gelir.",
                "Load an example: the graph, the step-by-step solution and the "
                "\"real-life explanation\" arrive together."),
        "gorsel": "visual.png",
    },
    # ──────────────────────────────────────────── ekran: lab'lar + tahta ──
    {
        "tip": "galeri",
        "baslik": ("🖥 Ekranda: bilim lab'ları ve çizim tahtası",
                   "🖥 On screen: the science labs and the drawing board"),
        "ogeler": [
            ("lab.png",
             ("🧪 Fizik Lab'ı — beş bilim lab'ından biri",
              "🧪 The Physics Lab — one of five science labs")),
            ("tahta.png",
             ("🖊️ Tablet çizim tahtası — çöz, \"ne çizdim?\" diye sor",
              "🖊️ Tablet drawing board — work, then ask \"what did I draw?\"")),
        ],
    },
    # ─────────────────────────────────────────────────────── yardımcılar ──
    {
        "tip": "madde",
        "baslik": ("📖 Sözlük · 🧮 Hesap · 🖊️ Tablet tahtası",
                   "📖 Dictionary · 🧮 Calculator · 🖊️ Drawing board"),
        "ogeler": [
            ("Dil & Bilim Sözlüğü: 9 alt sekme, PDF kelime tarayıcı, görsel/OCR "
             "çeviri, favoriler ve \"bu kelimenin matematikteki anlamı ne?\"",
             "Language & Science Dictionary: nine sub-tabs, a PDF vocabulary "
             "scanner, image/OCR translation, favourites and \"what does this "
             "word mean in maths?\""),
            ("Bilimsel hesap makinesi: kesir duyarlı, RAD/DEG, güvenli "
             "değerlendirici + AI sohbet kutusu.",
             "Scientific calculator: fraction-aware, RAD/DEG, a safe evaluator "
             "plus an AI chat box."),
            ("Tablet çizim tahtası: fare, kalemli ekran ya da çizim tabletiyle "
             "çöz; \"ne çizdim?\" diyerek çözümünü kontrol ettir.",
             "Tablet drawing board: work with a mouse, pen display or graphics "
             "tablet; ask \"what did I draw?\" to get your working checked."),
            ("X Düzeni: klasik, ayna ya da İKİ BAĞIMSIZ PDF okuyucu — dersle "
             "çözümü yan yana açarsın.",
             "X Layout: classic, mirrored, or TWO INDEPENDENT PDF readers — put "
             "the lesson and the solution side by side."),
        ],
    },
    # ────────────────────────────────────────── ekran: sözlük + hesap ──
    {
        "tip": "galeri",
        "baslik": ("🖥 Ekranda: sözlük ve hesap makinesi",
                   "🖥 On screen: the dictionary and the calculator"),
        "ogeler": [
            ("sozluk.png",
             ("📖 Dil & Bilim Sözlüğü — 9 alt sekme, PDF kelime tarayıcı",
              "📖 Language & Science Dictionary — 9 sub-tabs, PDF vocab scanner")),
            ("hesap.png",
             ("🧮 Bilimsel hesap makinesi + AI sohbet kutusu",
              "🧮 Scientific calculator with its AI chat box")),
        ],
    },
    # ───────────────────────────────────────────────────────────── V48 ──
    {
        "tip": "kart",
        "baslik": (f"Bu sürümde ({VERSION.split('—')[0].strip()})",
                   f"In this release ({VERSION.split('—')[0].strip()})"),
        "ogeler": [
            (("🌙 Koyu tema", "🌙 Dark theme"),
             ("Sıcak kimliği koruyan gece paleti. İçerik adaları (PDF sayfası, "
              "ders kartı) bilerek açık kalır.",
              "A night palette that keeps the warm identity. Content islands "
              "(PDF pages, lesson cards) deliberately stay light.")),
            (("🌍 Gerçek iki dillilik", "🌍 Real bilingualism"),
             ("Öğrenci takip, terminal, defter, hesap, tahta — öneri gerekçeleri "
              "ve haftalık rapor dâhil İngilizce konuşuyor.",
              "Student tracker, terminal, ledger, calculator, board — English "
              "now, including suggestion reasons and the weekly report.")),
            (("⚡ Tembel panel yükleme", "⚡ Lazy panel loading"),
             ("Paneller ilk kullanıldıklarında kurulur, açılışta değil. "
              "Yeniden üretilebilir bir açılış ölçüm düzeneği depoda YOK, bu "
              "yüzden bir hızlanma yüzdesi İDDİA EDİLMEZ.",
              "Panels are built on first use, not at startup. There is NO "
              "reproducible startup benchmark in this repository, so no "
              "speed-up percentage is CLAIMED.")),
            (("🎓 Kılavuz ve modül bölünmesi", "🎓 Guide and module split"),
             ("19 bölümlük çevrimdışı kılavuz (TR/EN aynı derinlikte); program "
              "tek dev dosya yerine ayrı modüllere bölündü.",
              "A 19-chapter offline guide (TR/EN at equal depth); the program "
              "was split out of one huge file into separate modules.")),
        ],
    },
    # ──────────────────────────────────────────────────────────── gizlilik ──
    {
        "tip": "madde",
        "baslik": ("🔒 Gizlilik — varsayılan değil, TASARIM",
                   "🔒 Privacy — by design, not by setting"),
        "ogeler": [
            ("Kurs PDF'lerin, notların, öğrenci verin ve çalışma geçmişin "
             "HİÇBİR yapay zekâ sağlayıcısına gönderilmez — ne yerele ne buluta. "
             "Telemetri, analitik ve güncelleme kontrolü YOKTUR.",
             "Your PDFs, notes, learner data and study history are sent to NO AI "
             "provider — neither local nor cloud. There is NO telemetry, NO "
             "analytics and NO update check."),
            ("Tek çıkış yolu: AI Terminali'nde bulut sağlayıcıyı O OTURUMDA "
             "seçip onay penceresini kabul edersen, yazdığın istem ve son 12 "
             "tur NVIDIA'ya gider (NVIDIA bunları loglar). Makinede anahtar "
             "bulunması İZİN DEĞİLDİR; varsayılan her zaman yereldir.",
             "The one way out: if you pick the cloud provider IN THAT SESSION "
             "and accept the consent dialog, your prompt and the last 12 turns "
             "go to NVIDIA (which logs them). Having a key on the machine is "
             "NOT consent; the default is always local."),
            ("Bir öğrenciyi silmek sınav cevapları dâhil ona ait TÜM satırları "
             "siler (silme testi ile kanıtlanır).",
             "Deleting a learner erases EVERY row belonging to them, exam "
             "answers included (proved by a regression test)."),
            ("Verin %APPDATA%\\MathCourseAI altında; programı yeniden derlesen "
             "ya da taşısan da çalışma geçmişin kaybolmaz.",
             "Your data lives under %APPDATA%\\MathCourseAI; rebuilding or "
             "moving the program never wipes your history."),
            ("Token defterinde istek METİNLERİ saklanmaz — yalnız sayaçlar. "
             "Tutanakta saklanır ve program bunu söyler.",
             "The token ledger stores no request TEXT — only counters. The work "
             "record does store it, and the program tells you."),
        ],
    },
    # ────────────────────────────────────────────────────────────── kalite ──
    {
        "tip": "sayi",
        "baslik": ("Nasıl geliştiriliyor", "How it is built"),
        "ogeler": [
            (("2 471", "2,471"), ("otomatik kontrol\n11 test paketinde",
                                  "automated checks\nacross 11 suites")),
            (("190", "190"), ("kurs kitaplığı yokken\natlanan kontrol",
                              "checks skipped when no\ncourse library is present")),
            (("11", "11"), ("CI adımı\nwindows-latest · Python 3.11",
                            "CI steps\nwindows-latest · Python 3.11")),
            (("MIT", "MIT"), ("kaynak kod lisansı\n(kurs içeriği hariç)",
                              "source-code licence\n(course content excluded)")),
        ],
        "dipnot": ("Bu deste CI rozeti ya da hatasızlık iddiası TAŞIMAZ: rozet "
                   "henüz olmamış bir koşu hakkında iddiadır. Gerçek durum "
                   "Actions sekmesindedir. Lisans notu: kaynak kod MIT; isteğe "
                   "bağlı PyMuPDF AGPL-3.0'dır ve bu depo ikili dağıtmaz "
                   "(THIRD_PARTY_NOTICES.md).",
                   "This deck carries NO CI badge and asserts NO defect-free "
                   "state: a badge asserts something about a run that has not happened "
                   "yet. The real state is in the Actions tab. Licence note: the "
                   "source is MIT; the optional PyMuPDF is AGPL-3.0 and this "
                   "repository distributes no binary (THIRD_PARTY_NOTICES.md)."),
    },
    # ─────────────────────────────────────────────────────────── kapanış ──
    {
        "tip": "kapanis",
        "baslik": ("Nasıl başlanır?", "How to start"),
        "ogeler": [
            ("Kurs PDF'lerini Resources\\ klasörüne koy ya da Gözat ile kendi "
             "klasörünü seç.",
             "Put your course PDFs in Resources\\ or pick your own folder with "
             "Browse."),
            ("PDF'in yoksa da olur: Soru Paketleri'nden yerleşik üreteçlerden "
             "birini içe aktar, hemen çalışmaya başla.",
             "No PDFs? That is fine: import a built-in generator from Question "
             "Packs and start straight away."),
            ("Yapay zekâ İSTEĞE BAĞLI: LM Studio kurmadan da PDF, notlar, "
             "banka, sınav, laboratuvarlar ve sözlük tam çalışır.",
             "The AI is OPTIONAL: without LM Studio the PDFs, notes, bank, "
             "exams, labs and dictionary all work fully."),
        ],
        "dipnot": ("Ayarlar → 🎓 Kullanma Kılavuzu: 19 bölümlük çevrimdışı "
                   "kılavuz, TR ve EN.",
                   "Settings → 🎓 User Guide: a 19-chapter offline guide, in "
                   "Turkish and English."),
    },
]
