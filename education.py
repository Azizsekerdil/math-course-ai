# -*- coding: utf-8 -*-
"""Math Course AI — 🎓 Eğitim & Tanıtım Modülü (Tkinter'siz, iki dilli).

Programın nasıl kullanılacağını "neden → sonuç → fayda" mantığıyla anlatan,
kendi kendine yeten (offline) tek sayfa HTML üretir. Ana program bu HTML'i
geçici klasöre yazıp sistem tarayıcısında açar (kilavuz_ac).

egitim_html(lang="tr") — "tr" Türkçe, "en" İngilizce içerik döndürür.
Yeni sürüm çıkınca HER İKİ dilde de _body_tr()/_body_en() güncellenir.

Kapsam notu: İngilizce gövde V48'de Türkçe gövdenin DERİNLİĞİNE çıkarıldı —
iki dil de aynı 19 bölümü, aynı 26 alt başlığı (aynı sırayla), aynı
neden→sonuç→fayda bloklarını ve aynı tabloları taşır. Çapa kimlikleri iki
dilde AYNIDIR, böylece derin bağlantılar ve testler her iki dilde çalışır.
test_egitim_token bu eşitliği (h2 + h3 + blok/tablo sayıları) doğrular; yeni
bölüm eklerken İKİ gövdeyi birlikte güncelle, yoksa test kırılır.

Çeviri bire bir değil, doğal İngilizcedir; teknik terimler README'nin
İngilizce bölümüyle tutarlıdır (question bank, exam engine, spaced
repetition, approval gate, model profiles, work record).
"""

__all__ = ["egitim_html", "kilavuz_ac", "sayfa_html", "BOLUM_SAYISI"]


# ══════════════════════════════════════════════════════════════════════════
# YARDIMCILAR — belgenin görsel dili
# ══════════════════════════════════════════════════════════════════════════

def _cause(neden, sonuc, fayda, lang="tr"):
    """Bir özelliği üç satırda anlatır: ne yaptın → ne oldu → ne işine yarar."""
    n, s, f = ("Neden", "Sonuç", "Fayda") if lang == "tr" else ("Why", "Result", "Benefit")
    return ('<div class="cause"><div class="row">'
            f'<span class="lab n">{n}</span><span>{neden}</span>'
            f'<span class="lab s">{s}</span><span>{sonuc}</span>'
            f'<span class="lab f">{f}</span><span>{fayda}</span>'
            '</div></div>')


def _tablo(basliklar, satirlar):
    th = "".join(f"<th>{b}</th>" for b in basliklar)
    trs = "".join("<tr>" + "".join(f"<td>{h}</td>" for h in satir) + "</tr>"
                  for satir in satirlar)
    return f'<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>'


def _h2(no, baslik, _id):
    return f'<h2 id="{_id}"><span class="n">{no}</span>{baslik}</h2>'


def _h3(baslik, _id):
    return f'<h3 id="{_id}">{baslik}</h3>'


def _toc(items, baslik="İçindekiler"):
    lis = ""
    for _id, txt, alt in items:
        lis += f'<a class="{"sub" if alt else "top"}" href="#{_id}">{txt}</a>'
    return f'<nav class="toc"><div class="toc-h">{baslik}</div>{lis}</nav>'


def _note(metin):
    return f'<div class="note">{metin}</div>'


def _warn(metin):
    return f'<div class="warn">{metin}</div>'


def _lead(metin):
    return f'<p class="lead">{metin}</p>'


# ══════════════════════════════════════════════════════════════════════════
# TÜRKÇE İÇERİK
# ══════════════════════════════════════════════════════════════════════════

def _body_tr():
    toc = _toc([
        ("genel", "Genel Bakış", False),
        ("yeni", "🎉 Bu Sürümdeki Yenilikler", False),
        ("ilk10", "🚀 İlk 10 Dakika", False),
        ("kaynak", "📚 Kurs Kaynakları", False),
        ("kaynak-agac", "Ağaç: Dersler & Soru Bankaları", True),
        ("kaynak-tik", "☐ Bitirdim Tiki & İlerleme", True),
        ("kaynak-info", "ℹ Konu Bilgisi (AI'sız, anında)", True),
        ("pdf", "📄 PDF Okuyucu & Not Alma", False),
        ("pdf-gezinme", "Zoom, Sayfa, Fit Width", True),
        ("pdf-not", "Kalem · İşaretleme · Metin · Silgi", True),
        ("pdf-kirp", "✂ Soru Kırp → Soru Bankası", True),
        ("ai", "🤖 Yapay Zekâ Öğretmen", False),
        ("ai-kurulum", "LM Studio Kurulumu", True),
        ("ai-profil", "Model Profilleri", True),
        ("ai-durum", "🟢 AI Durum Göstergesi", True),
        ("ai-gorsel", "🖼 Görsel Soru Çözücü", True),
        ("terminal", "🖥 AI Terminali", False),
        ("terminal-saglayici", "İki Sağlayıcı: Yerel · NVIDIA", True),
        ("terminal-kod", "▶ Kod Çalıştırma & Onay Kapısı", True),
        ("terminal-tutanak", "📜 Çalışma Tutanağı (kalıcı kayıt)", True),
        ("takip", "🎓 Öğrenci Takip", False),
        ("takip-bugun", "📅 Bugün Panosu", True),
        ("takip-hafta", "📌 Bu Hafta — kişisel öneriler", True),
        ("takip-srs", "🔁 Aralıklı Tekrar (Leitner)", True),
        ("takip-banka", "📥 Soru Bankası", True),
        ("takip-sinav", "📝 Sınav & ⏱ Süreli Mod", True),
        ("takip-istatistik", "📊 İstatistik & Sınav Dökümü", True),
        ("takip-rapor", "📄 Haftalık Özet raporu", True),
        ("paket", "📦 Soru Paketleri", False),
        ("paket-yerlesik", "Yerleşik Üreteçler (sınırsız)", True),
        ("paket-disa", "📤 Paket Dışa Aktarma (paylaşım)", True),
        ("paket-lisans", "Lisans Kuralı", True),
        ("lab", "🧪 Lab'lar", False),
        ("gorsel", "📐 Görsel Matematik Laboratuvarı", False),
        ("sozluk", "📖 Dil & Bilim Sözlüğü", False),
        ("hesap", "🧮 Hesap Makinesi", False),
        ("tablet", "🖊️ Tablet Çizim Tahtası", False),
        ("ayar", "⚙ Ayarlar", False),
        ("ayar-tema", "🌙 Koyu Tema", True),
        ("ayar-acilis", "Açılış Ekranı", True),
        ("ayar-alan", "Çalışma Alanları & X Düzeni", True),
        ("ayar-dil", "🌍 Dil: Türkçe / İngilizce", True),
        ("token", "📒 Token Kullanım Defteri", False),
        ("veri", "💾 Veri, Gizlilik & Yedek", False),
        ("sorun", "🔧 Sorun Giderme", False),
        ("uyari", "⚠ Önemli Notlar", False),
    ])

    genel = _h2("1", "Genel Bakış", "genel") + (
        _lead('<b>Math Course AI</b>, çevrimiçi matematik kurslarını takip ederken '
              'ihtiyacın olan her şeyi tek pencerede toplayan bir masaüstü öğrenme '
              'platformudur: PDF oku ve not al, soruyu kırp bankana at, aralıklı '
              'tekrarla çalış, sınav ol, takıldığında yapay zekâya sor.')
        + '<div class="legend">'
          '<b style="color:var(--blue)">Neden</b> = senin yaptığın eylem · '
          '<b style="color:var(--green)">Sonuç</b> = ekranda ne olur · '
          '<b style="color:var(--amber)">Fayda</b> = ne işine yarar.</div>'
        + _tablo(["Program neyi çözer", "Nasıl"], [
            ["<b>Dağınık çalışma</b> — PDF bir yerde, notlar başka yerde, sorular defterde",
             "Hepsi tek pencerede ve tek veritabanında; kaldığın yer hatırlanır"],
            ["<b>Ne çalışacağımı bilmiyorum</b>",
             "📅 Bugün panosu tekrar vakti geleni, yanlışlarını ve denenmemişleri "
             "gösterir; tek tıkla o konudan sınav başlatır"],
            ["<b>Unutma</b>", "Aralıklı tekrar (Leitner): doğru bildiğin 1 → 3 → 7 → 14 → "
             "30 → 60 gün sonra, yanlış bildiğin hemen karşına gelir"],
            ["<b>Takıldığım soruyu kimseye soramıyorum</b>",
             "Yerel yapay zekâ öğretmen (LM Studio) — internet gerekmez, veri "
             "bilgisayardan çıkmaz"],
            ["<b>Soru bulamıyorum</b>", "Yerleşik üreteçler sınırsız, telifsiz, TR/EN "
             "soru üretir; PDF'ten ✂ ile soru kırpabilirsin"],
        ])
        + _note('<b>Kimlik:</b> Program <b>yerel önceliklidir</b>: varsayılan yapay '
                'zekâ senin bilgisayarındaki LM Studio üzerinden konuşur ve kurs '
                'PDF\'lerin, notların, öğrenci verin ve çalışma geçmişin HİÇBİR '
                'sağlayıcıya gönderilmez. <b>İsteğe bağlı bulut:</b> <b>AI '
                'Terminali</b>\'nde NVIDIA sağlayıcısını <i>o oturumda sen seçip '
                'onay penceresini kabul edersen</i>, yazdığın istem ve son 12 tur '
                'NVIDIA\'ya gider ve orada loglanır. Makinede anahtar bulunması izin '
                'değildir; varsayılan her zaman yereldir.'))

    yeni = _h2("★", "🎉 Bu Sürümdeki Yenilikler", "yeni") + (
        _lead('En son eklenenler — ayrıntılar ilgili bölümlerde:')
        + _tablo(["Yenilik", "Ne kazandırır"], [
            ['<b>🖥 AI Terminali</b>', 'Kod ve işlerini yapay zekâya yazdır: yerel LM Studio '
             'ya da NVIDIA\'nın ücretsiz uçları. Üretilen kod <b>onay penceresinden '
             'geçmeden çalışmaz</b>. Ayrıntı: <a href="#terminal">🖥 AI Terminali</a>'],
            ['<b>📒 Token Kullanım Defteri</b>', 'Yapay zekâya giden her isteğin kaydı: '
             'hangi model, kaç token, kaç saniye. Özet kartlar + gruplu tablolar + CSV. '
             'Ayrıntı: <a href="#token">📒 Token Defteri</a>'],
            ['<b>🌙 Koyu tema</b>', 'Gece çalışması için sıcak koyu palet; Ayarlar\'dan '
             'seçilir, yeniden başlatınca uygulanır. <a href="#ayar-tema">Ayrıntı</a>'],
            ['<b>🧪 Lab\'lar tek sekmede</b>', '5 bilim laboratuvarı tek sekmede iç '
             'sekmelere taşındı — ana şerit 12\'den 8\'e indi. <a href="#lab">Ayrıntı</a>'],
            ['<b>⏱ Süreli sınav</b>', 'Sınava süre koy, geri sayım işlesin, süre bitince '
             'otomatik kapansın. <a href="#takip-sinav">Ayrıntı</a>'],
            ['<b>📤 Paket dışa aktarma</b>', 'Sorularını lisans+atıf bilgisiyle JSON pakete '
             'yaz, arkadaşına ver. <a href="#paket-disa">Ayrıntı</a>'],
            ['<b>🎓 Karşılama kartı</b>', 'Kurs klasörün boşsa program artık ne yapman '
             'gerektiğini üç adımda söylüyor. <a href="#ilk10">Ayrıntı</a>'],
            ['<b>🟢 AI durum göstergesi</b>', 'Üst çubukta yapay zekânın hazır olup '
             'olmadığı sürekli görünür. <a href="#ai-durum">Ayrıntı</a>'],
            ['<b>🌍 Gerçek iki dillilik</b>', 'Öğrenci Takip, AI Terminali, token defteri, '
             'hesap makinesi, tablet tahtası ve PDF araç çubuğu artık İngilizce de '
             'konuşuyor — öneri gerekçeleri ve haftalık rapor dâhil. '
             '<a href="#ayar-dil">Ayrıntı</a>'],
            ['<b>📦 Görselli paket paylaşımı</b>', '✂ ile kırptığın görsel sorular artık '
             '<code>.mcpack</code> ile arkadaşına gidiyor. '
             '<a href="#paket-disa">Ayrıntı</a>'],
            ['<b>📄 Haftalık Özet raporu</b>', 'Tek sayfa, yazdırılabilir hafta raporu + '
             'sınav geçmişinde <b>soru soru döküm</b>. '
             '<a href="#takip-rapor">Ayrıntı</a>'],
            ['<b>📌 Bu Hafta önerileri</b>', 'Bugün panosu artık "ne çalışayım?" sorusuna '
             'gerekçeli üç öneriyle cevap veriyor — kural tabanlı, AI çağrısı yok. '
             '<a href="#takip-hafta">Ayrıntı</a>'],
            ['<b>📜 Terminal çalışma tutanağı</b>', 'Terminaldeki her iş artık kalıcı: '
             'soru, yanıt, çalıştırılan kod ve çıktısı aranabilir bir kayda yazılıyor. '
             '<a href="#terminal-tutanak">Ayrıntı</a>'],
            ['<b>🚀 Açılış ekranı seçeneği</b>', 'Program son oturumunla mı yoksa '
             '📅 Bugün panosuyla mı açılsın — sen seç. <a href="#ayar-acilis">Ayrıntı</a>'],
            ['<b>⚡ %45 daha hızlı açılış</b>', 'Ağır modüller (Görsel Mat, OCR) artık '
             'ilk kullanımda yükleniyor: açılış 3,5 sn → 1,9 sn.'],
        ]))

    ilk10 = _h2("2", "🚀 İlk 10 Dakika", "ilk10") + (
        _lead('Programı ilk kez açtıysan sırasıyla şunları yap:')
        + _cause('Kurs PDF\'lerini <code>Resources\\</code> klasörüne koy ya da sol '
                 'üstteki <b>Gözat</b> ile kendi klasörünü seç',
                 'Sol paneldeki ağaç kurslarını 📘 Dersler ve 📝 Soru Bankaları '
                 'başlıkları altında listeler',
                 'Bütün kurs materyalin tek yerden erişilebilir olur')
        + _cause('Ağaçtan bir PDF\'e çift tıkla',
                 'PDF Okuyucu sekmesi açılır, dosya "📖 Okunuyor" işaretlenir',
                 'Nerede kaldığını program hatırlar; "▶ Devam Et" ile geri dönersin')
        + _cause('PDF\'te bir sorunun üstünde <b>✂ Soru Kırp</b> ile dikdörtgen çiz',
                 'Kırpılan görsel soru bankasına eklenir (kurs/konu/zorluk/şıklar sorulur)',
                 'Kitaptaki soru artık senin bankanda; sınavda karşına çıkar')
        + _cause('Öğrenci Takip → <b>Sınav</b> sekmesinden sınav başlat',
                 'Sorular tek tek gelir, cevabını görüp Doğru/Yanlış işaretlersin',
                 'Yanlışların otomatik "Yanlış" olur, tekrar çalışacağın liste kendiliğinden oluşur')
        + _note('<b>PDF\'in yok mu?</b> Sorun değil — Öğrenci Takip → <b>Soru Paketleri</b> '
                'sekmesinden yerleşik üreteçlerden birini seç (Pre-Algebra, Algebra, '
                'Geometri, Lineer Cebir, Calculus). Sınırsız, telifsiz, iki dilli soru üretir. '
                'Boş program açılışında bu üç adım <b>karşılama kartında</b> da yazar.')
        + _warn('<b>Yapay zekâ isteğe bağlıdır.</b> LM Studio kurmadan da programın her '
                'yeri çalışır: PDF, notlar, soru bankası, sınav, laboratuvarlar, sözlük, '
                'hesap makinesi. AI sadece "bunu bana açıkla" dediğinde devreye girer.'))

    kaynak = _h2("3", "📚 Kurs Kaynakları", "kaynak") + (
        _lead('Sol panel: kendi kurs klasörünün ders/bölüm ağacı, arama kutusu ve okuma takibi.')
        + _h3("Ağaç: Dersler & Soru Bankaları", "kaynak-agac")
        + _cause('Klasörünü seçtin',
                 'Ağaç iki kök altında toplanır: <b>📘 Dersler</b> ve <b>📝 Soru Bankaları</b> '
                 '(klasör adında "soru bank" geçenler ikinci gruba düşer)',
                 'Ders okumakla soru çözmeyi karıştırmazsın')
        + _cause('Arama kutusuna yazdın', 'Ağaç anında filtrelenir',
                 '300 dosyalık kursta aradığın konuyu saniyede bulursun')
        + _h3("☐ Bitirdim Tiki & İlerleme", "kaynak-tik")
        + _cause('Dosyanın yanındaki <b>☐ kutusuna</b> tıkladın',
                 'Dosya ✅ Bitirdim olur (dosya <i>açılmaz</i>), kurs başlığındaki sayaç '
                 '<code>3/12 ✅</code> güncellenir',
                 'Kursun neresinde olduğunu bir bakışta görürsün')
        + _cause('PDF açtın', 'Dosya otomatik "📖 Okunuyor" işaretlenir',
                 'Elle işaretlemeyi unutsan da ilerleme kaydı doğru kalır')
        + _h3("ℹ Konu Bilgisi — AI'sız, anında", "kaynak-info")
        + _cause('Dosya ya da konu klasörünün yanındaki <b>ℹ</b> simgesine tıkladın',
                 'Ayrı pencere açılır: günlük hayat benzetmesi → <i>Nedir?</i> → '
                 '<i>Ne İçin Kullanılır?</i> → (varsa) 📜 Tarih ve Biyografi',
                 'Konuya girmeden önce "bu ne işe yarıyor?" sorusunun cevabını alırsın')
        + _note('Bu bilgiler <b>elle yazılmış gömülü bir bankadan</b> gelir: 668 konunun '
                '667\'si hazır, <b>hiç AI çağrısı yapılmadan</b>, çevrimdışı ve anında. '
                'Salt işlemsel konularda (yuvarlama, PEMDAS gibi) <b>uydurma tarihçe '
                'yazılmaz</b> — o bölüm atlanır. Belgelenmemiş nadir bir konuda "🤖 Yerel '
                'AI\'dan Sor" düğmesi isteğe bağlı devreye girer.'))

    pdf = _h2("4", "📄 PDF Okuyucu & Not Alma", "pdf") + (
        _h3("Zoom, Sayfa, Fit Width", "pdf-gezinme")
        + _tablo(["Düğme", "Ne yapar", "Ne işine yarar"], [
            ["<b>+ / −</b>", "Yakınlaştırır/uzaklaştırır (0.35× – 5×)",
             "Küçük dizgili formülleri okursun"],
            ["<b>Fit Width</b>", "Sayfayı pencere genişliğine oturtur",
             "Her sayfada zoom ayarıyla uğraşmazsın"],
            ["<b>◀ ▶ / sayfa no</b>", "Sayfa gezinme",
             "Uzun kitapta hedef sayfaya atlarsın"],
        ])
        + _h3("Kalem · İşaretleme · Metin · Silgi", "pdf-not")
        + _cause('<b>Pen</b> ya da <b>Highlight</b> seçip PDF üzerine çizdin',
                 'Çizim sayfa numarasıyla birlikte ayrı bir not dosyasına kaydedilir '
                 '(orijinal PDF <b>değişmez</b>)',
                 'Kitabın bozulmaz; notların yedeklenebilir ve taşınabilir')
        + _cause('<b>Save Notes</b> / <b>Export Annotated PDF</b>',
                 'Notlar diske yazılır / işaretlerin gömülü olduğu yeni bir PDF üretilir',
                 'İşaretli hâlini yazdırabilir veya paylaşabilirsin')
        + _h3("✂ Soru Kırp → Soru Bankası", "pdf-kirp")
        + _cause('<b>✂ Soru Kırp</b> düğmesine basıp sorunun etrafına dikdörtgen çizdin',
                 'Bölge yüksek çözünürlükte kesilir; açılan pencerede kurs, konu, zorluk, '
                 'A–E şıkları ve doğru şık sorulur (∑ canlı LaTeX önizlemesiyle)',
                 'Kaynak PDF ve sayfa numarası otomatik kaydedilir — sınavda "bu soru '
                 'nereden geldi?" sorusunun cevabı hep elinde olur'))

    ai = _h2("5", "🤖 Yapay Zekâ Öğretmen", "ai") + (
        _lead('Yapay zekâ <b>senin bilgisayarında</b> çalışır. Program dosyaları yerelde '
              'okur ve modele yalnızca <b>seçtiğin metni/bağlamı</b> gönderir.')
        + _h3("LM Studio Kurulumu", "ai-kurulum")
        + _tablo(["Adım", "Ne yapılır"], [
            ["1", '<a href="https://lmstudio.ai">lmstudio.ai</a>\'dan LM Studio kur'],
            ["2", "Bir model indir (öneri: <code>qwen2.5-math-7b-instruct</code>)"],
            ["3", "LM Studio içinde <b>Server</b>\'ı başlat → <code>http://127.0.0.1:1234</code>"],
            ["4", "Önerilen ayarlar: Context 4096 · Keep Model in Memory: On · Flash Attention: On"],
            ["5", "Programda <b>Ayarlar</b> → model profillerini gir ya da "
                  "<b>Auto Detect Loaded Models</b>\'a bas"],
        ])
        + _h3("Model Profilleri", "ai-profil")
        + _cause('Ayarlar\'da her iş için ayrı model belirledin',
                 'Program isteği konuya göre yönlendirir: matematik → math modeli, '
                 'kimya → kimya modeli, görsel → vision modeli',
                 'Her işte o iş için güçlü modeli kullanırsın; 8 GB kartta bile doğru '
                 'model seçimiyle iyi sonuç alırsın')
        + _h3("🟢 AI Durum Göstergesi", "ai-durum")
        + _tablo(["Gösterge", "Anlamı", "Ne yapmalı"], [
            ["<b>🟢 AI hazır · model-adı</b>", "Sunucu açık, model yüklü — gösterilen "
             "model isteklerinde <i>gerçekten kullanılacak</i> olandır", "Bir şey yapma"],
            ["<b>🟡 AI sunucu açık, model yüklü değil</b>", "LM Studio çalışıyor ama model "
             "yüklenmemiş", "LM Studio'da bir model yükle"],
            ["<b>🔴 AI kapalı</b>", "Sunucuya ulaşılamıyor", "LM Studio'yu aç — ya da hiç "
             "açma, offline özellikler çalışmaya devam eder"],
        ])
        + _note('Göstergeye <b>tıklarsan</b> API Test penceresi açılır: bağlantı raporu, '
                'yüklü model listesi ve prompt şablonu denemesi.')
        + _h3("🖼 Görsel Soru Çözücü", "ai-gorsel")
        + _cause('Soru fotoğrafını/ekran görüntüsünü ekledin',
                 'Program önce OCR ile metni çıkarmayı dener; olmazsa görseli doğrudan '
                 'vision modeline gönderir, sonra çıkan soruyu matematik modeline verir',
                 'Elle yazmadan, fotoğraftan soru çözdürürsün'))

    terminal = _h2("6", "🖥 AI Terminali", "terminal") + (
        _lead('<b>Ayarlar → Ayar → 🖥 AI Terminali.</b> Kod ve işlerini yapay zekâya '
              'yazdırdığın pencere: sympy ile çözüm, matplotlib grafiği, küçük yardımcı '
              'skriptler.')
        + _h3("İki Sağlayıcı: Yerel · NVIDIA", "terminal-saglayici")
        + _tablo(["Sağlayıcı", "Maliyet", "Gizlilik", "Ne zaman"], [
            ["<b>Yerel (LM Studio)</b>", "Ücretsiz", "Veri bilgisayardan <b>çıkmaz</b>",
             "Varsayılan tercih; kişisel/özel her şey"],
            ["<b>NVIDIA NIM</b>", "Ücretsiz deneme uçları",
             "İstek ve yanıtlar <b>NVIDIA tarafından loglanır</b>",
             "Yerel model zorlanınca; hassas veri gönderme"],
        ])
        + _note('NVIDIA tarafında seçili üç model: <code>z-ai/glm-5.2</code> (hızlı ve '
                'isabetli — varsayılan), <code>llama-3.3-nemotron-super-49b</code> '
                '(matematik + araç çağrısı), <code>openai/gpt-oss-120b</code> (akıl '
                'yürütme; kuyruğa göre 1–2 dk sürebilir). Anahtar <b>Windows Credential '
                'Manager</b>\'da tutulur, diske düz metin yazılmaz; 🔑 düğmesiyle '
                'değiştirilir ve arayüzde hep maskeli görünür.')
        + _h3("▶ Kod Çalıştırma & Onay Kapısı", "terminal-kod")
        + _cause('Yapay zekâdan kod istedin', 'Yanıt bir <code>```python</code> bloğu içerir',
                 'Kodun tamamını görürsün — kutu içinde, kopyalanabilir')
        + _cause('<b>▶ Python bloğunu çalıştır</b>\'a bastın',
                 '<b>Ayrı bir onay penceresi</b> açılır ve kodun tamamını gösterir',
                 'Ne çalışacağını <i>çalışmadan önce</i> okursun')
        + _cause('<b>✔ Onayla ve çalıştır</b> dedin',
                 'Kod yalıtılmış bir alt süreçte (<code>python -I</code>), ayrı bir '
                 'çalışma klasöründe, 180 saniye zaman aşımıyla koşar; çıktı terminale düşer',
                 'Program dosyalarını etkilemeden deneme yaparsın')
        + _warn('<b>Üretilen kod asla otomatik çalışmaz.</b> Onay kapısı bilinçli bir '
                'tasarım kararıdır — yapay zekânın ürettiği hiçbir şey senin görüp '
                'onaylaman olmadan bilgisayarında çalışmaz.')
        + _h3("📜 Çalışma Tutanağı (kalıcı kayıt)", "terminal-tutanak")
        + _lead('Terminal penceresini kapatınca konuşma silinirdi; artık <b>tamamlanan '
                'her iş kalıcı olarak kaydediliyor.</b>')
        + _cause('Bir iş tamamlandı (yanıt geldi)',
                 'Soru, yanıt, sağlayıcı, model, süre ve durum '
                 '<code>%APPDATA%\\MathCourseAI\\terminal_tutanak.jsonl</code> dosyasına '
                 'yazılır; o işte <b>▶ ile kod çalıştırdıysan</b> kod ve çıktısı da '
                 '<i>aynı kayda</i> eklenir',
                 '"Geçen hafta şu grafiği çizdiren kodu yazdırmıştım" artık bulunabilir')
        + _cause('<b>📜 Tutanak</b> düğmesine bastın',
                 'Geçmiş işler tarih sırasıyla listelenir; arama kutusu soru, yanıt, model '
                 've kod metninde arar; seçili işin tamamı alt bölmede görünür',
                 'Eski bir çözümü aramak için sohbeti baştan kurmana gerek kalmaz')
        + _cause('<b>💾 Seçili işi metne aktar</b> ya da <b>📋 Panoya kopyala</b>',
                 'İş, başlıklı düz metin olarak dosyaya yazılır / panoya kopyalanır',
                 'Bir çözümü ödeve, nota ya da arkadaşına taşırsın')
        + _tablo(["", "📒 Token Defteri", "📜 Çalışma Tutanağı"], [
            ["<b>Ne saklar</b>", "Yalnız sayaçlar (model, token, saniye)",
             "<b>İsteğin ve yanıtın tam metni</b> + çalıştırılan kod ve çıktısı"],
            ["<b>Ne için</b>", "Farkındalık: hangi model yavaş, hangi iş token yiyor",
             "Hafıza: ne yaptırdın, ne üretildi, ne çalıştı"],
            ["<b>Nerede</b>", "<code>token_usage_v22.jsonl</code>",
             "<code>terminal_tutanak.jsonl</code>"],
        ])
        + _note('<b>Saklama:</b> tutanak en fazla 2000 iş tutar; sınır aşılınca en eski '
                'kayıtlar düşer. Yanıt metni <b>kırpılmaz</b>. Kayıt silme/düzenleme '
                'bilerek yoktur — tutanağın değeri yazılanın orada durmasından gelir.')
        + _warn('<b>Gizlilik:</b> tutanak istek metnini saklar (token defterinin aksine). '
                'Dosya yalnızca senin bilgisayarında durur, ama <b>%APPDATA% yedeğine '
                'dâhildir</b> — yedeği paylaşırken bunu hesaba kat.'))

    takip = _h2("7", "🎓 Öğrenci Takip", "takip") + (
        _lead('Programın öğrenme döngüsünü kapatan bölüm — 6 alt sekme.')
        + _h3("📅 Bugün Panosu", "takip-bugun")
        + _cause('Öğrenci Takip sekmesini açtın (ya da açılışta Bugün panosunu seçtin)',
                 'Dört kart görürsün: <b>Tekrar vakti</b> gelen sorular, <b>Yanlışlar</b>, '
                 '<b>Denenmemişler</b>, <b>Doğruluk</b>; altında zayıf konular ve kurs '
                 'ilerleme çubukları',
                 '"Bugün ne çalışayım?" sorusu 10 saniyede cevaplanır')
        + _cause('Karttaki <b>Tekrar Sınavı / Yanlış Drill / Yeni Soru Sınavı</b>\'na bastın',
                 'O havuzdan sınav anında başlar', 'Karar verme yükü olmadan çalışmaya başlarsın')
        + _h3("📌 Bu Hafta — kişisel öneriler", "takip-hafta")
        + _lead('Panonun ortasındaki turuncu kart, biriken çalışma verinden <b>en fazla '
                'üç öneri</b> çıkarır ve her birinin yanına tek tık bir eylem koyar.')
        + _tablo(["Öneri ne zaman çıkar", "Gerekçe böyle görünür", "Tek tık eylem"], [
            ["Bir konunun doğruluğu <b>%60'ın altında</b> ve <b>en az 5 puanlanmış "
             "denemen</b> var", "<i>Türev — Calculus 1 · son 12 denemede %41.7 doğruluk</i>",
             "→ Bu konudan 10 soruluk sınav"],
            ["Bir kursa <b>7+ gündür</b> hiç soru çözmemişsin",
             "<i>21 gündür hiç soru çözmedin (son: 2026-07-25)</i>", "→ Kursa devam et"],
            ["Tekrar kuyruğunda <b>tek güne 12+ soru</b> yığılmış",
             "<i>17 soru bugün tekrar vaktine geliyor</i>", "→ 10 soruluk tekrar sınavı"],
        ])
        + _note('<b>Gerekçe her zaman görünür:</b> "şunu çalış" demek yetmez, <i>neden</i> '
                'dediğini de görürsün — sayı ortada olunca öneriye güvenip güvenmeyeceğine '
                'sen karar verirsin.')
        + _warn('<b>Bu kart yapay zekâ kullanmaz.</b> Kurallar veriyi doğrudan okur; '
                'böylece pano anında açılır ve LM Studio kapalıyken de çalışır. '
                'Yeterli veri yoksa kart <b>tahmin üretmez</b>, "öneri için henüz yeterli '
                'veri yok" der. Zayıflık yoksa da bunu söyler — sessiz kalmaz.')
        + _h3("🔁 Aralıklı Tekrar (Leitner)", "takip-srs")
        + _tablo(["Durum", "Bir sonraki tekrar"], [
            ["Yanlış bildin", "<b>Hemen</b> (bugünkü listeye düşer)"],
            ["1. kez doğru", "1 gün sonra"], ["2. kez üst üste doğru", "3 gün sonra"],
            ["3. kez", "7 gün"], ["4. kez", "14 gün"], ["5. kez", "30 gün"],
            ["6. kez ve sonrası", "60 gün"],
        ])
        + _note('Bu takvim her sorunun <b>deneme geçmişinden</b> hesaplanır; ayrı bir '
                'şema ya da elle ayar gerekmez.')
        + _h3("📥 Soru Bankası", "takip-banka")
        + _cause('Soru ekledin (elle, ✂ kırparak, toplu metinle ya da CSV ile)',
                 'Soru kurs/konu/zorluk/etiket bilgisiyle veritabanına girer',
                 'Sorular tek yerde toplanır, filtrelenebilir hâle gelir')
        + _cause('Filtreleri kullandın (kurs · konu · zorluk · <b>durum</b> · <b>paket</b> · arama)',
                 'Liste anında daralır; her satırda durum rengi görünür',
                 '"Sadece Calculus\'ta yanlış yaptıklarım" gibi bir küme kurup üstünde çalışırsın')
        + _tablo(["Durum", "Anlamı"], [
            ["✔ <b>Çözdüm</b>", "Doğru bildin — SRS takvimi ilerler"],
            ["✘ <b>Yanlış</b>", "Yanlış bildin — hemen tekrara düşer"],
            ["🔁 <b>Tekrar</b>", "Emin değilsin, tekrar görmek istiyorsun"],
            ["○ <b>Çözülmedi</b>", "Henüz denenmedi"],
        ])
        + _h3("📝 Sınav & ⏱ Süreli Mod", "takip-sinav")
        + _cause('Havuz seçip (<b>Hepsi / Çözülmedi / Yanlış / Tekrar / Tekrar Vakti</b>) '
                 'sınavı başlattın',
                 'Sorular tek tek gelir; şıklı sorularda A–E tıklanabilir ve otomatik '
                 'puanlanır, açık uçlularda cevabı görüp kendin işaretlersin',
                 'Hem hızlı test hem gerçek sınav provası yaparsın')
        + _cause('<b>⏱ Süre (dk)</b> kutusuna 0\'dan büyük bir sayı yazdın',
                 'Üstte geri sayım işler (son 60 saniye kırmızı); süre bitince sınav '
                 '<b>otomatik kapanır</b> ve özet "süre doldu" der',
                 'Gerçek sınav baskısını provasını yaparsın; 0 bırakırsan süresiz çalışırsın')
        + _note('<b>Neden bazı soruları kendim işaretliyorum?</b> Matematikte cevabın '
                'eşdeğer biçimleri çoktur. Program sympy ile <code>0.5 = 1/2</code>, '
                '<code>x = 2 = 2</code>, <code>2x+2x = 4x</code> eşdeğerliklerini anlar ve '
                'EŞLEŞTİ / EŞDEĞER / FARKLI önerisi gösterir — ama <b>son kararı sen '
                'verirsin</b>. Şıklı sorularda karar programındır, elle işaretleme yoktur.')
        + _note('Her sorunun altında <b>✏️ Karalama Alanı</b> vardır (fare ya da kalemli '
                'tablet); soru değişince temizlenir. Kırpılmış soru görselleri doğrudan '
                'sınavda gösterilir.')
        + _h3("📊 İstatistik", "takip-istatistik")
        + _cause('İstatistik sekmesini açtın',
                 'Genel doğruluk, konu bazlı ustalık tablosu, <b>zayıf konular</b> '
                 '(kırmızı barlar) ve sınav puanı trendi',
                 'Nerede zayıf olduğunu tahmin etmez, ölçersin')
        + _cause('<b>Sınavlar</b> tablosunda bir satıra çift tıkladın',
                 'O sınavın <b>soru dökümü</b> açılır: her soruda ne yazdığın, doğru cevap, '
                 'doğru/yanlış/atlandı ve <b>o soruda ne kadar kaldığın</b>',
                 'Puanın neden o çıktığını soru soru görürsün — hangi soru zamanını yedi')
        + _note('Tabloda ayrıca sınavın <b>süreli olup olmadığı</b> yazar. Bu bilgi '
                'V48\'de kaydedilmeye başlandı; daha eski sınavlarda <b>"?"</b> görürsün — '
                'program bilmediği şeyi tahmin etmez.')
        + _h3("📄 Haftalık Özet raporu", "takip-rapor")
        + _cause('İstatistik sekmesindeki <b>📄 Haftalık Özet</b> düğmesine bastın',
                 'Tarayıcında tek sayfalık bir rapor açılır: son 7 günün çalışma günleri, '
                 'çözülen soru sayısı, doğruluğun <b>geçen haftaya göre değişimi</b>, '
                 'haftanın zayıf konuları ve bitirilen sınavlar',
                 'Haftalık gidişatını tek bakışta görür, istersen yazdırıp veli/eğitmenine '
                 'verirsin')
        + _note('Rapor kılavuzun şablonunu kullanır: üstteki şeritten <b>renkli ya da gri '
                'yazdırılır</b>, "PDF olarak kaydet" ile A4 PDF olur. İnternet gerekmez, '
                'veriler yalnızca senin bilgisayarındaki kayıtlardan üretilir.')
        + _warn('<b>Veri yoksa bölüm boş grafik çizmez</b>, "bu hafta veri yok" der. '
                'Bir konuda 3\'ten az deneme varsa o konu haftalık yoruma girmez — '
                'iki denemeden hafta çıkarımı yapılmaz.'))

    paket = _h2("8", "📦 Soru Paketleri", "paket") + (
        _h3("Yerleşik Üreteçler (sınırsız)", "paket-yerlesik")
        + _cause('Soru Paketleri sekmesinden bir üreteç seçip <b>İçe Aktar</b> dedin',
                 'Program o konudan istediğin sayıda soru <i>ve kesin cevabını</i> üretir '
                 've bankana ekler',
                 'Soru kaynağı derdin biter: sınırsız, telifsiz, TR/EN')
        + _tablo(["Paket", "İçerik"], [
            ["<code>prealgebra_core</code>", "Dört işlem, kesirler, yüzde, oran"],
            ["<code>algebra_core</code>", "Denklem, 2. derece, sistem, üslü ifadeler"],
            ["<code>geometry_core</code>", "Alan/çevre, Pisagor, çember"],
            ["<code>linear_algebra_core</code>", "Determinant, matris, nokta çarpım"],
            ["<code>calculus_intro</code>", "Eğim, türev"],
        ])
        + _h3("📤 Paket Dışa Aktarma — arkadaşınla paylaş", "paket-disa")
        + _cause('Soru Bankası\'nda filtreni kurup <b>📤 Paketi Dışa Aktar</b>\'a bastın',
                 'Paket adı, kurs, dil, lisans, atıf ve kaynak URL sorulur; filtreye uyan '
                 'sorular (şıklarıyla birlikte) tek bir JSON dosyasına yazılır',
                 'Hazırladığın soruları arkadaşına verirsin')
        + _cause('Arkadaşın dosyayı kendi <code>question_packs\\</code> klasörüne koydu',
                 'Soru Paketleri sekmesinde paket görünür ve tek tıkla içe aktarılır',
                 'Ortak çalışma grubu kurarsınız; kimse aynı soruyu iki kez yazmaz')
        + _tablo(["Biçim", "Ne taşır", "Ne zaman seç"], [
            ["<b>.mcpack</b> (ZIP)", "<code>paket.json</code> + <code>images/</code> — "
             "✂ ile kırptığın <b>görselli sorular da taşınır</b>",
             "Varsayılan; görselli soruların varsa mutlaka bunu seç"],
            ["<b>.json</b> (düz)", "Yalnız metin; görselli sorular atlanır ve kaç tanesinin "
             "atlandığı sana söylenir", "Karşı taraf eski bir sürüm kullanıyorsa"],
        ])
        + _note('<b>Alıcı tarafta ne oluyor?</b> <code>.mcpack</code> içe aktarılırken '
                'görseller <code>%APPDATA%\\MathCourseAI\\data\\question_images</code> '
                'klasörüne açılır ve soruya bağlanır — sınavda soru, <b>görseliyle '
                'birlikte</b> karşına gelir. Aynı adlı bir dosya varsa üzerine yazılmaz, '
                'ad numaralanır.')
        + _warn('Paketten gelen görsel yolları <b>doğrulanır</b>: yalnızca '
                '<code>images/</code> altındaki düz dosya adları kabul edilir. '
                '<code>../</code> içeren ya da mutlak yol veren bir paket, dosya sisteminde '
                'başka bir yere yazamaz.')
        + _h3("Lisans Kuralı", "paket-lisans")
        + _warn('<b>Telifli soru bankaları programa gömülmez.</b> MEB/EBA/ÖSYM arşivleri ve '
                'ticari yayınevi soruları teliflidir, dahil edilmemiştir. Harici paketlerde '
                'lisans + atıf her soruyla birlikte veritabanında saklanır; lisans '
                'belirtilmemişse paket <b>UNKNOWN</b> işaretlenir ve içe aktarmadan önce '
                'uyarı çıkar.'))

    lab = _h2("9", "🧪 Lab'lar", "lab") + (
        _lead('Beş bilim laboratuvarı tek <b>🧪 Lab\'lar</b> sekmesinde iç sekmeler '
              'hâlinde durur. Hepsinin ortak fikri aynı: <b>konuyu matematiğe çevirmek</b>.')
        + _tablo(["Lab", "Ne yapar"], [
            ["<b>Veri Lab</b>", "Görsel/metin/ses/video verisini matematiksel nesneye "
             "çevirir: vektör, matris, tensör, frekans, embedding"],
            ["<b>Fizik Lab</b>", "Hareket, Newton, atış, harmonik, dalga, elektrik alan"],
            ["<b>Kimya Lab</b>", "İdeal gaz, hız yasası, pH, bozunma, difüzyon, tampon + "
             "periyodik tablo, mol hesabı, stokiyometri"],
            ["<b>DNA Lab</b>", "DNA ↔ matematik: string/vektör/k-mer/bilgi, kodon tablosu, "
             "dijital veri → DNA"],
            ["<b>Kuantum</b>", "Qubit, kapılar, ölçüm, dolaşıklık (Bell), QFT, Grover — "
             "vektör/matris diliyle"],
        ])
        + _note('Laboratuvar panelleri <b>ilk kez sekmeye tıkladığında</b> kurulur; '
                'hiç açmazsan hiç yüklenmezler.'))

    gorsel = _h2("10", "📐 Görsel Matematik Laboratuvarı", "gorsel") + (
        _cause('Görsel Mat sekmesine bir ifade/konu girdin',
               'sympy ile <b>adım adım çözüm</b> + matplotlib grafiği üretilir',
               'Cevabı değil, yolu görürsün')
        + _tablo(["Kaynak", "İçerik"], [
            ["<b>50 gömülü simülasyon</b>", "Kurs konularının etkileşimli görselleştirmeleri"],
            ["<b>90 formül kartı</b>", "Formülün ne dediğini gösteren kartlar"],
            ["<b>Ders kartı üretici</b>", "Poster kalitesinde PNG (yazdırılabilir)"],
        ])
        + _note('Bu sekme sympy ve matplotlib yüklediği için <b>ilk açılışında biraz '
                'bekletir</b>; sonraki açılışlar anında olur. Hiç açmazsan program '
                'açılışında bu bedeli hiç ödemezsin.'))

    sozluk = _h2("11", "📖 Dil & Bilim Sözlüğü", "sozluk") + (
        _lead('9 alt sekmeli, SQLite tabanlı sözlük: İngilizce kurs takip ederken '
              'kelime engelini kaldırır.')
        + _tablo(["Özellik", "Ne işine yarar"], [
            ["<b>PDF kelime tarayıcı</b>", "Bir PDF'teki bilinmeyen kelimeleri toplu çıkarır"],
            ["<b>Görsel/OCR çeviri</b>", "Ekran görüntüsündeki metni okur ve çevirir"],
            ["<b>Favoriler & geçmiş</b>", "Tekrar bakacağın kelimeleri biriktirirsin"],
            ["<b>Kelime hakkında AI'ya sor</b>", "Sözcüğün matematikteki özel anlamını "
             "sorarsın (ör. \"degree\", \"root\", \"power\")"],
        ]))

    hesap = _h2("12", "🧮 Hesap Makinesi", "hesap") + (
        _cause('İfadeyi yazıp Enter\'a bastın (<code>sqrt(144)+6*8</code>)',
               'Güvenli değerlendirici sonucu verir ve geçmişe yazar',
               'Ayrı bir hesap makinesi açmazsın')
        + _tablo(["Özellik", "Örnek"], [
            ["Kesir duyarlı", "<code>3/4 + 2/5</code> → tam kesir sonucu"],
            ["RAD / DEG", "<code>sin(30)</code> DEG modunda derece olarak hesaplanır"],
            ["Fonksiyonlar", "<code>sqrt(25)</code>, <code>log10(100)</code>, <code>sin(pi/2)</code>"],
            ["<b>AI sohbet kutusu</b>", "\"200'e %15 KDV ekle\", \"x²−5x+6=0 çöz\", "
             "\"bu sonucu açıkla\""],
        ]))

    tablet = _h2("13", "🖊️ Tablet Çizim Tahtası", "tablet") + (
        _cause('Fare, kalemli ekran ya da çizim tabletiyle çizdin',
               'El yazısı/şekil/grafik çizimin tahtaya işlenir; ızgara ve eksen açılabilir',
               'Kağıt gibi çalışırsın ama çizimin kaydedilebilir')
        + _cause('<b>"Ne çizdim?"</b> ya da <b>AI Açıkla</b> dedin',
                 'Tahta görüntüsü vision modeline gider, ne çizdiğin yorumlanır',
                 'Çözümünü kontrol ettirirsin'))

    ayar = _h2("14", "⚙ Ayarlar", "ayar") + (
        _lead('Üst çubuktaki turuncu <b>Ayarlar</b> düğmesi → <b>Ayar</b> menüsü.')
        + _h3("🌙 Koyu Tema", "ayar-tema")
        + _cause('<b>Ayar → Tema: 🌙 Koyu</b> seçtin',
                 'Tercih kaydedilir ve "yeniden başlatınca uygulanır" notu çıkar; '
                 'programı kapatıp açtığında tüm arayüz koyu gelir',
                 'Gece çalışırken göz yorulmaz')
        + _note('Canlı geçiş bilinçli olarak yoktur: renkler pencere kurulurken okunur, '
                'yeniden başlatmadan doğru uygulanamaz. <b>PDF sayfaları ve LaTeX '
                'önizlemeleri açık kalır</b> — onlar kağıt gibi içerik alanlarıdır.')
        + _h3("Açılış Ekranı", "ayar-acilis")
        + _tablo(["Seçenek", "Ne olur"], [
            ["<b>Son oturum</b> (varsayılan)", "En son hangi sekmedeysen orada açılır; "
             "son PDF sayfası ve zoom da geri gelir"],
            ["<b>Bugün panosu</b>", "Program doğrudan Öğrenci Takip → Bugün ile açılır; "
             "PDF yine arka planda yüklenir"],
        ])
        + _h3("Çalışma Alanları & X Düzeni", "ayar-alan")
        + _cause('Bir sekmeye <b>orta tuşla</b> tıkladın ya da çipteki <b>×</b>\'e bastın',
                 'O çalışma alanı gizlenir; şerit sadeleşir',
                 'Kullanmadığın sekmeler gözünü yormaz')
        + _cause('<b>Çalışma Alanı Yöneticisi</b>\'ni açtın',
                 '13 alanın hepsini tek listeden aç/kapat yaparsın',
                 'Gizlediğin bir alanı geri getirmek tek tıktır')
        + _tablo(["X Düzeni", "Ne yapar"], [
            ["<b>Klasik</b>", "Kaynaklar solda, PDF sağda"],
            ["<b>Ayna</b>", "Kaynaklar sağda"],
            ["<b>Çift Pencere</b>", "İki bağımsız PDF okuyucu ayrı pencerelerde — "
             "ders ile çözümü yan yana açarsın"],
        ])
        + _h3("🌍 Dil: Türkçe / İngilizce", "ayar-dil")
        + _cause('<b>Ayarlar → Dil</b>\'den <b>Türkçe</b> ya da <b>English</b> seçtin',
                 'Tercih kaydedilir; arayüz metinleri, bu kılavuz ve yapay zekâya giden '
                 'sistem yönergesi seçtiğin dile geçer',
                 'İngilizce bir kurs takip ediyorsan program da o dilde konuşur')
        + _tablo(["Nerede", "Durum"], [
            ["Ana pencere, sekmeler, menüler", "✅ İki dilli"],
            ["🎓 Öğrenci Takip (6 alt sekme, 📌 Bu Hafta önerileri, sınav dökümü)",
             "✅ İki dilli — öneri <i>gerekçeleri</i> ve 📄 Haftalık Özet raporu dâhil"],
            ["🖥 AI Terminali + 📜 Çalışma Tutanağı", "✅ İki dilli (AI'ya giden sistem "
             "yönergesi de dile göre değişir — İngilizce seçiliyken AI da İngilizce yanıtlar)"],
            ["📒 Token Defteri, 🧮 Hesap, 🖊️ Tablet Tahtası, 📄 PDF araç çubuğu",
             "✅ İki dilli"],
            ["📐 Görsel Matematik Lab, 📖 Sözlük", "✅ İki dilli (kendi metin sözlükleri var)"],
            ["🧪 Lab'lar (Veri/Fizik/Kimya/DNA/Kuantum)",
             "⚠ Arayüz etiketleri hâlâ Türkçe — sırada"],
            ["ℹ Konu bilgi bankası (667 konu)", "⚠ İçerik Türkçe yazıldı"],
        ])
        + _note('Panellerin çoğu <b>ilk açıldıklarında</b> kurulur (açılışı hızlandıran '
                'tembel yükleme). Bu yüzden dili değiştirip paneli sonra açarsan zaten '
                'yeni dilde gelir; <b>zaten açık</b> paneller için program "yeniden '
                'başlatınca uygulanır" notunu gösterir.')
        + _warn('Yapay zekânın <b>cevap dili</b> modele bağlıdır: program sistem '
                'yönergesini seçtiğin dilde gönderir, ama küçük bir model yine de karışık '
                'dilde cevap verebilir. Bu bir hata değil, model sınırıdır.')
        + _h3("ℹ Hakkında · ⌨ Kısayollar · 💾 Yedek durumu", "ayar-hakkinda")
        + _cause('<b>Ayar → ℹ Hakkında</b> menüsünü açtın',
                 'Sürüm, sürüm tarihi, programın ne yaptığı, <b>klavye kısayolları</b>, '
                 'sürüm geçmişi ve lisans özeti tek pencerede; 📋 ile panoya kopyalanır',
                 '"Hangi sürümü kullanıyorsun?" sorusunun cevabı tek tık uzakta')
        + _tablo(["Kısayol", "Ne yapar"], [
            ["<code>Ctrl+Enter</code>", "AI Terminali: isteği gönder"],
            ["<code>Ctrl+L</code>", "AI Terminali: ekranı ve geçmişi temizle"],
            ["<code>Esc</code>", "AI Terminali: süren isteği durdur"],
            ["<b>Çift tık</b>", "İstatistik → Sınavlar: o sınavın soru dökümü"],
            ["<b>Orta tık</b>", "Sekme şeridi: o çalışma alanını gizle"],
            ["<code>Shift</code>+tekerlek", "Kaynak ağacı: yatay kaydırma"],
        ])
        + _cause('<b>Ayar</b> menüsünü açtın',
                 'Menüde <b>💾 Son yedek: X gün önce</b> yazar; 7 günden eskiyse ⚠ ile '
                 'işaretlenir, tıklayınca yedek klasörü açılır',
                 'Yedeğin çalışıp çalışmadığını görmek için hiçbir yere bakman gerekmez')
        + _warn('Yedek klasörü bulunamazsa program <b>tarih uydurmaz</b>: "Yedek klasörü '
                'bulunamadı" der ve kendi klasörünü nasıl tanımlayacağını söyler '
                '(<code>scripts/local_config.ps1</code>).'))

    token = _h2("15", "📒 Token Kullanım Defteri", "token") + (
        _lead('<b>Ayarlar → Ayar → 📒 Token Defteri.</b> Yapay zekâya giden her isteğin '
              'kaydı. Ne kadar iş yaptığını ve nerede yavaşladığını gösterir.')
        + _cause('Defteri açtın',
                 'Dört özet kart: <b>bugün</b>, <b>son 7 gün</b>, <b>son 30 gün</b>, '
                 '<b>tüm zamanlar</b> (token · istek · süre)',
                 'Çalışma temponu görürsün')
        + _tablo(["Sekme", "Ne gösterir"], [
            ["<b>Modele göre</b>", "Hangi model ne kadar iş yaptı — model karşılaştırması"],
            ["<b>Sağlayıcıya göre</b>", "Yerel mi NVIDIA mı ağır bastı"],
            ["<b>İşe göre</b>", "math / vision / terminal gibi profil dağılımı"],
            ["<b>Güne göre</b>", "Günlük kullanım — hangi gün yoğun çalıştın"],
            ["<b>Kayıtlar</b>", "Son 300 isteğin tek tek dökümü (zaman, model, token, "
             "süre, bitiş nedeni)"],
        ])
        + _cause('<b>📤 CSV dışa aktar</b>\'a bastın',
                 'Tüm defter Excel\'de açılabilecek bir CSV olur',
                 'Kendi analizini yaparsın')
        + _note('<b>Maliyet:</b> Yerel LM Studio kendi bilgisayarında çalışır, NVIDIA NIM '
                'ücretsiz deneme ucudur — <b>ikisi de para harcamaz</b>. Defterin amacı '
                'fatura değil, <b>kullanım farkındalığı</b>: hangi model yavaş, hangi iş '
                'çok token yiyor, istekler yarıda kesiliyor mu.')
        + _warn('Defterde <b>istek metinleri saklanmaz</b> — yalnızca sayaçlar (zaman, '
                'model, token sayısı, süre, bitiş nedeni). Sorduğun sorular deftere yazılmaz.'))

    veri = _h2("16", "💾 Veri, Gizlilik & Yedek", "veri") + (
        _tablo(["Ne", "Nerede"], [
            ["Ayarlar, düzen, oturum", "<code>%APPDATA%\\MathCourseAI\\config_v22.json</code>"],
            ["Kurs ilerlemesi + okuma işaretleri", "<code>course_progress_v22.json</code>"],
            ["<b>Öğrenci takip veritabanı</b>", "<code>data\\student_tracker.sqlite</code>"],
            ["<b>Sözlük veritabanı</b>", "<code>data\\language_dictionary.sqlite</code>"],
            ["Token defteri", "<code>token_usage_v22.jsonl</code>"],
            ["PDF notları / raporlar / çizimler", "<code>annotations</code> · <code>Reports</code> · <code>board_exports</code>"],
        ])
        + _note('Hepsi <b>%APPDATA%\\MathCourseAI</b> altındadır — program klasöründe '
                'değil. Böylece programı yeniden derlesen ya da taşısan da çalışma '
                'geçmişin kaybolmaz.')
        + _cause('Yedek aldın (otomasyon her gün ya da elle tek tık)',
                 'Kaynak kod + git geçmişi + <b>%APPDATA% kişisel verin</b> tek RAR\'a '
                 'yazılır ve Google Drive klasörüne kopyalanır',
                 'Bilgisayar değişse de çalışma geçmişin durur')
        + _warn('<b>Kurs PDF\'leri yedeğe ve GitHub\'a dâhil değildir</b> (üçüncü taraf '
                'telifi + boyut). Onları ayrıca sakla.'))

    sorun = _h2("17", "🔧 Sorun Giderme", "sorun") + _tablo(
        ["Belirti", "Sebep / Çözüm"], [
            ["Ağaç boş, hiç kurs görünmüyor",
             "Kurs klasörü seçilmemiş ya da içinde desteklenen dosya yok → "
             "karşılama kartındaki <b>📁 Kurs klasörünü seç</b>"],
            ["🔴 AI kapalı",
             "LM Studio çalışmıyor → uygulamayı aç ve Server'ı başlat. Yapay zekâ "
             "istemiyorsan yok say, diğer her şey çalışır"],
            ["🟡 sunucu açık, model yok", "LM Studio'da model yüklü değil → bir model yükle"],
            ["AI cevabı yarıda kesiliyor",
             "Model bağlamı dolmuş olabilir → LM Studio'da Context Length 4096'ya çıkar"],
            ["NVIDIA yanıtı çok yavaş",
             "Ücretsiz uçta kuyruk yoğun → <code>glm-5.2</code> genelde en hızlısıdır"],
            ["PDF açılmıyor", "PyMuPDF kurulu değil → <code>pip install PyMuPDF</code>"],
            ["OCR çalışmıyor",
             "Tesseract <b>uygulaması</b> ayrıca kurulmalı (Python paketi tek başına yetmez)"],
            ["Sınavda soru gelmiyor", "Seçtiğin havuz boş → Havuz'u <b>Hepsi</b> yap ya da "
             "önce soru ekle/paket içe aktar"],
            ["Koyu temayı seçtim, değişmedi", "Tema yeniden başlatınca uygulanır → "
             "programı kapatıp aç"],
        ])

    uyari = _h2("!", "⚠ Önemli Notlar", "uyari") + (
        _warn('<b>Kurs materyalleri üçüncü taraf telifidir.</b> Program <code>Resources\\</code> '
              'altındaki dosyaları yalnızca <b>yerelde okur</b>, dağıtmaz. Kendi lisanslı '
              'kopyanı kullan.')
        + _warn('<b>Yapay zekâ hata yapar.</b> Ürettiği çözümü ve kodu kontrol et; '
                'terminalin onay kapısı tam da bunun içindir.')
        + _note('<b>Program kodu MIT lisanslıdır.</b> Yerleşik soru üreteçleri bu programın '
                'orijinal içeriğidir. Bağımlılıklar (sympy, matplotlib, NumPy, Pillow, '
                'PyMuPDF, Tesseract) kendi lisanslarına tabidir.'))

    return ('<div class="wrap">' + toc + '<main class="content">'
            + genel + yeni + ilk10 + kaynak + pdf + ai + terminal + takip + paket
            + lab + gorsel + sozluk + hesap + tablet + ayar + token + veri + sorun + uyari
            + '<div class="foot"><span class="dot"></span>'
              '<span>Math Course AI — yerel, offline, çift dilli matematik öğrenme platformu.</span>'
              '<span class="r">Bu kılavuz programla birlikte güncellenir.</span></div>'
            + '</main></div>')


# ══════════════════════════════════════════════════════════════════════════
# İNGİLİZCE İÇERİK — aynı çapa kimlikleri, daha derli toplu anlatım
# ══════════════════════════════════════════════════════════════════════════

def _body_en():
    L = "en"
    toc = _toc([
        ("genel", "Overview", False),
        ("yeni", "🎉 What's New", False),
        ("ilk10", "🚀 First 10 Minutes", False),
        ("kaynak", "📚 Course Resources", False),
        ("kaynak-agac", "Tree: Lessons & Question Banks", True),
        ("kaynak-tik", "☐ Done ticks & progress", True),
        ("kaynak-info", "ℹ Topic info (no AI, instant)", True),
        ("pdf", "📄 PDF Reader & Notes", False),
        ("pdf-gezinme", "Zoom, pages, Fit Width", True),
        ("pdf-not", "Pen · Highlight · Text · Eraser", True),
        ("pdf-kirp", "✂ Clip Question → question bank", True),
        ("ai", "🤖 AI Tutor", False),
        ("ai-kurulum", "Setting up LM Studio", True),
        ("ai-profil", "Model profiles", True),
        ("ai-durum", "🟢 AI status indicator", True),
        ("ai-gorsel", "🖼 Image question solver", True),
        ("terminal", "🖥 AI Terminal", False),
        ("terminal-saglayici", "Two providers: Local · NVIDIA", True),
        ("terminal-kod", "▶ Running code & the approval gate", True),
        ("terminal-tutanak", "📜 Work Record (persistent)", True),
        ("takip", "🎓 Student Tracker", False),
        ("takip-bugun", "📅 Today dashboard", True),
        ("takip-hafta", "📌 This Week — personal suggestions", True),
        ("takip-srs", "🔁 Spaced repetition (Leitner)", True),
        ("takip-banka", "📥 Question bank", True),
        ("takip-sinav", "📝 Exams & ⏱ timed mode", True),
        ("takip-istatistik", "📊 Statistics & exam breakdown", True),
        ("takip-rapor", "📄 Weekly Summary report", True),
        ("paket", "📦 Question Packs", False),
        ("paket-yerlesik", "Built-in generators (unlimited)", True),
        ("paket-disa", "📤 Exporting a pack (sharing)", True),
        ("paket-lisans", "The licence rule", True),
        ("lab", "🧪 Labs", False),
        ("gorsel", "📐 Visual Math Lab", False),
        ("sozluk", "📖 Language & Science Dictionary", False),
        ("hesap", "🧮 Calculator", False),
        ("tablet", "🖊️ Tablet Drawing Board", False),
        ("ayar", "⚙ Settings", False),
        ("ayar-tema", "🌙 Dark theme", True),
        ("ayar-acilis", "Startup screen", True),
        ("ayar-alan", "Workspaces & X Layout", True),
        ("ayar-dil", "🌍 Language: Turkish / English", True),
        ("token", "📒 Token Usage Ledger", False),
        ("veri", "💾 Data, privacy & backup", False),
        ("sorun", "🔧 Troubleshooting", False),
        ("uyari", "⚠ Important notes", False),
    ], baslik="Contents")

    genel = _h2("1", "Overview", "genel") + (
        _lead('<b>Math Course AI</b> puts everything you need while following an online '
              'maths course into one window: read PDFs and annotate them, clip questions '
              'into your own bank, study with spaced repetition, sit exams, and ask a '
              'local AI when you get stuck.')
        + '<div class="legend">'
          '<b style="color:var(--blue)">Why</b> = what you do · '
          '<b style="color:var(--green)">Result</b> = what happens on screen · '
          '<b style="color:var(--amber)">Benefit</b> = why it helps.</div>'
        + _tablo(["The problem", "How the program solves it"], [
            ["<b>Scattered studying</b> — the PDF is in one place, notes in another, "
             "questions in a notebook",
             "All of it in one window and one database; where you left off is remembered"],
            ["<b>I don't know what to study</b>",
             "The 📅 Today dashboard shows what is due for review, what you got wrong and "
             "what you have never tried; one click starts an exam on it"],
            ["<b>Forgetting</b>", "Spaced repetition (Leitner): what you answer correctly "
             "comes back after 1 → 3 → 7 → 14 → 30 → 60 days; what you get wrong comes "
             "back immediately"],
            ["<b>Nobody to ask when I'm stuck</b>",
             "A local AI tutor through LM Studio - the default path needs no "
             "connection and keeps your data on this machine"],
            ["<b>I can't find practice questions</b>", "Built-in generators produce "
             "unlimited, licence-free, bilingual questions; and you can clip questions "
             "straight out of a PDF with ✂"],
        ])
        + _note('<b>Identity:</b> the program runs <b>fully locally</b>. The AI talks to '
                'LM Studio on your own machine; your PDFs, notes and study history never '
                'leave the computer. The only exception is the <b>AI Terminal</b>, where '
                '<i>you</i> may pick the NVIDIA provider — that request goes to NVIDIA and '
                'is logged there, and the window says so plainly.'))

    yeni = _h2("★", "🎉 What's New", "yeni") + (
        _lead('The most recent additions — details in the matching sections:')
        + _tablo(["Feature", "What it gives you"], [
            ["<b>🖥 AI Terminal</b>", "Have code and tasks written by local LM Studio or "
             "NVIDIA's free endpoints. Generated code <b>never runs without an approval "
             'dialog</b>. Details: <a href="#terminal">🖥 AI Terminal</a>'],
            ["<b>📜 Terminal work record</b>", "Every terminal job is now permanent: "
             "question, answer, executed code and output go into a searchable record. "
             'Details: <a href="#terminal-tutanak">📜 Work Record</a>'],
            ["<b>🌍 Real bilingualism</b>", "Student Tracker, AI Terminal, token ledger, "
             "calculator, drawing board and the PDF toolbar now speak English too — "
             'including suggestion reasons and the weekly report. '
             '<a href="#ayar-dil">Details</a>'],
            ["<b>📦 Packs with images</b>", "Questions you clipped with ✂ now travel to a "
             'friend inside a <code>.mcpack</code>. <a href="#paket-disa">Details</a>'],
            ["<b>📄 Weekly Summary report</b>", "A printable one-page week report, plus a "
             'question-by-question breakdown of every past exam. '
             '<a href="#takip-rapor">Details</a>'],
            ["<b>📌 This Week suggestions</b>", "The Today dashboard now answers \"what "
             "should I study?\" with three reasoned suggestions — rule-based, no AI call. "
             '<a href="#takip-hafta">Details</a>'],
            ["<b>📒 Token Usage Ledger</b>", "A record of every AI request: which model, "
             'how many tokens, how many seconds. <a href="#token">Details</a>'],
            ["<b>🌙 Dark theme</b>", "A warm dark palette for night study; picked in "
             'Settings, applied on restart. <a href="#ayar-tema">Details</a>'],
            ["<b>🧪 Labs in one tab</b>", "Five science labs moved into inner tabs — the "
             'main strip went from 12 tabs to 8. <a href="#lab">Details</a>'],
            ["<b>⏱ Timed exams</b>", "Put a clock on an exam, watch the countdown, let it "
             'close itself when time is up. <a href="#takip-sinav">Details</a>'],
            ["<b>📤 Pack export</b>", "Write your questions to a JSON pack with licence and "
             'attribution and hand it to a friend. <a href="#paket-disa">Details</a>'],
            ["<b>🎓 Welcome card</b>", "With an empty course folder the program now tells "
             'you what to do in three steps. <a href="#ilk10">Details</a>'],
            ["<b>🟢 AI status indicator</b>", "The top bar always shows whether the AI is "
             'ready. <a href="#ai-durum">Details</a>'],
            ["<b>🚀 Startup screen choice</b>", "Open on your last session or on the Today "
             'dashboard — your call. <a href="#ayar-acilis">Details</a>'],
            ["<b>⚡ 45% faster startup</b>", "Heavy modules load on first use: 3.5 s → 1.9 s."],
        ]))

    ilk10 = _h2("2", "🚀 First 10 Minutes", "ilk10") + (
        _lead('If this is your first time, do these in order:')
        + _cause('Put your course PDFs in <code>Resources\\</code>, or pick your own folder '
                 'with <b>Browse</b> at the top left',
                 'The tree in the left panel lists your courses under 📘 Lessons and '
                 '📝 Question Banks',
                 'All your course material becomes reachable from one place', L)
        + _cause('Double-click a PDF in the tree',
                 'The PDF Reader tab opens and the file is marked "📖 Reading"',
                 'The program remembers where you stopped; "▶ Resume" brings you back', L)
        + _cause('Use <b>✂ Clip Question</b> to drag a rectangle around a question',
                 'The crop is added to your question bank (it asks for course, topic, '
                 'difficulty and the A–E choices)',
                 'A question from the book becomes yours — it will come up in exams', L)
        + _cause('Start an exam from Student Tracker → <b>Exam</b>',
                 'Questions come one at a time; you see the stored answer and mark yourself '
                 'right or wrong',
                 'Wrong answers become "Wrong" automatically, so your revision list builds '
                 'itself', L)
        + _note('<b>No PDFs at all?</b> That is fine — open Student Tracker → <b>Question '
                'Packs</b> and import one of the built-in generators (Pre-Algebra, Algebra, '
                'Geometry, Linear Algebra, Calculus). Unlimited, licence-free, bilingual. '
                'On an empty first start these three steps also appear on the '
                '<b>welcome card</b>.')
        + _warn('<b>The AI is optional.</b> Everything works without installing LM Studio: '
                'PDFs, notes, the question bank, exams, the labs, the dictionary and the '
                'calculator. The AI only steps in when you ask it to explain something.'))

    kaynak = _h2("3", "📚 Course Resources", "kaynak") + (
        _lead('The left panel: a course/section tree of your own course folder, a search box and '
              'reading progress.')
        + _h3("Tree: Lessons & Question Banks", "kaynak-agac")
        + _cause('You picked your folder',
                 'The tree groups everything under two roots: <b>📘 Lessons</b> and '
                 '<b>📝 Question Banks</b> (folders whose name contains "soru bank" fall '
                 'into the second group)',
                 'Reading a lesson and drilling questions never get mixed up', L)
        + _cause('You typed in the search box', 'The tree filters as you type',
                 'In a 300-file course you find the topic you want in a second', L)
        + _h3("☐ Done ticks & progress", "kaynak-tik")
        + _cause('You clicked the <b>☐ box</b> next to a file',
                 'The file becomes ✅ Done (it does <i>not</i> open) and the counter in the '
                 'course header updates to <code>3/12 ✅</code>',
                 'You see where you are in the course at a glance', L)
        + _cause('You opened a PDF', 'The file is automatically marked "📖 Reading"',
                 'Even if you forget to tick anything, the progress record stays honest', L)
        + _h3("ℹ Topic info — no AI, instant", "kaynak-info")
        + _cause('You clicked the <b>ℹ</b> icon next to a file or topic folder',
                 'A separate window opens: an everyday analogy → <i>What is it?</i> → '
                 '<i>What is it used for?</i> → 📜 history and biography where there is any',
                 'You learn why a topic matters before you start it', L)
        + _note('These explanations come from a <b>hand-written embedded bank</b>: 667 of '
                '668 topics are ready, with <b>no AI call at all</b> — offline and instant. '
                'For purely procedural topics (rounding, PEMDAS and the like) <b>no history '
                'is invented</b>; that section is simply left out. For a rare undocumented '
                'topic an optional "🤖 Ask the local AI" button appears.'))

    pdf = _h2("4", "📄 PDF Reader & Notes", "pdf") + (
        _h3("Zoom, pages, Fit Width", "pdf-gezinme")
        + _tablo(["Button", "What it does", "Why it helps"], [
            ["<b>+ / −</b>", "Zooms in and out (0.35× – 5×)",
             "You can read formulas set in small type"],
            ["<b>Fit Width</b>", "Fits the page to the window width",
             "You stop fiddling with zoom on every page"],
            ["<b>◀ ▶ / page no</b>", "Page navigation",
             "You jump straight to a page in a long book"],
        ])
        + _h3("Pen · Highlight · Text · Eraser", "pdf-not")
        + _cause('You picked <b>Pen</b> or <b>Highlight</b> and drew on the PDF',
                 'The drawing is saved with its page number into a separate sidecar file '
                 '(the original PDF is <b>not modified</b>)',
                 'Your book stays clean, and your notes can be backed up and moved', L)
        + _cause('<b>Save Notes</b> / <b>Export Annotated PDF</b>',
                 'Notes are written to disk / a new PDF is produced with your marks baked in',
                 'You can print or share the marked-up version', L)
        + _h3("✂ Clip Question → question bank", "pdf-kirp")
        + _cause('You pressed <b>✂ Clip Question</b> and dragged a rectangle around a question',
                 'The region is cut at high resolution; a dialog asks for course, topic, '
                 'difficulty, the A–E choices and the correct one (with a live ∑ LaTeX preview)',
                 'The source PDF and page number are stored automatically — "where did this '
                 'question come from?" always has an answer', L))

    ai = _h2("5", "🤖 AI Tutor", "ai") + (
        _lead('The AI runs <b>on your own machine</b>. The program reads your files locally '
              'and sends the model only <b>the text or context you selected</b>.')
        + _h3("Setting up LM Studio", "ai-kurulum")
        + _tablo(["Step", "What to do"], [
            ["1", 'Install LM Studio from <a href="https://lmstudio.ai">lmstudio.ai</a>'],
            ["2", "Download a model (a good default: <code>qwen2.5-math-7b-instruct</code>)"],
            ["3", "Start the <b>Server</b> inside LM Studio → <code>http://127.0.0.1:1234</code>"],
            ["4", "Recommended settings: Context 4096 · Keep Model in Memory: On · "
                  "Flash Attention: On"],
            ["5", "In the program open <b>Settings</b> and fill in the model profiles, or "
                  "press <b>Auto Detect Loaded Models</b>"],
        ])
        + _h3("Model profiles", "ai-profil")
        + _cause('You set a separate model per kind of work in Settings',
                 'The program routes each request by subject: maths → the maths model, '
                 'chemistry → the chemistry model, images → the vision model',
                 'Every task gets the model that is good at it — even an 8 GB card gives '
                 'good results with the right choice', L)
        + _note('Profiles resolve against whatever is <b>actually installed</b>: removing or '
                'renaming a model degrades quality instead of breaking the feature. You can '
                'also override them from a <code>model_profiles.json</code> file without '
                'touching any code.')
        + _h3("🟢 AI status indicator", "ai-durum")
        + _tablo(["Indicator", "Meaning", "What to do"], [
            ["<b>🟢 AI ready · model-name</b>", "Server up, model loaded — the name shown is "
             "the model requests will <i>actually</i> use", "Nothing"],
            ["<b>🟡 server up, no model loaded</b>", "LM Studio is running but nothing is "
             "loaded", "Load a model in LM Studio"],
            ["<b>🔴 AI off</b>", "The server cannot be reached", "Start LM Studio — or "
             "ignore it entirely; the offline features keep working"],
        ])
        + _note('<b>Click</b> the indicator to open the API Test window: connection report, '
                'the list of loaded models and a prompt-template test.')
        + _h3("🖼 Image question solver", "ai-gorsel")
        + _cause('You attached a photo or screenshot of a question',
                 'The program first tries to pull the text out with OCR; if that fails it '
                 'sends the image straight to the vision model, then hands the recovered '
                 'question to the maths model',
                 'You get a question solved from a photo without typing it out', L))

    terminal = _h2("6", "🖥 AI Terminal", "terminal") + (
        _lead('<b>Settings → Setting → 🖥 AI Terminal.</b> The window where you have the AI '
              'write code and do jobs: sympy solutions, matplotlib plots, small helper '
              'scripts.')
        + _h3("Two providers: Local · NVIDIA", "terminal-saglayici")
        + _tablo(["Provider", "Cost", "Privacy", "When to use"], [
            ["<b>Local (LM Studio)</b>", "Free", "Nothing <b>leaves</b> the computer",
             "The default choice; anything personal or private"],
            ["<b>NVIDIA NIM</b>", "Free trial endpoints",
             "Requests and answers <b>are logged by NVIDIA</b>",
             "When the local model struggles; send nothing sensitive"],
        ])
        + _note('Three models are wired up on the NVIDIA side: <code>z-ai/glm-5.2</code> '
                '(fast and accurate — the default), '
                '<code>llama-3.3-nemotron-super-49b</code> (maths + tool calling) and '
                '<code>openai/gpt-oss-120b</code> (reasoning; 1–2 minutes depending on the '
                'queue). The key lives in <b>Windows Credential Manager</b> and is never '
                'written to disk in plain text; the 🔑 button changes it and the interface '
                'only ever shows it masked.')
        + _h3("▶ Running code & the approval gate", "terminal-kod")
        + _cause('You asked the AI for code',
                 'The answer contains a <code>```python</code> block',
                 'You see the whole thing — in a box, copyable', L)
        + _cause('You pressed <b>▶ Run the Python block</b>',
                 'A <b>separate approval window</b> opens and shows the complete code',
                 'You read exactly what will run <i>before</i> it runs', L)
        + _cause('You pressed <b>✔ Approve and run</b>',
                 'The code runs in an isolated subprocess (<code>python -I</code>), in a '
                 'separate working folder, with a 180-second timeout; the output lands in '
                 'the terminal',
                 'You can experiment without touching the program\'s own files', L)
        + _warn('<b>Generated code never runs by itself.</b> The approval gate is a '
                'deliberate design decision — nothing the AI writes runs on your computer '
                'without you seeing and approving it.')
        + _h3("📜 Work Record (persistent)", "terminal-tutanak")
        + _lead('Closing the terminal used to delete the conversation; now <b>every '
                'finished job is kept.</b>')
        + _cause('A job finishes (the answer arrives)',
                 'Question, answer, provider, model, duration and status are written to '
                 '<code>%APPDATA%\\MathCourseAI\\terminal_tutanak.jsonl</code>; if you ran '
                 'the code with ▶, the code and its output are added to the <i>same</i> record',
                 '"I had it write that plotting code last week" becomes findable', L)
        + _cause('You pressed <b>📜 Work Record</b>',
                 'Past jobs are listed newest first; the search box matches question, '
                 'answer, model and code text; the selected job is shown in full below',
                 'You never have to rebuild a conversation to find an old solution', L)
        + _cause('You pressed <b>💾 Export selected job</b> or <b>📋 Copy</b>',
                 'The job is written to a plain-text file / copied to the clipboard with '
                 'headings',
                 'You can move a solution into your homework, notes or a message', L)
        + _tablo(["", "📒 Token Ledger", "📜 Work Record"], [
            ["<b>Stores</b>", "Counters only (model, tokens, seconds)",
             "<b>The full text</b> of request and answer + executed code and output"],
            ["<b>Purpose</b>", "Awareness: which model is slow, which task eats tokens",
             "Memory: what you asked for, what was produced, what ran"],
            ["<b>Where</b>", "<code>token_usage_v22.jsonl</code>",
             "<code>terminal_tutanak.jsonl</code>"],
        ])
        + _note('<b>Retention:</b> at most 2000 jobs; the oldest drop once the limit is '
                'passed. Answer text is <b>never truncated</b>. There is deliberately no '
                'delete or edit — the record is worth having because what was written stays '
                'written.')
        + _warn('<b>Privacy:</b> unlike the token ledger, this record keeps your request '
                'text. It stays on your machine, but it <b>is inside the %APPDATA% '
                'backup</b> — keep that in mind before sharing a backup.'))

    takip = _h2("7", "🎓 Student Tracker", "takip") + (
        _lead('The part that closes the learning loop — six sub-tabs.')
        + _h3("📅 Today dashboard", "takip-bugun")
        + _cause('You opened Student Tracker (or chose the Today dashboard as your startup '
                 'screen)',
                 'Four cards: questions <b>due</b> for review, <b>Wrong</b>, <b>Untried</b> '
                 'and <b>Accuracy</b>; below them weak topics and per-course progress bars',
                 'The question "what should I study today?" is answered in ten seconds', L)
        + _cause('You pressed <b>Review Exam / Wrong Drill / New Question Exam</b> on a card',
                 'An exam from that pool starts immediately',
                 'You start studying without spending willpower on deciding what to do', L)
        + _h3("📌 This Week — personal suggestions", "takip-hafta")
        + _lead('The amber card in the middle of the dashboard turns your accumulated study '
                'data into <b>at most three suggestions</b>, each with a one-click action.')
        + _tablo(["When a suggestion appears", "How the reason reads", "One-click action"], [
            ["A topic is <b>below 60% accuracy</b> with <b>at least 5 graded attempts</b>",
             "<i>Derivatives — Calculus 1 · 41.7% over the last 12 attempts</i>",
             "→ 10-question exam on this topic"],
            ["A course has had <b>no questions answered for 7+ days</b>",
             "<i>21 days without a single question (last: 2026-07-25)</i>",
             "→ Continue the course"],
            ["<b>12+ questions</b> fall due for review on the same day",
             "<i>17 questions come up for review today</i>", "→ 10-question review exam"],
        ])
        + _note('<b>The reason is always visible:</b> "study this" is not enough — you also '
                'see <i>why</i>. With the numbers in front of you, you decide whether to '
                'trust the suggestion.')
        + _warn('<b>This card uses no AI.</b> Rules read the data directly, so the dashboard '
                'opens instantly and works with LM Studio switched off. With too little data '
                'it <b>invents nothing</b> and says "not enough data yet". If there is no '
                'weakness to report it says that too — it never just goes quiet.')
        + _h3("🔁 Spaced repetition (Leitner)", "takip-srs")
        + _tablo(["State", "Next review"], [
            ["Answered wrong", "<b>Immediately</b> (it drops into today's list)"],
            ["1st correct", "1 day later"], ["2nd correct in a row", "3 days"],
            ["3rd", "7 days"], ["4th", "14 days"], ["5th", "30 days"], ["6th+", "60 days"],
        ])
        + _note('The schedule is computed from each question\'s attempt history, so there is '
                'no separate scheduler state to go stale. The Today dashboard and the '
                '<b>Due for review</b> exam pool both read this queue.')
        + _h3("📥 Question bank", "takip-banka")
        + _cause('You added a question (by hand, from a bulk <code>question = answer</code> '
                 'paste, from CSV, or with ✂ from a PDF)',
                 'It enters the database with its course, topic, difficulty and tags',
                 'Your questions live in one place and become filterable', L)
        + _cause('You used the filters (course · topic · difficulty · <b>status</b> · '
                 '<b>pack</b> · text search)',
                 'The list narrows instantly and every row is colour-coded by status',
                 'You can build a set like "only the Calculus ones I got wrong" and work '
                 'through it', L)
        + _tablo(["Status", "Meaning"], [
            ["✔ <b>Solved</b>", "You got it right — the SRS schedule advances"],
            ["✘ <b>Wrong</b>", "You got it wrong — it goes back into review immediately"],
            ["🔁 <b>Review</b>", "You are not sure and want to see it again"],
            ["○ <b>Untried</b>", "Never attempted"],
        ])
        + _h3("📝 Exams & ⏱ timed mode", "takip-sinav")
        + _cause('You picked a pool (<b>All / Untried / Wrong / Review / Due</b>) and started',
                 'Questions come one at a time; multiple-choice questions are clickable A–E '
                 'and graded automatically, for open questions you see the stored answer and '
                 'mark it yourself',
                 'You get both quick drilling and real exam rehearsal', L)
        + _cause('You typed a number above 0 into <b>⏱ Duration (min)</b>',
                 'A countdown runs at the top (red for the last 60 seconds); when time runs '
                 'out the exam <b>closes itself</b> and the summary says so',
                 'You rehearse real exam pressure; leave it at 0 to study untimed', L)
        + _note('<b>Why do I mark some answers myself?</b> Maths answers have many '
                'equivalent forms. The program uses sympy to recognise <code>0.5 = 1/2</code>, '
                '<code>x = 2 = 2</code> and <code>2x+2x = 4x</code>, and suggests MATCH / '
                'EQUIVALENT / DIFFERENT — but <b>you make the final call</b>. For '
                'multiple-choice questions the program decides and there is no self-marking.')
        + _note('Every question has a <b>✏️ scratch pad</b> underneath (mouse or pen tablet); '
                'it clears when the question changes. Clipped question images are shown '
                'directly inside the exam.')
        + _h3("📊 Statistics & exam breakdown", "takip-istatistik")
        + _cause('You opened the Statistics tab',
                 'Overall accuracy, a per-topic mastery table, <b>weak topics</b> (red bars) '
                 'and the exam score trend',
                 'You measure where you are weak instead of guessing', L)
        + _cause('You double-clicked a row in the <b>Exams</b> table',
                 'That exam\'s <b>question breakdown</b> opens: what you answered, the '
                 'correct answer, right/wrong/skipped and <b>how long you spent</b> on each',
                 'You see question by question why the score came out that way — and which '
                 'question ate your time', L)
        + _note('The table also says <b>whether the exam was timed</b>. That has only been '
                'recorded since V48; for older exams you will see <b>"?"</b> — the program '
                'does not guess what it does not know.')
        + _h3("📄 Weekly Summary report", "takip-rapor")
        + _cause('You pressed <b>📄 Weekly Summary</b> on the Statistics tab',
                 'A single-page report opens in your browser: study days over the last 7 '
                 'days, questions answered, how your accuracy <b>changed against last '
                 'week</b>, this week\'s weak topics and the exams you finished',
                 'One glance at how the week went — print it and hand it to a parent or '
                 'tutor if you like', L)
        + _note('The report reuses this guide\'s page template: the strip at the top prints '
                'it <b>in colour or grayscale</b>, and "Save as PDF" turns it into an A4 PDF. '
                'No internet is involved; the numbers come only from the records on your '
                'own computer.')
        + _warn('<b>An empty section draws no chart</b> — it says "no data this week". A '
                'topic with fewer than 3 attempts is left out of the weekly reading: no '
                'conclusions are drawn from two attempts.'))

    paket = _h2("8", "📦 Question Packs", "paket") + (
        _h3("Built-in generators (unlimited)", "paket-yerlesik")
        + _cause('You picked a generator on the Question Packs tab and pressed <b>Import</b>',
                 'The program generates as many questions <i>and exact answers</i> as you '
                 'ask for and adds them to your bank',
                 'Running out of practice material stops being a problem: unlimited, '
                 'licence-free, TR/EN', L)
        + _tablo(["Pack", "Contents"], [
            ["<code>prealgebra_core</code>", "Arithmetic, fractions, percentages, ratios"],
            ["<code>algebra_core</code>", "Equations, quadratics, systems, exponents"],
            ["<code>geometry_core</code>", "Area/perimeter, Pythagoras, circles"],
            ["<code>linear_algebra_core</code>", "Determinants, matrices, dot product"],
            ["<code>calculus_intro</code>", "Slope, derivatives"],
        ])
        + _h3("📤 Exporting a pack — share with a friend", "paket-disa")
        + _cause('You set your filters in the question bank and pressed <b>📤 Export Pack</b>',
                 'It asks for a pack name, course, language, licence, attribution and source '
                 'URL, then writes every matching question (with its choices) into a single '
                 'JSON file',
                 'You can hand the questions you prepared to a friend', L)
        + _cause('Your friend dropped the file into their own <code>question_packs\\</code> '
                 'folder',
                 'The pack shows up on their Question Packs tab and imports in one click',
                 'You build a study group where nobody writes the same question twice', L)
        + _tablo(["Format", "What it carries", "When to pick it"], [
            ["<b>.mcpack</b> (ZIP)", "<code>paket.json</code> + <code>images/</code> — "
             "questions you clipped with ✂ <b>keep their images</b>",
             "The default; always pick this if you have image questions"],
            ["<b>.json</b> (flat)", "Text only; image questions are skipped and the dialog "
             "tells you how many", "If the other side runs an older version"],
        ])
        + _note('<b>What happens on the receiving side?</b> When a <code>.mcpack</code> is '
                'imported, the images are extracted into '
                '<code>%APPDATA%\\MathCourseAI\\data\\question_images</code> and linked to '
                'the question — so the exam shows the question <b>with its image</b>. An '
                'existing file with the same name is never overwritten; the name is numbered.')
        + _warn('Image paths inside a pack are <b>validated</b>: only plain filenames under '
                '<code>images/</code> are accepted. A pack containing <code>../</code> or an '
                'absolute path cannot write anywhere else on your filesystem.')
        + _h3("The licence rule", "paket-lisans")
        + _warn('<b>Copyrighted question banks are never embedded.</b> Turkish MEB/EBA/ÖSYM '
                'archives and commercial publishers\' questions are copyrighted and are not '
                'included. In external packs the licence and attribution are stored in the '
                'database <b>with every single question</b>; a pack with no licence stated is '
                'marked <b>UNKNOWN</b> and warned about before import.'))

    lab = _h2("9", "🧪 Labs", "lab") + (
        _lead('Five science labs live as inner tabs inside one <b>🧪 Labs</b> tab. They all '
              'share one idea: <b>turn the subject into maths</b>.')
        + _tablo(["Lab", "What it does"], [
            ["<b>Data Lab</b>", "Turns image/text/audio/video data into maths objects: "
             "vectors, matrices, tensors, frequency, embeddings"],
            ["<b>Physics Lab</b>", "Motion, Newton, projectiles, harmonics, waves, "
             "electric field"],
            ["<b>Chemistry Lab</b>", "Ideal gas, rate law, pH, decay, diffusion, buffers + "
             "periodic table, mole calculations, stoichiometry"],
            ["<b>DNA Lab</b>", "DNA ↔ maths: string/vector/k-mer/information, codon table, "
             "digital data → DNA"],
            ["<b>Quantum</b>", "Qubits, gates, measurement, entanglement (Bell), QFT, "
             "Grover — in the language of vectors and matrices"],
        ])
        + _note('Lab panels are built <b>the first time you click the tab</b>; if you never '
                'open them they are never loaded.'))

    gorsel = _h2("10", "📐 Visual Math Lab", "gorsel") + (
        _cause('You entered an expression or a topic in the Visual Math tab',
               'sympy produces a <b>step-by-step solution</b> plus a matplotlib plot',
               'You see the path, not just the answer', L)
        + _tablo(["Source", "Contents"], [
            ["<b>50 embedded simulations</b>", "Interactive visualisations of course topics"],
            ["<b>90 formula cards</b>", "Cards showing what a formula actually says"],
            ["<b>Lesson-card generator</b>", "Poster-quality PNG (printable)"],
        ])
        + _note('This tab loads sympy and matplotlib, so it <b>takes a moment the first time '
                'you open it</b>; after that it is instant. If you never open it, you never '
                'pay that cost at startup.'))

    sozluk = _h2("11", "📖 Language & Science Dictionary", "sozluk") + (
        _lead('A nine-tab SQLite dictionary that removes the vocabulary barrier while you '
              'follow an English-language course.')
        + _tablo(["Feature", "Why it helps"], [
            ["<b>PDF vocabulary scanner</b>", "Pulls the unfamiliar words out of a whole PDF "
             "at once"],
            ["<b>Image/OCR translation</b>", "Reads and translates the text in a screenshot"],
            ["<b>Favourites & history</b>", "You collect the words you want to revisit"],
            ["<b>Ask the AI about a word</b>", "You ask what a word means specifically in "
             "maths (e.g. \"degree\", \"root\", \"power\")"],
        ]))

    hesap = _h2("12", "🧮 Calculator", "hesap") + (
        _cause('You typed an expression and pressed Enter (<code>sqrt(144)+6*8</code>)',
               'A safe evaluator returns the result and records it in history',
               'You never need to open a separate calculator', L)
        + _tablo(["Feature", "Example"], [
            ["Fraction-aware", "<code>3/4 + 2/5</code> → an exact fraction"],
            ["RAD / DEG", "<code>sin(30)</code> is computed in degrees in DEG mode"],
            ["Functions", "<code>sqrt(25)</code>, <code>log10(100)</code>, "
             "<code>sin(pi/2)</code>"],
            ["<b>AI chat box</b>", "\"add 15% VAT to 200\", \"solve x²−5x+6=0\", "
             "\"explain this result\""],
        ]))

    tablet = _h2("13", "🖊️ Tablet Drawing Board", "tablet") + (
        _cause('You drew with a mouse, a pen display or a graphics tablet',
               'Your handwriting, sketch or graph appears on the board; grid and axes can be '
               'switched on',
               'You work like on paper, but the result can be kept', L)
        + _cause('You pressed <b>"What did I draw?"</b> or <b>Explain with AI</b>',
                 'The board image goes to the vision model and what you drew is interpreted',
                 'You get your working checked', L))

    ayar = _h2("14", "⚙ Settings", "ayar") + (
        _lead('The amber <b>Settings</b> button in the top bar → the <b>Setting</b> menu.')
        + _h3("🌙 Dark theme", "ayar-tema")
        + _cause('You chose <b>Setting → Theme: 🌙 Dark</b>',
                 'The preference is saved and a note says it applies after a restart; when '
                 'you reopen the program the whole interface comes up dark',
                 'Your eyes survive a night session', L)
        + _note('Live switching is deliberately absent: colours are read while windows are '
                'built and cannot be applied correctly without a restart. <b>PDF pages and '
                'LaTeX previews stay light</b> — they are paper-like content areas.')
        + _h3("Startup screen", "ayar-acilis")
        + _tablo(["Option", "What happens"], [
            ["<b>Last session</b> (default)", "You reopen on whichever tab you were last on; "
             "the last PDF page and zoom come back too"],
            ["<b>Today dashboard</b>", "The program opens straight on Student Tracker → "
             "Today; the PDF is still restored in the background"],
        ])
        + _h3("Workspaces & X Layout", "ayar-alan")
        + _cause('You middle-clicked a tab or pressed the <b>×</b> on its chip',
                 'That workspace is hidden and the strip gets simpler',
                 'Tabs you do not use stop competing for your attention', L)
        + _cause('You opened the <b>Workspace Manager</b>',
                 'You can show or hide all 13 workspaces from one list',
                 'Bringing a hidden workspace back is one click', L)
        + _tablo(["X Layout", "What it does"], [
            ["<b>Classic</b>", "Resources on the left, PDF on the right"],
            ["<b>Mirror</b>", "Resources on the right"],
            ["<b>Dual Window</b>", "Two independent PDF readers in two separate windows — "
             "you can put the lesson and the solution side by side"],
        ])
        + _h3("🌍 Language: Turkish / English", "ayar-dil")
        + _cause('You picked <b>Türkçe</b> or <b>English</b> under <b>Settings → Language</b>',
                 'The preference is saved; interface text, this guide and the system '
                 'instruction sent to the AI all switch to the language you chose',
                 'If you follow an English course, the program speaks English too', L)
        + _tablo(["Where", "Status"], [
            ["Main window, tabs, menus", "✅ Bilingual"],
            ["🎓 Student Tracker (6 sub-tabs, 📌 This Week suggestions, exam breakdown)",
             "✅ Bilingual — including suggestion <i>reasons</i> and the 📄 Weekly Summary"],
            ["🖥 AI Terminal + 📜 Work Record", "✅ Bilingual (the system instruction sent "
             "to the AI switches too — with English selected the AI answers in English)"],
            ["📒 Token Ledger, 🧮 Calculator, 🖊️ Drawing Board, 📄 PDF toolbar",
             "✅ Bilingual"],
            ["📐 Visual Math Lab, 📖 Dictionary", "✅ Bilingual (they carry their own text tables)"],
            ["🧪 Labs (Data/Physics/Chemistry/DNA/Quantum)",
             "⚠ Interface labels are still Turkish — next in line"],
            ["ℹ Topic knowledge bank (667 topics)", "⚠ The content was written in Turkish"],
        ])
        + _note('Most panels are built <b>the first time you open them</b> (the lazy '
                'loading that speeds up startup). So if you switch language and open a '
                'panel afterwards it already comes up in the new language; for panels that '
                'are <b>already open</b> the program shows an "applies after restart" note.')
        + _warn('The <b>language of the AI\'s answer</b> depends on the model: the program '
                'sends the system instruction in your chosen language, but a small model '
                'may still reply in mixed language. That is a model limit, not a bug.')
        + _h3("ℹ About · ⌨ Shortcuts · 💾 Backup status", "ayar-hakkinda")
        + _cause('<b>Setting → ℹ About</b>',
                 'Version, release date, what the program does, the <b>keyboard '
                 'shortcuts</b>, version history and a licence summary in one window; '
                 '📋 copies it to the clipboard',
                 '"Which version are you on?" is one click away when you ask for help', L)
        + _tablo(["Shortcut", "What it does"], [
            ["<code>Ctrl+Enter</code>", "AI Terminal: send the request"],
            ["<code>Ctrl+L</code>", "AI Terminal: clear the screen and history"],
            ["<code>Esc</code>", "AI Terminal: stop the running request"],
            ["<b>Double-click</b>", "Statistics → Exams: that exam's question breakdown"],
            ["<b>Middle-click</b>", "Tab strip: hide that workspace"],
            ["<code>Shift</code>+wheel", "Resource tree: horizontal scroll"],
        ])
        + _cause('You opened the <b>Setting</b> menu',
                 'It shows <b>💾 Last backup: X days ago</b>; anything older than 7 days is '
                 'marked ⚠, and clicking it opens the backup folder',
                 'You never have to go looking to check whether your backup still runs', L)
        + _warn('If the backup folder cannot be found the program <b>invents no date</b>: '
                'it says the folder was not found and tells you how to point it at your '
                'own (<code>scripts/local_config.ps1</code>).'))

    token = _h2("15", "📒 Token Usage Ledger", "token") + (
        _lead('<b>Settings → Setting → 📒 Token Ledger.</b> A record of every request that '
              'goes to the AI: how much work it did and where it slowed down.')
        + _cause('You opened the ledger',
                 'Four summary cards: <b>today</b>, <b>last 7 days</b>, <b>last 30 days</b> '
                 'and <b>all time</b> (tokens · requests · seconds)',
                 'You see your working rhythm', L)
        + _tablo(["Tab", "What it shows"], [
            ["<b>By model</b>", "Which model did how much work — a model comparison"],
            ["<b>By provider</b>", "Local versus NVIDIA split"],
            ["<b>By task</b>", "Profile distribution: math / vision / terminal"],
            ["<b>By day</b>", "Daily usage — which day you worked hard"],
            ["<b>Records</b>", "The last 300 requests one by one (time, model, tokens, "
             "seconds, finish reason)"],
        ])
        + _cause('You pressed <b>📤 Export CSV</b>',
                 'The whole ledger becomes a CSV you can open in Excel',
                 'You can run your own analysis', L)
        + _note('<b>Cost:</b> local LM Studio runs on your own machine and NVIDIA NIM uses '
                'free trial endpoints — <b>neither spends money</b>. The ledger is about '
                'awareness rather than billing: which model is slow, which task eats tokens, '
                'whether requests are being cut short.')
        + _warn('<b>Prompt text is never stored</b> in the ledger — only counters (time, '
                'model, token counts, seconds, finish reason). The questions you ask are not '
                'written into it.'))

    veri = _h2("16", "💾 Data, privacy & backup", "veri") + (
        _tablo(["What", "Where"], [
            ["Settings, layout, session", "<code>%APPDATA%\\MathCourseAI\\config_v22.json</code>"],
            ["Course progress + reading ticks", "<code>course_progress_v22.json</code>"],
            ["<b>Student tracker database</b>", "<code>data\\student_tracker.sqlite</code>"],
            ["<b>Dictionary database</b>", "<code>data\\language_dictionary.sqlite</code>"],
            ["Token ledger", "<code>token_usage_v22.jsonl</code>"],
            ["Terminal work record", "<code>terminal_tutanak.jsonl</code>"],
            ["PDF notes / reports / drawings",
             "<code>annotations</code> · <code>Reports</code> · <code>board_exports</code>"],
        ])
        + _note('All of it lives under <b>%APPDATA%\\MathCourseAI</b> — not in the program '
                'folder. That way rebuilding or moving the program never wipes your study '
                'history.')
        + _cause('You took a backup (the automation runs daily, or you click once)',
                 'Source code + git history + <b>your %APPDATA% personal data</b> go into a '
                 'single RAR that is copied into a Google Drive folder',
                 'Your study history survives a change of computer', L)
        + _warn('<b>Course PDFs are excluded from backups and from GitHub</b> (third-party '
                'copyright + size). Keep your own copy of those.'))

    sorun = _h2("17", "🔧 Troubleshooting", "sorun") + _tablo(
        ["Symptom", "Cause / fix"], [
            ["The tree is empty, no courses at all",
             "No course folder is selected, or it contains no supported files → "
             "<b>📁 Choose course folder</b> on the welcome card"],
            ["🔴 AI off", "LM Studio is not running → open it and start the Server. If you "
             "do not want the AI at all, ignore it; everything else works"],
            ["🟡 server up, no model", "Nothing is loaded in LM Studio → load a model"],
            ["The AI answer is cut off",
             "The model's context is probably full → raise Context Length to 4096 in LM Studio"],
            ["NVIDIA answers very slowly",
             "The free endpoint queue is busy → <code>glm-5.2</code> is usually the fastest"],
            ["PDFs will not open", "PyMuPDF is missing → <code>pip install PyMuPDF</code>"],
            ["OCR does not work",
             "The Tesseract <b>application</b> has to be installed separately, not just the "
             "Python package"],
            ["The theme did not change",
             "The theme is applied at startup → close and reopen the program"],
            ["A suggestion card says \"not enough data\"",
             "That is not a fault: fewer than 5 graded attempts on a topic is too little to "
             "draw a conclusion from — solve a few more questions"],
        ])

    uyari = _h2("!", "⚠ Important notes", "uyari") + (
        _warn('<b>Course material is third-party copyright.</b> The program only reads the '
              'files under <code>Resources\\</code> locally and never redistributes them. '
              'Use your own licensed copy.')
        + _warn('<b>The AI makes mistakes.</b> Check the solutions and the code it produces — '
                'that is exactly what the terminal\'s approval gate is for.')
        + _warn('<b>NVIDIA NIM is a trial endpoint.</b> If you pick it, that request leaves '
                'your computer and is logged on NVIDIA\'s side. Everything else in the '
                'program stays offline.')
        + _note('<b>Program code is MIT licensed.</b> The built-in question generators are '
                'original content with no third-party licence. Dependencies (sympy, '
                'matplotlib, NumPy, Pillow, PyMuPDF, Tesseract …) keep their own licences.'))

    return ('<div class="wrap">' + toc + '<main class="content">'
            + genel + yeni + ilk10 + kaynak + pdf + ai + terminal + takip + paket
            + lab + gorsel + sozluk + hesap + tablet + ayar + token + veri + sorun + uyari
            + '<div class="foot"><span class="dot"></span>'
              '<span>Math Course AI — a local, offline, bilingual maths learning platform.</span>'
              '<span class="r">This guide ships with the program.</span></div>'
            + '</main></div>')


BOLUM_SAYISI = 19  # her iki dilde de _h2 sayisi (test bunu dogrular)


# ══════════════════════════════════════════════════════════════════════════
# SAYFA ŞABLONU — programın sıcak paleti; koyu tema için ayrı sürüm gerekmez
# ══════════════════════════════════════════════════════════════════════════

_PAGE = """<!DOCTYPE html>
<html lang="__LANG__"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root{
    --ink:#2B2620; --mut:#8A7E6E; --line:#ECE3D8; --soft:#FBF7F1; --sand:#F6EFE4;
    --green:#16A55A; --blue:#2f6fed; --amber:#E07B39; --red:#C0392B;
  }
  *{box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{margin:0;background:#F3EBE0;color:var(--ink);
    font-family:'Segoe UI',system-ui,-apple-system,Arial,sans-serif;line-height:1.55;}
  .hero{background:linear-gradient(135deg,#2B2620,#4A4033);color:#fff;padding:26px 40px;}
  .hero .kicker{color:#F5C08A;font-weight:700;letter-spacing:2px;font-size:12px;}
  .hero h1{margin:6px 0 4px;font-size:26px;}
  .hero p{margin:0;color:#D8C9B6;font-size:14px;}
  .hero .mark{display:inline-flex;align-items:center;gap:9px;margin-bottom:10px;}
  .hero .mark .ic{width:34px;height:34px;border-radius:9px;
    background:linear-gradient(135deg,#E07B39,#C4632A);display:flex;align-items:center;
    justify-content:center;font-size:18px;}
  .hero .mark b{font-size:14px;letter-spacing:.5px;}

  .wrap{max-width:1120px;margin:0 auto;display:grid;grid-template-columns:250px 1fr;
    background:#fff;}
  .toc{position:sticky;top:0;align-self:start;max-height:100vh;overflow:auto;
    padding:18px 14px;border-right:1px solid var(--line);background:var(--soft);}
  .toc-h{font-size:12px;font-weight:700;color:var(--mut);letter-spacing:1px;
    text-transform:uppercase;margin-bottom:8px;}
  .toc a{display:block;text-decoration:none;color:#3a3128;font-size:13px;padding:4px 8px;
    border-radius:6px;}
  .toc a.sub{padding-left:20px;color:var(--mut);font-size:12.5px;}
  .toc a:hover{background:#FBEADD;color:var(--amber);}
  .content{padding:10px 34px 40px;min-width:0;}

  h2{font-size:20px;margin:30px 0 6px;padding-top:14px;border-top:2px solid var(--sand);
    scroll-margin-top:12px;}
  h2 .n{display:inline-flex;min-width:27px;height:27px;padding:0 6px;border-radius:7px;
    background:var(--amber);color:#fff;align-items:center;justify-content:center;
    font-size:14px;margin-right:9px;}
  h3{font-size:15.5px;margin:20px 0 4px;scroll-margin-top:12px;color:#5A4A38;}
  p{margin:7px 0;} .lead{color:#5f5344;font-size:14.5px;}
  code{background:var(--sand);padding:1px 5px;border-radius:4px;font-size:12.5px;}
  a{color:var(--amber);}

  .cause{border:1px solid var(--line);border-left:4px solid var(--amber);
    border-radius:9px;background:var(--soft);padding:11px 14px;margin:11px 0;}
  .cause .row{display:grid;grid-template-columns:auto 1fr;gap:7px 10px;font-size:14px;}
  .cause .lab{font-weight:700;white-space:nowrap;}
  .cause .lab.n{color:var(--blue);} .cause .lab.s{color:var(--green);}
  .cause .lab.f{color:var(--amber);}

  table{border-collapse:collapse;width:100%;margin:12px 0;font-size:13.5px;}
  th,td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top;}
  th{background:var(--sand);} td:first-child{white-space:normal;}

  .legend{color:var(--mut);font-size:12.5px;margin:6px 0;background:var(--sand);
    border:1px solid var(--line);border-radius:8px;padding:9px 12px;}
  .note{background:#EAF4EC;border:1px solid #CFE6D6;border-radius:9px;padding:11px 14px;
    margin:13px 0;font-size:13.5px;}
  .warn{background:#FDF0E3;border:1px solid #F3DDB5;border-radius:9px;padding:11px 14px;
    margin:13px 0;font-size:13.5px;}
  .foot{margin-top:26px;padding-top:14px;border-top:2px solid var(--sand);
    color:var(--mut);font-size:12.5px;display:flex;gap:10px;align-items:center;}
  .foot .dot{width:7px;height:7px;border-radius:50%;background:var(--green);}
  .foot .r{margin-left:auto;}

  @media(max-width:820px){
    .wrap{grid-template-columns:1fr;} .toc{position:static;max-height:none;
      border-right:none;border-bottom:1px solid var(--line);}
    .content{padding:10px 18px 30px;}
  }
  .yazdir-serit{display:flex;gap:8px;align-items:center;margin:10px 0 0;padding:0 26px;}
  .yazdir-serit button{font:inherit;font-size:13px;font-weight:600;padding:6px 12px;
    cursor:pointer;border:1px solid var(--line);background:var(--soft);border-radius:8px;}
  .yazdir-serit .kucuk{color:var(--mut);font-size:12px;}
  body.gri{filter:grayscale(1);}
  @page{size:A4 portrait;margin:14mm 12mm;}
  @media print{
    body{background:#fff;print-color-adjust:exact;-webkit-print-color-adjust:exact;}
    .toc{display:none;} .noprint{display:none !important;}
    .wrap{grid-template-columns:1fr;max-width:none;}
    h2{break-after:avoid;} .cause,.note,.warn,table{break-inside:avoid;}
  }
</style></head>
<body>
<div class="hero"><div class="mark"><span class="ic">Σ</span><b>MATH COURSE AI</b></div>
<div class="kicker">__KICKER__</div><h1>__TITLE__</h1><p>__SUB__</p></div>
<div class="noprint yazdir-serit">
<button onclick="document.body.classList.remove('gri');window.print()">__YAZDIR_RENKLI__</button>
<button onclick="document.body.classList.add('gri');window.print()">__YAZDIR_GRI__</button>
<span class="kucuk">__YAZDIR_NOT__</span>
</div>__BODY__</body></html>"""


def sayfa_html(baslik, alt, kicker, govde, lang="tr",
               yazdir_renkli=None, yazdir_gri=None, yazdir_not=None):
    """_PAGE şablonunu DIŞARIDAN doldurmanın tek yolu.

    Kılavuzun sıcak paleti, yazdırma şeridi ve A4 print CSS'i başka
    raporlarda da (📄 Haftalık Özet) aynen kullanılsın diye ayrıldı — şablon
    kopyalansaydı iki yerde ayrı ayrı bozulurdu.

    `govde` tam HTML gövdesidir; içindekiler istemeyen sayfalar
    `<div class="wrap" style="grid-template-columns:1fr">` ile tek sütuna
    geçebilir (şablonun grid'i satır içi stille ezilir).
    """
    lang = "en" if str(lang).lower().startswith("en") else "tr"
    if lang == "en":
        vr, vg = "🖨 Print in colour", "🖨 Print in grayscale"
        vn = "Choosing “Save as PDF” turns this page into a PDF (A4)."
    else:
        vr, vg = "🖨 Renkli Yazdır", "🖨 Gri Yazdır"
        vn = "“PDF olarak kaydet” seçilirse aynı sayfa PDF olur (A4)."
    return (_PAGE.replace("__LANG__", lang).replace("__TITLE__", baslik)
            .replace("__SUB__", alt).replace("__KICKER__", kicker)
            .replace("__YAZDIR_RENKLI__", yazdir_renkli or vr)
            .replace("__YAZDIR_GRI__", yazdir_gri or vg)
            .replace("__YAZDIR_NOT__", yazdir_not or vn)
            .replace("__BODY__", govde))


def egitim_html(lang="tr"):
    """Eğitim modülünün tam HTML'ini döndürür. lang: 'tr' (varsayılan) veya 'en'."""
    lang = "en" if str(lang).lower().startswith("en") else "tr"
    if lang == "en":
        body = _body_en()
        titre = "Math Course AI — User Guide"
        alt = ("Everything the program does, in why → result → benefit form. "
               "Works offline; no internet needed to read this page.")
        kicker = "LEARNING MODULE"
        y_renkli, y_gri = "🖨 Print in colour", "🖨 Print in grayscale"
        y_not = "Choosing “Save as PDF” turns this page into a PDF (A4)."
    else:
        body = _body_tr()
        titre = "Math Course AI — Kullanma Kılavuzu"
        alt = ("Programın yaptığı her şey, neden → sonuç → fayda biçiminde. "
               "Çevrimdışı çalışır; bu sayfayı okumak için internet gerekmez.")
        kicker = "EĞİTİM MODÜLÜ"
        y_renkli, y_gri = "🖨 Renkli Yazdır", "🖨 Gri Yazdır"
        y_not = "“PDF olarak kaydet” seçilirse aynı sayfa PDF olur (A4)."
    return sayfa_html(titre, alt, kicker, body, lang=lang,
                      yazdir_renkli=y_renkli, yazdir_gri=y_gri, yazdir_not=y_not)


def kilavuz_ac(lang="tr"):
    """Kılavuzu geçici dosyaya yazıp sistem tarayıcısında açar → (ok, yol|hata)."""
    import tempfile
    import time
    import webbrowser
    from pathlib import Path
    try:
        klasor = Path(tempfile.gettempdir()) / "MathCourseAI_Kilavuz"
        klasor.mkdir(parents=True, exist_ok=True)
        yol = klasor / ("kilavuz_%s_%d.html" % (lang, int(time.time())))
        yol.write_text(egitim_html(lang), encoding="utf-8")
        webbrowser.open("file:///" + str(yol).replace("\\", "/"))
        return True, str(yol)
    except Exception as exc:
        return False, str(exc)
