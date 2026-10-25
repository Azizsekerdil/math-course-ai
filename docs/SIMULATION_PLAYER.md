# Simülasyon Oynatıcı / Simulation Player

*English below.*

## Türkçe

Kurs ağacındaki **her konu satırının sağında bir ▶ düğmesi** vardır (kurs, klasör ve
PDF satırları). Ona tıklamak — ya da sağ tık → **▶ Simülasyon**, sol paneldeki
**▶ Simülasyon** düğmesi veya ℹ penceresindeki aynı düğme — **Simülasyon Oynatıcı**'yı
o konu için açar.

**Neyi gösterir?**

- **Bu konu:** konu adına (ör. `02 Slope.pdf`, `Riemann sums`, `Eigenvalues`) ve kursa
  göre seçilen, programa gömülü örnek sorular. Konu adı eşleşmeyen genel klasörlerde
  (`01 Formula Sheet`, `05 Final Exams`…) kursun tüm örnekleri listelenir.
- **Kaynaktan taranan:** "📄 Kaynaktaki örnekleri tara" seçili konu klasörünü/PDF'ini
  tarar; bulunan örnek sorular (doğru denklemi, ikinci derece denklem, denklem sistemi,
  türev, limit, integral, diferansiyel denklem, Pisagor, daire, zar, işlem önceliği,
  fonksiyon grafiği…) çalıştırılabilir simülasyona çevrilir.
- **Tüm kurs / Tüm dersler:** gömülü kütüphanenin tamamı.

**Oynatma:** ▶ Oynat / ⏸ Duraklat (Boşluk), ◀ Adım / Adım ▶ (←/→), ⏮ ⏭, kare sürgüsü,
hız (0.25x–4x), döngü. Çözüm adımları animasyonla **eşzamanlı** açılır; son karede
cevap yazılır.

**🎲 Yeni sayılar:** aynı soru tipini başka sayılarla üretir; çözüm adımları da yeni
sayılarla yeniden hesaplanır. **↺ Orijinal soru** geri döner.

**Python kodu sekmesi:** oynatıcının çalıştırdığı kaynağın **ta kendisi**. `P = {...}`
içindeki sayıları (veya kodu) değiştirip **▶ Kodu çalıştır** ile yeniden oynatabilirsiniz.
**💾 .py kaydet** programdan bağımsız çalışan bir betik (`python dosya.py`), **💾 GIF**
ve **🖼 PNG** dışa aktarım verir.

**Gereken:** yalnızca programın zaten kullandığı `numpy`, `matplotlib`, `sympy`.
Manim, FFmpeg, TeX, VLC **gerekmez**. PDF taraması için `pypdf` (BSD) veya isteğe bağlı
PyMuPDF; Windows/macOS paketleme betikleri `pypdf`'i kurar.

**Telif/lisans:** taranan kitabın metni **ne saklanır ne gösterilir**. Bir örnekten
yalnızca matematiksel içerik (ifade, katsayılar, sınırlar) ve kaynak referansı
(dosya adı + sayfa) alınır; soru cümlesi programın kendi cümlesiyle yeniden yazılır.
"Sayıları değiştir" (varsayılan açık) katsayıları da değiştirir. Gömülü örnek sorular
kitaplardan kopyalanmamıştır: kendi ifademizle yazılmış tipik ders alıştırmalarıdır.

**Sınırlar:** Tarayıcı kural tabanlıdır; PDF'te resim olarak duran ya da metne kötü
dönüşen matematik (çok satırlı kesirler, matrisler, integral işaretleri) her zaman
okunamaz — o örnekler atlanır, konunun gömülü örnekleri yine gösterilir.
Düzenlenmiş kod, çalışmadan önce `ai_code_guard` izin politikasından geçer (dosya, ağ,
süreç erişimi reddedilir); bu statik bir denetimdir, **sandbox değildir** — ayrıntı
için [known-limitations.md](known-limitations.md) §9.

## English

Every row of the course tree has a **▶ button** (course, folder and PDF rows). Clicking
it (or right-click → **▶ Simulation**, the **▶ Simulation** button under the tree, or
the same button in the ℹ window) opens the **Simulation Player** for that topic.

- **This topic:** embedded example problems chosen by the topic name and the course.
  Generic folders (`01 Formula Sheet`, …) list every example of the course.
- **Scanned from source:** "📄 Scan source examples" reads the selected topic folder/PDF
  and turns the example problems it recognises into runnable simulations.
- **Playback:** play/pause (Space), step (←/→), seek, speed, loop; the worked solution
  is revealed in sync with the animation and the answer appears on the last frame.
- **🎲 New numbers** regenerates the same problem type with new numbers.
- **Python code tab:** exactly the source being run; edit `P = {...}` or the code and
  press **▶ Run code**. Export a standalone `.py`, a GIF or a PNG.
- Needs only `numpy`, `matplotlib`, `sympy` — no Manim/FFmpeg/TeX/VLC. PDF scanning uses
  `pypdf` (BSD) or the optional PyMuPDF.
- No book text is stored or shown: only the mathematical content and a file/page
  reference are kept, and the question is reworded by the program.

Counts (simulation kinds, embedded examples per course) are measured, not written by
hand: `python tools/measure_facts.py`.
