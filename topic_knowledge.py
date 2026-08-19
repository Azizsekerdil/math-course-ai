# -*- coding: utf-8 -*-
"""
topic_knowledge — embedded "Nedir ve Ne İçin Kullanılır?" bilgi bankası
========================================================================

V45'ten itibaren konu bilgi penceresi ÖNCE burada yazılı, elle hazırlanmış
açıklamalara bakar — hiçbir AI çağrısı yapmadan, tamamen çevrimdışı ve anında.
Yerel LM Studio AI'sı artık yalnızca burada bulunmayan (henüz eklenmemiş) bir
konu için, kullanıcı açıkça "🤖 Yerel AI'dan Sor" düğmesine basarsa devreye girer.

İçerik ilkesi: her girişte gerçek matematiksel tarih/biyografi yalnızca
DOĞRULANABİLİR olduğunda verilir (kim, ne zaman, kısaca neden önemli). Salt
işlemsel/prosedürel konularda (yuvarlama, birim fiyat, işlem önceliği gibi)
uydurma bir "kâşif" hikâyesi YAZILMAZ — bu tür girişlerde Tarih bölümü atlanır.

Bu, sabit/kapalı bir liste değildir: `TOPIC_KNOWLEDGE` sözlüğüne yeni anahtar
eklemek yeterlidir; ağaçtaki her dosya/klasör adı otomatik olarak
`normalize_topic_key()` ile buradaki anahtarlarla eşleştirilir (yaklaşık
eşleşme dahil), böylece küçük yazım farkları (büyük/küçük harf, kesme işareti,
"ve" / "and") sorun çıkarmaz.
"""

import re
import unicodedata
import difflib


def normalize_topic_key(text):
    """'L'Hôpital's Rule' / "L'Hopital's Rule" -> 'lhopitals rule' gibi kaba
    ama tutarlı bir anahtara indirger, böylece küçük yazım farkları eşleşir."""
    s = str(text or "")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = s.replace("&", " and ")
    for ch in ("'", "’", "‘", "`", "´"):
        s = s.replace(ch, "")
    s = re.sub(r"[-_.,:;/()=+]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


_NORMALIZED_INDEX = None


def _build_index():
    global _NORMALIZED_INDEX
    if _NORMALIZED_INDEX is None:
        _NORMALIZED_INDEX = {normalize_topic_key(k): k for k in TOPIC_KNOWLEDGE}
    return _NORMALIZED_INDEX


def get_topic_info(topic_name):
    """Return the embedded dict for `topic_name`, or None if not documented yet.

    Tries an exact normalized match first, then a close (fuzzy) match so minor
    file-name variations still resolve — but never guesses wildly (cutoff is
    strict enough that unrelated topics return None instead of a wrong entry).
    """
    if not topic_name:
        return None
    index = _build_index()
    key = normalize_topic_key(topic_name)
    if key in index:
        return TOPIC_KNOWLEDGE[index[key]]
    close = difflib.get_close_matches(key, index.keys(), n=1, cutoff=0.86)
    if close:
        return TOPIC_KNOWLEDGE[index[close[0]]]
    return None


def coverage_count():
    return len(TOPIC_KNOWLEDGE)


# ===========================================================================
# delatex — downgrade the light LaTeX used in these bodies (and in AI-
# generated fallback answers, which follow the same convention) to readable
# plain Unicode for display in a plain tk.Text widget.
#
# This is deliberately NOT a LaTeX engine: rendering true math typesetting
# would need an image per entry and risks ugly wrapping on long, mixed
# prose+math paragraphs. A text substitution covers the constructs actually
# used here (√, fractions, exponents/indices, Greek letters, common symbols)
# and keeps the result selectable/copyable — good enough for a quick
# reference popup, and it never crashes on unexpected input.
# ===========================================================================
_GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
    "zeta": "ζ", "eta": "η", "theta": "θ", "iota": "ι", "kappa": "κ",
    "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "pi": "π", "rho": "ρ",
    "sigma": "σ", "tau": "τ", "phi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Sigma": "Σ",
    "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
}
_SUPER = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶",
          "7": "⁷", "8": "⁸", "9": "⁹", "n": "ⁿ", "i": "ⁱ", "+": "⁺", "-": "⁻"}
_SUB = {"0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄", "5": "₅", "6": "₆",
        "7": "₇", "8": "₈", "9": "₉", "a": "ₐ", "i": "ᵢ", "j": "ⱼ", "k": "ₖ",
        "n": "ₙ", "x": "ₓ", "+": "₊", "-": "₋"}

_SYMBOLS = {
    r"\cdot": "·", r"\times": "×", r"\div": "÷", r"\pm": "±", r"\mp": "∓",
    r"\neq": "≠", r"\leq": "≤", r"\geq": "≥", r"\le": "≤", r"\ge": "≥",
    r"\approx": "≈", r"\equiv": "≡", r"\sim": "∼",
    r"\infty": "∞", r"\rightarrow": "→", r"\Rightarrow": "⇒", r"\to": "→",
    r"\leftrightarrow": "↔", r"\in": "∈", r"\notin": "∉",
    r"\subset": "⊂", r"\cup": "∪", r"\cap": "∩", r"\emptyset": "∅",
    r"\forall": "∀", r"\exists": "∃", r"\perp": "⊥", r"\parallel": "∥",
    r"\angle": "∠", r"\triangle": "△", r"\degree": "°",
    r"\sum": "Σ", r"\prod": "Π", r"\int": "∫", r"\oint": "∮",
    r"\partial": "∂", r"\nabla": "∇",
    r"\{": "{", r"\}": "}", r"\%": "%", r"\quad": "  ", r"\qquad": "    ",
    r"\,": " ", r"\;": " ", r"\!": "", r"\ ": " ",
    r"\ldots": "…", r"\cdots": "⋯", r"\vec": "",
    r"\|": "|",   # norm delimiters, e.g. \|v\| -> |v|
}


def _simplify_script(token):
    """Content of a ^{...}/_{...} group. Short alnum/+/- tokens become real
    Unicode super/subscript characters; anything more complex (spaces,
    arrows, multi-word) is just parenthesized instead of producing garbage
    like mixed '_h_→_ ₀' from a naive per-character mapping."""
    token = re.sub(r"\s+", " ", token).strip()
    if not token:
        return ""
    if len(token) <= 2 and all(ch.isalnum() or ch in "+-" for ch in token):
        return token  # caller applies the super/sub map
    return "(" + token + ")"


def _apply_super(token):
    simple = _simplify_script(token)
    if simple.startswith("("):
        return simple
    return "".join(_SUPER.get(ch, "^" + ch) for ch in simple)


def _apply_sub(token):
    simple = _simplify_script(token)
    if simple.startswith("("):
        return simple
    return "".join(_SUB.get(ch, "_" + ch) for ch in simple)


def _find_balanced(s, start):
    """`s[start]` must be '{'. Returns (inner_content, index_after_closing_brace),
    correctly handling nested braces (e.g. a \\sqrt inside a \\frac numerator)."""
    depth, i, n = 0, start, len(s)
    while i < n:
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[start + 1:i], i + 1
        i += 1
    return s[start + 1:], n   # unbalanced input — best effort, never raises


def _replace_structural(s):
    """One manual pass replacing \\frac{a}{b}, \\dfrac{a}{b}, \\binom{a}{b},
    \\sqrt{a} and \\sqrt[n]{a} — with PROPER nested-brace handling, which a
    simple regex cannot do (needed for e.g. \\dfrac{-b}{\\sqrt{b^2-4ac}})."""
    out, i, n = [], 0, len(s)
    while i < n:
        if s[i] != "\\":
            out.append(s[i]); i += 1
            continue
        matched = False
        for cmd in ("dfrac", "frac", "binom", "sqrt"):
            if s[i + 1:i + 1 + len(cmd)] != cmd:
                continue
            j = i + 1 + len(cmd)
            if cmd == "sqrt":
                root = ""
                if j < n and s[j] == "[":
                    k = s.find("]", j)
                    if k != -1:
                        root, j = s[j + 1:k], k + 1
                if j < n and s[j] == "{":
                    inner, j2 = _find_balanced(s, j)
                    inner = _replace_structural(inner)
                    out.append(f"{root}-kök({inner})" if root else f"√({inner})")
                    i, matched = j2, True
            elif j < n and s[j] == "{":
                a, j2 = _find_balanced(s, j)
                if j2 < n and s[j2] == "{":
                    b, j3 = _find_balanced(s, j2)
                    a2, b2 = _replace_structural(a), _replace_structural(b)
                    tmpl = "C({0},{1})" if cmd == "binom" else "({0})/({1})"
                    out.append(tmpl.format(a2, b2))
                    i, matched = j3, True
            if matched:
                break
        if not matched:
            out.append(s[i]); i += 1
    return "".join(out)


def delatex(text):
    """'$\\sqrt{2}$ ve $x^{n-1}$' -> '√(2) ve xⁿ⁻¹' gibi okunabilir düz metne
    çevirir. Bilinmeyen bir yapı bulursa olduğu gibi bırakır, asla hata vermez."""
    s = str(text or "")
    try:
        s = _replace_structural(s)
        # \overline{x} -> x + combining overline (best effort)
        s = re.sub(r"\\overline\{([^{}]*)\}", lambda m: m.group(1) + "̅", s)
        # \left( \right) \left[ \right] \left\{ \right\} -> plain delimiters
        s = re.sub(r"\\left\\?([\(\[\{])", r"\1", s)
        s = re.sub(r"\\right\\?([\)\]\}])", r"\1", s)
        # \text{...} -> ... (drop the wrapper, keep the words)
        s = re.sub(r"\\text\{([^{}]*)\}", r"\1", s)
        # Greek letters (word-boundary; longest names first to avoid partial hits)
        for name in sorted(_GREEK, key=len, reverse=True):
            s = re.sub(r"\\" + name + r"\b", _GREEK[name], s)
        # Common symbols (longest keys first so e.g. \leq beats \le)
        for k in sorted(_SYMBOLS, key=len, reverse=True):
            s = s.replace(k, _SYMBOLS[k])
        # Exponents / subscripts: ^{...}, ^x, _{...}, _x
        s = re.sub(r"\^\{([^{}]*)\}", lambda m: _apply_super(m.group(1)), s)
        s = re.sub(r"\^([A-Za-z0-9+\-])", lambda m: _apply_super(m.group(1)), s)
        s = re.sub(r"_\{([^{}]*)\}", lambda m: _apply_sub(m.group(1)), s)
        s = re.sub(r"_([A-Za-z0-9+\-])", lambda m: _apply_sub(m.group(1)), s)
        # Drop now-redundant math-mode $ delimiters and stray braces/backslashes
        s = s.replace("$", "")
        s = re.sub(r"\\([a-zA-Z]+)", r"\1", s)   # any leftover \command -> command
        s = s.replace("{", "").replace("}", "")
        s = re.sub(r"[ \t]{2,}", " ", s)
    except Exception:
        return str(text or "")
    return s


# ===========================================================================
# TOPIC_KNOWLEDGE — kurs bazında, en temel/kavramsal önemli konular.
# Bu ilk parti (V45) ~140 giriş içerir; kapsam sürüm sürüm ("Döngü
# Mühendisliği" ile) genişletilecek. Anahtarlar zaten normalize edilmiş
# biçimdedir (bkz. normalize_topic_key) — yeni ekleme yaparken küçük harfle,
# kesme işaretsiz yazmak yeterlidir.
# ===========================================================================
TOPIC_KNOWLEDGE = {}


def _add(course, keys, body):
    entry = {"course": course, "body": body.strip()}
    for k in (keys if isinstance(keys, (list, tuple)) else [keys]):
        TOPIC_KNOWLEDGE[normalize_topic_key(k)] = entry


# ---------------------------------------------------------------------------
# Pre-Algebra
# ---------------------------------------------------------------------------
_add("Pre-Algebra", "Fractions", """
Kesirler, bir bütünün eşit parçalara bölünmüş hâlinin kaydıdır — bir pastanın
4 dilimden 3'ünü aldığında elindeki $3/4$'tür; pay (numerator) kaç dilim
aldığını, payda (denominator) bütünün kaça bölündüğünü söyler.

Nedir?
Bir kesir $a/b$ ($b \\neq 0$), $a$'nın $b$'ye bölümünü ifade eder. Sadeleştirme,
ortak payda bulma ve dört işlem kuralları, kesirlerin "aynı büyüklüğü farklı
biçimde" temsil edebilmesinden gelir: $2/4 = 1/2$.

Ne İçin Kullanılır?
1. Oran ve Bölüşüm Problemleri
Tarif ölçekleme, indirim hesabı, harita ölçeği gibi "parçanın bütüne oranı"
gerektiren her günlük hesapta kullanılır.
2. Cebirin Temeli
Rasyonel ifadeler, olasılık hesapları ve orantı problemlerinin hepsi kesir
aritmetiğine dayanır; kesirlerde zayıf olmak ileride cebiri zorlaştırır.

📜 Tarih ve Biyografi
Kesir kavramı MÖ 1650 civarına tarihlenen Mısır Rhind Papirüsü'nde birim
kesirler (1/n biçiminde) olarak karşımıza çıkar. Bugünkü pay/payda çizgili
gösterimi Ortaçağ İslam matematikçisi el-Hassar'ın (12. yüzyıl, Fas) eserlerinde
görülür; Fibonacci bu notasyonu 1202'de "Liber Abaci" ile Avrupa'ya taşıdı.
""")

_add("Pre-Algebra",
     ["Rules of exponents", "Exponents", "Negative and other exponent rules", "Power rule for exponents"], """
Üs, "aynı sayıyı kaç kez çarptığının" kısa yazımıdır — $2^3$, "2'yi 3 kez
çarp" demenin kısayoludur; üs kuralları da bu kısayolları birleştirmenin
tutarlı yollarıdır.

Nedir?
$a^m \\cdot a^n = a^{m+n}$, $a^m / a^n = a^{m-n}$, $(a^m)^n = a^{mn}$,
$a^0 = 1$ ($a \\neq 0$) ve $a^{-n} = 1/a^n$ kuralları, üslü ifadeleri
sadeleştirmenin temel gramerini oluşturur.

Ne İçin Kullanılır?
1. Büyük/Küçük Sayıları Yönetmek
Bilimsel gösterim, bileşik faiz, nüfus/bakteri büyümesi gibi hızlı artan veya
küçülen miktarları yönetilebilir kılar.
2. Cebirsel Sadeleştirme
Polinom ve rasyonel ifadeleri sadeleştirmenin, denklemleri çözmenin ön koşuludur.
3. Bilgisayar Biliminde Karmaşıklık
Algoritma çalışma sürelerini ifade eden $O(2^n)$ gibi büyüme oranları doğrudan
üs kurallarıyla okunur.

📜 Tarih ve Biyografi
Üslü gösterimin modern sembolik biçimi (bugün kullandığımız $x^2$, $x^3$
yazımı) Fransız matematikçi René Descartes tarafından 1637'de "La Géométrie"
adlı eserinde tanıtıldı. Negatif ve kesirli üs kavramları ise İngiliz
matematikçi John Wallis tarafından 1656'da sistematik hâle getirildi.
""")

_add("Pre-Algebra", ["Scientific notation", "Powers of 10"], """
Bilimsel gösterim, çok büyük veya çok küçük sayıları taşınabilir hâle
getiren bir "paketleme" yöntemidir — bir virüsün boyutunu ya da bir
galaksideki yıldız sayısını sıfırlarla boğulmadan yazmanı sağlar.

Nedir?
Bir sayı $a \\times 10^n$ biçiminde yazılır; burada $1 \\le |a| < 10$ ve $n$
tam sayıdır. Örneğin ışık hızı $3 \\times 10^8$ m/s'dir.

Ne İçin Kullanılır?
1. Bilim ve Mühendislikte Ölçek Yönetimi
Atom boyutlarından (10⁻¹⁰ m) evrenin yaşına (10¹⁰ yıl) kadar her ölçekte
sayıları karşılaştırılabilir kılar.
2. Hesap Makinesi ve Yazılımda Kesinlik
Bilgisayarlar kayan noktalı sayıları (floating point) bu mantıkla saklar;
taşma (overflow) ve hassasiyet hatalarını anlamak için gereklidir.

📜 Tarih ve Biyografi
Sistemin kökleri, ondalık kesirleri ve üslü gösterimi birleştiren Flaman
matematikçi Simon Stevin'in 1585 tarihli "De Thiende" adlı çalışmasına
dayanır; modern $a \\times 10^n$ biçimi 19. yüzyılda bilim camiasında
standartlaştı.
""")

_add("Pre-Algebra", ["Prime and composite", "Prime factorization and product of primes",
                                         "Greatest common factor", "Least common multiple", "Divisibility", "Multiples"], """
Asal sayılar, matematiğin "atomlarıdır" — tıpkı her molekülün atomlardan
oluşması gibi, her sayı da asal sayıların çarpımı olarak tek bir şekilde
inşa edilebilir.

Nedir?
Bir asal sayı, yalnızca 1'e ve kendisine bölünen 1'den büyük bir tam sayıdır
(2, 3, 5, 7, 11, ...). Asal çarpanlara ayırma, bir sayıyı bu atomların
çarpımı olarak yazmaktır: $60 = 2^2 \\times 3 \\times 5$. OBEB (en büyük ortak
bölen) ve OKEK (en küçük ortak kat), bu çarpanlardan türetilir.

Ne İçin Kullanılır?
1. Kesirleri Sadeleştirmek
OBEB, bir kesri en sade hâline indirmenin anahtarıdır.
2. Kriptografi ve Bilgisayar Güvenliği
Modern şifreleme (RSA), çok büyük sayıları asal çarpanlarına ayırmanın
pratikte imkânsız derecede zor olmasına dayanır.
3. Zamanlama ve Döngü Problemleri
OKEK, "iki olay ne zaman aynı anda tekrar gerçekleşir?" (örn. iki farklı
periyotta yanıp sönen ışıklar) türü problemleri çözer.

📜 Tarih ve Biyografi
Asal sayıların sonsuz olduğunun ilk kanıtı, MÖ 300 civarında Yunan
matematikçi Euclid'in "Elementler" adlı eserinde verilmiştir. Asal
sayıları elemeyle bulan "Eratosthenes Kalburu" yöntemi ise MÖ 240
civarında İskenderiyeli bilgin Eratosthenes'e atfedilir.
""")

_add("Pre-Algebra", ["Radicals", "Radical expressions", "Adding and subtracting radicals",
                                         "Multiplying radicals", "Dividing radicals"], """
Kök, üs almanın tersidir — üs bir sayıyı "büyütürken", kök onu "küçük
tohumuna" geri döndürür: $\\sqrt{9} = 3$ çünkü $3^2 = 9$.

Nedir?
$\\sqrt[n]{a}$, $n$. kuvveti $a$'yı veren sayıdır. Karekök ($n=2$) en yaygın
biçimdir. Kök işlemleri toplarken/çıkarırken "benzer terim" mantığıyla
($2\\sqrt{3} + 5\\sqrt{3} = 7\\sqrt{3}$), çarparken/bölerken üs kurallarıyla
($\\sqrt{a}\\cdot\\sqrt{b} = \\sqrt{ab}$) ilerler.

Ne İçin Kullanılır?
1. Geometride Uzunluk Hesabı
Pisagor teoremi ve mesafe formülü doğrudan karekök içerir; bir TV ekranının
köşegenini veya iki nokta arası mesafeyi bulmak kök gerektirir.
2. Fizik ve Mühendislik Formüllerinde
Serbest düşme süresi, dalga hızı gibi birçok fiziksel formülde kök terimleri
bulunur.

📜 Tarih ve Biyografi
Kök alma işleminin sayısal yaklaşıklığı Babillilere kadar uzanır (MÖ 1800
civarı bir tablette $\\sqrt{2}$'nin şaşırtıcı derecede doğru bir yaklaşımı
bulunmuştur). Bugün kullandığımız $\\sqrt{\\ }$ (radikal) sembolü, Alman
matematikçi Christoff Rudolff tarafından 1525'te tanıtılmıştır.
""")

_add("Pre-Algebra", ["Adding and subtracting signed numbers", "Multiplying signed numbers",
                                         "Dividing signed numbers", "Opposite of a number"], """
Negatif sayılar, "eksi" fikrinin sayı doğrusunda sıfırın diğer tarafına
taşınmasıdır — bir borcu, deniz seviyesinin altındaki bir derinliği veya
sıfırın altındaki bir sıcaklığı ifade eder.

Nedir?
İşaretli sayılarla işlemler, "aynı işaretliler toplanır, farklı işaretliler
çıkarılır (büyükten küçük çıkarılır ve büyüğün işareti alınır)" ve "çift
sayıda eksi çarpımı artıya döner" kurallarıyla yürür.

Ne İçin Kullanılır?
1. Finans ve Muhasebe
Banka bakiyesi, kâr/zarar, borç/alacak hesapları negatif sayılar olmadan
ifade edilemez.
2. Bilim ve Mühendislikte Yön/Büyüklük
Sıcaklık, rakım, elektrik yükü gibi "yönü olan" ölçümlerin doğal dili
işaretli sayılardır.

📜 Tarih ve Biyografi
Negatif sayılarla sistematik işlem kuralları ilk kez Hintli matematikçi
Brahmagupta tarafından MS 628'de "Brahmasphutasiddhanta" adlı eserinde
yazıya döküldü; Avrupa matematikçileri negatif sayıları "anlamsız" bularak
16-17. yüzyıla kadar kuşkuyla yaklaştılar.
""")

_add("Pre-Algebra", ["Number sets", "Identity numbers"], """
Sayı kümeleri, matematiğin farklı "mahallelerini" haritalandırır — her
küme bir öncekini içine alan daha geniş bir bölgedir: doğal sayılardan
başlayıp gerçek sayılara kadar genişler.

Nedir?
Doğal sayılar ($\\mathbb{N}$) → tam sayılar ($\\mathbb{Z}$, negatifler eklenir)
→ rasyonel sayılar ($\\mathbb{Q}$, kesirler eklenir) → gerçek sayılar
($\\mathbb{R}$, irrasyoneller eklenir) şeklinde iç içe geçmiş kümelerdir.

Ne İçin Kullanılır?
1. Bir Denklemin "Nerede Yaşadığını" Bilmek
$x^2=2$'nin çözümü rasyonel sayılarda yokken gerçek sayılarda vardır — hangi
kümede çalıştığın, hangi çözümlerin mümkün olduğunu belirler.
2. Yazılımda Veri Tipi Seçimi
Programlamada integer, float gibi veri tiplerinin ayrımı doğrudan bu sayı
kümesi hiyerarşisinden gelir.

📜 Tarih ve Biyografi
İrrasyonel sayıların varlığı ilk kez MÖ 5. yüzyılda Pisagorcular tarafından,
bir karenin köşegen uzunluğunun ($\\sqrt{2}$) hiçbir kesirle tam ifade
edilemeyeceğinin keşfiyle ortaya çıktı — bu, dönemin "her şey tam sayı
oranıdır" inancını sarsan bir kriz yarattı. Sayı kümelerinin modern küme
teorisi temelli tanımı ise Alman matematikçi Georg Cantor'un 1870'lerdeki
çalışmalarına dayanır.
""")

# ---------------------------------------------------------------------------
# Algebra
# ---------------------------------------------------------------------------
_add("Algebra", ["Cartesian coordinate system"], """
Kartezyen koordinat sistemi, cebir ile geometri arasında kurulan bir
köprüdür — bir denklemi "görünür" kılar: artık $y = x^2$ yazmak yerine onun
çizdiği parabolü gözünle görebilirsin.

Nedir?
Düzlemdeki her nokta, birbirine dik iki eksene (x ve y) olan uzaklığıyla
$(x, y)$ ikilisi olarak ifade edilir. Bu, cebirsel denklemlerin geometrik
şekillere (doğru, parabol, çember) dönüştürülebilmesini sağlar.

Ne İçin Kullanılır?
1. Analitik Geometrinin Temeli
Eğim, mesafe, orta nokta gibi tüm geometrik kavramlar koordinatlarla
sayısal hâle gelir.
2. Veri Görselleştirme ve Grafikler
Bilgisayar ekranındaki her grafik, harita, oyun motoru bu ızgara sistemine
dayanır.

📜 Tarih ve Biyografi
Sistem, Fransız filozof ve matematikçi René Descartes tarafından 1637'de
yayımlanan "La Géométrie" adlı eserinde tanıtıldı — "Kartezyen" adı onun
Latince adı Cartesius'tan gelir. Efsaneye göre fikir, Descartes'ın tavanda
gezinen bir sineğin konumunu iki duvara olan uzaklığıyla tarif etmeye
çalışmasından doğmuştur.
""")

_add("Algebra", ["Function notation", "Domain and range", "Composite functions",
                                  "Domains of composite functions", "Combinations of functions",
                                  "Decomposing composite functions", "Product of functions", "Sum of functions"], """
Fonksiyon, bir "makinedir" — içine bir girdi ($x$) atarsın, o girdiyi belirli
bir kurala göre işler ve tek bir çıktı ($f(x)$) verir. Bileşke fonksiyon ise
bu makinelerden birinin çıktısını diğerinin girdisi yapmaktır: $f(g(x))$.

Nedir?
$f(g(x))$ ifadesinde önce $g$ makinesi çalışır, çıktısı $f$ makinesine
girdi olarak verilir. Bu bileşke ifadenin tanım kümesi, hem $g(x)$'in tanımlı
olduğu HEM DE $g(x)$'in çıktısının $f$'i tanımsız yapmadığı tüm $x$
değerlerinden oluşur — iki güvenlik testinden birden geçmesi gerekir.

Ne İçin Kullanılır?
1. Matematiksel Güvenlik Zinciri Kurmak
Çok aşamalı hesaplamalarda sıfıra bölünme veya negatifin karekökü gibi
"krizlerin" çıkmasını, tanım kümesini önceden bilerek engeller.
2. Yazılım ve Algoritmalarda Çökmeleri Önlemek
Bir fonksiyonun çıktısı başka bir fonksiyona girdi olarak aktarıldığında
(örn. koordinat → görünürlük oranı), tanım kümesi ihlali `NaN` veya
`Division by Zero` hatasına yol açabilir; bunu koda yazmadan önce tespit
etmeyi sağlar.
3. Gerçek Sistemleri Modellemek
Vergi dilimi → net maaş → harcanabilir gelir gibi art arda işleyen gerçek
hayat süreçleri bileşke fonksiyonlarla modellenir.

📜 Tarih ve Biyografi
Modern $f(x)$ fonksiyon gösterimi, İsviçreli matematikçi Leonhard Euler
tarafından 1734'te tanıtıldı. Fonksiyon kavramının kendisi ise Gottfried
Wilhelm Leibniz'in 17. yüzyıl sonu çalışmalarına, "bir değişkenin başka bir
değişkene bağımlılığı" fikrine dayanır.
""")

_add("Algebra", ["Inverse functions", "Finding a function from its inverse",
                                  "One-to-one functions and the Horizontal Line Test", "Inverse operations"], """
Ters fonksiyon, bir işlemi "geri sarmaktır" — bir fonksiyon seni A'dan B'ye
götürüyorsa, tersi seni B'den tam olarak A'ya geri getirir: ayakkabı giymenin
tersi ayakkabıyı çıkarmaktır.

Nedir?
$f^{-1}(x)$, $f(f^{-1}(x)) = x$ olacak şekilde tanımlanır. Bir fonksiyonun
tersinin de bir fonksiyon olabilmesi için orijinalin "bire bir" olması
gerekir — bunu Yatay Çizgi Testi ile kontrol ederiz.

Ne İçin Kullanılır?
1. Denklem Çözmenin Temeli
Bir denklemi çözmek genellikle bir fonksiyonun tersini bulmaktır: $2x=6$'yı
çözmek, "2 ile çarpma" işleminin tersi olan "2'ye bölmeyi" uygulamaktır.
2. Şifreleme ve Kod Çözme
Bir mesajı şifrelemek bir fonksiyon uygulamaksa, şifreyi çözmek onun
tersini uygulamaktır — kriptografinin temel mantığı budur.
3. Birim Dönüşümleri
Fahrenheit'tan Celsius'a çevirme fonksiyonunun tersi, Celsius'tan
Fahrenheit'a çevirir.

📜 Tarih ve Biyografi
Ters fonksiyon kavramı, 18. yüzyılda Euler'in fonksiyon teorisini
sistemleştirmesiyle birlikte gelişti; logaritma ile üstel fonksiyonun
birbirinin tersi olduğunun anlaşılması (John Napier'in 1614'teki logaritma
çalışmasının ardından) bu fikrin en etkili erken uygulamasıydı.
""")

_add("Algebra", ["What is a logarithm", "Laws of logarithms", "Evaluating logs",
                                  "Change of base", "The general log rule", "Solving logarithmic equations",
                                  "Laws of natural logs", "Graphing log functions"], """
Logaritma, üs almanın tersini soran bir sorudur — $2^x=8$ denkleminde
"kaçıncı kuvvet 8 eder?" sorusunun cevabı $\\log_2 8 = 3$'tür.

Nedir?
$\\log_b(x) = y$ ifadesi $b^y = x$ demektir. Logaritma kuralları
($\\log(ab)=\\log a+\\log b$ gibi) çarpmayı toplamaya, bölmeyi çıkarmaya
çevirerek büyük sayılarla işlemi kolaylaştırır.

Ne İçin Kullanılır?
1. Üstel Büyüme/Azalmayı Çözmek
Nüfus artışı, radyoaktif bozunma, bileşik faiz gibi $b^x = a$ biçimindeki
her denklem logaritma ile çözülür.
2. Büyük Ölçek Farklarını Ölçmek
Deprem şiddeti (Richter), ses şiddeti (desibel) ve pH ölçeği, logaritmik
skalalardır — çünkü doğal büyüklükler arasındaki fark trilyonlarca kat olabilir.
3. Bilgisayar Biliminde Algoritma Hızı
İkili arama gibi "böl ve yönet" algoritmalarının hızı $\\log n$ ile ifade edilir.

📜 Tarih ve Biyografi
Logaritma, İskoç matematikçi John Napier tarafından 1614'te "Mirifici
Logarithmorum Canonis Descriptio" adlı eserinde, çarpma işlemlerini
toplamaya indirgeyerek gökbilimcilerin elle yaptığı devasa hesapları
kolaylaştırmak amacıyla icat edildi. Doğal logaritmanın tabanı $e$ ise
adını İsviçreli matematikçi Leonhard Euler'den alır.
""")

_add("Algebra", ["Quadratic formula", "Coefficients in quadratics", "Quadratic polynomials",
                                  "Quadratic inequalities"], """
İkinci derece denklem çözümü, "parabolün sıfırı nerede kesiyor?" sorusuna
genel bir cevaptır — hangi sayılar verilirse verilsin, formül her zaman
işler.

Nedir?
$ax^2+bx+c=0$ denkleminin kökleri
$x = \\dfrac{-b \\pm \\sqrt{b^2-4ac}}{2a}$ formülüyle bulunur. Kök içindeki
$b^2-4ac$ (diskriminant), kaç ve ne tür kök olduğunu (gerçek/karmaşık)
belirler.

Ne İçin Kullanılır?
1. Fizikte Hareket Problemleri
Bir cismin ne zaman yere düşeceği, atış hareketinde menzil gibi birçok
fizik problemi ikinci derece denklemle modellenir.
2. Optimizasyon Problemleri
Bir işletmenin kârını maksimize eden fiyatı bulmak gibi "en iyi değer"
problemleri genellikle parabolün tepe noktasına iner.

📜 Tarih ve Biyografi
İkinci derece denklemleri çözme yöntemleri MÖ 2000 civarında Babillilere
kadar uzanır; genel geometrik/sözel çözüm ise Fars matematikçi
el-Harezmi'nin (Al-Khwarizmi) 820 yılında yazdığı "el-Cebr" adlı eserde
sistemleştirildi — "cebir" (algebra) kelimesi bu eserin adından gelir.
Bugünkü sembolik formül, 16-17. yüzyılda François Viète ve René Descartes'ın
sembolik cebir çalışmalarıyla şekillendi.
""")

_add("Algebra", ["Imaginary and complex numbers"], """
Karmaşık sayılar, "negatifin karekökü yoktur" duvarını yıkan bir buluştur —
matematikçiler bu duvarın ardında yepyeni, tutarlı bir sayı sistemi keşfetti.

Nedir?
$i = \\sqrt{-1}$ tanımlanır ve karmaşık sayı $a+bi$ biçiminde yazılır ($a$
gerçek, $b$ sanal kısım). Bu sayılar toplama, çarpma gibi işlemler altında
tutarlı bir cebir oluşturur.

Ne İçin Kullanılır?
1. Elektrik Mühendisliğinde Alternatif Akım
AC devre analizinde gerilim ve akımın faz farkı karmaşık sayılarla ifade
edilir — bu alan olmadan modern elektronik tasarlanamazdı.
2. Sinyal İşleme ve Ses/Görüntü Sıkıştırma
Fourier dönüşümü (MP3, JPEG'in temeli) karmaşık sayılar üzerine kuruludur.
3. Kuantum Mekaniği
Kuantum durumları doğası gereği karmaşık sayılarla tanımlanır.

📜 Tarih ve Biyografi
Karmaşık sayılarla ilk karşılaşma, İtalyan matematikçi Gerolamo Cardano'nun
1545'teki kübik denklem çalışmalarına dayanır; ancak sistemli işlem
kurallarını Rafael Bombelli 1572'de verdi. "Sanal" (imaginary) adını alaycı
bir tavırla René Descartes 1637'de koydu; $i$ sembolünü Leonhard Euler
1777'de tanıttı ve "karmaşık sayı" terimini Carl Friedrich Gauss 1831'de
yaygınlaştırdı.
""")

_add("Algebra", ["Slope", "Point-slope and slope-intercept forms of a line",
                                  "Parallel and perpendicular lines", "Distance between two points"], """
Eğim, bir doğrunun "ne kadar dik tırmandığını" ölçer — bir rampanın
sertliğini, bir yolun eğimini sayıyla ifade eder.

Nedir?
$m = \\dfrac{y_2-y_1}{x_2-x_1}$, iki nokta arasındaki dikey değişimin yatay
değişime oranıdır. Paralel doğrular aynı eğime, dik doğrular ise çarpımları
$-1$ olan eğimlere sahiptir.

Ne İçin Kullanılır?
1. Doğrusal İlişkileri Modellemek
Sabit hızla giden bir aracın mesafe-zaman grafiği, sabit ücretli bir
aboneliğin maliyet grafiği gibi "sabit oranlı" her ilişki eğimle ifade
edilir.
2. Mühendislik ve İnşaatta Eğim Standartları
Rampa, çatı, yol eğimi hesaplarının hepsi bu orana dayanır.

📜 Tarih ve Biyografi
Eğim kavramı, Descartes ve Pierre de Fermat'nın 17. yüzyılda geliştirdiği
analitik geometrinin doğal bir sonucudur; doğrunun $y=mx+b$ biçimindeki
modern gösterimi 19. yüzyılda ders kitaplarında yaygınlaştı.
""")

_add("Algebra", ["Distributive Property", "Associative Property", "Commutative Property",
                                  "Distributive Property with fractions"], """
Bu üç özellik, cebirin "trafik kurallarıdır" — sayıları hangi sırayla
gruplayıp çarpabileceğini garanti altına alır, böylece $2\\times(3+4)$'ü
güvenle $2\\times3+2\\times4$'e açabilirsin.

Nedir?
Değişme (Commutative): $a+b=b+a$. Birleşme (Associative): $(a+b)+c=a+(b+c)$.
Dağılma (Distributive): $a(b+c)=ab+ac$. Bunlar toplama ve çarpmanın temel
davranış kurallarıdır.

Ne İçin Kullanılır?
1. Cebirsel İfadeleri Sadeleştirmek
Parantez açma, ortak parantez çıkarma gibi her cebirsel manipülasyon bu üç
kurala dayanır.
2. Zihinden Hesaplama Kısayolları
$7\\times 102$'yi $7\\times100+7\\times2$ olarak hızlıca hesaplamak dağılma
özelliğinin günlük hayattaki hâlidir.

📜 Tarih ve Biyografi
Bu özellikler ilkel/örtük biçimde binlerce yıldır kullanılsa da resmî
adlarını 19. yüzyılda aldılar: "distributive" terimi Fransız matematikçi
François Servois tarafından 1814'te; "commutative" terimi İrlandalı
matematikçi William Rowan Hamilton tarafından 1843'te tanıtıldı.
""")

_add("Algebra", ["Solving systems three ways", "Solving systems with elimination",
                                  "Solving systems with substitution", "Systems of linear inequalities",
                                  "Systems with non-linear equations"], """
Denklem sistemi, birden fazla koşulu AYNI ANDA sağlayan noktayı arar —
"iki doğru nerede kesişir?" sorusunun cebirsel karşılığıdır.

Nedir?
İki (veya daha fazla) denklemi aynı anda sağlayan $(x,y)$ değerlerini
bulmaktır. Yerine koyma (substitution), yok etme (elimination) ve grafik
yöntemi, aynı çözüme farklı yollardan ulaşır.

Ne İçin Kullanılır?
1. Kısıtlı Kaynak Problemleri
"İki ürün, sınırlı bütçe ve sınırlı zamanla en kârlı üretim planı nedir?"
gibi işletme problemleri denklem sistemleriyle çözülür.
2. Karışım ve Hız Problemleri
İki farklı konsantrasyondaki karışımı belirli bir orana getirmek veya iki
aracın ne zaman buluşacağını bulmak sistem kurmayı gerektirir.

📜 Tarih ve Biyografi
Sistematik yok etme (elimination) yöntemi, MÖ 200 civarına tarihlenen Çin
matematik klasiği "Dokuz Bölüm" (Jiuzhang Suanshu) içinde "fangcheng"
adıyla zaten kullanılıyordu — bugün okulda öğretilen yönteme çok benzer bir
matris temelli teknikti.
""")

# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------
_add("Geometry", ["Pythagorean Theorem", "Pythagorean inequalities"], """
Pisagor Teoremi, dik üçgenin kenarları arasındaki en ünlü ilişkidir — bir
merdiveni duvara nasıl güvenle dayayacağını, bir TV ekranının köşegenini
bulmanı sağlar.

Nedir?
Dik açılı bir üçgende, dik kenarların karelerinin toplamı hipotenüsün
karesine eşittir: $a^2+b^2=c^2$.

Ne İçin Kullanılır?
1. Mesafe Hesaplamak
Koordinat düzleminde iki nokta arası mesafe formülü doğrudan bu teoremden
türetilir — GPS, harita yazılımları bunu kullanır.
2. İnşaat ve Marangozlukta "Dik Açı" Kontrolü
3-4-5 üçgeni kullanarak bir köşenin tam dik olup olmadığı binlerce yıldır
bu teoremle kontrol edilir.
3. Bilgisayar Grafiklerinde Vektör Uzunluğu
3B oyunlarda ve grafiklerde bir vektörün büyüklüğünü hesaplamak bu
teoremin genellemesidir.

📜 Tarih ve Biyografi
Teorem, adını MÖ 570-495 yılları arasında yaşamış Yunan filozof ve
matematikçi Pisagor'dan (Pythagoras) alır; ancak ilişkinin özel durumları
Babilliler tarafından ondan çok daha önce, MÖ 1800 civarında (Plimpton 322
tableti) biliniyordu. Pisagor'un okulu bu ilişkiyi ilk kez genel olarak
ispatlayan topluluk olarak kabul edilir.
""")

_add("Geometry", ["SSS, ASA, and SAS congruence", "AAS and HL congruence", "CPCTC"], """
Eşlik (congruence) kuralları, "iki üçgenin birebir aynı olduğunu" en az
bilgiyle kanıtlamanın kısayollarıdır — her kenarı tek tek ölçmeden, sadece
birkaç ipucuyla eminlik kazanırsın.

Nedir?
SSS (kenar-kenar-kenar), SAS (kenar-açı-kenar), ASA (açı-kenar-açı), AAS ve
HL (dik üçgende hipotenüs-dik kenar), iki üçgenin eş olduğunu kanıtlamak
için yeterli minimum bilgi kombinasyonlarıdır. CPCTC ("Corresponding Parts
of Congruent Triangles are Congruent"), eşlik kanıtlandıktan SONRA
üçgenlerin karşılık gelen tüm parça ve açılarının da eş olduğunu söyler.

Ne İçin Kullanılır?
1. Geometrik İspatların Omurgası
Daha karmaşık şekil özelliklerini (paralelkenar köşegenleri, açıortaylar)
kanıtlamanın standart ilk adımıdır.
2. Ölçüm ve Mühendislikte Simetri Garantisi
Bir parçanın üretimde her seferinde birebir aynı çıktığını doğrulamanın
mantıksal temelidir.

📜 Tarih ve Biyografi
Bu eşlik kuralları, MÖ 300 civarında Yunan matematikçi Euclid'in
"Elementler" adlı eserinin I. Kitabı'nda sistematik olarak kanıtlanmıştır —
Batı matematiğinin en eski ve en etkili aksiyomatik yapılarından biridir.
""")

_add("Geometry", ["Similar triangles", "Triangle similarity theorems",
                                  "Triangle Side-Splitting Theorem"], """
Benzerlik, "aynı şekil ama farklı boyut" fikridir — bir haritanın gerçek
dünyayla, küçük bir maketin gerçek binayla ilişkisi benzerliktir.

Nedir?
İki üçgen, karşılık gelen açıları eşit ve kenarları orantılıysa benzerdir.
AA (açı-açı) tek başına benzerliği kanıtlamaya yeter, çünkü üçüncü açı
otomatik eşit olur.

Ne İçin Kullanılır?
1. Ulaşılamayan Mesafeleri Ölçmek
Bir ağacın gölgesiyle boyunu, bir nehrin karşı kıyısına olan mesafeyi
ölçmek benzer üçgenlerle yapılır — haritacılığın temel yöntemidir.
2. Ölçekleme ve Model Tasarımı
Mimari maketler, harita ölçekleri, kamera perspektifi hep benzerlik
oranlarıyla çalışır.

📜 Tarih ve Biyografi
Benzer üçgenlerle yükseklik ölçme yönteminin ilk kaydı, MÖ 600 civarında
Yunan filozof Thales'e atfedilir — rivayete göre Mısır'da bir piramidin
yüksekliğini, kendi gölgesiyle piramidin gölgesini karşılaştırarak ölçmüştür.
Euclid bu fikri MÖ 300'de aksiyomatik olarak kanıtladı.
""")

_add("Geometry", ["Area of a circle", "Circumference of a circle", "Arc length",
                                  "Degree measure of an arc"], """
Çember, sonsuz kenarlı bir çokgen gibi düşünülebilir — alan ve çevre
formülleri, bu "sonsuz küçük dilimlere bölme" fikrinin ürünüdür.

Nedir?
Çevre $C=2\\pi r$, alan $A=\\pi r^2$'dir; burada $\\pi \\approx 3.14159$,
herhangi bir çemberin çevresinin çapına oranıdır (sabittir).

Ne İçin Kullanılır?
1. Mühendislikte Dairesel Parça Tasarımı
Boru, dişli, teker gibi dairesel her parçanın malzeme/hacim hesabı bu
formüllere dayanır.
2. Astronomi ve Navigasyonda
Gezegen yörüngeleri, Dünya'nın çevresi (ilk kez Eratosthenes tarafından
tahmin edilmiştir) bu formüllerle hesaplanır.

📜 Tarih ve Biyografi
$\\pi$'nin ilk titiz matematiksel yaklaşımı, MÖ 250 civarında Yunan
matematikçi Arşimet (Archimedes) tarafından, çembere iç ve dış açılı
çokgenler çizerek yapılmıştır — bu yöntemle $\\pi$'yi $223/71$ ile $22/7$
arasında olduğunu kanıtlamıştır.
""")

_add("Geometry", ["Nets, surface area, and volume of spheres", "Surface area and volume of spheres",
                                  "Nets, surface area, and volume of cylinders", "Nets, surface area, and volume of cones",
                                  "Nets, surface area, and volume of prisms", "Nets, surface area, and volume of pyramids",
                                  "Surface area to volume ratio of prisms"], """
Yüzey alanı ve hacim, bir cismin "dışını kaplamak" için gereken malzemeyle
"içini doldurmak" için gereken miktarı ayırt eder — bir hediye paketinin
kağıdı (yüzey alanı) ile içindeki hediyenin büyüklüğü (hacim) gibi.

Nedir?
Her katı cismin (prizma, silindir, koni, piramit, küre) kendine özgü
alan/hacim formülü vardır; örneğin kürenin hacmi $V=\\frac{4}{3}\\pi r^3$,
yüzey alanı $A=4\\pi r^2$'dir.

Ne İçin Kullanılır?
1. Üretim ve Ambalaj Mühendisliği
Bir kutunun ne kadar karton, bir tankın ne kadar boya gerektirdiği yüzey
alanından; ne kadar sıvı/gaz alacağı hacimden hesaplanır.
2. Biyolojide Ölçek Etkisi
Yüzey/hacim oranı, hücrelerin neden belirli bir boyuttan büyüyemediğini
(ısı/madde alışverişi yüzeyle, ihtiyaç hacimle orantılı büyür) açıklar.

📜 Tarih ve Biyografi
Kürenin hacim ve yüzey alanı formüllerinin kanıtı, Arşimet'in en gurur
duyduğu başarısıydı (MÖ 3. yüzyıl); rivayete göre mezar taşına, içine
tam oturan bir silindirle birlikte bir küre çizilmesini vasiyet etmiştir —
çünkü kürenin hacim ve yüzey alanının çevreleyen silindirin $2/3$'ü
olduğunu kanıtlamıştı.
""")

_add("Geometry", ["Translating figures in coordinate space", "Rotating figures in coordinate space",
                                  "Reflecting figures in coordinate space", "Translation vectors",
                                  "Dilations and scale factors"], """
Geometrik dönüşümler, bir şekli "hareket ettirmenin" dört temel yoludur:
kaydırma (translation), döndürme (rotation), yansıtma (reflection) ve
ölçekleme (dilation) — animasyon ve oyun motorlarının temel dili budur.

Nedir?
Öteleme bir şekli kaydırır (boyut/açı değişmez), döndürme bir nokta
etrafında çevirir, yansıtma bir eksene göre ayna görüntüsünü alır, ölçekleme
ise büyütür/küçültür. İlk üçü şeklin boyutunu korur (izometri), ölçekleme
korumaz.

Ne İçin Kullanılır?
1. Bilgisayar Grafikleri ve Oyun Geliştirme
Bir karakterin ekranda hareket etmesi, dönmesi, büyümesi bu dönüşümlerin
matris hesaplarıyla gerçek zamanlı uygulanmasıdır.
2. Robotikte Konum ve Yönelim
Bir robot kolunun bir nesneyi doğru açıyla kavraması bu dönüşümlerin
zincirlenmesiyle hesaplanır.

📜 Tarih ve Biyografi
Geometriyi "dönüşümler altında korunan özellikler" olarak yeniden
tanımlayan yaklaşım, Alman matematikçi Felix Klein'ın 1872'deki ünlü
"Erlangen Programı" ile matematiğe kazandırıldı ve modern geometri
anlayışını kökten değiştirdi.
""")

# ---------------------------------------------------------------------------
# Linear Algebra
# ---------------------------------------------------------------------------
_add("Linear Algebra", ["Matrix multiplication", "Matrix addition and subtraction",
                                        "Matrix dimensions and entries", "Identity matrices",
                                        "Multiplying matrices by vectors"], """
Matris, sayıları bir ızgara hâlinde düzenleyip TEK bir nesne gibi işleme
sokmanın yoludur — bir denklem sistemini, bir resmin piksellerini veya bir
3B dönüşümü kompakt biçimde taşır.

Nedir?
$m \\times n$ boyutlu bir matris, satır ve sütunlara dizilmiş sayılardan
oluşur. Matris çarpımı $A \\times B$, sıradan çarpmadan farklıdır: $A$'nın
satırlarıyla $B$'nin sütunlarının "nokta çarpımı" alınır ve genelde
$AB \\neq BA$'dır.

Ne İçin Kullanılır?
1. Bilgisayar Grafikleri ve 3B Oyunlar
Bir nesnenin döndürülmesi, ölçeklenmesi, ekrana yansıtılması hep matris
çarpımlarıyla yapılır — her karede binlerce kez.
2. Yapay Zekâ ve Makine Öğrenmesi
Sinir ağlarındaki her katman, girdiyi bir ağırlık matrisiyle çarpar; derin
öğrenmenin hesaplama yükünün büyük kısmı matris çarpımıdır.
3. Denklem Sistemlerini Kompakt Çözmek
Yüzlerce bilinmeyenli sistemler $Ax=b$ biçiminde tek satırda ifade edilip
bilgisayarla hızlıca çözülür.

📜 Tarih ve Biyografi
"Matris" terimi İngiliz matematikçi James Joseph Sylvester tarafından
1850'de ortaya atıldı. Matrislerin cebirsel bir sistem (toplama, çarpma
kurallarıyla) olarak sistemli incelenmesi ise arkadaşı Arthur Cayley'nin
1858 tarihli "A Memoir on the Theory of Matrices" adlı çalışmasıyla
başladı.
""")

_add("Linear Algebra", ["Determinants", "Modifying determinants",
                                        "Using determinants to find area", "Transposes and their determinants"], """
Determinant, bir matrisin "büyütme/küçültme gücünü" tek bir sayıya
sığdırır — bir dönüşümün bir alanı ya da hacmi kaç kat değiştirdiğini
(ve yönünü tersine çevirip çevirmediğini) söyler.

Nedir?
$2\\times2$ bir matris için $\\det[[a, b], [c, d]]=ad-bc$.
Determinant sıfırsa, matrisin tersi yoktur — dönüşüm bilgiyi "düzleştirip"
kaybeder.

Ne İçin Kullanılır?
1. Bir Sistemin Çözülüp Çözülemeyeceğini Anlamak
Determinant sıfır değilse, $Ax=b$ sisteminin tek bir çözümü olduğu
garanti edilir (Cramer Kuralı bu mantıkla çalışır).
2. Alan ve Hacim Hesabı
İki vektörün oluşturduğu paralelkenarın alanı, üç vektörün oluşturduğu
paralelyüzün hacmi doğrudan determinantla bulunur.

📜 Tarih ve Biyografi
Determinant fikri, matrislerden ÖNCE ortaya çıktı: Japon matematikçi Seki
Takakazu 1683'te ve Alman filozof-matematikçi Gottfried Leibniz 1693'te
birbirinden bağımsız olarak denklem sistemlerini çözmek için kullandılar.
İsviçreli matematikçi Gabriel Cramer, 1750'de bugün "Cramer Kuralı" olarak
bilinen çözüm yöntemini yayımladı.
""")

_add("Linear Algebra", ["Gauss-Jordan elimination", "Pivot entries and row-echelon forms",
                                        "Simple row operations", "Solving Ax=b", "Number of solutions to the linear system"], """
Gauss-Jordan yok etme, bir denklem sistemini adım adım en sade hâline
"süzme" yöntemidir — karmaşık bir sistemi, çözümü doğrudan okunabilecek bir
forma indirger.

Nedir?
Bir matrise satır işlemleri (satır değiştirme, bir satırı sabitle çarpma,
bir satırı diğerine ekleme) uygulayarak onu indirgenmiş satır-eşelon
forma getirmektir; bu formda çözüm doğrudan görülür.

Ne İçin Kullanılır?
1. Büyük Denklem Sistemlerini Bilgisayarla Çözmek
Mühendislik simülasyonlarında binlerce bilinmeyenli sistemler bu yöntemin
bilgisayar uyarlamalarıyla çözülür.
2. Matrisin Tersini Bulmak
Bir matrisin tersi, aynı satır işlemlerini birim matrise uygulayarak
bulunur.

📜 Tarih ve Biyografi
Yöntemin özü, MÖ 200 civarındaki Çin matematik klasiği "Dokuz Bölüm"de
zaten vardı. Batı'daki adını, 19. yüzyılda gezegen yörüngesi hesaplarında
bu tekniği kullanan Alman matematikçi Carl Friedrich Gauss'tan alır;
"Jordan" kısmı ise yöntemi 1888'de daha da sistematikleştiren Alman
jeodezist Wilhelm Jordan'a atıfla eklenmiştir.
""")

_add("Linear Algebra", ["Eigenvalues, eigenvectors, eigenspaces", "Eigen in three dimensions"], """
Özdeğer/özvektör, bir dönüşümün "değişmeyen yönlerini" bulur — bir matris
çoğu vektörü döndürüp uzatırken, bazı özel vektörleri sadece UZATIR,
yönlerini hiç değiştirmez; işte bu özel vektörler özvektördür.

Nedir?
$Av = \\lambda v$ denklemini sağlayan sıfırdan farklı $v$ vektörüne
özvektör, $\\lambda$ katsayısına ise özdeğer denir — matrisin $v$ yönünü
değiştirmeden onu $\\lambda$ kat büyüttüğünü/küçülttüğünü gösterir.

Ne İçin Kullanılır?
1. Google'ın Arama Algoritması (PageRank)
İnternetin devasa bağlantı matrisinin en büyük özvektörü, web sayfalarının
önem sıralamasını verir.
2. Titreşim ve Yapı Mühendisliği
Bir köprünün veya binanın doğal titreşim frekansları, yapının matrisinin
özdeğerleridir — depreme dayanıklı tasarımda kritik rol oynar.
3. Veri Sıkıştırma ve Yüz Tanıma
Temel Bileşen Analizi (PCA), verinin en önemli yönlerini bulmak için
özvektörleri kullanır; "eigenfaces" yüz tanıma yöntemi buna dayanır.

📜 Tarih ve Biyografi
Kavramın kökleri, Fransız matematikçi Augustin-Louis Cauchy'nin 1826'daki
kuadratik form çalışmalarına dayanır. "Eigen" (Almanca "kendine özgü/
karakteristik") terimini İngilizce matematik literatürüne kazandıran ise
Alman matematikçi David Hilbert'tir (1904).
""")

_add("Linear Algebra", ["Vectors", "Vector operations", "Unit vectors and basis vectors",
                                        "Scalar multiplication"], """
Vektör, hem "ne kadar" hem "hangi yöne" sorularının cevabını tek bir
nesnede taşır — bir rüzgârın hızını söylemek için sadece "30 km/s" yetmez,
"kuzeyden 30 km/s" demen gerekir; işte bu bir vektördür.

Nedir?
Vektör, büyüklüğü ve yönü olan bir niceliktir; genelde bir ok veya
$(x, y, z)$ bileşenleriyle gösterilir. Vektörler toplanabilir, bir
sayıyla (skaler) çarpılabilir.

Ne İçin Kullanılır?
1. Fizikte Kuvvet ve Hareket
Kuvvet, hız, ivme gibi tüm "yönlü" fiziksel nicelikler vektörlerle
ifade edilir; bir uçağın rüzgâra karşı gerçek rotası vektör toplamıyla
bulunur.
2. Bilgisayar Grafikleri ve Oyun Fiziği
Bir karakterin hareketi, ışık yönü, kamera açısı — hepsi vektör
işlemleriyle hesaplanır.
3. Makine Öğrenmesinde Veri Temsili
Bir kelime, bir resim veya bir kullanıcı profili genellikle çok boyutlu
bir vektör olarak temsil edilir ("word embeddings" gibi).

📜 Tarih ve Biyografi
Modern vektör kavramının öncüsü, İrlandalı matematikçi William Rowan
Hamilton'ın 1843'te bulduğu kuaterniyonlardır. Bugün kullandığımız $i, j,
k$ bileşenli, üç boyutlu vektör cebiri ise Amerikalı fizikçi Josiah
Willard Gibbs ve İngiliz mühendis Oliver Heaviside tarafından 1880'lerde,
birbirinden bağımsız olarak sadeleştirildi.
""")

_add("Linear Algebra", ["Dot products", "Cross products", "Dot and cross products as opposite ideas",
                                        "Angle between vectors"], """
Nokta çarpım "ne kadar aynı yöndeler?" sorusunu, çapraz çarpım ise
"ikisine birden dik olan yön nedir?" sorusunu cevaplar.

Nedir?
Nokta çarpım $u \\cdot v = |u||v|\\cos\\theta$ bir SAYI verir (iki vektörün
ne kadar hizalı olduğunu ölçer). Çapraz çarpım $u \\times v$ ise her iki
vektöre de dik yeni bir VEKTÖR verir; büyüklüğü aralarındaki paralelkenarın
alanına eşittir.

Ne İçin Kullanılır?
1. Işıklandırma ve 3B Grafikler
Bir yüzeyin ışığa ne kadar döndüğü (parlaklık) nokta çarpımla, bir
yüzeyin normal (dik) vektörü çapraz çarpımla bulunur — her 3B oyun bunu
saniyede milyonlarca kez hesaplar.
2. Fizikte Tork ve Manyetik Kuvvet
Bir kuvvetin bir cismi ne kadar döndürdüğü (tork) çapraz çarpımla; yapılan
iş nokta çarpımla hesaplanır.

📜 Tarih ve Biyografi
Her iki işlem de Gibbs ve Heaviside'ın 1880'lerdeki vektör analizi
çalışmalarıyla bugünkü net biçimine kavuştu; kökleri ise Hamilton'ın
kuaterniyon cebirinin "skaler" ve "vektörel" parçalarına dayanır.
""")

_add("Linear Algebra", ["Basis", "Linear combinations and span", "Linear subspaces",
                                        "Spans as subspaces", "Linear independence in two dimensions",
                                        "Linear independence in three dimensions"], """
Baz (basis), bir uzayı inşa etmek için gereken "asgari yapı taşları"
kümesidir — tıpkı üç ana rengin (kırmızı, yeşil, mavi) karışımıyla ekrandaki
her rengin üretilebilmesi gibi, bir bazın vektörlerinin kombinasyonuyla o
uzaydaki her vektör üretilebilir.

Nedir?
Bir küme, uzayı GERER (span) ve vektörleri BİRBİRİNDEN BAĞIMSIZSA (fazlalık
yoksa) bir bazdır. Bir uzayın boyutu, bazındaki vektör sayısıdır.

Ne İçin Kullanılır?
1. Veriyi Sadeleştirmek (Boyut İndirgeme)
Yüzlerce özelliği olan bir veri kümesini birkaç "temel yöne" indirgemek
(PCA gibi yöntemler) baz değiştirme fikrine dayanır.
2. Bilgisayar Grafiklerinde Koordinat Sistemleri
Bir nesnenin kendi yerel ekseni ile dünya ekseni arasında geçiş yapmak
baz değişimidir.

📜 Tarih ve Biyografi
Vektör uzayı, span, boyut gibi kavramların soyut cebirsel temeli, Alman
matematikçi Hermann Grassmann tarafından 1844'te yayımlanan "Die lineale
Ausdehnungslehre" (Doğrusal Genişleme Kuramı) adlı, döneminde pek
anlaşılamamış ama sonradan çığır açtığı kabul edilen eserinde atıldı.
""")

_add("Linear Algebra", ["Dimensionality, nullity, and rank", "Null space of a matrix",
                                        "Null and column spaces of the transpose", "Preimage, image, and the kernel"], """
Rank (rütbe) ve nullity (çekirdek boyutu), bir matrisin "bilgiyi ne kadar
koruduğunu" ölçer — bazı dönüşümler bilgiyi kaybetmeden taşır, bazıları ise
farklı girdileri aynı çıktıya "ezer".

Nedir?
Rank, bir matrisin bağımsız satır/sütun sayısıdır (gerçekte kaç boyutu
kullandığı). Nullity, $Ax=0$'ı sağlayan çözüm uzayının boyutudur. Rank-
Nullity Teoremi, ikisinin toplamının her zaman sütun sayısına eşit
olduğunu söyler — bu, Hermann Grassmann'ın 1844'teki
$\\dim(U{+}W)=\\dim U+\\dim W-\\dim(U{\\cap}W)$ boyut formülüyle aynı ailedendir:
her ikisi de "boyutların nasıl birleştiği/kaybolduğu" sorusuna cevap verir.

Ne İçin Kullanılır?
1. Bir Sistemin Çözülebilirliğini Anlamak
Rank, bir denklem sisteminin tek, sonsuz veya hiç çözümü olmadığını
belirler.
2. Veri Sıkıştırma ve Gürültü Ayıklama
Düşük ranklı bir matris yaklaşıklaması, büyük veri kümelerini (görüntü,
öneri sistemleri) çok daha az sayıyla temsil etmeyi sağlar.

📜 Tarih ve Biyografi
Rank kavramı Alman matematikçi Georg Frobenius tarafından 1879'da titizce
tanımlandı; terimin İngilizcesi ise 1850'lerde James Joseph Sylvester
tarafından kullanılmıştı. Grassmann'ın boyut formülü ise 1844'te, matris
rank kavramından önce, soyut vektör uzayları için ortaya konmuştu.
""")

_add("Linear Algebra", ["Gram-Schmidt process for change of basis", "Orthonormal bases",
                                        "Orthogonal complements", "Projection onto the subspace",
                                        "Projection onto an orthonormal basis", "Projections as linear transformations"], """
Gram-Schmidt süreci, "eğik" bir vektör kümesini birbirine tam dik (90°) ve
birim uzunlukta temiz bir kümeye dönüştürür — dağınık bir dolabı
düzenlemeye benzer.

Nedir?
Verilen bir baza sırayla izdüşüm alıp çıkararak, aynı uzayı geren ama
birbirine dik (ortogonal) yeni bir baz üretir. İzdüşüm (projection),
bir vektörün bir başka vektör/altuzay üzerine "gölgesini düşürme"
işlemidir.

Ne İçin Kullanılır?
1. En Küçük Kareler Yöntemi (Regresyon)
Bir veri bulutuna "en iyi uyan doğruyu" bulmak, veri vektörünün bir
altuzaya izdüşümünü almaktır — istatistiksel regresyonun matematiksel
temeli budur.
2. Sinyal İşleme ve Sıkıştırma
Fourier ve dalgacık (wavelet) dönüşümleri, sinyali ortonormal bir baza
göre ayrıştırmaya dayanır.

📜 Tarih ve Biyografi
Yöntem, Danimarkalı matematikçi Jørgen Pedersen Gram'ın 1883'teki ve
Alman matematikçi Erhard Schmidt'in 1907'deki çalışmalarına dayanır ve
ikisinin adını taşır; benzer bir teknik aslında daha önce Pierre-Simon
Laplace ve Cauchy tarafından da kullanılmıştı.
""")

_add("Linear Algebra", ["Cauchy-Schwarz inequality", "Vector triangle inequality"], """
Cauchy-Schwarz eşitsizliği, iki vektörün nokta çarpımına bir "tavan"
koyar — hiçbir zaman iki vektörün uzunluklarının çarpımından büyük
olamayacağını garanti eder.

Nedir?
$|u \\cdot v| \\le |u||v|$ eşitsizliği her zaman doğrudur; eşitlik yalnızca
vektörler paralelken sağlanır. Üçgen eşitsizliği ($|u+v|\\le|u|+|v|$) bu
sonuçtan türetilir.

Ne İçin Kullanılır?
1. Olasılık ve İstatistikte Korelasyon Sınırı
İki değişken arasındaki korelasyon katsayısının neden her zaman $-1$ ile
$1$ arasında kaldığının matematiksel kanıtı bu eşitsizliğe dayanır.
2. Optimizasyon ve Makine Öğrenmesi
Birçok optimizasyon algoritmasının yakınsama garantisi bu eşitsizlik
üzerine inşa edilir.

📜 Tarih ve Biyografi
Eşitsizlik, Fransız matematikçi Augustin-Louis Cauchy tarafından 1821'de
toplamlar için; Alman matematikçi Hermann Amandus Schwarz tarafından ise
1888'de integrallere genelleştirilerek verildi — bu yüzden iki ismi birden
taşır (bazı kaynaklarda Rus matematikçi Viktor Bunyakovsky'nin 1859'daki
katkısıyla "Cauchy-Bunyakovsky-Schwarz" olarak da anılır).
""")

_add("Linear Algebra", ["Linear transformations as matrix-vector products",
                                        "Functions and transformations", "Compositions of linear transformations",
                                        "Linear transformations as rotations", "Transformation matrices and the image of the subset"], """
Doğrusal dönüşüm, uzayı "büker ama kırmadan" — doğruları doğru, orijini
orijin olarak bırakarak döndürür, uzatır veya eğriltir; her doğrusal
dönüşüm bir matrisle tam olarak temsil edilebilir.

Nedir?
$T(v) = Av$ biçimindeki bir fonksiyon, toplamayı ve skaler çarpmayı
koruyorsa (yani $T(u+v)=T(u)+T(v)$ ve $T(cv)=cT(v)$) doğrusal dönüşümdür.

Ne İçin Kullanılır?
1. Bilgisayar Grafiklerinde Nesne Dönüşümü
Bir 3B modelin döndürülmesi, ölçeklenmesi, eğiltilmesi — tamamı doğrusal
dönüşüm matrisleriyle yapılır.
2. Makine Öğrenmesinde Katmanlar
Bir sinir ağının her katmanı, temelde bir doğrusal dönüşüm (+ doğrusal
olmayan bir aktivasyon) uygular.

📜 Tarih ve Biyografi
Doğrusal dönüşüm fikrinin cebirsel temeli Grassmann'ın 1844 çalışmasına,
matris temsili ise Cayley'nin 1858'deki matris teorisine dayanır;
"dönüşümler altında değişmeyen özellikler" bakış açısı ise Felix Klein'ın
1872 Erlangen Programı'yla geometri diline kazandırıldı.
""")

# ---------------------------------------------------------------------------
# Calculus 1
# ---------------------------------------------------------------------------
_add("Calculus 1", ["Idea of the limit", "Precise definition of the limit",
                                    "One-sided limits", "Limits of combinations", "Limits of composites",
                                    "Infinite limits and vertical asymptotes", "Limits at infinity and horizontal asymptotes"], """
Limit, bir fonksiyonun bir noktaya "sonsuz derecede yaklaşırken" ne
yaptığını sorar — o noktada ne olduğuyla değil, ETRAFINDA ne olduğuyla
ilgilenir.

Nedir?
$\\lim_{x\\to a} f(x) = L$, $x$ değeri $a$'ya istediğin kadar yaklaştıkça
$f(x)$'in $L$'ye istediğin kadar yaklaştığı anlamına gelir — $x=a$'da
fonksiyonun tanımlı olup olmaması bile önemli değildir.

Ne İçin Kullanılır?
1. Kalkülüsün Tüm Temelini Kurmak
Türev ve integral, ikisi de birer limit olarak TANIMLANIR — limit
olmadan kalkülüs var olamazdı.
2. "Anlık" Değişimi Anlamlandırmak
Bir arabanın "şu an" ne kadar hızlı gittiği, sıfır uzunluktaki bir zaman
aralığının limitiyle tanımlanır.

📜 Tarih ve Biyografi
Limit fikri sezgisel olarak Newton ve Leibniz'in 17. yüzyıl kalkülüsünde
vardı, ama titiz bir tanımı yoktu. Modern epsilon-delta tanımı Fransız
matematikçi Augustin-Louis Cauchy tarafından 1821'de önerildi ve Alman
matematikçi Karl Weierstrass tarafından 1861'de bugün ders kitaplarında
kullanılan kesin biçimine kavuşturuldu.
""")

_add("Calculus 1", ["Definition of the derivative", "Average rate of change",
                                    "Position, velocity, and acceleration"], """
Türev, "anlık değişim hızını" ölçer — bir arabanın hız göstergesinin o
anki değeri, konum fonksiyonunun türevidir.

Nedir?
$f'(x) = \\lim_{h\\to 0} \\dfrac{f(x+h)-f(x)}{h}$, fonksiyonun eğrisine o
noktada çizilen teğetin eğimidir. Konumun türevi hız, hızın türevi ivmedir.

Ne İçin Kullanılır?
1. Fizikte Hareket Analizi
Bir roketin hızı ve ivmesi, konum verisinin ardışık türevleriyle
hesaplanır.
2. Optimizasyon (En İyi Değeri Bulma)
Bir kutunun en az malzemeyle en çok hacmi alması gibi "en iyi" problemleri,
türevin sıfır olduğu noktaları bularak çözülür — mühendislik ve
ekonomideki optimizasyonun temelidir.

📜 Tarih ve Biyografi
Türev kavramı, İngiliz fizikçi/matematikçi Isaac Newton (1665-1666,
"fluxion" adıyla) ve Alman filozof/matematikçi Gottfried Wilhelm Leibniz
(1675, bugün kullandığımız $dy/dx$ notasyonuyla) tarafından birbirinden
BAĞIMSIZ olarak geliştirildi — bu, matematik tarihinin en ünlü öncelik
tartışmalarından birine yol açtı.
""")

_add("Calculus 1", ["Power rule", "Product rule with two functions", "Quotient rule",
                                    "Chain rule with power rule", "Power rule for fractional powers",
                                    "Power rule for negative powers"], """
Türev kuralları (kuvvet, çarpım, bölüm, zincir), her türev problemini
sıfırdan limit hesaplamak yerine, hazır "tarifler" kullanarak hızla
çözmeni sağlar.

Nedir?
Kuvvet kuralı: $\\frac{d}{dx}x^n = nx^{n-1}$. Çarpım kuralı:
$(fg)'=f'g+fg'$. Bölüm kuralı: $(f/g)' = (f'g-fg')/g^2$. Zincir kuralı:
$(f(g(x)))' = f'(g(x))\\cdot g'(x)$ — iç içe geçmiş fonksiyonların türevini
alır.

Ne İçin Kullanılır?
1. Karmaşık Fonksiyonları Hızlıca Türetmek
Gerçek dünyadaki hemen her formül (fizik, ekonomi, mühendislik) bu dört
kuralın bir kombinasyonuyla türetilir.
2. Makine Öğrenmesinde Geri Yayılım (Backpropagation)
Yapay sinir ağlarının "öğrenmesi", zincir kuralının binlerce kez ardışık
uygulanmasıyla çalışır.

📜 Tarih ve Biyografi
Bu kurallar, Newton ve Leibniz'in temellerinin ardından 18. yüzyılda
İsviçreli matematikçi Leonhard Euler ve Fransız matematikçi Joseph-Louis
Lagrange tarafından sistemli bir hesap diline (kalkülüs) dönüştürüldü.
""")

_add("Calculus 1", ["L'Hospital's Rule"], """
L'Hôpital Kuralı, "0/0" gibi belirsiz görünen limitleri çözmek için bir
kısayoldur — pay ve payda ayrı ayrı türetilerek limit yeniden denenir.

Nedir?
Eğer $\\lim f(x)/g(x)$ ifadesi $0/0$ veya $\\infty/\\infty$ belirsizliğine
yol açıyorsa, $\\lim f(x)/g(x) = \\lim f'(x)/g'(x)$ olur (limit varsa).

Ne İçin Kullanılır?
1. Belirsiz Limitleri Hızla Çözmek
Cebirsel manipülasyonla (çarpanlara ayırma, sadeleştirme) saatler
sürebilecek limitleri saniyeler içinde çözer.
2. Büyüme Oranlarını Karşılaştırmak
Üstel fonksiyonların polinomlardan, polinomların logaritmalardan
"sonsuzda" ne kadar hızlı büyüdüğünü kanıtlamada kullanılır.

📜 Tarih ve Biyografi
Kural, Fransız asilzade Guillaume de l'Hôpital'in 1696'da yayımladığı
ilk kalkülüs ders kitabında yer alır — ancak matematik tarihinin en
ünlü "yanlış atıf" vakalarından biridir: kuralı aslında İsviçreli
matematikçi Johann Bernoulli bulmuş ve bir anlaşma karşılığında
l'Hôpital'e özel ders notları olarak satmıştır.
""")

_add("Calculus 1", ["Mean Value Theorem", "Rolle's Theorem"], """
Ortalama Değer Teoremi, "bir noktada gerçek anlık hız, ortalama hıza
tam eşit olmalıdır" der — bir yolculukta ortalama 80 km/s gittiysen,
yolun bir noktasında hızın TAM OLARAK 80 km/s olmuş olmalıdır.

Nedir?
Sürekli ve türevlenebilir bir $f$ için $[a,b]$ aralığında öyle bir $c$
noktası vardır ki $f'(c) = \\dfrac{f(b)-f(a)}{b-a}$. Rolle Teoremi,
$f(a)=f(b)$ özel durumunda $f'(c)=0$ olduğunu söyleyen özel hâlidir.

Ne İçin Kullanılır?
1. Hız Sınırı İhlallerini Kanıtlamak
Bir aracın ortalama hızı sınırı aştıysa, yolun bir noktasında ANLIK hızın
da sınırı aştığı bu teoremle matematiksel olarak kanıtlanabilir.
2. Diğer Kalkülüs Teoremlerinin Temeli
Fonksiyonların artan/azalan olduğunu kanıtlamak, integral hesabının
Ortalama Değer Teoremi gibi ileri sonuçlar bu teoreme dayanır.

📜 Tarih ve Biyografi
Rolle Teoremi, Fransız matematikçi Michel Rolle tarafından 1691'de
(ironik biçimde, kalkülüse başlangıçta şüpheyle yaklaşan biri olarak)
kanıtlandı. Genel Ortalama Değer Teoremi ise İtalyan-Fransız matematikçi
Joseph-Louis Lagrange tarafından 1797'de verildi.
""")

_add("Calculus 1", ["Intermediate Value Theorem with an interval",
                                    "Intermediate Value Theorem without an interval", "Estimating a root"], """
Ara Değer Teoremi, "eğer bir çizgiyi kalemi kaldırmadan çizersen, aradaki
her yüksekliğe en az bir kez uğramış olursun" sezgisini matematikselleştirir.

Nedir?
$f$ sürekli ve $f(a) < N < f(b)$ ise, $(a,b)$ aralığında $f(c)=N$ olan en
az bir $c$ vardır. En yaygın kullanımı, işareti $a$'da negatif $b$'de
pozitif olan bir fonksiyonun arada mutlaka bir kökü olduğunu garanti
etmektir.

Ne İçin Kullanılır?
1. Denklemlerin Kökünü Garanti Etmek ve Bulmak
Cebirsel olarak çözülemeyen denklemlerin bir kökü olduğunu kanıtlamak ve
"ikiye bölme yöntemi" gibi sayısal yöntemlerle o kökü daraltmak için
kullanılır.
2. Mühendislik Simülasyonlarında Kök Bulma
Bilgisayarların karmaşık denklemleri sayısal olarak çözmesinin
teorik güvencesidir.

📜 Tarih ve Biyografi
Teoremin ilk titiz kanıtı, Çek matematikçi Bernard Bolzano tarafından
1817'de verildi — Bolzano, o dönem matematikte sezgiye dayanan birçok
"aşikâr" fikri titizlikle kanıtlamaya çalışan öncülerden biriydi.
""")

_add("Calculus 1", ["Newton's Method"], """
Newton Yöntemi, bir denklemin kökünü "tahmin et, düzelt, tekrarla"
mantığıyla adım adım yaklaşarak bulur — GPS'in konumunu sürekli
düzelterek doğru konuma yakınsaması gibi.

Nedir?
Bir tahminden ($x_n$) başlayarak $x_{n+1} = x_n - \\dfrac{f(x_n)}{f'(x_n)}$
formülüyle her adımda gerçek köke çok daha yakın yeni bir tahmin üretir.

Ne İçin Kullanılır?
1. Elle Çözülemeyen Denklemleri Bilgisayarla Çözmek
Kapalı formda çözümü olmayan denklemlerin (örn. $\\cos x = x$) kökünü
bulmanın standart yoludur; hesap makineleri ve mühendislik yazılımları
bunu kullanır.
2. Optimizasyon Algoritmalarının Temeli
Makine öğrenmesindeki birçok "en iyi ayarı bulma" algoritması bu
yöntemin bir türevidir.

📜 Tarih ve Biyografi
Yöntemin temel fikri Isaac Newton tarafından 1669'da geliştirildi, ancak
günümüzde kullanılan türev tabanlı yinelemeli biçim İngiliz matematikçi
Joseph Raphson tarafından 1690'da verildi — bu yüzden yöntem literatürde
sık sık "Newton-Raphson Yöntemi" olarak da anılır.
""")

# ---------------------------------------------------------------------------
# Calculus 2
# ---------------------------------------------------------------------------
_add("Calculus 2", ["Part 1 of the Fundamental Theorem of Calculus",
                                    "Part 2 of the Fundamental Theorem of Calculus", "Definite integrals",
                                    "Indefinite integrals", "Computing indefinite integrals",
                                    "Estimating definite integrals", "Estimating indefinite integrals"], """
Kalkülüsün Temel Teoremi, türev ve integralin birbirinin TERS işlemi
olduğunu söyler — bu, kalkülüsün belki de en şaşırtıcı ve en güçlü
sonucudur, iki farklı problemi (eğim bulma ve alan bulma) birbirine bağlar.

Nedir?
Bölüm 1: $\\frac{d}{dx}\\int_a^x f(t)\\,dt = f(x)$ (integral almanın türevi,
orijinal fonksiyonu geri verir). Bölüm 2:
$\\int_a^b f(x)\\,dx = F(b)-F(a)$, burada $F$, $f$'in bir ters türevidir —
belirli integrali, sonsuz ince dilimler toplamadan, sadece iki değeri
çıkararak hesaplamayı sağlar.

Ne İçin Kullanılır?
1. Alan, Hacim ve Toplam Miktar Hesabı
Bir eğrinin altındaki alan, bir cismin aldığı toplam yol, bir tankı
doldurmak için gereken toplam iş — hepsi bu teoremle Riemann toplamı
hesaplamadan hızlıca bulunur.
2. Fizik ve Mühendislikte Biriken Miktarlar
Değişen bir hızdan toplam mesafeyi, değişen bir akımdan toplam yükü
hesaplamak bu teoreme dayanır.

📜 Tarih ve Biyografi
Teoremin özü Newton ve Leibniz'in 17. yüzyıl çalışmalarında zaten
mevcuttu; bugünkü rigorous (titiz) kanıtı ise Cauchy tarafından 1823'te,
integrali Riemann toplamlarının limiti olarak tanımladıktan sonra
verildi.
""")

_add("Calculus 2", ["Riemann sums", "Midpoint Rule", "Trapezoidal Rule", "Simpson's Rule",
                                    "Limit process to find area", "Over and underestimation"], """
Riemann toplamı, eğri altındaki alanı bulmanın en temel fikridir: alanı
çok sayıda ince dikdörtgene böl, her birinin alanını topla, dikdörtgenleri
sonsuz inceltince gerçek alana ulaş.

Nedir?
$[a,b]$ aralığı $n$ eşit parçaya bölünür, her parçada bir dikdörtgenin
alanı $f(x_i^*)\\Delta x$ hesaplanır ve toplanır;
$n\\to\\infty$ iken bu toplam $\\int_a^b f(x)\\,dx$'e yakınsar. Trapez ve
Simpson kuralları, dikdörtgen yerine yamuk/parabol kullanarak daha az
adımda daha doğru tahmin verir.

Ne İçin Kullanılır?
1. Kapalı Formda Çözülemeyen İntegralleri Hesaplamak
Birçok gerçek dünya fonksiyonunun (örn. normal dağılım eğrisi) analitik
ters türevi yoktur; bilgisayarlar bu integralleri Riemann toplamlarının
sayısal versiyonlarıyla (Simpson, trapez) hesaplar.
2. Mühendislik Yazılımlarında Sayısal İntegrasyon
Yapı analizi, sinyal işleme gibi alanlarda "gerçek zamanlı" integral
hesabı bu yöntemlerle yapılır.

📜 Tarih ve Biyografi
Yöntem adını Alman matematikçi Bernhard Riemann'dan alır; Riemann,
1854'te Göttingen Üniversitesi'ndeki habilitasyon (doçentlik) tezinde
integrali bugün ders kitaplarında öğretilen titiz limit tanımıyla
formülleştirdi.
""")

_add("Calculus 2", ["Integration by parts", "Integration by parts two and three times",
                                    "Integration by parts with substitution", "Tabular integration"], """
Kısmi integrasyon, çarpım kuralının integral versiyonudur — iki
fonksiyonun çarpımını integre etmenin zor olduğu durumlarda, problemi
"biraz daha kolay" bir integrale dönüştürür.

Nedir?
$\\int u\\,dv = uv - \\int v\\,du$ formülü, $\\int x e^x dx$ gibi bir
polinomla üstel/trigonometrik fonksiyonun çarpımını içeren integralleri
çözer.

Ne İçin Kullanılır?
1. Fizik ve Mühendislikte Karma Fonksiyon İntegralleri
Titreşim, dalga denklemleri gibi birçok fiziksel model, polinom ve
trigonometrik/üstel terimlerin çarpımını integre etmeyi gerektirir.
2. Olasılıkta Beklenen Değer Hesabı
Sürekli bir rastgele değişkenin beklenen değerini (ortalamasını) bulmak
genellikle kısmi integrasyon gerektirir.

📜 Tarih ve Biyografi
Yöntem, İngiliz matematikçi Brook Taylor tarafından 1715'te
yayımlanmıştır — Taylor, aynı zamanda kendi adını taşıyan Taylor
serisinin de mucididir.
""")

_add("Calculus 2", ["Sequences vs. series", "Partial sums", "Convergence and sum of a telescoping series",
                                    "Convergence and the limit of a sequence", "Monotonic and bounded sequences"], """
Dizi, sonsuz bir sayı listesidir; seri ise bu listenin TOPLAMIDIR — bir
dizi $1, 1/2, 1/4, 1/8, ...$ iken, seri $1+1/2+1/4+1/8+\\cdots$'tür ve
şaşırtıcı biçimde SONLU bir sayıya (2'ye) yakınsayabilir.

Nedir?
Bir seri, kısmi toplamlar dizisinin ($S_n = a_1+a_2+\\cdots+a_n$) bir
limite yakınsayıp yakınsamadığına göre "yakınsak" veya "ıraksak" olarak
sınıflandırılır.

Ne İçin Kullanılır?
1. Sonsuz Bir Süreci Sonlu Bir Sayıyla İfade Etmek
Bileşik faiz ödemelerinin sonsuza kadar sürmesi, bir topun sonsuz kez
zıplaması gibi "sonsuz ama toplamı sonlu" durumları modellemek için
kullanılır.
2. Fonksiyonları Polinomlarla Yaklaşık İfade Etmek (Taylor Serileri)
Hesap makinelerinin $\\sin x$, $e^x$ gibi fonksiyonları nasıl hesapladığının
temelidir.

📜 Tarih ve Biyografi
Sonsuz serilerle ilk ciddi çalışma, Arşimet'in MÖ 250 civarında bir
parabol diliminin alanını geometrik seri toplayarak bulmasına dayanır.
Yakınsaklığın titiz (rigorous) tanımı ise Cauchy tarafından 1821'de
verildi.
""")

_add("Calculus 2", ["Ratio test", "Root test", "Comparison test", "Limit comparison test",
                                    "Integral test", "Geometric series test", "Harmonic series and p-series",
                                    "nth term test for divergence", "Alternating series test",
                                    "Alternating series estimation theorem"], """
Yakınsaklık testleri, bir serinin sonsuz toplamının sonlu bir sayıya
"ulaşıp ulaşamayacağını", tüm terimleri toplamadan ÖNCEDEN anlamanı
sağlayan bir dizi kısayoldur.

Nedir?
Oran testi, kök testi, karşılaştırma testi, integral testi gibi her biri
farklı seri tiplerinde en etkili olan, serinin terimlerinin davranışına
bakarak yakınsaklık/ıraksaklık kararı veren araçlardır.

Ne İçin Kullanılır?
1. Bir Yaklaşıklığın Güvenilir Olup Olmadığını Belirlemek
Mühendislik hesaplamalarında bir sonsuz seri yaklaşıklığı kullanılmadan
önce, o serinin gerçekten bir değere yakınsadığının garanti edilmesi
gerekir.
2. Taylor Serilerinin Geçerlilik Aralığını Bulmak
Bir fonksiyonun Taylor seri yaklaşıklığının hangi $x$ değerleri için
güvenilir olduğunu (yakınsaklık aralığını) belirlemede kullanılır.

📜 Tarih ve Biyografi
Bu testlerin büyük çoğunluğu 19. yüzyılda, serilerin yakınsaklığını
titizlikle inceleyen Augustin-Louis Cauchy'nin çalışmalarından
doğmuştur; alternatif seriler testi ise özellikle Gottfried Leibniz'in
17. yüzyıl sonu gözlemlerine dayanır ve literatürde "Leibniz testi"
olarak da anılır.
""")

_add("Calculus 2", ["Taylor series", "Maclaurin series", "Power series representation",
                                    "Radius and interval of convergence", "Power series differentiation",
                                    "Binomial series"], """
Taylor serisi, karmaşık bir fonksiyonu (sinüs, üstel, logaritma gibi)
sonsuz bir polinoma dönüştürür — hesap makinen $\\sin(1.2)$'yi hesaplarken
aslında böyle bir polinomu topluyor.

Nedir?
$f(x) = f(a) + f'(a)(x{-}a) + \\dfrac{f''(a)}{2!}(x{-}a)^2 + \\cdots$
formülü, bir fonksiyonu $a$ noktası civarında sonsuz bir polinom serisi
olarak yazar. $a=0$ özel durumu Maclaurin serisi olarak anılır.

Ne İçin Kullanılır?
1. Hesap Makinelerinin ve Bilgisayarların Fonksiyon Hesaplaması
İşlemciler $\\sin$, $\\cos$, $e^x$ gibi fonksiyonları doğrudan
hesaplayamaz; bunun yerine bu fonksiyonların Taylor polinom
yaklaşıklarını hesaplar.
2. Fizikte Yaklaşık Modeller Kurmak
Küçük açılar için $\\sin\\theta \\approx \\theta$ yaklaşıklığı (sarkaç
hareketinde kullanılır) bir Taylor serisi kesmesidir.

📜 Tarih ve Biyografi
Genel seri, İngiliz matematikçi Brook Taylor tarafından 1715'te
yayımlandı. Özel durumu ($a=0$) İskoç matematikçi Colin Maclaurin
tarafından 1742'de o kadar etkili biçimde kullanıldı ki kendi adıyla
anılmaya başladı — ironik biçimde, bu özel durum aslında daha önce
1742'den de eski, Newton'un çalışmalarında zaten görülüyordu.
""")

_add("Calculus 2", ["Polar coordinates", "Converting polar equations", "Converting rectangular equations",
                                    "Converting to polar coordinates", "Sketching polar curves"], """
Kutupsal koordinatlar, bir noktayı "ne kadar uzakta ve hangi açıda"
olduğuyla tarif eder — bir radarın bir uçağı "12 km, kuzeydoğu yönünde"
diye tarif etmesi gibi; bazı eğriler (spiraller, güller) bu sistemde çok
daha basit ifade edilir.

Nedir?
Bir nokta $(r, \\theta)$ ile ifade edilir; $r$ merkeze uzaklık, $\\theta$
pozitif x eksenine göre açıdır. $x=r\\cos\\theta$, $y=r\\sin\\theta$
dönüşümüyle Kartezyen sisteme çevrilir.

Ne İçin Kullanılır?
1. Dairesel/Dönel Sistemleri Modellemek
Radar, sonar, gezegen yörüngeleri gibi merkeze göre simetrik sistemler
kutupsal koordinatlarda çok daha doğal ifade edilir.
2. Karmaşık Sayılarla İşlem Yapmak
Karmaşık sayıların çarpımı ve kuvvetleri (De Moivre formülü) kutupsal
formda çok daha kolay hesaplanır.

📜 Tarih ve Biyografi
Kutupsal koordinat fikri Isaac Newton'un 1670'lerdeki eserlerinde ve
İsviçreli matematikçi Jacob Bernoulli'nin 1691'deki spiral eğri
çalışmalarında bağımsız olarak ortaya çıktı; sistemin bugünkü adı ve
notasyonu 18. yüzyılda yaygınlaştı.
""")

# ---------------------------------------------------------------------------
# Calculus 3
# ---------------------------------------------------------------------------
_add("Calculus 3", ["Partial derivatives in two variables", "Partial derivatives in three or more variables",
                                    "Higher order partial derivatives", "Chain rule for multivariable functions"], """
Kısmi türev, birden fazla değişkene bağlı bir yüzeyde "sadece bir
yönde" ne kadar eğimli olduğunu sorar — bir dağın yamacında sadece kuzeye
doğru mu, yoksa sadece doğuya doğru mu yürüdüğünü sorman gibi.

Nedir?
$\\partial f/\\partial x$, $y$'yi SABİT tutup yalnızca $x$'e göre türev
almaktır. Çok değişkenli bir fonksiyonun her yöndeki eğimi, bu kısmi
türevlerin bir kombinasyonuyla (gradyan) tanımlanır.

Ne İçin Kullanılır?
1. Optimizasyon: Çok Değişkenli En İyi Değer Bulma
Bir ürünün fiyatı VE reklam bütçesi aynı anda kârı etkiliyorsa, en
yüksek kârı bulmak kısmi türevler gerektirir.
2. Fizikte Isı, Akışkan ve Dalga Denklemleri
Sıcaklığın hem konuma hem zamana göre nasıl değiştiğini tanımlayan ısı
denklemi gibi temel fizik denklemleri kısmi türevlerle yazılır.

📜 Tarih ve Biyografi
Çok değişkenli kalkülüsün sistemli gösterimi, 1740'larda Leonhard
Euler'in akışkanlar mekaniği çalışmalarıyla gelişti; $\\partial$
sembolünü ise Fransız matematikçi Adrien-Marie Legendre 1786'da
kullanıma soktu.
""")

_add("Calculus 3", ["Gradient vectors", "Gradient vectors and the tangent plane",
                                    "Directional derivatives"], """
Gradyan, bir yüzeyde "en dik tırmanış" yönünü gösteren bir pusuladır —
bir dağcının zirveye en hızlı çıkacağı yönü anında söyler.

Nedir?
$\\nabla f = \\left(\\dfrac{\\partial f}{\\partial x}, \\dfrac{\\partial
f}{\\partial y}\\right)$ vektörü, fonksiyonun en hızlı ARTIŞ yönünü ve bu
yöndeki artış oranını verir.

Ne İçin Kullanılır?
1. Makine Öğrenmesinde "Gradyan İnişi"
Bir yapay sinir ağının hata payını en aza indirmek için kullanılan en
temel öğrenme algoritması, gradyanın TERSİ yönünde küçük adımlar atarak
çalışır.
2. Görüntü İşleme ve Kenar Tespiti
Bir görüntüdeki renk yoğunluğunun gradyanı, nesnelerin kenarlarını tespit
etmek için kullanılır.

📜 Tarih ve Biyografi
"Nabla" ($\\nabla$) operatörü fikri William Rowan Hamilton'ın 1846'daki
çalışmalarına dayanır; gradyan, diverjans ve rotasyonel gibi vektör
kalkülüsü kavramları ise Josiah Willard Gibbs ve Oliver Heaviside
tarafından 1880'lerde bugünkü pratik biçimine kavuşturuldu.
""")

_add("Calculus 3", ["Lagrange multipliers"], """
Lagrange çarpanları, "bir kısıtlama altında en iyiyi bulma" problemini
çözer — sınırlı bir bütçeyle maksimum mutluluğu, sabit bir çevre uzunluğuyla
maksimum alanı bulmak gibi.

Nedir?
$g(x,y)=c$ kısıtı altında $f(x,y)$'yi maksimize/minimize etmek için,
$\\nabla f = \\lambda \\nabla g$ denklemi çözülür — optimum noktada, hedef
fonksiyonun ve kısıtlamanın gradyanları birbirine paraleldir.

Ne İçin Kullanılır?
1. Ekonomi: Kısıtlı Kaynak Optimizasyonu
Sabit bir bütçeyle maksimum fayda/üretim elde etmenin standart
matematiksel aracıdır — mikroekonominin temel taşlarından biri.
2. Mühendislik Tasarımında Kısıtlı Optimizasyon
Sabit malzeme miktarıyla maksimum dayanıklılığa sahip bir yapı tasarlamak
gibi problemlerde kullanılır.

📜 Tarih ve Biyografi
Yöntem, İtalyan-Fransız matematikçi Joseph-Louis Lagrange tarafından
1788'de yayımlanan "Mécanique Analytique" (Analitik Mekanik) adlı, klasik
mekaniği tamamen matematiksel bir dille yeniden yazan ünlü eserinde
tanıtıldı.
""")

_add("Calculus 3", ["Iterated and double integrals", "Iterated and triple integrals",
                                    "Finding volume with a double integral", "Finding volume of a triple integral",
                                    "Type I and type II regions"], """
Çift ve üçlü integral, alan/hacim hesabını iki veya üç boyuta taşır —
tek değişkenli integral eğri altındaki alanı verirken, çift integral bir
yüzeyin ALTINDAKİ hacmi verir.

Nedir?
$\\iint_R f(x,y)\\,dA$, $R$ bölgesi üzerinde $f$ yüzeyinin altında kalan
hacmi hesaplar; pratikte iki ardışık (iterated) tek değişkenli integrale
dönüştürülerek çözülür.

Ne İçin Kullanılır?
1. Kütle, Kütle Merkezi ve Yoğunluk Hesabı
Değişken yoğunluklu bir cismin toplam kütlesi veya ağırlık merkezi çoklu
integralle hesaplanır.
2. Olasılıkta Ortak Dağılımlar
İki rastgele değişkenin birlikte olasılığını hesaplamak (örn. hem boy
hem kilo dağılımı) çift integral gerektirir.

📜 Tarih ve Biyografi
Çoklu integral fikri 18. yüzyılda Euler ve Lagrange'ın akışkanlar ve
mekanik çalışmalarında ortaya çıktı; bugünkü sistematik gösterim ve
hesaplama yöntemleri 19. yüzyılda gelişti.
""")

_add("Calculus 3", ["Green's theorem for two regions", "Greens theorem for one region"], """
Green Teoremi, bir bölgenin SINIRI boyunca yapılan bir hesaplamayı,
bölgenin İÇİNDEKİ bir hesaplamaya bağlar — kıyı şeridini dolaşarak
ölçtüğün bir şeyi, karayı hiç dolaşmadan, içindeki toplam değeri
hesaplayarak da bulabilirsin.

Nedir?
$\\oint_C (P\\,dx + Q\\,dy) = \\iint_R \\left(\\dfrac{\\partial Q}{\\partial x}
- \\dfrac{\\partial P}{\\partial y}\\right) dA$ — kapalı bir eğri boyunca
çizgi integrali ile o eğrinin çevrelediği bölge üzerindeki çift integrali
birbirine eşitler.

Ne İçin Kullanılır?
1. Akışkanlar Mekaniği ve Elektromanyetizma
Bir bölgenin sınırından geçen akışı (su, hava, elektrik alanı) hesaplamak
için kullanılır; Maxwell denklemlerinin temel araçlarından biridir.
2. Düzensiz Şekillerin Alanını Hesaplamak
Bir bölgenin alanını, sadece sınırını "dolaşarak" (örn. bir planimetre
aletiyle) ölçmeyi mümkün kılar.

📜 Tarih ve Biyografi
Teorem, kendi kendini yetiştirmiş İngiliz matematikçi George Green
tarafından 1828'de, kendi bastırdığı özel bir eserde yayımlandı — Green
bir değirmenci oğluydu, resmî matematik eğitimi neredeyse hiç yoktu ve bu
çalışması yıllarca fark edilmeden kaldı; sonradan matematiksel fiziğin
temel taşlarından biri olarak tanındı.
""")

_add("Calculus 3", ["Jacobian for two variables", "Jacobian for three variables"], """
Jacobian, bir koordinat sisteminden diğerine geçerken "alanın/hacmin nasıl
büzüldüğünü veya genişlediğini" ölçen bir "döviz kuru" gibidir — Kartezyen
koordinatlardan kutupsal koordinatlara geçince alan birimini doğru
ayarlamanı sağlar.

Nedir?
Bir dönüşümün kısmi türevlerinden oluşan determinanttır; $dA$ veya $dV$
birimini yeni koordinat sistemine göre düzeltmek için integralin içine
çarpan olarak eklenir (örn. kutupsalda $dA = r\\,dr\\,d\\theta$).

Ne İçin Kullanılır?
1. Karmaşık Bölgelerin İntegralini Kolaylaştırmak
Dairesel/küresel simetrisi olan bölgelerin integralini Kartezyen yerine
kutupsal/silindirik/küresel koordinatlarda çok daha kolay hesaplamayı
sağlar.
2. Robotik ve Bilgisayarlı Görüde Koordinat Dönüşümleri
Bir kameranın veya robot kolunun farklı koordinat sistemleri arasında
tutarlı hesap yapabilmesi Jacobian matrisine dayanır.

📜 Tarih ve Biyografi
Kavram, Alman matematikçi Carl Gustav Jacob Jacobi tarafından 1841'de
yayımlanan "De determinantibus functionalibus" adlı çalışmasında
sistemli olarak incelendi ve adını ondan alır.
""")

# ---------------------------------------------------------------------------
# Probability & Statistics  (+ Math for Data Science overlap)
# ---------------------------------------------------------------------------
_add("Probability & Statistics", ["Simple probability", "Discrete probability",
                                                   "The addition rule, and union vs. intersection",
                                                   "Independent and dependent events and conditional probability"], """
Olasılık, belirsizliği SAYIYLA ifade etme sanatıdır — bir olayın "kesinlikle
olmayacağı" 0 ile "kesin olacağı" 1 arasında nerede durduğunu ölçer.

Nedir?
Bir olayın olasılığı, istenen sonuç sayısının tüm olası sonuç sayısına
oranıdır: $P(A) = \\dfrac{\\text{istenen}}{\\text{toplam}}$. Koşullu olasılık
$P(A|B)$, "B olduğu BİLİNDİĞİNDE A'nın olasılığı nedir?" sorusunu sorar.

Ne İçin Kullanılır?
1. Risk Değerlendirmesi ve Sigortacılık
Sigorta primleri, kredi risk skorları, tıbbi teşhis testlerinin
güvenilirliği — hepsi olasılık hesaplarıyla belirlenir.
2. Oyun Teorisi ve Karar Verme
Poker, zar oyunları, borsa yatırım kararları belirsizlik altında en
mantıklı seçimi yapmak için olasılığı kullanır.

📜 Tarih ve Biyografi
Sistemli olasılık teorisinin doğuşu, Fransız matematikçiler Blaise
Pascal ve Pierre de Fermat'nın 1654'teki ünlü mektuplaşmasına dayanır —
bir kumar oyununun yarıda kesilmesi durumunda bahsin nasıl adil
paylaştırılacağını ("problem of points") çözmeye çalışırken modern
olasılık teorisinin temellerini attılar. İtalyan hekim/kumarbaz Gerolamo
Cardano ise bundan bir asır önce, 1560'larda, konuyla ilgili ilk
sistematik notları yazmıştı (eseri ölümünden sonra 1663'te yayımlandı).
""")

_add("Probability & Statistics", ["Permutations and combinations"], """
Permütasyon "sıralamanın önemli olduğu", kombinasyon ise "sıralamanın
önemli olmadığı" seçim sayma yöntemleridir — bir yarışta 1.-2.-3. sırayı
belirlemek permütasyon, bir pizza için 3 malzeme seçmek kombinasyondur.

Nedir?
$n$ nesneden $r$ tanesini SIRALI seçmenin yolu $P(n,r) = n!/(n-r)!$;
SIRASIZ seçmenin yolu $C(n,r) = n!/(r!(n-r)!)$'dir.

Ne İçin Kullanılır?
1. Olasılık Hesaplarının Temeli
Loto kazanma şansından bir şifrenin kaç farklı kombinasyonu olduğuna
kadar her "kaç farklı yol var?" sorusu bu formüllerle cevaplanır.
2. Bilgisayar Biliminde Algoritma Karmaşıklığı
Bir problemin kaç olası çözümü olduğunu (ve bu yüzden "kaba kuvvet"
yöntemin ne kadar süreceğini) hesaplamada kullanılır.

📜 Tarih ve Biyografi
Kombinasyon sayma yöntemlerinin en eski izleri, MÖ 2. yüzyılda Hint
matematikçi Pingala'nın hece kombinasyonlarını incelediği çalışmalara
kadar uzanır. Bugün "Pascal Üçgeni" olarak bildiğimiz ve kombinasyonları
gösteren üçgen, ondan çok önce Çin ve Fars matematikçilerince biliniyordu,
ancak Batı'da adını 1653'te bu üçgeni ayrıntılı inceleyen Blaise
Pascal'dan aldı.
""")

_add("Probability & Statistics", ["Bayes' Theorem"], """
Bayes Teoremi, YENİ bir kanıt geldiğinde bir inancı nasıl GÜNCELLEMEN
gerektiğini söyler — bir tıbbi test pozitif çıktığında, hastalığa
yakalanma ihtimalinin GERÇEKTE ne kadar değiştiğini hesaplar (çoğu zaman
insanların sandığından çok daha az).

Nedir?
$P(A|B) = \\dfrac{P(B|A)\\,P(A)}{P(B)}$ formülü, "B gözlemlendiğinde A'nın
olasılığını", A ve B'nin ayrı ayrı bilinen olasılıklarından hesaplar.

Ne İçin Kullanılır?
1. Tıbbi Teşhis ve Test Güvenilirliği
Nadir bir hastalık için test pozitif çıksa bile, gerçekten o hastalığa
sahip olma ihtimalinin neden düşük kalabileceğini (yanlış pozitif
tuzağı) açıklar.
2. Spam Filtreleri ve Makine Öğrenmesi
E-posta spam filtreleri, tıbbi teşhis yapay zekâları ve birçok makine
öğrenmesi modeli ("Naive Bayes") doğrudan bu teoremi kullanır.

📜 Tarih ve Biyografi
Teorem, İngiliz Presbiteryen papaz ve matematikçi Thomas Bayes'in
çalışmalarına dayanır; Bayes bunu hayattayken yayımlamadı, ölümünden
sonra 1763'te arkadaşı Richard Price tarafından bulunup yayımlandı.
Fransız matematikçi Pierre-Simon Laplace, teoremi ondan bağımsız olarak
yeniden keşfedip 1774'te modern, genel biçimine kavuşturdu.
""")

_add("Probability & Statistics", ["Binomial random variables", "Bernoulli random variables"], """
Bernoulli değişkeni en basit rastgele olaydır: sadece "başarı" veya
"başarısızlık" (yazı/tura, evet/hayır). Binom dağılımı ise "bu basit
denemeyi $n$ kez tekrarlarsan kaç başarı beklersin?" sorusunun cevabıdır.

Nedir?
$n$ bağımsız Bernoulli denemesinde tam $k$ başarı olma olasılığı
$P(X=k) = \\binom{n}{k}p^k(1-p)^{n-k}$ formülüyle verilir.

Ne İçin Kullanılır?
1. Kalite Kontrol ve Üretim
Bir üretim hattında 100 parçadan kaçının bozuk çıkacağını tahmin etmek
binom dağılımıyla modellenir.
2. Anket ve Seçim Tahminleri
Bir seçmen anketinde "evet" oranının güven aralığı binom dağılımına
dayanır.

📜 Tarih ve Biyografi
Binom dağılımının ilk sistematik incelemesi, İsviçreli matematikçi Jacob
Bernoulli'nin ölümünden sonra 1713'te yayımlanan "Ars Conjectandi"
("Tahmin Sanatı") adlı eserinde yer alır; aynı eserde Büyük Sayılar
Yasası'nın ilk kanıtı da bulunur.
""")

_add("Probability & Statistics", ["Normal distributions and z-scores"], """
Normal dağılım, doğada ve toplumda tekrar tekrar karşımıza çıkan ünlü
"çan eğrisidir" — boy uzunluğu, ölçüm hataları, test puanları gibi birçok
şey bu simetrik, ortada yığılmış şekle uyar.

Nedir?
Ortalama ($\\mu$) etrafında simetrik, standart sapması ($\\sigma$) ile
yayılımı belirlenen bir dağılımdır. $z$-skoru, bir değerin ortalamadan
kaç standart sapma uzakta olduğunu söyler: $z=(x-\\mu)/\\sigma$.

Ne İçin Kullanılır?
1. Standartlaştırılmış Test ve Ölçüm Karşılaştırması
SAT, IQ testi gibi puanların "ne kadar iyi" olduğunu farklı ölçeklerde
karşılaştırmak z-skoruyla yapılır.
2. Kalite Kontrol (Altı Sigma)
Üretimde hata oranlarını standart sapma cinsinden ölçmek ve azaltmak
("Six Sigma" metodolojisi) bu dağılıma dayanır.
3. Doğa Bilimlerinde Ölçüm Hatası Modellemesi
Bilimsel deneylerdeki rastgele ölçüm hataları neredeyse her zaman normal
dağılıma yakın davranır.

📜 Tarih ve Biyografi
Dağılım ilk kez Fransız matematikçi Abraham de Moivre tarafından 1733'te,
binom dağılımına bir yaklaşıklık olarak türetildi. Adını asıl veren ise
Alman matematikçi Carl Friedrich Gauss'tur — 1809'da gökbilimsel ölçüm
hatalarını incelerken bu dağılımı bağımsız olarak yeniden keşfetti ve o
kadar etkili kullandı ki bugün "Gauss dağılımı" olarak da anılır.
""")

_add("Probability & Statistics", ["Poisson distributions"], """
Poisson dağılımı, "belirli bir zaman/alan aralığında nadir bir olayın kaç
kez gerçekleşeceğini" tahmin eder — bir çağrı merkezine saatte kaç çağrı
geleceği, bir sayfada kaç yazım hatası olacağı gibi.

Nedir?
Ortalama olay sıklığı $\\lambda$ bilindiğinde, tam $k$ olay gözlenme
olasılığı $P(X=k) = \\dfrac{\\lambda^k e^{-\\lambda}}{k!}$ formülüyle
verilir.

Ne İçin Kullanılır?
1. Hizmet ve Kapasite Planlaması
Bir hastane acil servisine, bir çağrı merkezine saatte kaç kişinin
geleceğini tahmin edip yeterli personel planlamak için kullanılır.
2. Sigorta ve Risk Modellemesi
Nadir olayların (deprem, büyük hasar) yıllık sıklığını modellemede
kullanılır.

📜 Tarih ve Biyografi
Dağılım, Fransız matematikçi Siméon Denis Poisson tarafından 1837'de
yayımlanan bir çalışmada, ceza mahkemelerinde nadir yanlış hüküm
olaylarını incelerken tanıtıldı.
""")

_add("Probability & Statistics", ["Mean, variance, and standard deviation",
                                                   "Measures of central tendency", "Measures of spread",
                                                   "At least and at most, and mean, variance, and standard deviation"], """
Ortalama, verinin "merkezini"; standart sapma ise verinin bu merkez
etrafında "ne kadar dağınık" olduğunu tek bir sayıyla özetler.

Nedir?
Ortalama $\\mu = \\frac{1}{n}\\sum x_i$, veri noktalarının aritmetik
ortalamasıdır. Varyans, her noktanın ortalamadan sapmasının karesinin
ortalamasıdır; standart sapma ($\\sigma$) varyansın karekökü olup
sapmayı orijinal birimlere geri döndürür.

Ne İçin Kullanılır?
1. Riski ve Tutarlılığı Ölçmek
Finansta bir yatırımın "riski" genellikle getirisinin standart sapması
ile ölçülür — yüksek standart sapma yüksek belirsizlik demektir.
2. Kalite Kontrolde Tutarlılığı İzlemek
Bir üretim hattının çıktılarının ne kadar TUTARLI olduğunu (standart
sapması düşük mü) izlemek kalite kontrolün temelidir.

📜 Tarih ve Biyografi
"Standart sapma" terimi ve $\\sigma$ sembolü, İngiliz istatistikçi Karl
Pearson tarafından 1894'te tanıtıldı; ortalama ve yayılım kavramlarının
kendisi ise çok daha eski olup 18. yüzyıl gözlemsel astronomi
çalışmalarına (ölçüm hatalarını özetleme ihtiyacına) dayanır.
""")

_add("Probability & Statistics", ["Correlation coefficient", "Correlation coefficient and the residual",
                                                   "Scatterplots and regression", "Covariance",
                                                   "Coefficient of determination and RMSE"], """
Korelasyon, iki değişkenin "birlikte hareket edip etmediğini" ölçer;
regresyon ise bu ilişkiyi tahmin yapmakta kullanılabilecek bir DOĞRUYA
dönüştürür.

Nedir?
Korelasyon katsayısı $r$, $-1$ (mükemmel ters ilişki) ile $+1$ (mükemmel
doğru ilişki) arasında değişir; $0$ ilişkisizlik demektir. Regresyon
doğrusu, veri noktalarına "en iyi uyan" doğruyu (en küçük kareler
yöntemiyle) bulur.

Ne İçin Kullanılır?
1. Tahmin ve Öngörü Modelleri
Reklam bütçesinden satışları, çalışma saatinden not ortalamasını tahmin
etmek — modern veri biliminin ve makine öğrenmesinin en temel aracıdır.
2. Bilimsel Çalışmalarda İlişki Tespiti
Sigara ile akciğer kanseri, gelir ile eğitim seviyesi arasındaki
ilişkiler ilk olarak korelasyon analiziyle ortaya konur (ancak korelasyon
NEDENSELLİK anlamına gelmez — bu, istatistikte en sık yapılan hatalardan
biridir).

📜 Tarih ve Biyografi
Korelasyon fikri İngiliz bilim insanı Francis Galton tarafından 1888'de,
ebeveyn ve çocuk boyları arasındaki ilişkiyi incelerken ortaya atıldı
(ve "ortalamaya regresyon" fikrini de o keşfetti). Bugün kullandığımız
kesin matematiksel formül ise öğrencisi İngiliz istatistikçi Karl Pearson
tarafından 1896'da verildi — bu yüzden "Pearson korelasyon katsayısı"
olarak da bilinir.
""")

_add("Probability & Statistics", ["Chi-square tests"], """
Ki-kare testi, "gözlemlediğim veri, beklediğim (rastgele/eşit) dağılıma
gerçekten uyuyor mu, yoksa aralarında anlamlı bir fark mı var?" sorusunu
cevaplar.

Nedir?
$\\chi^2 = \\sum \\dfrac{(O-E)^2}{E}$ formülü, gözlenen ($O$) ve beklenen
($E$) frekanslar arasındaki farkı tek bir istatistiğe indirger; bu değer
büyüdükçe "fark tesadüften kaynaklanıyor olamaz" sonucuna varılır.

Ne İçin Kullanılır?
1. Anket ve Pazar Araştırmasında Bağımsızlık Testi
"Cinsiyet ile ürün tercihi arasında gerçek bir ilişki var mı, yoksa
tesadüf mü?" gibi soruları cevaplar.
2. Genetik ve Biyolojide Beklenen Oranları Test Etmek
Mendel'in genetik oranlarının gözlenen verilere uyup uymadığını test
etmede kullanılır.

📜 Tarih ve Biyografi
Test, İngiliz istatistikçi Karl Pearson tarafından 1900'de yayımlandı ve
modern istatistiksel hipotez testinin ilk örneklerinden biri kabul
edilir.
""")

_add("Probability & Statistics", ["Inferential statistics and hypotheses",
                                                   "Significance level and type I and II errors",
                                                   "The p-value and rejecting the null",
                                                   "Test statistics for one- and two-tailed tests",
                                                   "Hypothesis testing for the population proportion",
                                                   "Hypothesis testing for the difference of means",
                                                   "Hypothesis testing for the difference of proportions",
                                                   "Matched-pair hypothesis testing"], """
Hipotez testi, "gördüğüm fark gerçek mi, yoksa sadece şans eseri mi
ortaya çıktı?" sorusuna disiplinli bir cevap arama yöntemidir — bir ilacın
gerçekten işe yarayıp yaramadığını anlamanın bilimsel yoludur.

Nedir?
"Hiçbir fark yok" varsayımıyla (sıfır hipotezi, $H_0$) başlanır; eldeki
veri bu varsayım altında ne kadar "olağandışıysa" o kadar düşük bir
p-değeri elde edilir. p-değeri, önceden belirlenen anlamlılık düzeyinin
(genelde 0.05) altındaysa $H_0$ reddedilir.

Ne İçin Kullanılır?
1. Tıpta İlaç ve Tedavi Etkinliği Testi
Yeni bir ilacın plasebodan GERÇEKTEN daha etkili olup olmadığını
kanıtlamanın standart bilimsel yoludur; klinik denemelerin temelidir.
2. A/B Testleri ve Ürün Kararları
Bir web sitesinin yeni tasarımının gerçekten daha çok satış getirip
getirmediğini anlamak için teknoloji şirketlerinin kullandığı yöntemdir.

📜 Tarih ve Biyografi
Modern hipotez testi çerçevesi büyük ölçüde İngiliz istatistikçi ve
genetikçi Ronald Fisher'ın 1925 tarihli "Statistical Methods for Research
Workers" adlı kitabına dayanır (p-değeri kavramını o popülerleştirdi).
Alternatif hipotez, Tip I/II hata ayrımı ise Jerzy Neyman ve Egon Pearson
tarafından 1930'larda geliştirilen tamamlayıcı bir çerçeveden gelir.
""")

_add("Probability & Statistics", ["Confidence interval for the mean", "Confidence interval for the proportion",
                                                   "Confidence interval for the difference of means",
                                                   "Confidence interval for the difference of proportions",
                                                   "Conditions for inference with the SDSM", "Conditions for inference with the SDSP",
                                                   "Sampling distribution of the sample mean", "Sampling distribution of the sample proportion"], """
Güven aralığı, tek bir tahmin yerine "gerçek değerin muhtemelen bu ARALIKTA
olduğunu" söyler — bir seçim anketinin "%52 ± 3" sonucu vermesi gibi.

Nedir?
Bir örneklemden hesaplanan istatistik (örn. örneklem ortalaması) etrafında,
gerçek popülasyon parametresini belirli bir güvenle (genelde %95) içeren
bir aralık kurulur; aralığın genişliği örneklem büyüklüğü ve değişkenliğe
bağlıdır.

Ne İçin Kullanılır?
1. Seçim Anketleri ve Kamuoyu Araştırmaları
"Hata payı ±3 puan" ifadesi doğrudan bir güven aralığıdır.
2. Tıbbi ve Bilimsel Raporlamada Belirsizliği İfade Etmek
Bir ilacın etkisinin "tam olarak" değil, hangi ARALIKTA olduğunu dürüstçe
raporlamanın standart yoludur.

📜 Tarih ve Biyografi
Güven aralığı kavramı, Polonyalı-Amerikalı istatistikçi Jerzy Neyman
tarafından 1937'de resmî olarak tanımlandı ve modern çıkarımsal
istatistiğin temel araçlarından biri hâline geldi.
""")

_add("Probability & Statistics", ["The student's t-distribution"], """
Student t-dağılımı, ÖRNEKLEM KÜÇÜKKEN ve gerçek varyans bilinmiyorken
normal dağılımın yerini alan, "daha temkinli" (kalın kuyruklu) bir
dağılımdır.

Nedir?
Normal dağılıma benzer ama daha basık ve kalın kuyrukludur; örneklem
büyüklüğü arttıkça normal dağılıma yaklaşır. Küçük örneklemlerle ortalama
hakkında çıkarım yaparken kullanılır.

Ne İçin Kullanılır?
1. Küçük Örneklemli Bilimsel Deneyler
Tıbbi denemeler, kalite kontrol testleri gibi az sayıda gözlemle
yapılan analizlerde güvenilir sonuç vermek için kullanılır.
2. A/B Testleri ve Karşılaştırmalı Analiz
İki grubun ortalamasını (örn. iki ilaç dozu) karşılaştıran t-testinin
temelidir.

📜 Tarih ve Biyografi
Dağılım, İngiliz kimyager ve istatistikçi William Sealy Gosset
tarafından 1908'de geliştirildi. Gosset, Guinness bira fabrikasında
çalışıyordu ve işvereni ticari sırların açığa çıkmasından çekindiği için
çalışanların kendi adlarıyla yayın yapmasını yasaklamıştı — bu yüzden
Gosset makalesini "Student" (Öğrenci) mahlasıyla yayımladı ve dağılım
bugün hâlâ bu isimle anılıyor.
""")

_add("Probability & Statistics", ["Venn diagrams"], """
Venn şeması, kümeler arasındaki ilişkileri (kesişim, birleşim, ayrık
kümeler) iç içe geçen dairelerle GÖRSEL olarak anlatır.

Nedir?
Her daire bir kümeyi temsil eder; dairelerin kesişen bölgesi her iki
kümede de bulunan ortak elemanları gösterir.

Ne İçin Kullanılır?
1. Olasılıkta Görsel Muhakeme
"En az biri", "her ikisi de", "hiçbiri" gibi olasılık sorularını görsel
olarak çözmenin en hızlı yoludur.
2. Mantık ve Veritabanı Sorgularında Küme İşlemleri
Veritabanı sorgularındaki VE/VEYA/DEĞİL mantığı doğrudan Venn şemalarıyla
görselleştirilir.

📜 Tarih ve Biyografi
Şemalar, İngiliz mantıkçı John Venn tarafından 1880'de "On the Diagrammatic
and Mechanical Representation of Propositions and Reasonings" adlı
makalede tanıtıldı; adını da ondan alır.
""")

_add("Probability & Statistics", ["Joint distributions", "Combinations of random variables",
                                                   "Transforming random variables"], """
Ortak dağılım, İKİ rastgele değişkenin BİRLİKTE nasıl davrandığını
anlatır — sadece boy dağılımını değil, boy VE kilonun birlikte hangi
kombinasyonlarda ne sıklıkla görüldüğünü tarif eder.

Nedir?
$P(X=x, Y=y)$, iki değişkenin AYNI ANDA belirli değerleri alma
olasılığıdır. Buradan her bir değişkenin tek başına dağılımı (marjinal
dağılım) ve birbirine bağımlı olup olmadıkları çıkarılabilir.

Ne İçin Kullanılır?
1. Çok Değişkenli Veri Bilimi Modelleri
Gerçek dünya verileri neredeyse hiç tek değişkenli değildir; bir
müşterinin hem yaşı hem geliri hem alışveriş sıklığı birlikte modellenir.
2. Risk Modellemesinde Bağımlı Olayları Yakalamak
İki finansal varlığın aynı anda değer kaybetme olasılığı (birbirinden
bağımsız değillerse) ortak dağılımla hesaplanır.

📜 Tarih ve Biyografi
Çok değişkenli olasılık teorisinin titiz temelleri, 20. yüzyıl başında
Rus matematikçi Andrey Kolmogorov'un 1933'te olasılık teorisini küme
teorisi üzerine aksiyomatik olarak inşa etmesiyle atıldı.
""")

_add("Probability & Statistics", ["Sampling and bias", "Types of studies", "Frequency tables and dot plots",
                                                   "Histograms and stem-and-leaf plots", "Bar graphs and pie charts",
                                                   "Box-and-whisker plots"], """
Örnekleme, koca bir popülasyon hakkında konuşmak için onun KÜÇÜK ve
TEMSİLİ bir parçasını incelemektir — bir tencere çorbayı yemeden önce
tek kaşıkla tatmaya benzer; kaşığın karıştırılmış (rastgele) olması
şarttır, yoksa yanlış bir izlenim edinirsin (yanlılık/bias).

Nedir?
İyi bir örneklem, popülasyonun her üyesine adil bir seçilme şansı verir
(rastgele örnekleme). Histogram, kutu grafiği gibi araçlar ise bu
örneklemden toplanan veriyi görsel olarak özetler.

Ne İçin Kullanılır?
1. Anket ve Pazar Araştırması Güvenilirliği
Bir anketin milyonlarca kişi yerine birkaç bin kişiyle yapılıp yine de
güvenilir sonuç vermesinin bilimsel temelidir.
2. Veriyi Hızlıca Anlamlandırmak
Bir veri kümesinin şeklini, aykırı değerlerini, dağılımını saniyeler
içinde kavramanın standart aracıdır.

📜 Tarih ve Biyografi
Rastgele örnekleme teorisinin bilimsel temelleri, 20. yüzyıl başında
Ronald Fisher'ın tarım deneylerindeki çalışmalarıyla ve Jerzy Neyman'ın
1934'teki "temsili örnekleme" üzerine yazdığı etkili makaleyle atıldı.
""")

# ---------------------------------------------------------------------------
# Math for Data Science (ağırlıkla üstteki olasılık/istatistik
# girişleriyle örtüşür; buraya özgü/ek birkaç kavram)
# ---------------------------------------------------------------------------
_add("Math for Data Science", ["Law of large numbers", "Central limit theorem"], """
Büyük Sayılar Yasası, "yeterince çok deneme yaparsan ortalaman gerçek
olasılığa yaklaşır" der; Merkezi Limit Teoremi ise çok daha güçlü bir
iddiada bulunur: hangi dağılımdan gelirse gelsin, örneklem ortalamalarının
dağılımı örneklem büyüdükçe NORMAL dağılıma yaklaşır.

Nedir?
Bir yazı-tura denemesini binlerce kez tekrarlarsan oran %50'ye yaklaşır
(Büyük Sayılar Yasası). Farklı örneklemlerden hesaplanan ortalamaların
KENDİSİ bir çan eğrisi (normal dağılım) oluşturur (Merkezi Limit
Teoremi) — istatistiğin neredeyse tüm çıkarım yöntemlerinin dayandığı
"mucizevi" sonuçtur.

Ne İçin Kullanılır?
1. Neden Normal Dağılım Her Yerde Karşımıza Çıkıyor?
Boy uzunluğu gibi birçok doğal ölçümün normal dağılıma benzemesinin
teorik açıklamasıdır — çoğu doğal ölçüm, çok sayıda küçük bağımsız
etkinin toplamıdır.
2. Veri Bilimi ve Makine Öğrenmesinde Güven Aralıkları
Bir modelin tahmininin ne kadar güvenilir olduğunu ölçmek, bu teoremin
garantisine dayanır.

📜 Tarih ve Biyografi
Büyük Sayılar Yasası'nın ilk kanıtı Jacob Bernoulli'nin 1713 tarihli
"Ars Conjectandi" eserinde yer alır. Merkezi Limit Teoremi'nin ilk hâli
Abraham de Moivre tarafından 1733'te verildi, Pierre-Simon Laplace
1810'da genelleştirdi; tam titiz kanıtı ise Rus matematikçi Aleksandr
Lyapunov tarafından 1901'de tamamlandı.
""")

_add("Math for Data Science", ["Weighted means and grouped data", "Two-way tables", "One-way tables",
                                           "Relative frequency tables", "Symmetric and skewed distributions and outliers",
                                           "Changing the data, and outliers"], """
Betimsel istatistik araçları (ağırlıklı ortalama, çapraz tablo, çarpıklık),
ham veriyi anlamlı bir HİKÂYEYE dönüştürmenin ilk adımıdır — herhangi bir
model kurmadan önce veriyi "tanımak" gerekir.

Nedir?
Ağırlıklı ortalama, bazı değerlerin diğerlerinden daha "önemli" sayıldığı
durumlarda kullanılır (örn. not ortalaması hesaplarken kredi ağırlıkları).
Çarpıklık (skewness), bir dağılımın simetrik mi yoksa bir yöne "kuyruklu"
mu olduğunu; aykırı değerler ise geri kalan veriden anormal derecede
uzak noktaları tanımlar.

Ne İçin Kullanılır?
1. Veri Temizleme (Veri Bilimindeki İlk Adım)
Bir makine öğrenmesi modeli kurmadan önce veri setindeki aykırı
değerleri ve çarpıklığı tespit edip ele almak, modelin güvenilirliği
için kritiktir.
2. Adil Değerlendirme Sistemleri
Farklı ağırlıklardaki sınavların/ödevlerin genel notu nasıl etkilediğini
doğru hesaplamak ağırlıklı ortalamayla yapılır.

📜 Tarih ve Biyografi
Betimsel istatistiğin sistemli görsel/sayısal araçları büyük ölçüde 19.
yüzyıl sonunda Karl Pearson'ın "biyometri" (biyolojik ölçümlerin
istatistiği) çalışmalarıyla ve 20. yüzyılda John Tukey'in 1977'deki
"Exploratory Data Analysis" (Keşifsel Veri Analizi) yaklaşımıyla
gelişti.
""")

# ===========================================================================
# "Döngü Mühendisliği" 2. tur — kapsamı genişletir (bkz. topic_knowledge_round2.py).
# Bu import BURADA, TOPIC_KNOWLEDGE ve _add tanımlandıktan SONRA yapılır ki
# round2 modülü bunları güvenle geri import edebilsin.
# ===========================================================================
try:
    import topic_knowledge_round2  # noqa: F401  (populates TOPIC_KNOWLEDGE further)
except Exception:
    pass
