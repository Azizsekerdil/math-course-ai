# -*- coding: utf-8 -*-
"""
topic_knowledge_round2 — "Döngü Mühendisliği" 2. tur ek konu girişleri.

topic_knowledge.py'nin dosya sonunda bu modülü import ederek TOPIC_KNOWLEDGE
sözlüğünü genişletir. `_add` fonksiyonu ana modülden gelir; burada sadece
yeni girişler eklenir. Aynı ilke geçerlidir: gerçek tarih/biyografi sadece
doğrulanabilir olduğunda yazılır, prosedürel konularda atlanır.
"""

from topic_knowledge import _add

# ---------------------------------------------------------------------------
# Pre-Algebra — round 2
# ---------------------------------------------------------------------------
_add("Pre-Algebra", ["Absolute value", "Absolute value of an expression"], """
Mutlak değer, bir sayının işaretini yok sayıp yalnızca "sıfırdan uzaklığını"
söyler — hem $-5$ hem $5$, sıfırdan aynı uzaklıktadır (5 birim).

Nedir?
$|x|$, $x$ pozitifse $x$'in kendisi, negatifse $-x$'tir (yani her zaman
negatif olmayan bir sonuç verir). Bir ifadenin mutlak değeri de aynı mantıkla,
parantez içindeki sonucun işaretini kaldırır.

Ne İçin Kullanılır?
1. Hata Payı ve Fark Hesaplarında
İki değer arasındaki "fark" konuşulurken yön önemsizse (örn. hedef sıcaklıkla
gerçek sıcaklık arasındaki fark) mutlak değer kullanılır.
2. Mesafe Kavramının Cebirsel Karşılığı
Sayı doğrusunda iki nokta arasındaki mesafe $|a-b|$ ile ifade edilir.

📜 Tarih ve Biyografi
Bugün kullanılan $|x|$ gösterimi, Alman matematikçi Karl Weierstrass
tarafından 1841'de tanıtıldı.
""")

_add("Pre-Algebra", ["Adding and subtracting fractions", "Multiplying and dividing fractions",
                                         "Multiplying and dividing mixed numbers", "Mixed numbers and improper fractions",
                                         "Simplifying fractions and equivalent fractions", "Signs of fractions",
                                         "Reciprocals"], """
Kesir işlemleri, farklı "dilim büyüklüklerini" (paydaları) karşılaştırılabilir
hâle getirip sonra toplama/çıkarma/çarpma/bölme yapmanın kurallarıdır.

Nedir?
Toplama/çıkarma ortak payda gerektirir; çarpma pay ile payı, payda ile paydayı
çarpar; bölme ise ikinci kesrin TERSİYLE (reciprocal — pay/payda yer
değiştirmiş hâli) çarpmaya dönüşür. Bileşik (mixed) sayılar, tam sayı +
kesir toplamıdır ve işlem öncesi bileşik kesre çevrilir.

Ne İçin Kullanılır?
1. Tarif Ölçekleme ve Ölçüm İşleri
Bir tarifi 1.5 katına çıkarmak, bir kumaşı $3/4$ metreye bölmek gibi günlük
işler kesir işlemi gerektirir.
2. Cebirin Önkoşulu
Rasyonel ifadelerle (değişkenli kesirler) işlem yapabilmek, sayısal kesir
işlemlerinde akıcı olmayı gerektirir.
""")

_add("Pre-Algebra", ["Decimal arithmetic", "Repeating decimals"], """
Ondalık sayılar, kesirlerin "10'un katları" cinsinden yazılmış hâlidir —
$3/4$ yerine $0.75$ yazmak, aynı miktarı farklı bir dille ifade etmektir.

Nedir?
Ondalık aritmetik, virgülün konumunu doğru hizalayarak dört işlemi
yürütür. Bazı kesirler ($1/3=0.333\\ldots$ gibi) sonsuz tekrar eden bir
ondalık üretir; bu, üzerine çizgi konarak ($0.\\overline{3}$) gösterilir.

Ne İçin Kullanılır?
1. Para ve Ölçüm Hesapları
Fiyatlar, ölçümler, bilimsel veriler neredeyse her zaman ondalık biçimde
tutulur — kesirlerden çok daha hızlı karşılaştırılabilirler.
2. Bilgisayarların Sayı Saklaması
Bilgisayarlar sayıları ikili tabanda tutar; bazı basit ondalık sayıların
(0.1 gibi) bilgisayarda TAM saklanamamasının nedeni bu iki taban arasındaki
uyumsuzluktur — yazılımdaki yuvarlama hatalarının kök nedenidir.
""")

_add("Pre-Algebra", ["Place value"], """
Basamak değeri, aynı rakamın bulunduğu YERE göre farklı bir büyüklük ifade
etmesidir — 5, "5 birim" de olabilir "5 bin" de; hangisi olduğunu basamağı
belirler.

Nedir?
Onlu (pozisyonel) sayı sisteminde her basamak, bir öncekinin 10 katı
değerindedir; bu sayede sadece 10 rakamla (0-9) sonsuz büyüklükte sayı
yazılabilir.

Ne İçin Kullanılır?
1. Büyük Sayılarla Verimli Çalışmak
Toplama, çıkarma, çarpma algoritmalarının ("elden taşıma" gibi) hepsi
basamak değeri mantığına dayanır.
2. Farklı Sayı Tabanlarını Anlamak
Bilgisayarların kullandığı ikili (binary) sistem de aynı pozisyonel
mantığı taban 2 ile kullanır.

📜 Tarih ve Biyografi
Bugün kullandığımız pozisyonel onlu sistem (sıfır dahil), Hint
matematikçileri tarafından geliştirildi, Fars matematikçi el-Harezmi'nin
9. yüzyıl eserleriyle İslam dünyasına yayıldı ve İtalyan matematikçi
Fibonacci'nin 1202 tarihli "Liber Abaci" adlı eseriyle Avrupa'ya taşınarak
Roma rakamlarının yerini aldı.
""")

_add("Pre-Algebra", ["Division by zero"], """
Sıfıra bölme, matematiğin "yasak bölgesidir" — hiçbir sayı sıfıra
bölünemez, çünkü bu işlem tutarlı, tek bir cevap üretmez.

Nedir?
$a/0$ tanımsızdır: eğer $a/0=c$ olsaydı, $0 \\times c = a$ olması gerekirdi,
ama $0$ ile çarpım her zaman $0$ verir — $a \\neq 0$ iken bu imkânsızdır.

Ne İçin Kullanılır?
1. Yazılımda Çökmeleri Önlemek
"Division by zero" hatası, programlama dillerinde en sık karşılaşılan
çalışma zamanı hatalarından biridir; bu kuralı bilmek kodu önceden
korumayı sağlar.
2. Kalkülüsün Kapısını Aralamak
$0/0$ gibi ifadelerin ne anlama gelebileceği sorusu, limit kavramının ve
dolayısıyla kalkülüsün doğmasına zemin hazırlamıştır.
""")

_add("Pre-Algebra", ["Ratio and proportion", "Unit price", "Unit multipliers",
                                         "Adding mixed measures"], """
Oran, iki miktarı KARŞILAŞTIRIR; orantı ise iki oranın birbirine EŞİT
olduğunu söyler — bir tarifteki malzeme oranını büyük bir grup için
ölçeklerken kullandığın mantık budur.

Nedir?
$a:b$ oranı, $a/b$ kesriyle aynıdır. Orantı, $a/b = c/d$ biçiminde iki
oranın eşitliğidir ve "içler dışlar çarpımı" ($ad=bc$) ile çözülür. Birim
fiyat (unit price), bir birimin maliyetini bulmak için bu mantığı kullanır;
birim çarpanları (unit multipliers) ise ölçü birimlerini (km→m gibi)
dönüştürmenin standart yoludur.

Ne İçin Kullanılır?
1. Alışverişte Akıllı Karşılaştırma
İki farklı boyuttaki ürünün hangisinin daha ucuz olduğunu (TL/kg) birim
fiyatla karşılaştırırsın.
2. Bilim ve Mühendislikte Birim Dönüşümü
Mil'i kilometreye, Fahrenheit'ı Celsius'a çevirmek birim çarpanlarıyla
yapılır — NASA'nın 1999'daki Mars Climate Orbiter kaybının nedeni tam
olarak birim dönüşümü (metrik/emperyal) hatasıydı.
""")

_add("Pre-Algebra", ["Rounding"], """
Yuvarlama, bir sayıyı GEREKENDEN FAZLA hassasiyet taşımadan, en yakın
"temiz" değere basitleştirmektir.

Nedir?
Belirli bir basamağa yuvarlarken, bir sonraki basamağa bakılır: 5 veya
üzeriyse bir yukarı yuvarlanır, 4 veya altıysa aynı kalır.

Ne İçin Kullanılır?
1. Anlamlı Hassasiyeti Korumak
Bilimsel ölçümlerde, aletin hassasiyetinden daha fazla basamak yazmak
yanıltıcıdır; yuvarlama gerçekçi bir kesinlik sunar.
2. Para ve Günlük Hesaplarda Sadelik
Fiyatlar, faturalar genellikle kuruşa/tam sayıya yuvarlanarak
okunabilirlik kazanır.
""")

_add("Pre-Algebra", ["Relationship of numbers"], """
Sayılar arasındaki ilişki, iki sayının birbirine göre "nerede durduğunu"
(büyük/küçük/eşit) veya nasıl bağlı olduğunu (kat, bölen gibi) tanımlar.

Nedir?
Sayı doğrusunda solda kalan sayı sağdakinden küçüktür ($<$); eşitlik ($=$)
ve büyüklük ($>$) ile birlikte bu üç ilişki her iki sayıyı karşılaştırmaya
yeter (Trichotomy — Üçe Ayrım İlkesi).

Ne İçin Kullanılır?
1. Sıralama ve Karar Verme Algoritmaları
Bilgisayarların veri sıralaması (küçükten büyüğe dizme) doğrudan bu
karşılaştırma ilişkisine dayanır.
2. Eşitsizliklerin Temelini Kurmak
Daha ileri eşitsizlik çözme, aralık bulma gibi konuların ön koşuludur.
""")

_add("Pre-Algebra", ["Dividing scientfic notation", "Estimating scientific notation",
                                         "Multiplying and dividing scientific notation", "Multiplying scientific notation"], """
Bilimsel gösterimde çarpma/bölme, "sayı kısmını" ve "10'un kuvvetini" AYRI
AYRI işleyip sonra tekrar birleştirmektir.

Nedir?
$(a\\times10^m)\\times(b\\times10^n) = (a\\times b)\\times10^{m+n}$;
bölmede ise üsler çıkarılır: $10^{m-n}$. Sonuç, $1\\le|a{\\times}b|<10$
olacak şekilde yeniden düzenlenir.

Ne İçin Kullanılır?
1. Astronomi ve Fizik Hesaplarını Hızlandırmak
İki gezegen arası kütleçekim kuvveti gibi devasa/minik sayılar içeren
hesaplar, üsleri ayrı toplayıp sayı kısmını çarparak çok daha hızlı
yapılır.
2. Hesap Makinesi ve Yazılımda Taşma Kontrolü
Çok büyük/küçük sayılarla çalışan yazılımlar bu ayrıştırılmış temsili
kullanarak sayısal taşmayı (overflow) önler.
""")

# ---------------------------------------------------------------------------
# Algebra — round 2 (part 1: functions, graphing, properties)
# ---------------------------------------------------------------------------
_add("Algebra", ["Vertical Line Test", "Testing for functions"], """
Dikey Çizgi Testi, bir grafiğin GERÇEKTEN bir fonksiyon olup olmadığını
saniyeler içinde söyler — bir fonksiyon, her girdiye tek bir çıktı vermek
zorundadır.

Nedir?
Grafiğin üzerinden herhangi bir yerde dikey bir çizgi geçirildiğinde,
çizgi eğriyi BİRDEN FAZLA noktada kesiyorsa, bu grafik bir fonksiyon
DEĞİLDİR (aynı $x$ için iki farklı $y$ demektir).

Ne İçin Kullanılır?
1. Bir İlişkinin Fonksiyon Olup Olmadığını Hızla Belirlemek
Bir çember denklemi neden "fonksiyon değil" olarak sınıflandırılır —
bu testle anında görülür.
2. Ters Fonksiyon Almaya Uygunluğu Ön Kontrol Etmek
Bir fonksiyonun tersini almadan önce orijinalin geçerli bir fonksiyon
olduğunu doğrulamanın ilk adımıdır.
""")

_add("Algebra", ["Even, odd, or neither"], """
Bir fonksiyonun çift/tek olması, grafiğinin bir SİMETRİ türü taşıyıp
taşımadığını söyler — çift fonksiyonlar ayna gibi, tek fonksiyonlar 180°
döndürülmüş gibi simetriktir.

Nedir?
$f(-x)=f(x)$ ise fonksiyon ÇİFTTİR (y-eksenine göre simetrik, örn.
$x^2$). $f(-x)=-f(x)$ ise TEKTİR (orijine göre simetrik, örn. $x^3$).
İkisi de değilse "ne çift ne tek"tir.

Ne İçin Kullanılır?
1. Grafik Çizmeyi Yarıya İndirmek
Bir fonksiyonun simetrisini bilmek, grafiğin yarısını çizip diğer yarısını
"yansıtarak" tamamlamanı sağlar.
2. Fourier Analizinde Sinyal Ayrıştırma
Ses ve görüntü işlemede kullanılan Fourier serileri, her sinyali çift
(kosinüs) ve tek (sinüs) parçalara ayırarak analiz eder.
""")

_add("Algebra", ["Graphing linear equations", "Graphing inequalities on a number line",
                                  "Graphing inequalities in the plane", "Graphing conjunctions on a number line",
                                  "Graphing disjunctions on a number line"], """
Doğru ve eşitsizlik grafikleri, cebirsel bir ifadeyi GÖRSEL bir bölgeye
dönüştürür — bir denklemin "hangi noktalardan geçtiğini", bir eşitsizliğin
"hangi bölgeyi kapsadığını" gösterir.

Nedir?
Bir doğru, $y=mx+b$ formundaki tüm $(x,y)$ çözümlerinin kümesidir.
Eşitsizlikte ($y<mx+b$ gibi) sınır doğrusunun bir tarafındaki TÜM bölge
taranır; "ve" (conjunction) iki koşulun KESİŞİMİNİ, "veya" (disjunction)
BİRLEŞİMİNİ gösterir.

Ne İçin Kullanılır?
1. Kısıtları Görselleştirmek
"Bütçe en fazla 500 TL VE en az 3 ürün" gibi çoklu kısıtları içeren
kararları görsel bölge olarak ifade etmek, doğrusal programlamanın
(işletmede kaynak optimizasyonu) temelidir.
2. Çözüm Kümesini Sezgisel Kılmak
Bir eşitsizlik sisteminin ortak çözüm bölgesini (uygun bölge) tek bakışta
görmeyi sağlar.
""")

_add("Algebra", ["Graphing circles", "Center and radius of a circle"], """
Çemberin grafiği, sabit bir merkezden hep aynı uzaklıkta olan noktaların
oluşturduğu şekli çizer.

Nedir?
Merkezi $(h,k)$, yarıçapı $r$ olan çemberin denklemi
$(x-h)^2+(y-k)^2=r^2$'dir — bu, Pisagor Teoremi'nin merkez ile çember
üzerindeki herhangi bir nokta arasına uygulanmış hâlidir.

Ne İçin Kullanılır?
1. Konum Tabanlı Kapsama Alanı Hesabı
Bir cep telefonu kulesinin sinyal kapsama alanı, bir GPS'in "bu yarıçap
içinde" araması çember denklemiyle modellenir.
2. Çarpışma ve Mesafe Kontrolü (Oyun Geliştirme)
Video oyunlarında iki dairesel nesnenin çarpışıp çarpışmadığını kontrol
etmek bu denklemin bir uygulamasıdır.
""")

_add("Algebra", ["Graphing parabolas"], """
Parabol grafiği, ikinci derece bir denklemin "U" biçimli eğrisini çizer —
tepe noktası, ekseni ve açıklığı denklemin katsayılarından okunur.

Nedir?
$y=a(x-h)^2+k$ formunda, $(h,k)$ tepe noktasıdır; $a$'nın işareti
parabolün yukarı ($a>0$) veya aşağı ($a<0$) açıldığını, büyüklüğü ise
"ne kadar dar/geniş" olduğunu belirler.

Ne İçin Kullanılır?
1. Atış Hareketini Modellemek
Bir topun, roketin ya da su fıskiyesinin çizdiği yol yerçekimi altında
parabolik bir eğridir.
2. Anten ve Reflektör Tasarımı
Çanak antenler ve far reflektörleri, parabolün tüm paralel ışınları TEK
bir odak noktasında topladığı geometrik özelliğinden yararlanır.
""")

_add("Algebra", ["Graphing exponential functions", "Graphing transformations of exponential functions",
                                  "Graphing transformations of log functions"], """
Üstel ve logaritmik fonksiyonların grafikleri, "hızla büyüyen/azalan"
süreçleri (üstel) ve bunların "tersini" (logaritmik) görselleştirir.

Nedir?
$y=a\\cdot b^x$ grafiği $b>1$ iken hızla yükselir, $0<b<1$ iken hızla
sıfıra yaklaşır. Kaydırma ($+k$), yansıtma (işaret) ve ölçekleme ($a$
katsayısı) gibi dönüşümler bu temel grafiği kaydırır/çevirir/gerer.

Ne İçin Kullanılır?
1. Büyüme/Azalma Senaryolarını Görsel Karşılaştırmak
Farklı faiz oranlarının veya farklı yayılma hızlarının grafiklerini
üst üste koyup karşılaştırmak için kullanılır.
2. Veri Bilimi ve Modellemede Uygun Fonksiyonu Seçmek
Bir verinin üstel mi yoksa logaritmik mi büyüdüğünü grafikten tanımak,
doğru modeli seçmenin ilk adımıdır.
""")

_add("Algebra", ["Transitive Property"], """
Geçişme özelliği, "A ile B eşitse, B ile C de eşitse, A ile C de eşit
olmalı" der — zincirleme bir mantık kuralıdır.

Nedir?
Eğer $a=b$ ve $b=c$ ise, $a=c$'dir. Aynı mantık $<$ ve $>$ için de
geçerlidir: $a<b$ ve $b<c$ ise $a<c$'dir.

Ne İçin Kullanılır?
1. Cebirsel İspatların ve Denklem Çözümünün Temeli
Bir denklem zincirinde ara adımları birbirine bağlamanın (örn.
$x=2y, 2y=10 \\Rightarrow x=10$) mantıksal gerekçesidir.
2. Geometrik İspatlarda Mantık Zinciri Kurmak
"Açı A açı B'ye eşit, açı B açı C'ye eşit, öyleyse A=C" türü geometri
ispatlarında kullanılır.
""")

_add("Algebra", ["Variables", "Understood 1", "Identifying multiplication"], """
Değişken, bilinmeyen ya da değişebilen bir miktarı temsil eden bir HARFTİR
— cebirin sayılardan farkı, artık belirli bir sayı yerine "herhangi bir
sayı olabilir" diyebilmesidir.

Nedir?
$x, y, n$ gibi harfler sayıların yerini tutar. Bir değişkenin önünde
görünmeyen katsayı "1" kabul edilir (Understood 1: $x = 1x$). Bitişik
yazılmış bir harf ve sayı ($3x$) ya da iki harf ($xy$) çarpma işlemini
ifade eder.

Ne İçin Kullanılır?
1. Genel Kuralları Tek Bir İfadeyle Yazmak
"Herhangi iki sayının toplamı sırayla değişmez" kuralını $a+b=b+a$ olarak
TEK bir ifadeyle, sonsuz sayı çifti için yazmayı sağlar.
2. Programlamanın Temel Yapı Taşı
Yazılımdaki her "değişken" (variable) kavramı doğrudan bu cebirsel
fikirden gelir.

📜 Tarih ve Biyografi
Bilinmeyenler İÇİN harf kullanma fikri eskiye dayansa da, hem bilinen hem
bilinmeyen miktarlar için sistematik olarak harf kullanmayı (bugünkü
"sembolik cebiri") Fransız matematikçi François Viète 1591'de "In Artem
Analyticem Isagoge" adlı eserinde başlattı — bu, cebir tarihinde bir
dönüm noktası kabul edilir.
""")

_add("Algebra", ["Direct variation", "Inverse variation"], """
Doğru ve ters orantı, iki değişkenin birbirine nasıl BAĞLI değiştiğini
tarif eden iki temel ilişki türüdür.

Nedir?
Doğru orantıda ($y=kx$) biri artarken diğeri de aynı oranda artar (hız
sabitken, zaman arttıkça mesafe artar gibi). Ters orantıda ($y=k/x$) biri
artarken diğeri azalır (sabit bir işi daha çok işçiyle daha kısa sürede
bitirmek gibi).

Ne İçin Kullanılır?
1. Fizik Formüllerini Sınıflandırmak
Kuvvet-ivme (doğru orantı), basınç-hacim (Boyle Yasası, ters orantı) gibi
birçok fizik yasası bu iki kalıptan birine uyar.
2. Kaynak Planlamasında Hızlı Tahmin
"İşçi sayısını iki katına çıkarırsam süre yarıya iner mi?" gibi soruları
hızla cevaplamayı sağlar.
""")

_add("Algebra", ["Modeling a piecewise-defined function"], """
Parçalı fonksiyon, TEK bir kuralın yetmediği, aralığa göre FARKLI kuralların
geçerli olduğu durumları modelleyen bir fonksiyondur.

Nedir?
$f(x) = x^2$ ($x<0$ için) veya $f(x) = x+1$ ($x\\ge 0$ için) gibi,
her aralık için ayrı bir formül tanımlanır.

Ne İçin Kullanılır?
1. Kademeli Fiyatlandırma ve Vergi Dilimleri
Elektrik faturası, gelir vergisi gibi "belirli bir eşiğe kadar bu oran,
sonrasında başka oran" mantığıyla işleyen sistemler parçalı fonksiyondur.
2. Mutlak Değer ve Basamak Fonksiyonlarının Temeli
$|x|$ fonksiyonunun kendisi aslında iki parçalı bir fonksiyondur.
""")

_add("Algebra", ["Common bases and restricted values", "Zero Theorem"], """
Ortak taban yöntemi, üstel bir denklemi HIZLICA çözmenin bir yoludur;
Sıfır Teoremi (Sıfır Çarpım Özelliği) ise bir çarpımın sıfır olmasının
tek yolunun çarpanlardan EN AZ BİRİNİN sıfır olması gerektiğini söyler.

Nedir?
$b^x = b^y$ ise (taban aynıysa) $x=y$'dir — üsleri karşılaştırmak yeter.
Sıfır Teoremi: $ab=0$ ise $a=0$ VEYA $b=0$'dır; bu, çarpanlara ayırarak
denklem çözmenin (örn. ikinci derece denklemler) temel dayanağıdır.

Ne İçin Kullanılır?
1. Üstel Denklemleri Cebirsel Yoldan Çözmek
Logaritma almadan, sadece tabanları eşitleyerek hızlı çözüm sağlar.
2. Çarpanlara Ayırarak Denklem Çözmenin Gerekçesi
"Neden çarpanlara ayırıp her birini sıfıra eşitliyoruz?" sorusunun
matematiksel cevabıdır.
""")

# ---------------------------------------------------------------------------
# Algebra — round 2 (part 2: polynomials, factoring, rational)
# ---------------------------------------------------------------------------
_add("Algebra", ["Adding and subtracting like terms", "Adding and subtracting polynomials",
                                  "Multiplying and dividing like terms", "Multiplying polynomials",
                                  "Multiplying multivariable polynomials", "Dividing polynomials",
                                  "Dividing multivariable polynomials"], """
Polinom işlemleri, birden çok terimli ifadeleri (çok terimliler) toplama,
çıkarma, çarpma ve bölme kurallarıdır — "benzer terimleri" bir araya
getirmek, sayısal aritmetiğin cebirsel karşılığıdır.

Nedir?
Benzer terimler (aynı değişken ve aynı üs, örn. $3x^2$ ve $5x^2$) sadece
katsayıları toplanarak/çıkarılarak birleştirilir. Çarpmada dağılma
özelliği (her terim diğer her terimle çarpılır — "FOIL" bunun iki terimli
özel hâlidir), bölmede ise uzun bölme veya sentetik bölme kullanılır.

Ne İçin Kullanılır?
1. Mühendislik ve Fizik Formüllerini Sadeleştirmek
Karmaşık bir sistemin toplam davranışını tek bir polinomla ifade edip
sadeleştirmek, hesaplamayı yönetilebilir kılar.
2. Bilgisayar Cebiri Sistemlerinin (CAS) Temeli
Wolfram Alpha, MATLAB gibi yazılımların sembolik sadeleştirme motorları
bu kuralların otomatikleştirilmiş hâlidir.
""")

_add("Algebra", ["Difference of squares", "Difference of cubes", "Sum of cubes",
                                  "Completing the square", "Grouping", "Factoring to find a common denominator"], """
Çarpanlara ayırma kalıpları, bir ifadeyi TOPLAM biçiminden ÇARPIM
biçimine dönüştürmenin kısayollarıdır — bir ifadeyi çarpanlarına ayırmak,
onu daha basit parçalara "bölmek" gibidir.

Nedir?
İki kare farkı: $a^2-b^2=(a-b)(a+b)$. Küp farkı/toplamı için benzer
kalıplar vardır. Gruplama, dört terimli bir ifadeyi ikişerli gruplara
ayırıp ortak çarpan çıkarır. Kareye tamamlama, $x^2+bx$ ifadesini
$(x+b/2)^2$ biçimine getirerek ikinci derece denklemleri çözer (ve
kuadratik formülün KENDİSİ bu yöntemle türetilir).

Ne İçin Kullanılır?
1. Denklemleri Sıfır Çarpım Özelliğiyle Çözmek
Bir denklemi çarpanlarına ayırmak, onu "A çarpı B sıfır" biçimine
getirerek çözmenin en hızlı yoludur.
2. Rasyonel İfadeleri Sadeleştirmek
Karmaşık kesirli ifadeleri sadeleştirmenin ilk adımı genellikle pay ve
paydayı çarpanlarına ayırmaktır.

📜 Tarih ve Biyografi
Kareye tamamlama yöntemi, ikinci derece denklemleri çözmek için Fars
matematikçi el-Harezmi tarafından MS 820'de geometrik bir yöntem olarak
sistemleştirildi — kuadratik formülün cebirsel kökeni budur.
""")

_add("Algebra", ["Complex fractions", "Proportions with complex fractions"], """
Bileşik (karmaşık) kesir, payında veya paydasında YİNE bir kesir bulunan
kesirdir — "kesir içinde kesir" durumudur.

Nedir?
$\\dfrac{1/2}{3/4}$ gibi bir ifade, iç kesirleri bölme işlemine
çevirerek ($\\frac{1}{2} \\div \\frac{3}{4}$) veya tüm ifadeyi ortak bir
paydayla çarparak sadeleştirilir.

Ne İçin Kullanılır?
1. Fizikte Birleşik Direnç/Odak Uzaklığı Formülleri
Paralel dirençlerin toplam direnci ($1/R = 1/R_1+1/R_2$) gibi formüller
çözülürken bileşik kesirlerle karşılaşılır.
2. Oran Problemlerini Sadeleştirmek
İki oranın oranını almayı gerektiren karışık problemleri yönetilebilir
hâle getirir.
""")

_add("Algebra", ["Rational equations", "Fractional equations", "Adding and subtracting rational functions",
                                  "Multiplying rational functions", "Dividing rational functions",
                                  "Simplifying rational functions", "Multivariable rational equations"], """
Rasyonel ifadeler, payı ve paydası polinom olan kesirlerdir — sayısal
kesirlerle aynı kurallarla toplanır, çıkarılır, çarpılır, bölünür ve
sadeleştirilir, ama artık değişken içerirler.

Nedir?
$\\dfrac{P(x)}{Q(x)}$ biçimindeki bir ifadede $Q(x)\\neq0$ olmalıdır.
Rasyonel bir DENKLEM çözerken önce paydaları eşitleyip (veya çapraz
çarparak) kesirlerden kurtulunur, sonra elde edilen polinom denklem
çözülür — ama bulunan kökler orijinal paydaları sıfır YAPMAMALIDIR
(yabancı kök kontrolü).

Ne İçin Kullanılır?
1. Oran/Hız Problemlerini Modellemek
"İki musluk birlikte havuzu ne kadar sürede doldurur?" gibi klasik "iş"
problemleri rasyonel denklemlerle çözülür.
2. Mühendislikte Transfer Fonksiyonları
Kontrol sistemleri mühendisliğinde bir sistemin girdi-çıktı davranışı
rasyonel fonksiyonlarla (transfer fonksiyonu) modellenir.
""")

_add("Algebra", ["Rationalizing the denominator", "Rationalizing complex denominators",
                                  "Rationalizing with conjugate method", "Radical equations"], """
Paydayı rasyonelleştirme, bir kesrin paydasındaki "rahatsız edici" kökü
(veya karmaşık sayıyı) TEMİZLEYİP paydayı sade bir tam sayı hâline
getirmektir.

Nedir?
$\\dfrac{1}{\\sqrt{2}}$ ifadesi, pay ve payda $\\sqrt{2}$ ile çarpılarak
$\\dfrac{\\sqrt{2}}{2}$'ye dönüştürülür. Payda iki terimliyse (örn.
$\\sqrt{a}+\\sqrt{b}$), eşlenik (conjugate — işareti ters versiyon,
$\\sqrt{a}-\\sqrt{b}$) ile çarpılarak iki kare farkı kalıbı kullanılır ve
kökler paydadan temizlenir. Kök içeren denklemler (radical equations) ise
her iki tarafın kuvvetini alarak köklerden kurtulur — ama bu işlem
YABANCI KÖK üretebileceğinden bulunan çözümler mutlaka orijinal denklemde
kontrol edilmelidir.

Ne İçin Kullanılır?
1. Geleneksel Olarak "Temiz" Sonuç Sunmak
Matematikte paydada kök bırakmamak, sonucu karşılaştırmayı ve elle
işlemeyi kolaylaştıran bir gelenektir (bilgisayar öncesi dönemden kalma).
2. Limit ve Türev Hesaplarında Belirsizliği Gidermek
Kalkülüste $0/0$ türü belirsiz limitleri çözmenin standart
tekniklerinden biri, paydayı eşlenikle rasyonelleştirmektir.
""")

_add("Algebra", ["Fractional exponents", "Negative exponents", "Negative exponents and product rule",
                                  "Powers of fractions", "Powers of negative bases", "Zero as an exponent"], """
Kesirli ve negatif üsler, üs kurallarını KÖK ve TERS almaya kadar
genişletir — üslü sayı sistemi böylece tüm rasyonel sayılarla tutarlı
çalışır.

Nedir?
$a^{1/n} = \\sqrt[n]{a}$ (kesirli üs = kök), $a^{-n} = 1/a^n$ (negatif üs
= ters), $a^0=1$ ($a\\neq0$). Negatif tabanlı üslerde ($(-2)^3=-8$ ama
$(-2)^2=4$) üssün TEK/ÇİFT olması sonucun işaretini belirler.

Ne İçin Kullanılır?
1. Kök İfadelerini Üs Diliyle Birleştirmek
$\\sqrt[3]{x^2}$ gibi ifadeleri $x^{2/3}$ olarak yazmak, türev/integral
alma gibi ileri işlemleri kolaylaştırır (kalkülüs kuralları üslerle çok
daha kolay uygulanır).
2. Çok Küçük Sayıları İfade Etmek
Negatif üsler, atom altı parçacık boyutları gibi çok küçük büyüklükleri
(örn. $10^{-9}$ metre) ifade etmenin standart yoludur.

📜 Tarih ve Biyografi
Kesirli ve negatif üslerin sistemli cebirsel kuralları, İngiliz
matematikçi John Wallis tarafından 1656'da "Arithmetica Infinitorum"
adlı eserinde ortaya kondu.
""")

_add("Algebra", ["Balancing equations", "Simple equations", "Decimal equations",
                                  "Equations with subscripts", "Multivariable equations", "Two-step problems",
                                  "Evaluating expressions"], """
Denklem çözmenin temeli, bir TERAZİYİ dengede tutmaktır — denklemin bir
tarafına ne yaparsan (topla, çıkar, çarp, böl), diğer tarafa da AYNISINI
yapman gerekir, aksi hâlde terazi (eşitlik) bozulur.

Nedir?
Bir denklemi çözmek, ters işlemleri sırayla uygulayarak bilinmeyeni YALNIZ
bırakmaktır. İki adımlı denklemler önce toplama/çıkarma sonra
çarpma/bölme gerektirir. Bir ifadeyi "değerlendirmek" (evaluate), verilen
sayısal değerleri yerine koyup sonucu hesaplamaktır.

Ne İçin Kullanılır?
1. Her Türlü Bilinmeyeni Bulmanın Evrensel Yöntemi
Fizikten finansa, mühendislikten günlük hesaplara kadar "bilinmeyeni
bulma" ihtiyacının tamamı bu temel tekniğe dayanır.
2. Programlamada Değişken Atama ve Hesaplama
Bir formülü koda dökmek, önce onu elle "değerlendirebilmeyi" gerektirir.
""")

_add("Algebra", ["Inequalities and negative numbers", "Trichotomy"], """
Eşitsizliklerde negatif sayılarla çarpma/bölme özel bir kural gerektirir:
işlemi yaparken eşitsizliğin YÖNÜ TERS ÇEVRİLİR.

Nedir?
$-2x < 6$ denkleminde her iki tarafı $-2$'ye bölerken $x > -3$ olur
(yön değişir) — çünkü negatifle çarpma/bölme sayı doğrusundaki sıralamayı
tersine çevirir. Trichotomy (Üçe Ayrım İlkesi), herhangi iki gerçek
sayının ya birbirine eşit, ya biri diğerinden büyük, ya da küçük
olduğunu — üçüncü bir olasılık olmadığını söyler.

Ne İçin Kullanılır?
1. Eşitsizlik Çözümünde En Sık Yapılan Hatayı Önlemek
Yön değiştirme kuralını unutmak, eşitsizlik problemlerinde öğrencilerin
en sık düştüğü hatadır; bu kuralı bilmek doğru çözümü garanti eder.
2. Sıralama Temelli Algoritmaların Mantığını Kurmak
Bilgisayar bilimindeki her karşılaştırma tabanlı sıralama algoritması bu
üç kesin durumdan birinin geçerli olacağı varsayımına dayanır.
""")

_add("Algebra", ["Age word problems", "Number word problems", "Consecutive integers",
                                  "Uniform motion problems", "Word problems into equations", "Equation modeling",
                                  "Sketching graphs from story problems"], """
Sözel problemler, günlük dildeki bir durumu CEBİRSEL bir denkleme
çevirme becerisidir — matematiğin gerçek dünyaya uygulanmasının ilk ve en
önemli adımı budur.

Nedir?
Bilinmeyen miktara bir değişken atanır (genelde $x$), problemdeki
ilişkiler ("toplamları", "3 fazlası", "sabit hızla") denklem parçalarına
çevrilir ve elde edilen denklem çözülür. Ardışık tam sayılar $n, n{+}1,
n{+}2,\\ldots$ olarak; sabit hızlı hareket problemleri "mesafe = hız ×
zaman" ($d=vt$) formülüyle ifade edilir.

Ne İçin Kullanılır?
1. Matematiği Gerçek Kararlara Bağlamak
İki aracın ne zaman buluşacağı, bir yatırımın ne zaman ikiye katlanacağı
gibi gerçek hayat sorularının hepsi önce bir denkleme çevrilir.
2. Mühendislik ve Bilimde Problem Çözmenin İlk Adımı
Karmaşık mühendislik problemlerinin çözümü de aynı şekilde başlar: önce
sözel/fiziksel durumu matematiksel bir modele (denkleme) dönüştürmek.
""")

_add("Algebra", ["Calculating commision", "Calculating simple interest", "Percent markdown",
                                  "Percent markup", "Fractions to decimals to percents"], """
Yüzde tabanlı hesaplar (komisyon, faiz, indirim, zam), bir miktarın belirli
bir ORANININ nasıl hesaplanacağını gösterir — hepsi aynı "yüzde × taban
miktar" mantığına dayanır.

Nedir?
Basit faiz $I = P \\cdot r \\cdot t$ (anapara × oran × süre) formülüyle
hesaplanır. İndirim (markdown), fiyattan bir yüzde düşülmesi; zam
(markup), fiyata bir yüzde eklenmesidir. Kesir–ondalık–yüzde arasındaki
geçiş ($3/4 = 0.75 = \\%75$), aynı miktarın üç farklı gösterimidir.

Ne İçin Kullanılır?
1. Kişisel Finans Okuryazarlığı
Kredi faizi, mevduat getirisi, satış komisyonu, indirimli fiyat
hesaplarının hepsi bu formüllerle yapılır.
2. Perakende ve İşletme Fiyatlandırması
Bir ürünün maliyetinden satış fiyatına nasıl ulaşıldığı (kâr marjı, zam)
bu yüzde mantığıyla hesaplanır.

📜 Tarih ve Biyografi
Basit faiz hesaplamalarına dair en eski kayıtlar, MÖ 2000 civarına
tarihlenen Babil kil tabletlerinde bulunur — bu, matematiğin en eski
pratik ticari uygulamalarından biridir.
""")

_add("Algebra", ["Chemical compounds"], """
Kimyasal bileşik problemleri, cebirin kimya ile kesiştiği noktadır —
karışım problemleri, bir çözeltinin konsantrasyonunu değişkenle ifade
edip denklem kurmayı gerektirir.

Nedir?
İki farklı derişimdeki karışımı birleştirip istenen üçüncü bir derişime
ulaşmak, "derişim × miktar" toplamlarının eşitliğine dayanan bir denklem
sistemidir.

Ne İçin Kullanılır?
1. Laboratuvar ve Endüstriyel Karışım Hesapları
İlaç üretiminde, gıda endüstrisinde belirli bir konsantrasyona ulaşmak
için ne kadar karıştırılacağını hesaplamak bu tür denklemlerle yapılır.
2. Cebirin Disiplinler Arası Gücünü Göstermek
Aynı denklem kurma mantığının hem finans (karışık faiz oranları) hem
kimya problemlerinde işlediğini gösterir.
""")

_add("Algebra", ["Systems of three equations", "Systems with subscripts",
                                  "Systems with quadratic inequalities"], """
Üç bilinmeyenli sistemler ve karma sistemler, iki değişkenli sistem
mantığını daha fazla bilinmeyene veya farklı denklem türlerine
genişletir.

Nedir?
Üç denklem üç bilinmeyenle, sırayla bir değişkeni yok ederek (elimination)
iki denklem iki bilinmeyene indirgenir. Kuadratik eşitsizlik içeren
sistemlerde ise hem doğrusal hem parabolik sınırların KESİŞTİĞİ bölge
aranır.

Ne İçin Kullanılır?
1. Çok Değişkenli Gerçek Dünya Problemleri
Üç farklı ürünün üretim planlaması gibi üç kısıtlı problemler bu şekilde
modellenir.
2. Karma Kısıtlı Optimizasyon
Hem doğrusal hem eğrisel sınırları olan gerçek kaynak planlaması
problemlerinde kullanılır.
""")

# ---------------------------------------------------------------------------
# Geometry — round 2
# ---------------------------------------------------------------------------
_add("Geometry", ["Acute, obtuse, and right triangles", "Scalene, isosceles, and equilateral triangles",
                                  "Isosceles Triangle Theorem"], """
Üçgen sınıflandırması, açılarına (dar/dik/geniş) veya kenar uzunluklarına
(çeşitkenar/ikizkenar/eşkenar) göre yapılır — her sınıf, farklı garantili
özellikler taşır.

Nedir?
Açıya göre: tüm açıları 90°'den küçükse DAR, biri 90° ise DİK, biri
90°'den büyükse GENİŞ üçgendir. Kenara göre: tüm kenarları farklıysa
ÇEŞİTKENAR, ikisi eşitse İKİZKENAR, üçü eşitse EŞKENAR üçgendir.
İkizkenar Üçgen Teoremi, eşit kenarların karşısındaki açıların da eşit
olduğunu söyler.

Ne İçin Kullanılır?
1. Yapısal Mühendislikte Kararlılık
Üçgenler tek şekilde "kilitlenen" (rijit) tek çokgen olduğu için köprü ve
çatı kafeslerinde neredeyse hep üçgen kullanılır; üçgen türü malzeme
dağılımını belirler.
2. Trigonometrinin Ön Koşulu
Hangi trigonometrik oranların (sinüs, kosinüs) uygulanabileceği, üçgenin
dik olup olmamasına bağlıdır.
""")

_add("Geometry", ["30-60-90 triangles", "45-45-90 triangles"], """
Özel dik üçgenler, kenar oranları HER ZAMAN aynı olan iki "şablon"
üçgendir — bir açıyı bilmen, diğer tüm kenarları oranla hesaplamana
yeter.

Nedir?
30-60-90 üçgeninde kenar oranı $1 : \\sqrt3 : 2$'dir; 45-45-90 (ikizkenar
dik) üçgende oran $1 : 1 : \\sqrt2$'dir. Bu oranlar doğrudan Pisagor
Teoremi'nden türetilir.

Ne İçin Kullanılır?
1. Trigonometrik Değerleri Hesap Makinesiz Bulmak
$\\sin 30°, \\cos 45°$ gibi "özel açı" değerlerinin tam kesirli/kök
biçimleri bu üçgenlerden gelir.
2. Hızlı Ölçüm ve Tasarım Hesapları
Mimarlıkta çatı eğimi, marangozlukta 45° kesim gibi standart açılarla
çalışırken kenar uzunluklarını hızlıca hesaplamayı sağlar.
""")

_add("Geometry", ["Median, centroid, and altitude"], """
Üçgenin özel doğruları (kenarortay, yükseklik) ve bunların kesişim
noktaları (ağırlık merkezi), üçgenin geometrik "iskeletini" oluşturur.

Nedir?
Kenarortay (median), bir köşeyi karşı kenarın orta noktasına birleştirir;
üç kenarortay AĞIRLIK MERKEZİNDE (centroid) kesişir. Yükseklik (altitude),
bir köşeden karşı kenara (veya uzantısına) inen dik doğrudur.

Ne İçin Kullanılır?
1. Fizikte Kütle Merkezi Hesabı
Üçgen biçimli düz bir levhanın gerçek denge/ağırlık merkezi tam olarak
centroid noktasındadır.
2. Bilgisayar Grafiklerinde Üçgen Ağlarının (Mesh) İşlenmesi
3B modellerin yüzeyini oluşturan üçgen ağlarında, ağırlık merkezi
hesaplamaları ışıklandırma ve normal vektör hesaplarında kullanılır.
""")

_add("Geometry", ["Adjacent and nonadjacent angles", "Complementary and supplementary angles",
                                  "Vertical angles", "Angles and transversals", "Measures of angles"], """
Açı ilişkileri, iki veya daha fazla açının BİRBİRİNE göre nasıl konumlandığını
ve bu konumun açı ölçülerini nasıl bağladığını tarif eder.

Nedir?
Tümler (complementary) açılar toplamı 90°, bütünler (supplementary)
açılar toplamı 180°'dir. Ters açılar (vertical angles, iki doğrunun
kesişiminde karşılıklı oluşan açılar) HER ZAMAN eşittir. Bir kesen
(transversal) iki paralel doğruyu kestiğinde, oluşan açı çiftleri
(iç ters açı, dış ters açı, karşılık açılar) belirli eşitlik/tümleyicilik
kurallarına uyar.

Ne İçin Kullanılır?
1. Geometrik İspatların En Sık Kullanılan Aracı
Neredeyse her geometri ispatı bu temel açı ilişkilerinden en az birini
kullanır.
2. Mimarlık ve Mühendislikte Açı Kontrolü
Bir çatının, bir yolun kesişiminin doğru açıda olup olmadığını doğrulamak
bu ilişkilere dayanır.
""")

_add("Geometry", ["Angle bisectors and trisectors", "Perpendicular and angle bisectors"], """
Açıortay, bir açıyı TAM ORTADAN ikiye bölen ışındır — açının her iki
kenarına da eşit uzaklıkta kalan noktaların oluşturduğu yoldur.

Nedir?
Bir açıortay, açıyı iki eşit parçaya ayırır. Dikme (perpendicular
bisector), bir doğru parçasını ortadan dik olarak keser ve bu doğru
üzerindeki her nokta, parçanın iki ucuna eşit uzaklıktadır.

Ne İçin Kullanılır?
1. Üçgende İç Teğet Çemberi Bulmak
Bir üçgenin üç açıortayının kesiştiği nokta, üçgene içten teğet olan
çemberin (iç teğet çember) merkezidir.
2. Eşit Uzaklık Gerektiren Tasarım Problemleri
İki noktaya (örn. iki şehre) eşit uzaklıkta bir nokta bulmak (yeni bir
tesis yeri seçmek gibi) dikme mantığını kullanır.
""")

_add("Geometry", ["Convex and concave polygons", "Interior angles of polygons",
                                  "Exterior angles of polygons", "Interior angles of triangles", "Quadrilaterals"], """
Çokgen açı kuralları, kenar sayısı arttıkça iç açı toplamının nasıl
DÜZENLİ biçimde arttığını gösterir.

Nedir?
$n$ kenarlı bir çokgenin iç açıları toplamı $(n-2)\\times180°$'dir (bir
üçgenin iç açı toplamı olan 180° buradan $n=3$ için çıkar). Dış açıların
toplamı ise KENAR SAYISINDAN BAĞIMSIZ olarak her zaman 360°'dir.
Dışbükey (convex) bir çokgende tüm iç açılar 180°'den küçüktür; en az bir
açı 180°'yi aşıyorsa çokgen içbükeydir (concave).

Ne İçin Kullanılır?
1. Mimari ve Tasarımda Çokgen Planlama
Düzgün çokgen şeklindeki bir yapının (altıgen bir oda gibi) her açısının
kaç derece olacağını önceden hesaplamayı sağlar.
2. Bilgisayar Grafiklerinde Şekil Doğrulama
Bir 3B modelin yüzeylerinin dışbükey mi içbükey mi olduğunu bilmek,
render ve çarpışma algoritmalarının doğru çalışması için gereklidir.
""")

_add("Geometry", ["Parallelograms", "Rhombuses, rectangles, and squares", "Trapezoids and kites"], """
Dörtgen aileleri, paralel/dik kenar ve köşegen özelliklerine göre iç içe
geçmiş bir hiyerarşi oluşturur — her kare aynı zamanda bir dikdörtgen VE
bir eşkenar dörtgendir, ama tersi doğru değildir.

Nedir?
Paralelkenar, karşılıklı kenarları paralel olan dörtgendir. Dikdörtgen
(tüm açıları 90°), eşkenar dörtgen (tüm kenarları eşit) ve kare (ikisi
birden) paralelkenarın özel hâlleridir. Yamuk yalnızca bir çift kenarı
paralel olan; uçurtma (kite) ise iki çift bitişik kenarı eşit olan
dörtgendir.

Ne İçin Kullanılır?
1. Yapı ve Mobilya Tasarımında Doğru Şekli Seçmek
Bir masanın, bir çerçevenin hangi köşegen/açı garantilerine sahip
olduğunu bilmek üretim toleranslarını belirler.
2. Köşegen Özelliklerinden Hızlı İspat Yapmak
Bir şeklin hangi dörtgen ailesine ait olduğunu bilmek, köşegenlerinin
birbirini ortalayıp ortalamadığı veya dik kesişip kesişmediği gibi
sonuçları anında verir.
""")

_add("Geometry", ["Area of a parallelogram", "Area of a trapezoid", "Area of a triangle",
                                  "Area of composite shapes", "Area of rhombuses and kites",
                                  "Area of squares and rectangles", "Perimeter of a polygon",
                                  "Perimeter of a quadrilateral", "Perimeter of a triangle"], """
Alan ve çevre formülleri, bir şeklin "iç yüzeyini" (alan) ve "dış
sınırını" (çevre) sayısallaştırır — bir zemine döşenecek karo miktarı
alandan, çevresine çekilecek çit miktarı çevreden hesaplanır.

Nedir?
Her çokgenin kendine özgü alan formülü vardır (üçgen: $\\frac12 taban
\\times yükseklik$; yamuk: $\\frac12(taban_1{+}taban_2)\\times yükseklik$
gibi); karmaşık (bileşik) şekiller, basit şekillere bölünüp alanları
toplanarak/çıkarılarak bulunur. Çevre ise tüm kenar uzunluklarının
toplamıdır.

Ne İçin Kullanılır?
1. İnşaat ve Peyzajda Malzeme Hesabı
Bir arazinin çit, boya, karo, çim ihtiyacını hesaplamak doğrudan alan ve
çevre formüllerine dayanır.
2. Düzensiz Arazi/Şekillerin Ölçülmesi
Gerçek dünyadaki hemen hiçbir arazi mükemmel bir dikdörtgen değildir;
bileşik şekil yaklaşımı bu düzensiz alanları hesaplanabilir kılar.
""")

_add("Geometry", ["Midsegments of triangles", "Midsegments of trapezoids"], """
Kenarortay doğru parçası (midsegment), bir şeklin iki kenarının orta
noktalarını birleştiren ve diğer kenar(lar)a her zaman PARALEL, onun
YARISI (üçgende) veya ORTALAMASI (yamukta) uzunlukta olan özel bir doğru
parçasıdır.

Nedir?
Üçgende bir kenarortay doğru parçası, üçüncü kenara paraleldir ve
uzunluğu onun yarısıdır. Yamukta ise iki yan kenarın orta noktalarını
birleştiren doğru parçası, iki tabana paraleldir ve uzunluğu
tabanların ortalamasıdır.

Ne İçin Kullanılır?
1. Ölçülemeyen Bir Uzunluğu Dolaylı Bulmak
Doğrudan ölçülemeyen bir kenar uzunluğunu, ona paralel ve ölçülebilir
bir kenarortay parçasından hesaplamayı sağlar.
2. Geometrik İspatlarda Paralellik Kanıtlamak
Bir doğru parçasının başka bir kenara paralel olduğunu kanıtlamanın
standart araçlarından biridir.
""")

_add("Geometry", ["Equation of a circle", "General form of the equation of a circle",
                                  "Special cases of the equation of a circle"], """
Çemberin analitik denklemi, geometrik bir şekli (çember) CEBİRSEL bir
ifadeye (denklem) bağlar — Descartes'ın koordinat sisteminin en temel
uygulamalarından biridir.

Nedir?
Standart form $(x-h)^2+(y-k)^2=r^2$ merkez ve yarıçapı doğrudan gösterir.
Genel form ($x^2+y^2+Dx+Ey+F=0$) ise kareye tamamlama yöntemiyle standart
forma çevrilir. Yarıçapın karesi negatif çıkarsa, denklemin gerçek bir
çemberi temsil ETMEDİĞİ (boş küme veya tek nokta) anlaşılır.

Ne İçin Kullanılır?
1. Konumsal Analiz ve Haritacılık
Bir noktanın belirli bir dairesel bölge içinde olup olmadığını cebirsel
olarak test etmeyi sağlar (örn. bir teslimat bölgesi sınırı).
2. Analitik Geometrinin Çember Uygulaması
Bir çemberle bir doğrunun veya iki çemberin kesişim noktalarını cebirsel
olarak (denklem sistemleri çözerek) bulmayı mümkün kılar.
""")

_add("Geometry", ["Inscribed angles of circles", "Properties of arcs and chords",
                                  "Intersecting chords", "Intersecting tangents and secants",
                                  "Tangent lines of circles", "Vertex on, inside, and outside the circle",
                                  "Circumscribed and inscribed circles of a triangle"], """
Çember teoremleri, bir çemberin içindeki/üzerindeki/dışındaki açıları,
kirişleri ve teğetleri birbirine bağlayan bir dizi zarif ilişkidir.

Nedir?
İç açı teoremi, çember üzerindeki bir açının gördüğü yayın yarısına eşit
olduğunu söyler. Kesişen kirişlerde, kirişlerin parçalarının çarpımları
eşittir. Teğet-kesen ilişkilerinde ise açının konumuna (çember üzerinde,
içinde, dışında) göre farklı formüller ilgili yayların toplamı/farkının
yarısını verir. Bir üçgene içten teğet olan çember (iç teğet çember,
merkezi açıortayların kesişimi) ve dıştan geçen çember (çevrel çember,
merkezi kenar orta dikmelerinin kesişimi) da bu ailedendir.

Ne İçin Kullanılır?
1. Optik ve Navigasyon Hesaplarında
Bir gözlemcinin bir yapıyı hangi açıyla gördüğünü, dairesel bir rotanın
geometrisini hesaplamada kullanılır.
2. GPS Üçgenlemesi ve Konum Belirleme
Bir noktanın üç bilinen noktaya olan mesafesinden konumunu bulmak
(triangulation), çember ve teğet ilişkilerinin bir uygulamasıdır.
""")

_add("Geometry", ["Direct proofs", "Indirect proofs", "Paragraph proofs", "Flowchart proofs",
                                  "Two-column proofs", "Coordinate proofs", "Arranging conditionals in a logical chain",
                                  "Conditionals and Euler diagrams", "Converses, inverses, and contrapositives"], """
Geometrik ispat, bir iddianın DOĞRU olduğunu, kabul edilmiş kurallardan
(aksiyom, tanım, önceden kanıtlanmış teorem) adım adım, tartışmasız bir
mantık zinciriyle göstermektir.

Nedir?
İki-sütunlu ispat, ifade ve gerekçeyi yan yana listeler; paragraf ispatı
aynı mantığı düz yazıyla anlatır; akış şeması (flowchart) ispatı adımları
oklarla bağlar. Dolaylı (indirect/çelişki ile) ispat, iddianın YANLIŞ
olduğunu VARSAYIP bir çelişkiye ulaşarak doğruluğunu gösterir. Koşullu
bir önermenin ("A ise B") karşıtı ("B ise A"), tersi ("A değilse B
değil") ve karşıt-tersi ("B değilse A değil") farklı mantıksal
değerler taşır — yalnızca karşıt-ters, orijinal önermeyle HER ZAMAN aynı
doğruluk değerine sahiptir.

Ne İçin Kullanılır?
1. Kesin/Tartışmasız Sonuçlara Ulaşmanın Tek Yolu
Bilimde ve hukukta "kanıtlanmış" ile "muhtemel" arasındaki farkı anlamak,
bu mantıksal ispat yapısını kavramaktan geçer.
2. Bilgisayar Biliminde Algoritma Doğrulama
Bir algoritmanın HER durumda doğru çalıştığını kanıtlamak (doğruluk
ispatı), burada öğrenilen aynı mantıksal ispat tekniklerini kullanır.

📜 Tarih ve Biyografi
Aksiyomlardan başlayıp mantıksal adımlarla teorem kanıtlama yöntemi, MÖ
300 civarında Euclid'in "Elementler" adlı eserinde kusursuz bir sistem
hâline getirildi ve 2000 yılı aşkın süredir matematiksel ispatın altın
standardı olarak kabul edilir. Önermeler arası ilişkileri gösteren iç
içe daireler (bugün "Venn şeması" ile karıştırılan ama ondan farklı olan
"Euler diyagramları") İsviçreli matematikçi Leonhard Euler tarafından
1768'de tanıtıldı.
""")

_add("Geometry", ["Distance and midpoint in two and three dimensions", "Length of a line segment",
                                  "Slope and midpoint of a line segment"], """
Mesafe ve orta nokta formülleri, iki nokta arasındaki uzaklığı ve tam
ortasındaki noktayı KOORDİNATLARDAN hesaplar.

Nedir?
Mesafe formülü $d=\\sqrt{(x_2{-}x_1)^2+(y_2{-}y_1)^2}$, Pisagor
Teoremi'nin koordinat düzlemine uygulanmış hâlidir (üç boyutta üçüncü bir
terim eklenir). Orta nokta ise iki ucun koordinatlarının ortalamasıdır:
$\\left(\\frac{x_1+x_2}{2}, \\frac{y_1+y_2}{2}\\right)$.

Ne İçin Kullanılır?
1. Harita ve Navigasyon Uygulamaları
İki konum arasındaki kuş uçuşu mesafeyi ve tam ortadaki buluşma noktasını
hesaplamak bu formüllerle yapılır.
2. Bilgisayar Grafiklerinde Nesne Konumlandırma
İki nesnenin tam ortasına üçüncü bir nesne yerleştirmek (örn. bir
çizginin ortasına etiket koymak) orta nokta formülünü kullanır.
""")

_add("Geometry", ["Diagonal of a right rectangular prism"], """
Dikdörtgenler prizmasının uzay köşegeni, Pisagor Teoremi'nin İKİ KEZ
art arda uygulanmasıyla üç boyuta taşınmasıdır.

Nedir?
Kenarları $a, b, c$ olan bir dikdörtgenler prizmasının köşegeni
$d=\\sqrt{a^2+b^2+c^2}$ formülüyle bulunur — önce tabanın köşegeni
($\\sqrt{a^2+b^2}$), sonra bu köşegenle yükseklik arasında ikinci kez
Pisagor uygulanır.

Ne İçin Kullanılır?
1. Ambalaj ve Nakliyede En Uzun Nesnenin Sığıp Sığmadığını Bulmak
Bir kutuya çapraz olarak sığabilecek en uzun nesnenin (örn. bir bagete)
boyunu hesaplamak bu formülle yapılır.
2. 3B Bilgisayar Grafiklerinde Sınırlayıcı Kutu Hesabı
Bir 3B nesnenin "bounding box" köşegen uzunluğu, çarpışma ve görüş alanı
hesaplarında kullanılır.
""")

_add("Geometry", ["Naming simple geometric figures"], """
Geometrik şekillerin adlandırılması, nokta, doğru, ışın ve düzlem gibi
temel yapı taşlarını standart sembollerle ifade etmenin kurallarıdır.

Nedir?
Bir nokta büyük harfle ($A$), bir doğru üzerindeki iki noktayla ve çift
yönlü ok işaretiyle ($\\overleftrightarrow{AB}$), bir ışın tek yönlü okla
($\\overrightarrow{AB}$), bir doğru parçası üstü çizgiyle
($\\overline{AB}$) gösterilir.

Ne İçin Kullanılır?
1. Belirsizliği Ortadan Kaldıran Ortak Bir Dil
Bu semboller olmadan "AB" ifadesinin bir uzunluk mu, bir doğru mu, bir
ışın mı olduğu belirsiz kalır; standart gösterim tüm geometri
literatüründe aynı anlamı garanti eder.
2. İspatlarda Kesin Referans Vermek
Bir ispatta hangi nesneden (nokta, doğru, ışın) bahsedildiğini net
biçimde belirtmek için kullanılır.
""")

# ---------------------------------------------------------------------------
# Linear Algebra — round 2
# ---------------------------------------------------------------------------
_add("Linear Algebra", ["A=LU factorization", "Upper and lower triangular matrices",
                                        "The elimination matrix"], """
LU ayrışımı, bir matrisi "alt üçgen" ve "üst üçgen" iki basit matrisin
çarpımı olarak yeniden yazar — Gauss yok etmenin adımlarını, tekrar
kullanılabilir bir biçimde "kaydeder".

Nedir?
$A = LU$; burada $L$ alt üçgen (köşegenin üstü sıfır), $U$ üst üçgen
(köşegenin altı sıfır) matristir. Bu ayrışım, Gauss yok etme sırasında
uygulanan satır işlemlerinin ("yok etme matrisleri") bir araya
toplanmasıyla elde edilir. Üst/alt üçgen matrislerde denklem çözmek,
genel bir matrisle çözmekten çok daha hızlıdır.

Ne İçin Kullanılır?
1. Aynı Sistemi Farklı Sağ Taraflarla Hızlı Tekrar Çözmek
Mühendislik simülasyonlarında $Ax=b$ sistemi FARKLI $b$ değerleriyle
tekrar tekrar çözülüyorsa, $A$'yı bir kez $LU$'ya ayırmak, her seferinde
sıfırdan Gauss yok etme yapmaktan çok daha hızlıdır.
2. Sayısal Analiz Yazılımlarının Temel Motoru
MATLAB, NumPy gibi yazılımların doğrusal sistem çözücüleri arka planda
LU ayrışımını kullanır.
""")

_add("Linear Algebra", ["Cramer's rule for solving systems"], """
Cramer Kuralı, küçük denklem sistemlerini SADECE determinant hesaplayarak
(satır işlemi yapmadan) doğrudan çözen zarif bir formüldür.

Nedir?
$Ax=b$ sisteminde $x_i = \\dfrac{\\det(A_i)}{\\det(A)}$; burada $A_i$,
$A$'nın $i$. sütununun $b$ ile değiştirilmiş hâlidir. $\\det(A)\\neq0$
olması gerekir.

Ne İçin Kullanılır?
1. Küçük Sistemlerde Hızlı, Kapalı-Form Çözüm
2×2 veya 3×3 sistemlerde Gauss yok etmeden daha hızlı, doğrudan bir
formül sunar — mühendislik ders kitaplarında sık kullanılır.
2. Bir Çözümün VARLIĞINI Teorik Olarak Kanıtlamak
Determinant sıfır değilse tek bir çözüm olduğunu GARANTİ eder; büyük
sistemlerde pratik olmasa da teorik ispatlarda değerlidir.

📜 Tarih ve Biyografi
Kural, İsviçreli matematikçi Gabriel Cramer tarafından 1750'de "Introduction
à l'analyse des lignes courbes algébriques" adlı eserinde yayımlandı;
benzer bir fikir ondan önce Japon matematikçi Seki Takakazu (1683) ve
Alman matematikçi-filozof Gottfried Leibniz (1693) tarafından da
bağımsız olarak kullanılmıştı.
""")

_add("Linear Algebra", ["Inverse of a transformation", "Inverse transformations are linear",
                                        "Invertibility from the matrix-vector product", "Matrix inverses, and invertible and singular matrices",
                                        "Solving systems with inverse matrices"], """
Matris tersi, bir dönüşümü TAM OLARAK geri alan matristir — bir kilidi
açan anahtar gibi, $A$'nın yaptığı her şeyi $A^{-1}$ geri sarar.

Nedir?
$AA^{-1}=A^{-1}A=I$ (birim matris) olacak şekilde $A^{-1}$ tanımlanır;
yalnızca $\\det(A)\\neq0$ olan (tersinir/invertible) kare matrislerin
tersi vardır — determinantı sıfır olan matrisler tekildir (singular) ve
tersi yoktur. $Ax=b$ sistemi, ters varsa $x=A^{-1}b$ ile doğrudan
çözülür.

Ne İçin Kullanılır?
1. Şifreleme ve Kod Çözme
Bir mesajı bir matrisle "şifrelemek", tersini kullanarak "çözmekle"
simetriktir — basit matris şifreleme sistemlerinin temelidir.
2. Bilgisayar Grafiklerinde Dönüşümü Geri Almak
Bir nesneyi döndürüp/ölçekledikten sonra orijinal konumuna dönmek,
uygulanan dönüşüm matrisinin tersini almayı gerektirir.
""")

_add("Linear Algebra", ["Least squares solution"], """
En küçük kareler çözümü, TAM olarak çözülemeyen (aşırı belirlenmiş) bir
sistem için "mümkün olan en iyi" yaklaşık çözümü bulur.

Nedir?
$Ax=b$ sisteminin tam çözümü yoksa (denklem sayısı bilinmeyenden fazlaysa),
$\\|Ax-b\\|$ hatasını minimize eden $x$ aranır; bu, $A^TAx=A^Tb$ normal
denklemlerini çözerek bulunur.

Ne İçin Kullanılır?
1. İstatistiksel Regresyonun Matematiksel Temeli
Bir veri bulutuna "en iyi uyan doğruyu/eğriyi" bulmak (doğrusal
regresyon) tam olarak bir en küçük kareler problemidir.
2. GPS ve Sinyal İşlemede Gürültülü Veriden Tahmin
Birden fazla, birbiriyle tam uyuşmayan (gürültülü) ölçümden en tutarlı
konumu/sinyali kestirmek bu yöntemle yapılır.

📜 Tarih ve Biyografi
Yöntem, Fransız matematikçi Adrien-Marie Legendre tarafından 1805'te
yayımlandı; ancak Alman matematikçi Carl Friedrich Gauss, yöntemi daha
önce (1795'ten beri) gökcisimlerinin yörüngesini hesaplamak için
kullandığını iddia etti — bu, matematik tarihinin bir diğer ünlü öncelik
tartışmasıdır.
""")

_add("Linear Algebra", ["Linear systems in three unknowns", "Linear systems in two unknowns",
                                        "Representing systems with matrices", "Equation of a plane, and normal vectors"], """
Doğrusal sistemleri matrisle temsil etmek, birden fazla denklemi TEK bir
$Ax=b$ ifadesine sıkıştırır — iki veya üç bilinmeyenli her sistem bu
kompakt forma dönüştürülebilir.

Nedir?
Her denklemin katsayıları $A$ matrisinin bir satırını, sabit terimler ise
$b$ vektörünü oluşturur. Üç boyutta bir düzlemin denklemi
($ax+by+cz=d$) da normal (düzleme dik) bir vektörün bileşenlerini
katsayı olarak kullanan, aynı ailenin bir üyesidir.

Ne İçin Kullanılır?
1. Bilgisayarla Büyük Sistemleri Çözmek
Yüzlerce denklemi tek bir matris ifadesi olarak yazmak, bilgisayarların
bu sistemleri verimli işleyebilmesini sağlar.
2. 3B Grafiklerde Yüzey Tanımlamak
Bir 3B modeldeki her düz yüzey, bir düzlem denklemiyle (ve onun normal
vektörüyle, ışıklandırma hesabı için) temsil edilir.
""")

_add("Linear Algebra", ["Orthogonal complements of the fundamental subspaces"], """
Ortogonal tümleyen, bir altuzaya DİK olan tüm vektörlerin oluşturduğu
yeni bir altuzaydır — bir matrisin dört temel altuzayı (satır, sütun,
null, sol null uzayı) birbirleriyle şaşırtıcı derecede düzenli dik
ilişkiler kurar.

Nedir?
Bir matrisin null uzayı, satır uzayının ortogonal tümleyenidir; sol null
uzayı da sütun uzayının ortogonal tümleyenidir — bu ilişki "Doğrusal
Cebirin Temel Teoremi" olarak bilinir.

Ne İçin Kullanılır?
1. En Küçük Kareler Çözümünün Geometrik Açıklaması
Bir vektörün bir altuzaya en yakın izdüşümünün NEDEN "hata" vektörünü
altuzaya dik bıraktığını açıklar.
2. Sinyal İşlemede Gürültüyü Yararlı Sinyalden Ayırmak
Bir sinyali "istenen" ve "istenmeyen (gürültü)" bileşenlerine ayırmak
genellikle dik altuzaylara ayrıştırmayla yapılır.
""")

_add("Linear Algebra", ["The column space and Ax=b", "The null space and Ax=O"], """
Sütun uzayı ve null uzay, bir matrisin $Ax=b$ sistemine "hangi $b$
değerleri için çözüm var?" ve "kaç farklı çözüm var?" sorularının
cevabını verir.

Nedir?
Sütun uzayı, $A$'nın sütunlarının tüm doğrusal kombinasyonlarının kümesidir
— $Ax=b$'nin bir çözümü olması için $b$'nin bu uzayda olması gerekir. Null
uzay ise $Ax=0$'ı sağlayan TÜM $x$ vektörlerinin kümesidir; sıfırdan
farklı bir null uzay varsa, sistemin sonsuz çözümü vardır.

Ne İçin Kullanılır?
1. Bir Sistemin Çözülebilirliğini Önceden Anlamak
Mühendislik simülasyonlarında bir $b$ değeri için sistemin çözülüp
çözülemeyeceğini, tüm sistemi çözmeden ÖNCE anlamayı sağlar.
2. Belirsizliği (Serbestlik Derecesini) Ölçmek
Bir robot kolunun kaç farklı şekilde aynı hedefe ulaşabileceği (fazladan
serbestlik derecesi) null uzayın boyutuyla ilişkilidir.
""")

_add("Linear Algebra", ["The product of a matrix and its transpose",
                                        "Transposes of products, sums, and inverses"], """
Transpoze (devrik) matris, bir matrisin satır ve sütunlarını YER
DEĞİŞTİREN hâlidir; bir matrisi kendi transpozesiyle çarpmak, birçok
önemli hesaplamada ortaya çıkan özel bir simetrik yapı üretir.

Nedir?
$A^T$'de $A$'nın $i$. satırı $j$. sütun olur. $A^TA$ her zaman simetrik
bir matristir (kare olmayan $A$ için bile). $(AB)^T = B^TA^T$ (sıra
TERSİNE döner) ve $(A^{-1})^T = (A^T)^{-1}$ gibi kurallar transpoze
alırken sırayı ve tersini nasıl etkilediğini gösterir.

Ne İçin Kullanılır?
1. En Küçük Kareler ve Regresyonun Formülü
$A^TAx=A^Tb$ normal denklemleri, istatistiksel regresyonun ve makine
öğrenmesindeki doğrusal modellerin matematiksel kalbidir.
2. Verinin Kovaryans Yapısını Ortaya Çıkarmak
Veri bilimi ve makine öğrenmesinde bir veri matrisinin kendi
transpozesiyle çarpımı, değişkenler arasındaki ilişkiyi (kovaryans)
ortaya çıkarır.
""")

_add("Linear Algebra", ["Zero matrices"], """
Sıfır matris, tüm girdileri sıfır olan matristir — matris cebirinde
sıradan aritmetikteki "0" sayısının rolünü oynar.

Nedir?
Herhangi bir $A$ matrisi için $A+0=A$'dır; sıfır matrisle çarpım her
zaman yine sıfır matris verir.

Ne İçin Kullanılır?
1. Matris Cebirinin Temel Aksiyomunu Sağlamak
Toplama işleminin "etkisiz elemanı" olarak, matrislerin bir cebirsel
yapı (grup) oluşturmasını garanti eder.
2. Bir Sistemin "Homojen" Hâlini Tanımlamak
$Ax=0$ biçimindeki (sağ tarafı sıfır matris/vektör olan) sistemler, null
uzay analizinin başlangıç noktasıdır.
""")

_add("Probability & Statistics", ["Chebyshev's Theorem"], """
Chebyshev Teoremi, dağılımın ŞEKLİNİ bilmesen bile (normal olsun olmasın)
verinin ortalama etrafında ne kadarının hangi aralıkta olacağına dair bir
ALT SINIR garantisi verir.

Nedir?
Herhangi bir dağılımda, verinin en az $1-\\frac{1}{k^2}$ oranı, ortalamadan
$k$ standart sapma içinde bulunur (örn. $k=2$ için en az $\\%75$).

Ne İçin Kullanılır?
1. Dağılım Şekli Bilinmeyen Verilerde Güvenli Tahmin
Bir verinin normal dağıldığından emin olunmadığı durumlarda bile
kullanılabilecek, "en kötü senaryo" garantisi sunan tek araçtır.
2. Kalite Kontrol ve Risk Yönetiminde Kesin Alt Sınır
Bir üretim sürecinin ne kadarının belirli toleranslar içinde kalacağının
garanti edilebilir minimum oranını hesaplamada kullanılır.

📜 Tarih ve Biyografi
Teorem, Rus matematikçi Pafnuty Chebyshev tarafından 1867'de kanıtlandı;
İrlandalı matematikçi Irénée-Jules Bienaymé'nin 1853'teki daha önceki bir
çalışmasına da atıfla bazı kaynaklarda "Bienaymé-Chebyshev Eşitsizliği"
olarak da anılır.
""")

_add("Probability & Statistics", ["Geometric random variables"], """
Geometrik dağılım, "ilk başarıya kadar kaç deneme gerekir?" sorusunun
olasılık dağılımıdır — bir zar atıp ilk kez 6 gelene kadar kaç kez
atman gerektiğini modeller.

Nedir?
Başarı olasılığı $p$ olan bağımsız denemelerde, İLK başarının tam $k$.
denemede gelme olasılığı $P(X=k) = (1-p)^{k-1}p$ formülüyle verilir.

Ne İçin Kullanılır?
1. "Ne Kadar Beklemem Gerekir?" Sorularını Modellemek
Bir ürünün kalite kontrolünde ilk hatalı parçaya kadar kaç parça
üretileceğini, bir satış temsilcisinin ilk satışa kadar kaç görüşme
yapacağını tahmin etmede kullanılır.
2. Güvenilirlik Mühendisliğinde
Bir sistemin ilk arızaya kadar geçen "deneme" sayısını modellemek için
kullanılır.
""")

_add("Probability & Statistics", ["Frequency histograms and polygons, and density curves",
                                                   "Line graphs and ogives"], """
Histogram, frekans poligonu, yoğunluk eğrisi ve ogif, aynı veriyi FARKLI
görsel amaçlarla özetleyen grafik türleridir.

Nedir?
Histogram, veriyi aralıklara (bin) bölüp her aralığın yüksekliğini
frekansla gösteren çubuklardır; frekans poligonu bu çubukların tepe
noktalarını birleştiren çizgidir. Yoğunluk eğrisi, örneklem büyüdükçe bu
poligonun yumuşak bir eğriye (örn. normal dağılım çanına) yaklaşmasıdır.
Ogif ise BİRİKİMLİ (kümülatif) frekansı gösteren artan bir çizgi
grafiğidir — "bu değerin altında kaç veri var?" sorusunu anında
cevaplar.

Ne İçin Kullanılır?
1. Veri Dağılımının Şeklini Hızla Görmek
Bir verinin simetrik mi, çarpık mı, tek mi çok tepeli mi olduğunu
histogram/yoğunluk eğrisiyle saniyeler içinde anlarsın.
2. Yüzdelik Dilim ve Medyan Bulmak
Ogif grafiği, "öğrencilerin %90'ı bu puanın altında" gibi yüzdelik dilim
sorularını grafikten doğrudan okumayı sağlar.
""")

_add("Linear Algebra", ["Adding and scaling linear transformations", "Coordinates in a new basis",
                                        "Transformation matrix for a basis"], """
Bir dönüşümün matrisi, HANGİ BAZA göre yazıldığına bağlıdır — aynı
dönüşüm, standart bazda karmaşık görünürken, doğru seçilmiş bir bazda
(örn. özvektör bazında) çarpıcı biçimde sadeleşebilir.

Nedir?
Doğrusal dönüşümler de vektörler gibi toplanabilir ve bir sayıyla
çarpılabilir (skaler ile ölçeklenebilir) — bu işlemler karşılık gelen
matrislerin toplanması/ölçeklenmesiyle aynıdır. Bir vektörün "yeni bazdaki
koordinatları", onu o bazın vektörlerinin bir kombinasyonu olarak yeniden
yazmaktır; bir dönüşümün YENİ BAZDAKİ matrisi de buna göre değişir.

Ne İçin Kullanılır?
1. Karmaşık Bir Dönüşümü Basitleştirmek
Doğru baz seçimi (örn. özvektör bazı), bir matrisi köşegen forma
indirger — bu, matrisin kuvvetlerini almayı (örn. $A^{100}$) uygulanabilir
kılar.
2. Bilgisayar Grafiklerinde Yerel/Global Koordinat Dönüşümü
Bir nesnenin kendi yerel bazındaki tanımını, dünya sahnesinin global
bazına çevirmek bu fikri kullanır.
""")

# ---------------------------------------------------------------------------
# Calculus 1 — round 2
# ---------------------------------------------------------------------------
_add("Calculus 1", ["Endpoint discontinuities", "Infinite discontinuities", "Jump discontinuities",
                                    "Point discontinuities", "Making the function continuous",
                                    "Intercepts and vertical asymptotes", "Horizontal and slant asymptotes",
                                    "Proving that the limit does not exist"], """
Süreksizlik türleri, bir fonksiyon grafiğinin "kalemi kaldırmadan"
çizilemediği noktaları sınıflandırır — HER kopukluk aynı sebepten
olmaz.

Nedir?
Nokta süreksizliği (bir "delik"), fonksiyonun o noktada limiti var ama
tanımsız/farklı olduğunda oluşur. Sıçrama (jump) süreksizliği, sağdan ve
soldan limitler FARKLI olduğunda; sonsuz süreksizlik ise fonksiyon o
noktada sonsuza gittiğinde (dikey asimptot) oluşur. Yatay/eğik
asimptotlar, fonksiyonun $x\\to\\pm\\infty$'daki davranışını tarif eder.

Ne İçin Kullanılır?
1. Fiziksel Sistemlerdeki "Ani Değişimleri" Modellemek
Bir anahtarın açılıp kapanması (sıçrama), bir kaynağın tükenmesi
(sonsuz süreksizlik) gibi ani olayları matematiksel olarak sınıflandırır.
2. Fonksiyonların Uzun Vadeli Davranışını Tahmin Etmek
Bir sistemin "sonsuzda" nereye yakınsayacağını (yatay asimptot) bilmek,
mühendislikte kararlılık analizinin temelidir.
""")

_add("Calculus 1", ["Squeeze Theorem", "Trigonometric limits"], """
Sıkıştırma Teoremi, doğrudan hesaplanamayan bir limiti, onu İKİ TARAFTAN
"sıkıştıran" daha kolay iki fonksiyonun limitiyle bulur — ortadaki
fonksiyon, alt ve üst sınır aynı değere gittiğinde ZORUNLU olarak aynı
yere gider.

Nedir?
$g(x)\\le f(x)\\le h(x)$ ve $\\lim g(x)=\\lim h(x)=L$ ise,
$\\lim f(x)=L$'dir. Bu teknik özellikle $\\lim_{x\\to0}\\frac{\\sin
x}{x}=1$ gibi doğrudan yerine koymayla çözülemeyen trigonometrik
limitleri kanıtlamak için kullanılır.

Ne İçin Kullanılır?
1. Trigonometrik Türev Kurallarının Temelini Kanıtlamak
$\\sin x$'in türevinin $\\cos x$ olduğunun titiz kanıtı, bu teoremle
bulunan temel limite dayanır.
2. Zor Limitleri Kolay Sınırlarla Çözmek
Bir ifadeyi doğrudan hesaplamak yerine, onu daha basit iki fonksiyon
arasına sıkıştırarak çözmeyi mümkün kılar.
""")

_add("Calculus 1", ["Chain rule with product rule", "Chain rule with quotient rule",
                                    "Chain rule with trig, log, and exponential functions",
                                    "Product rule with three or more functions"], """
Zincir kuralının çarpım/bölüm kuralıyla birleşimi, gerçek dünyadaki
"iç içe VE çarpım hâlinde" olan fonksiyonları türetmenin standart
yoludur — çoğu gerçek formül tek bir kuralla değil, kuralların
birleşimiyle türetilir.

Nedir?
Bir fonksiyon hem çarpım/bölüm HEM bileşke içeriyorsa, önce dış yapıya
(çarpım/bölüm kuralı) uygulanır, sonra her parçanın türevi alınırken iç
fonksiyonlar için zincir kuralı devreye girer. Üç veya daha fazla
fonksiyonun çarpımında, kural her seferinde BİR fonksiyonu türetip
diğerlerini sabit tutarak genişletilir.

Ne İçin Kullanılır?
1. Gerçek Dünya Formüllerinin Çoğu Bu Kombinasyonu Gerektirir
Fizik, mühendislik ve ekonomideki formüllerin büyük kısmı basit tek bir
kuralla değil, bu kuralların iç içe uygulanmasıyla türetilir.
2. Makine Öğrenmesinde Çok Katmanlı Zincirleme Türev
Derin sinir ağlarındaki geri yayılım, onlarca katmanda zincirlenmiş
çarpım ve bileşke fonksiyonların türevini otomatik olarak hesaplar.
""")

_add("Calculus 1", ["Trigonometric derivatives", "Inverse trigonometric derivatives",
                                    "Exponential derivatives", "Logarithmic derivatives", "Logarithmic differentiation",
                                    "Hyperbolic derivatives", "Inverse hyperbolic derivatives"], """
Özel fonksiyon türev kuralları (trigonometrik, üstel, logaritmik,
hiperbolik), temel türev kurallarının belirli fonksiyon ailelerine
uygulanmış, ezberlenmeye değer sonuçlarıdır.

Nedir?
$(\\sin x)'=\\cos x$, $(e^x)'=e^x$ (kendi türevine eşit olan tek
fonksiyon ailesi), $(\\ln x)' = 1/x$ gibi kurallar bu kategoridedir.
Logaritmik türev alma (logarithmic differentiation), $\\ln$ uygulayıp
türetmenin, karmaşık çarpım/üs içeren fonksiyonları türetmeyi
kolaylaştırdığı özel bir tekniktir.

Ne İçin Kullanılır?
1. Titreşim, Dalga ve Salınım Modellerini Türetmek
Ses dalgaları, alternatif akım, sarkaç hareketi gibi periyodik olaylar
trigonometrik fonksiyonlarla modellenir; bu modellerin hızını/ivmesini
bulmak bu kuralları gerektirir.
2. Büyüme/Bozunma Hızını Hesaplamak
Nüfus artışı, radyoaktif bozunma gibi üstel süreçlerin "o anki" değişim
hızı bu türev kurallarıyla bulunur.
""")

_add("Calculus 1", ["Higher-order derivatives"], """
Yüksek mertebeden türevler, "değişimin değişimini" (ve onun da
değişimini) ölçer — hız, konumun; ivme, hızın; "sarsıntı" (jerk) ivmenin
türevidir.

Nedir?
$f''(x)$ (ikinci türev), $f'(x)$'in türevidir; $f'''(x)$ üçüncü türevdir
ve bu böyle devam eder. İkinci türev, fonksiyonun İÇBÜKEY/DIŞBÜKEY
olduğunu belirler.

Ne İçin Kullanılır?
1. İvme ve Ötesini Hesaplamak
Bir aracın hızındaki değişim (ivme) ikinci türevle, konfor açısından
önemli olan ivme değişimi (jerk) üçüncü türevle ölçülür.
2. Grafiklerin Şeklini Analiz Etmek
Bir fonksiyonun büküm noktalarını (inflection points) ve bu noktalarda
eğrinin nasıl döndüğünü ikinci türev belirler.
""")

_add("Calculus 1", ["Implicit differentiation", "Equation of the tangent line with implicit differentiation",
                                    "Second derivatives with implicit differentiation"], """
Kapalı türev alma, $y$'yi $x$ cinsinden YALNIZ BIRAKAMADIĞIN denklemlerde
(örn. bir çember denklemi) yine de $dy/dx$'i bulmanı sağlayan bir
teknik.

Nedir?
Denklemin HER İKİ tarafı $x$'e göre türetilir; $y$ içeren her terimde
zincir kuralı uygulanıp $dy/dx$ çarpanı eklenir, sonra denklem $dy/dx$
için çözülür. İkinci türev de aynı işlemi bir kez daha uygulayarak
bulunur.

Ne İçin Kullanılır?
1. Fonksiyon Olmayan Eğrilere Teğet Bulmak
Bir çemberin veya elipsin (bunlar birer fonksiyon değildir, Dikey Çizgi
Testini geçemezler) belirli bir noktadaki teğet doğrusunu bulmanın tek
yoludur.
2. Fizikte Örtük İlişkileri Çözmek
Bir gaz kanunu ($PV=nRT$ gibi) birden fazla değişkeni birbirine örtük
biçimde bağladığında, değişkenlerin birbirine göre değişim hızını bulmak
için kullanılır.
""")

_add("Calculus 1", ["Linear approximation", "Normal lines", "Tangent lines"], """
Doğrusal yaklaşıklık, bir eğriyi belirli bir noktanın YAKININDA, ona
çizilen teğet DOĞRUYLA yaklaşık olarak temsil etmektir — yeterince
yakından bakıldığında her pürüzsüz eğri neredeyse düz görünür.

Nedir?
$L(x) = f(a) + f'(a)(x-a)$, $f$'in $x=a$ civarındaki en iyi doğrusal
yaklaşıklığıdır (teğet doğrunun kendisi). Normal doğru, aynı noktada
teğete DİK olan doğrudur.

Ne İçin Kullanılır?
1. Karmaşık Hesapları Basitleştirmek
$\\sqrt{4.02}$ gibi bir değeri, $\\sqrt{4}=2$ civarındaki doğrusal
yaklaşıklıkla, kök almadan hızlıca tahmin etmeyi sağlar.
2. Mühendislikte Küçük Sapma Analizi
Bir yapının küçük bir yük altındaki davranışını, tam (doğrusal olmayan)
denklem yerine, çok daha basit doğrusal bir yaklaşıklıkla modellemek
mühendislikte standart bir pratiktir.
""")

_add("Calculus 1", ["Critical points and the first derivative test", "Inflection points and the second derivative test",
                                    "Extrema on a closed interval", "Applied optimization"], """
Ekstremum (en büyük/en küçük değer) bulma, türevin SIFIR olduğu veya
tanımsız olduğu noktaları inceleyerek bir fonksiyonun tepe ve dip
noktalarını bulur — kalkülüsün en pratik ve en çok kullanılan
uygulamalarından biridir.

Nedir?
Kritik noktalar ($f'(x)=0$ veya tanımsız) adaylardır; Birinci Türev
Testi, türevin işaret DEĞİŞİMİNE bakarak bunun maksimum mu minimum mu
olduğunu söyler. İkinci Türev Testi ise $f''(x)$'in işaretine bakar
($f''>0$ minimum, $f''<0$ maksimum demektir) ve aynı zamanda büküm
noktalarını (içbükeyliğin değiştiği yerleri) bulur. Kapalı bir aralıkta
mutlak ekstremum, kritik noktalar VE uç noktalar karşılaştırılarak
bulunur.

Ne İçin Kullanılır?
1. En Az Malzemeyle En Çok Hacim (Mühendislik Tasarımı)
Bir kutunun, bir kutunun en az malzemeyle en çok hacmi alacak boyutlarını
bulmak klasik bir optimizasyon problemidir.
2. Ekonomide Kâr Maksimizasyonu
Bir ürünün fiyatını, kârı maksimize edecek şekilde belirlemek türevin
sıfır olduğu noktayı bulmayı gerektirir.

📜 Tarih ve Biyografi
Bir eğrinin maksimum/minimum noktalarını, türevin "sıfır olduğu yer"
mantığıyla bulma fikri, Newton ve Leibniz'in kalkülüsünden ÖNCE, Fransız
matematikçi Pierre de Fermat tarafından 1630'larda "adequality" adını
verdiği bir yöntemle zaten kullanılıyordu — bu yüzden Fermat, optimizasyon
kalkülüsünün öncüsü sayılır.
""")

_add("Calculus 1", ["Ball thrown up from the ground", "Coin dropped from the roof"], """
Serbest düşme ve dikey atış problemleri, yerçekimi altındaki hareketi
türev/integral ilişkisiyle (konum-hız-ivme) modeller.

Nedir?
Yerçekimi sabit bir ivme ($g\\approx9.8$ m/s²) uyguladığından, konum
fonksiyonu $t$'nin ikinci dereceden bir polinomudur; hız (türev) doğrusal,
ivme (ikinci türev) sabittir. "Ne zaman yere düşer/en yüksek noktaya
ulaşır" soruları, konum sıfır olduğunda veya hız sıfır olduğunda
sorulur.

Ne İçin Kullanılır?
1. Balistik ve Spor Bilimi
Bir topun, bir mermi merminin trajektoresini hesaplamak bu modele
dayanır.
2. Güvenlik Mühendisliği
Bir nesnenin düşme süresini ve çarpma hızını hesaplayarak güvenlik
önlemleri (düşme mesafesi sınırları gibi) belirlenir.

📜 Tarih ve Biyografi
Tüm cisimlerin (ağırlıklarından bağımsız olarak) aynı ivmeyle düştüğü
ve düşme mesafesinin zamanın KARESİYLE orantılı olduğu ilk kez İtalyan
bilim insanı Galileo Galilei tarafından 1589-1604 yılları arasında
yaptığı (rivayete göre Pisa Kulesi'nden top düşürme dahil) deneylerle
titizce gösterildi — Newton'un hareket yasalarının öncüsü kabul edilir.
""")

_add("Calculus 1", ["Ladder sliding down the wall", "Radius of the balloon", "Water level in the tank",
                                    "Observer and the airplane"], """
İlgili hız (related rates) problemleri, birbirine BAĞLI birden fazla
büyüklüğün, biri değişirken diğerinin ne hızla değiştiğini bulur —
zincir kuralının en klasik uygulama alanıdır.

Nedir?
İki (veya daha fazla) değişken arasında bir denklem kurulur (örn. Pisagor
Teoremi'yle merdiven-duvar-zemin ilişkisi), sonra denklemin HER İKİ
tarafı zamana ($t$) göre örtük olarak türetilir; bu, bilinen bir hızdan
bilinmeyen hızı bulmayı sağlar.

Ne İçin Kullanılır?
1. Birbirine Bağlı Değişen Sistemleri Analiz Etmek
Bir balonun şişirilme hızından yarıçapının artış hızını, bir gölgenin
uzama hızından bir kişinin yürüme hızıyla ilişkisini bulmak gibi
gerçek zamanlı değişim problemlerini çözer.
2. Robotik ve Kontrol Sistemlerinde
Bir mekanizmanın bir parçasının hızından diğer parçanın hızını hesaplamak
(örn. bir krank-biyel mekanizması) bu tekniğe dayanır.
""")

_add("Calculus 1", ["Marginal cost, revenue, and profit", "Price of the product", "Sales decline",
                                    "Compounding interest"], """
Ekonomide türev, "marjinal" kavramını (bir birim daha üretme/satmanın
EK etkisini) matematiksel olarak tanımlar.

Nedir?
Marjinal maliyet/gelir/kâr, sırasıyla maliyet, gelir ve kâr
fonksiyonlarının TÜREVİDİR — "bir birim daha üretirsem maliyetim/gelirim
ne kadar değişir?" sorusunun anlık cevabıdır. Kâr, marjinal gelir marjinal
maliyete eşit olduğunda MAKSİMUMDUR (ikisinin farkının türevi sıfırdır).

Ne İçin Kullanılır?
1. İşletmelerde Optimum Üretim Miktarını Belirlemek
Bir şirketin kârını maksimize eden üretim/satış miktarını bulmak,
doğrudan marjinal analiz kullanır.
2. Sürekli Bileşik Faizi Modellemek
Faizin sürekli (her an) bileşiklendiği finansal modeller ($A=Pe^{rt}$),
üstel fonksiyonların türevine dayanır.
""")

_add("Calculus 1", ["Newton's Law of Cooling", "Half-life"], """
Newton'un Soğuma Yasası ve yarı ömür, ikisi de aynı matematiksel kalıbı
(üstel bozunma) farklı fiziksel bağlamlarda kullanır.

Nedir?
Soğuma Yasası, bir cismin sıcaklığının, ortam sıcaklığıyla arasındaki
FARKLA orantılı bir hızla değiştiğini söyler — bu bir diferansiyel denklem
olup çözümü üstel bir fonksiyondur. Yarı ömür, radyoaktif bir maddenin
miktarının YARIYA inmesi için geçen sabit süredir; aynı üstel bozunma
denklemiyle modellenir.

Ne İçin Kullanılır?
1. Adli Tıp ve Arkeolojide Zaman Tahmini
Bir cesedin ölüm saatini soğuma yasasıyla, bir fosilin yaşını (karbon-14
yarı ömrüyle) tahmin etmek bu modele dayanır.
2. Nükleer Tıp ve Enerjide Doz/Yakıt Planlaması
Radyoaktif bir ilacın veya nükleer yakıtın zamanla ne kadar azalacağını
hesaplamak yarı ömür formülüyle yapılır.

📜 Tarih ve Biyografi
Soğuma yasası, İngiliz fizikçi/matematikçi Isaac Newton tarafından
1701'de (anonim olarak) yayımlandı. Radyoaktif yarı ömür kavramı ise
Yeni Zelandalı fizikçi Ernest Rutherford ve İngiliz kimyager Frederick
Soddy tarafından 1902-1903'te radyoaktif bozunma çalışmalarında ortaya
kondu.
""")

_add("Calculus 1", ["Absolute, relative, and percentage error"], """
Hata türleri, bir tahminin gerçek değerden ne kadar SAPTIĞINI farklı
şekillerde ölçer — bazen mutlak farkı, bazen bu farkın gerçek değere
ORANINI bilmek daha anlamlıdır.

Nedir?
Mutlak hata $|tahmin - gerçek|$'tir (birimlidir). Bağıl hata, mutlak
hatanın gerçek değere oranıdır (birimsizdir): $|tahmin-gerçek|/|gerçek|$.
Yüzde hata, bağıl hatanın 100 ile çarpılmış hâlidir.

Ne İçin Kullanılır?
1. Farklı Ölçeklerdeki Hataları Adil Karşılaştırmak
1 metrelik bir hata, bir bina ölçümünde önemsizken bir cıvata ölçümünde
felaket olabilir — bağıl/yüzde hata bu ölçek farkını hesaba katar.
2. Sayısal Yöntemlerin Doğruluğunu Raporlamak
Mühendislik ve bilimde bir sayısal yaklaşıklığın (Newton Yöntemi, Taylor
serisi gibi) ne kadar güvenilir olduğunu raporlamanın standart yoludur.
""")

_add("Calculus 1", ["Sketching f(x) from f'(x)", "Sketching graphs", "Crazy graphs"], """
Türevden orijinal fonksiyonun grafiğini çizmek, $f'(x)$'in işaret ve
davranışından $f(x)$'in "hikayesini" (artan/azalan, tepe/dip, içbükey/
dışbükey) yeniden inşa etmektir.

Nedir?
$f'(x)>0$ olan aralıklarda $f$ ARTAR, $f'(x)<0$ olan aralıklarda AZALIR;
$f'$'nin sıfır olduğu ve işaret değiştirdiği yerler tepe/dip noktalarıdır.
$f''$'nin işareti ise $f$'in içbükey mi dışbükey mi olduğunu belirler.

Ne İçin Kullanılır?
1. Veri Grafiğinden Davranışı Okumak
Bir hız-zaman grafiğinden konumun nasıl değiştiğini (veya tam tersini)
görsel olarak çıkarmak mühendislik ve fizikte sık kullanılan bir
beceridir.
2. Fonksiyon Analizini Sağlamlaştırmak
Bir fonksiyonun tüm davranışını (kritik noktalar, asimptotlar, içbükeylik)
TEK bir doğru grafikte birleştirme becerisidir.
""")

_add("Calculus 1", ["Solving with conjugate method", "Solving with factoring"], """
Limit çözme teknikleri (eşlenik ve çarpanlara ayırma), doğrudan yerine
koyduğunda $0/0$ belirsizliği veren limitleri, ifadeyi CEBİRSEL olarak
yeniden yazarak "belirsizliği ortadan kaldırmanın" yollarıdır.

Nedir?
Çarpanlara ayırma yöntemi, payda sıfır yapan çarpanı payla SADELEŞTİRİR.
Eşlenik yöntemi ise kök içeren ifadelerde, payı/paydayı eşlenikle çarparak
kökü ortadan kaldırır ve ardından sadeleştirmeyi mümkün kılar.

Ne İçin Kullanılır?
1. L'Hôpital Kuralından Önce Elle Limit Çözmek
Türev almadan, saf cebirsel manipülasyonla belirsiz limitleri çözmenin
temel yoludur — türevin tanımının kendisi de bu teknikleri kullanır.
2. Türevin Limit Tanımını Doğrudan Uygulamak
$f'(x)$'i limit tanımından ($\\lim_{h\\to0}\\frac{f(x+h)-f(x)}{h}$)
hesaplarken ortaya çıkan $0/0$ ifadesini çözmenin standart yoludur.
""")

_add("Calculus 1", ["Value that makes two tangent lines parallel", "Values that make the function differentiable"], """
Bu problem türleri, türev kavramının iki önemli sonucunu sınar: teğet
doğruların eğimlerini eşitlemek ve bir fonksiyonun türevlenebilir
olması için gereken koşulları bulmak.

Nedir?
İki noktadaki teğetlerin PARALEL olması, o noktalardaki türev
değerlerinin EŞİT olması demektir ($f'(a)=f'(b)$). Bir fonksiyonun bir
noktada türevlenebilir olması için önce o noktada SÜREKLİ olması, sonra
sağdan ve soldan türevlerinin EŞİT olması gerekir (parçalı
fonksiyonların "birleşim noktalarında" sıkça sorgulanır).

Ne İçin Kullanılır?
1. Parçalı Fonksiyonların Pürüzsüzlüğünü Garanti Etmek
Mühendislikte bir yolun/rayın iki farklı eğri parçasının birleştiği
noktada "sarsıntısız" geçiş sağlaması, tam olarak bu türevlenebilirlik
koşuluna dayanır.
2. Ortalama Değer Teoreminin Ön Koşulunu Sağlamak
Bu teoremin uygulanabilmesi için fonksiyonun ilgili aralıkta
türevlenebilir olması ZORUNLUDUR; bu koşulun ne zaman sağlandığını
anlamak gerekir.
""")

# ---------------------------------------------------------------------------
# Calculus 2 — round 2 (part 1: integration techniques)
# ---------------------------------------------------------------------------
_add("Calculus 2", ["Trigonometric integrals", "Integrating products of single sine and cosine factors",
                                    "Integrating sin^m cos^n", "Integrating tan^m sec^n"], """
Trigonometrik integrasyon teknikleri, $\\sin, \\cos, \\tan, \\sec$'in
kuvvetlerini içeren integralleri, trigonometrik ÖZDEŞLİKLER kullanarak
çözülebilir hâle getirir.

Nedir?
Tek kuvvetli sinüs/kosinüs terimleri $u$-yerine koymayı mümkün kılacak
şekilde ayrılır (örn. $\\sin^3x = \\sin x(1-\\cos^2x)$); çift kuvvetlerde
yarım açı özdeşlikleri ($\\sin^2x=\\frac{1-\\cos2x}{2}$) kullanılır.
$\\tan^m x\\sec^n x$ integralleri de benzer biçimde $\\sec^2x=1+\\tan^2x$
özdeşliğiyle parçalanır.

Ne İçin Kullanılır?
1. Dalga ve Titreşim Enerjisi Hesaplarında
Bir ses veya elektrik dalgasının bir periyot boyunca ürettiği ortalama
güç/enerji hesabı, $\\sin^2$ veya $\\cos^2$ integrali gerektirir.
2. Trigonometrik Yerine Koymanın Ön Koşulu
Kök içindeki ifadeleri trigonometrik yerine koyma ile çözdükten sonra,
ortaya çıkan trigonometrik integralleri bu tekniklerle bitirmek gerekir.
""")

_add("Calculus 2", ["Trigonometric substitution setup", "Trigonometric substitution with secant",
                                    "Trigonometric substitution with sine", "Trigonometric substitution with tangent"], """
Trigonometrik yerine koyma, kök içinde $a^2-x^2$, $a^2+x^2$ veya
$x^2-a^2$ biçiminde ifadeler gördüğünde, $x$'i BİR AÇININ trigonometrik
fonksiyonu olarak yeniden yazıp kökten kurtulmanın standart yoludur.

Nedir?
$\\sqrt{a^2-x^2}$ için $x=a\\sin\\theta$, $\\sqrt{a^2+x^2}$ için
$x=a\\tan\\theta$, $\\sqrt{x^2-a^2}$ için $x=a\\sec\\theta$ yerine
konur; Pisagor özdeşlikleri ($\\sin^2+\\cos^2=1$ ve türevleri) kökü tam
olarak yok eder.

Ne İçin Kullanılır?
1. Elips ve Çemberle İlgili Alan/Uzunluk Hesapları
Bir elipsin çevresi, bir çemberin yay uzunluğu gibi kök içeren
integraller bu teknikle çözülür.
2. Fizikte Alan Işığı ve Kuvvet Hesaplarında
Elektrik/manyetik alan hesaplarında ortaya çıkan kök içeren integraller
sıkça bu yöntemi gerektirir.
""")

_add("Calculus 2", ["Distinct and repeated quadratic factors", "Distinct linear factors",
                                    "Repeated linear factors"], """
Kısmi kesirlere ayırma, karmaşık bir rasyonel ifadeyi, her biri AYRI AYRI
kolayca integre edilebilen basit kesirlerin TOPLAMINA parçalar.

Nedir?
Paydası çarpanlarına ayrılmış bir rasyonel ifade, her doğrusal çarpan
için bir sabit/pay ($\\frac{A}{x-r}$), tekrar eden çarpanlar için artan
kuvvetli terimler, ikinci dereceden (indirgenemez) çarpanlar için
doğrusal pay ($\\frac{Ax+B}{x^2+bx+c}$) içeren bir toplama ayrıştırılır;
katsayılar denklem eşitleyerek bulunur.

Ne İçin Kullanılır?
1. Karmaşık Rasyonel İntegralleri Basitleştirmek
Doğrudan integre edilemeyen bir rasyonel fonksiyonu, tablo integralleri
olan basit parçalara böler.
2. Kontrol Sistemleri Mühendisliğinde Ters Laplace Dönüşümü
Mühendislikte bir sistemin zaman-domenindeki davranışını bulmak için
transfer fonksiyonlarını kısmi kesirlere ayırmak standart bir adımdır.

📜 Tarih ve Biyografi
Rasyonel fonksiyonları basit kesirlere ayırma tekniği, İsviçreli
matematikçi Johann Bernoulli tarafından 1702 civarında integral alma
problemlerinde kullanılmaya başlandı.
""")

_add("Calculus 2", ["Integrals using tables", "Tabular integration"], """
İntegral tabloları ve tablo yöntemi (tabular integration), sık karşılaşılan
integral kalıplarını HER SEFERİNDE sıfırdan türetmek yerine, önceden
hazırlanmış bir referanstan veya sistemli bir tablodan hızlıca bulmayı
sağlar.

Nedir?
İntegral tabloları, yüzlerce standart integralin sonucunu listeler.
Tablo (sütunlu) integrasyon ise kısmi integrasyonu, bir polinomun ardışık
türevleri ile diğer fonksiyonun ardışık integrallerini yan yana
dizerek, tekrar tekrar kısmi integrasyon uygulamadan hızlıca yapmanın bir
kısayoludur.

Ne İçin Kullanılır?
1. Mühendislik Hesaplarında Zaman Kazanmak
Standart bir integral kalıbını her seferinde yeniden türetmek yerine,
mühendisler ve fizikçiler referans tablolarını kullanır.
2. Çok Aşamalı Kısmi İntegrasyonu Hızlandırmak
Bir polinomla çarpılmış üstel/trigonometrik fonksiyonların integralini,
klasik yöntemden çok daha hızlı bulmayı sağlar.
""")

_add("Calculus 2", ["Improper integrals, cases 1-3", "Improper integrals, cases 4-6"], """
Has olmayan (improper) integraller, sınırları SONSUZ olan veya
integrali alınan fonksiyonun aralık içinde bir yerde SONSUZA giden
integrallerdir.

Nedir?
$\\int_a^\\infty f(x)\\,dx$ gibi bir integral, önce sonlu bir sınırla
($\\int_a^t f(x)\\,dx$) hesaplanıp sonra $t\\to\\infty$ limiti alınarak
tanımlanır; limit varsa integral YAKINSAK, yoksa IRAKSAKTIR. Fonksiyonun
kendisinin bir noktada sonsuza gittiği durumlarda da benzer bir limit
işlemi uygulanır.

Ne İçin Kullanılır?
1. Olasılıkta Toplam Olasılığın 1 Olduğunu Doğrulamak
Sürekli bir olasılık yoğunluk fonksiyonunun TÜM gerçek sayılar üzerindeki
integralinin 1 olması gerektiğini kanıtlamak improper integral
gerektirir.
2. Fizikte Sonsuza Kadar Uzanan Alanları/Enerjileri Hesaplamak
Bir elektrik alanının sonsuza kadar yaptığı iş, bir yıldızın kütleçekim
potansiyel enerjisi gibi hesaplar bu tür integraller kullanır.
""")

_add("Calculus 2", ["Hyperbolic integrals", "Inverse hyperbolic integrals"], """
Hiperbolik integraller, $\\sinh, \\cosh, \\tanh$ gibi hiperbolik
fonksiyonların (ve terslerinin) integrallerini, sıradan trigonometrik
integrallere ÇOK BENZER kurallarla çözer.

Nedir?
$\\int \\sinh x\\,dx = \\cosh x + C$ gibi kurallar, hiperbolik
fonksiyonların $e^x$ ve $e^{-x}$ cinsinden tanımından türetilir; ters
hiperbolik fonksiyonların integralleri ise genellikle bir logaritmik
ifadeye eşdeğerdir.

Ne İçin Kullanılır?
1. Asılı Kablo ve Zincir Şeklini Modellemek (Catenary Eğrisi)
İki direk arasında sarkan bir elektrik kablosunun veya köprü halatının
aldığı doğal şekil ($\\cosh$ fonksiyonu, "catenary") bu fonksiyonlarla
tanımlanır.
2. Özel Görelilik ve İleri Fizikte
Einstein'ın özel görelilik denklemlerinde hız dönüşümleri hiperbolik
fonksiyonlarla doğal biçimde ifade edilir.
""")

_add("Calculus 2", ["Integrating even and odd functions", "Integrating piecewise functions",
                                    "Properties of integrals"], """
İntegral özellikleri (doğrusallık, aralık toplanabilirliği, çift/tek
fonksiyon simetrisi), bir integrali hesaplamadan ÖNCE onu basitleştirmenin
yollarını sunar.

Nedir?
Simetrik bir aralıkta ($-a$'dan $a$'ya), TEK bir fonksiyonun integrali
her zaman SIFIRDIR (pozitif ve negatif alanlar birbirini götürür); ÇİFT
bir fonksiyonun integrali ise $0$'dan $a$'ya olan integralin İKİ KATIDIR.
Parçalı fonksiyonlar, her parçanın kendi aralığında ayrı ayrı integre
edilip toplanarak integre edilir.

Ne İçin Kullanılır?
1. Hesabı Önceden Basitleştirmek
Bir integralin simetriden dolayı sıfır olduğunu FARK ETMEK, saatler
sürebilecek bir hesabı saniyeler içinde bitirebilir.
2. Karmaşık, Parçalı Tanımlı Gerçek Veri Fonksiyonlarını İntegre Etmek
Kademeli vergi dilimleri gibi parçalı tanımlanan gerçek fonksiyonların
toplam etkisini (integralini) hesaplamak için gereklidir.
""")

_add("Calculus 2", ["Substitution", "Substitution in definite integrals", "Rationalizing substitutions"], """
Değişken değiştirme (u-substitution), zincir kuralının TERSİNİ integral
almaya uygulayarak, karmaşık bir integrali daha basit bir forma
"paketler".

Nedir?
İçteki bir ifade $u$ olarak adlandırılır, $du$ hesaplanır ve integral
tamamen $u$ cinsinden yeniden yazılır — genellikle çok daha basit bir
integrale (örn. $\\int u^n\\,du$) dönüşür. Belirli integrallerde,
sınırların da $u$ cinsine ÇEVRİLMESİ gerekir (sonunda tekrar $x$'e
dönmeye gerek kalmaz).

Ne İçin Kullanılır?
1. İntegral Almanın En Sık Kullanılan Tekniği
Kalkülüs 2'deki hemen her integral probleminin ilk denenen çözüm
tekniğidir — diğer tüm ileri tekniklerin (trigonometrik yerine koyma
dahil) temelini oluşturur.
2. Karmaşık Bileşke Fonksiyonları Integre Edilebilir Kılmak
Zincir kuralıyla türetilmiş her fonksiyonun integralini geri almanın
doğal yoludur.
""")

_add("Calculus 2", ["Recognizing types of series", "Sum of a geometric series",
                                    "Values for which a geometric series converges", "Sum of a series from its partial sums",
                                    "Formula for the general term", "Finding the terms of a sequence"], """
Geometrik seri, her terimin bir öncekinin SABİT bir katı olduğu özel bir
seri türüdür — belki de en kullanışlı ve en çok uygulaması olan seri
tipidir.

Nedir?
İlk terimi $a$, ortak çarpanı $r$ olan bir geometrik serinin toplamı
$|r|<1$ iken $\\dfrac{a}{1-r}$'ye yakınsar; $|r|\\ge1$ ise ıraksar. Bir
serinin genel terim formülünü tanımak (aritmetik mi, geometrik mi,
başka bir kalıp mı), hangi yakınsaklık testinin uygulanacağını seçmenin
ilk adımıdır.

Ne İçin Kullanılır?
1. Sonsuz Tekrarlayan Ödeme/Süreçleri Toplamak
Sonsuza kadar sürecek bir kira/temettü ödemesinin BUGÜNKÜ toplam
değerini hesaplamak (finansta "perpetuity") geometrik seri formülüdür.
2. Fraktal ve Kendine Benzer Şekillerin Toplam Alanını Bulmak
Sonsuz kez küçülerek tekrar eden geometrik şekillerin (Koch kar tanesi
gibi) toplam alanı/çevresi geometrik seriyle hesaplanır.
""")

_add("Calculus 2", ["Ratio test with factorials"], """
Faktöriyelli oran testi, oran testinin (ratio test) faktöriyel ($n!$)
içeren serilere özel uygulamasıdır — faktöriyeller çok hızlı büyüdüğü
için bu testte genellikle çok net bir yakınsaklık sonucu çıkar.

Nedir?
$\\lim_{n\\to\\infty}\\left|\\dfrac{a_{n+1}}{a_n}\\right|$ hesaplanırken,
$\\dfrac{(n+1)!}{n!}=n+1$ gibi sadeleşmeler faktöriyelli serilerin
davranışını hızla ortaya çıkarır.

Ne İçin Kullanılır?
1. Taylor Serilerinin Yakınsaklığını Kanıtlamak
$e^x, \\sin x, \\cos x$ gibi fonksiyonların Taylor serilerinin
paydasında $n!$ bulunur; bu serilerin HER $x$ için yakınsadığını
kanıtlamanın standart yolu bu testtir.
2. Olasılıkta Poisson ve Üstel Dağılım Serilerini Doğrulamak
Poisson dağılımının olasılıklarının toplamının 1'e eşit olduğunu
kanıtlamak faktöriyelli bir seri yakınsaklığı gerektirir.
""")

_add("Calculus 2", ["Radius and interval of convergence of a Maclaurin series",
                                    "Radius and interval of convergence of a Taylor series",
                                    "Sum of the Maclaurin series", "Power series division", "Power series multiplication",
                                    "Taylors inequality"], """
Taylor/Maclaurin serilerinin yakınsaklık yarıçapı, bu seri
yaklaşıklığının HANGİ $x$ değerleri için GÜVENİLİR olduğunu belirler —
yaklaşıklık her yerde değil, belirli bir aralıkta işe yarar.

Nedir?
Yakınsaklık yarıçapı $R$, serinin $|x-a|<R$ için kesinlikle yakınsadığını,
$|x-a|>R$ için ıraksadığını söyler; uç noktalar ($x=a\\pm R$) ayrıca
test edilmelidir (yakınsaklık ARALIĞI). Taylor Eşitsizliği, seriyi belirli
bir terimde KESTİĞİNDE yapılan hatanın büyüklüğüne bir üst sınır koyar.
Kuvvet serileri de sıradan polinomlar gibi terim terim çarpılabilir/
bölünebilir.

Ne İçin Kullanılır?
1. Bir Yaklaşıklığın Ne Kadar Güvenilir Olduğunu Bilmek
Bir hesap makinesinin $\\sin(100)$'ü hesaplarken hangi $x$ aralığında
Taylor serisinin güvenilir olduğunu bilmesi gerekir.
2. Bilgisayarların Hata Payını Garanti Etmesi
Taylor Eşitsizliği, bir yazılımın "bu sonuç gerçek değerden en fazla şu
kadar sapabilir" garantisini matematiksel olarak vermesini sağlar.
""")

_add("Calculus 2", ["Remainder estimate for a convergent series", "Error bounds"], """
Kalan terim tahmini, sonsuz bir seriyi SONLU sayıda terimde kestiğinde
ne kadar hata yaptığını önceden tahmin etmeni sağlar.

Nedir?
Bir seriyi $n$ terimde kesersen, gerçek toplamla kısmi toplam arasındaki
fark (kalan), serinin türüne özel formüllerle (örn. alternatif seri
testinde kalan, bir sonraki terimden büyük olamaz) sınırlandırılır.

Ne İçin Kullanılır?
1. "Kaç Terim Yeterli?" Sorusunu Cevaplamak
Bir hesap makinesinin $e$ sayısını 10 ondalık basamak doğrulukla vermesi
için serinin kaç teriminin toplanması gerektiğini önceden hesaplamayı
sağlar.
2. Sayısal Yöntemlerde Güvenilir Hata Raporlaması
Bilimsel hesaplamalarda bir yaklaşıklığın hata payını KANIT olarak
sunmanın standart yoludur.
""")

# ---------------------------------------------------------------------------
# Calculus 2 — round 2 (part 2: parametric/polar, volumes, physics)
# ---------------------------------------------------------------------------
_add("Calculus 2", ["Eliminating the parameter", "Derivative of a parametric curve",
                                    "Second derivative of a parametric curve", "Tangent line to the parametric curve",
                                    "Sketching parametric curves by plotting points"], """
Parametrik denklemler, bir eğrinin $x$ ve $y$ koordinatlarını, ÜÇÜNCÜ bir
değişkenin ($t$, genelde "zaman") fonksiyonu olarak ayrı ayrı tarif
eder — bu, bir noktanın zamanla nasıl HAREKET ettiğini doğal biçimde
anlatır.

Nedir?
$x=f(t), y=g(t)$ biçiminde verilir. Parametreyi yok etmek ($t$'yi
denklemlerden çekip birleştirmek), eğriyi tanıdık bir $x$-$y$ denklemine
çevirir. Eğrinin eğimi $dy/dx = (dy/dt)/(dx/dt)$ ile, ikinci türev ise
bu ifadenin tekrar $t$'ye göre türetilip $dx/dt$'ye bölünmesiyle bulunur.

Ne İçin Kullanılır?
1. Bir Cismin Yolunu Zamanla Tarif Etmek
Bir merminin, bir gezegenin yörüngesinin "ne zaman nerede olduğunu"
(sadece şeklini değil) tarif etmenin doğal yoludur — animasyon ve
robotik yol planlamasının temelidir.
2. Fonksiyon Olmayan Eğrileri Tanımlamak
Bir çember veya spiral gibi Dikey Çizgi Testini geçemeyen eğrileri,
parametrik formda kolayca tanımlamak mümkündür.
""")

_add("Calculus 2", ["Area under a parametric curve", "Area under one arc or loop of a parametric curve",
                                    "Parametric arc length"], """
Parametrik eğrilerde alan ve yay uzunluğu, standart alan/uzunluk
formüllerinin, eğrinin $t$ parametresiyle tarif edildiği durumlara
uyarlanmış hâlleridir.

Nedir?
Alan $\\int y\\,\\dfrac{dx}{dt}\\,dt$ ile, yay uzunluğu ise
$\\int\\sqrt{(dx/dt)^2+(dy/dt)^2}\\,dt$ formülüyle (Pisagor Teoremi'nin
sonsuz küçük parçalara uygulanmış hâli) hesaplanır.

Ne İçin Kullanılır?
1. Karmaşık Mekanik Yolların Uzunluğunu Bulmak
Bir krank mekanizmasının, bir dişlinin çizdiği karmaşık yolun toplam
uzunluğunu hesaplamak bu formülle yapılır.
2. Animasyon ve CAD Yazılımlarında Eğri Ölçümü
Bilgisayar destekli tasarım yazılımları, Bezier eğrileri gibi parametrik
eğrilerin uzunluğunu bu prensiple sayısal olarak hesaplar.
""")

_add("Calculus 2", ["Arc length of a polar curve", "Tangent line to the polar curve",
                                    "Vertical and horizontal tangent lines to the polar curve",
                                    "Intersection of polar curves", "Distance between polar points"], """
Kutupsal eğrilerde teğet, uzunluk ve kesişim, kutupsal koordinat sisteminin
kalkülüs araçlarıyla (türev, integral) birleştirilmesidir.

Nedir?
Kutupsal bir eğrinin eğimi, önce $x=r\\cos\\theta, y=r\\sin\\theta$
parametrik forma çevrilip parametrik türev kuralı uygulanarak bulunur.
İki kutupsal eğrinin kesişim noktaları bulunurken DİKKAT gerekir — aynı
nokta farklı $(r,\\theta)$ çiftleriyle ifade edilebildiğinden, denklemleri
eşitlemek bazı kesişimleri KAÇIRABİLİR.

Ne İçin Kullanılır?
1. Radar ve Anten Işın Desenlerini Analiz Etmek
Bir antenin sinyal gücünün yöne göre değişimi (ışın deseni) kutupsal
eğrilerle tanımlanır; iki antenin kapsama alanının nerede kesiştiğini
bulmak bu tekniği gerektirir.
2. Gezegen Yörüngelerinde Kritik Noktaları Bulmak
Bir yörüngenin Güneş'e en yakın/uzak olduğu noktalar (kutupsal
koordinatlarda türev sıfır olan noktalar) bu yöntemle bulunur.
""")

_add("Calculus 2", ["Area inside a polar curve", "Area between polar curves",
                                    "Area bounded by one loop of a polar curve", "Area inside both polar curves"], """
Kutupsal koordinatlarda alan, dikdörtgenler yerine küçük "dilimler"
(sektörler) toplayarak hesaplanır — kutupsal sistemin doğal geometrisine
uygun bir yaklaşımdır.

Nedir?
Alan formülü $\\frac12\\int r^2\\,d\\theta$'dır (bir dairesel dilimin
alanı $\\frac12r^2\\theta$ formülünün sonsuz küçük parçalara
uygulanmasıdır). İki eğri arasındaki veya İKİSİNİN ORTAK (kesişim)
bölgesindeki alan, kesişim noktaları bulunup doğru $\\theta$ aralıklarında
doğru $r$ ifadesi kullanılarak hesaplanır.

Ne İçin Kullanılır?
1. Çiçek/Gül Eğrisi Gibi Karmaşık Şekillerin Alanını Bulmak
Kutupsal koordinatlarda tanımlanan güzel, simetrik şekillerin
(kardioidler, gül eğrileri) alanını hesaplamanın tek pratik yoludur.
2. Radar Kapsama Alanı Örtüşmesini Hesaplamak
İki radar/anten sisteminin ORTAK kapsadığı alanı hesaplamak, iki
kutupsal eğrinin kesişim alanı problemidir.
""")

_add("Calculus 2", ["Surface area of revolution", "Surface area of revolution of a parametric curve, horizontal axis",
                                    "Surface area of revolution of a parametric curve, vertical axis",
                                    "Surface area of revolution of a polar curve"], """
Dönel yüzey alanı, düz bir eğriyi bir eksen etrafında döndürdüğünde
oluşan 3B yüzeyin (örn. bir vazonun dış yüzeyinin) alanını hesaplar.

Nedir?
$2\\pi\\int y\\sqrt{1+(dy/dx)^2}\\,dx$ formülü, eğri üzerindeki her
sonsuz küçük parçanın döndürülmesiyle oluşan ince "bilezik" şeritlerin
alanlarını toplar; parametrik ve kutupsal eğriler için formül, o
sistemlerin yay uzunluğu ifadesiyle uyarlanır.

Ne İçin Kullanılır?
1. Üretimde Malzeme Miktarını Hesaplamak
Bir vazonun, bir tankın, bir lambanın abajurunun dış yüzeyini kaplamak
için gereken malzeme miktarını hesaplamada kullanılır.
2. Isı Transferi Mühendisliğinde
Bir borunun veya tankın ısı kaybının hesaplanması, dış yüzey alanına
bağlıdır ve bu formülle hesaplanır.
""")

_add("Calculus 2", ["Volume of revolution, disk method", "Volume of revolution, washer method",
                                    "Volume of revolution, cylindrical shells", "Volume of revolution of a parametric curve"], """
Dönel cisimlerin hacmi, düz bir bölgeyi bir eksen etrafında
döndürdüğünde oluşan 3B cismin hacmini üç farklı (ama denk) yöntemle
hesaplar.

Nedir?
Disk yöntemi, cismi ince DAİRESEL dilimlere ($\\pi r^2$ alanlı) böler.
Yıkayıcı (washer) yöntemi, ortasında bir DELİK olan (iç içe iki eğri
arasındaki bölgenin döndürülmesiyle oluşan) dilimleri kullanır. Silindirik
kabuk (shell) yöntemi ise cismi iç içe geçmiş İNCE SİLİNDİR
yüzeylerine böler — dönme ekseni bölgeye paralel olmadığında genelde
daha kolaydır.

Ne İçin Kullanılır?
1. Endüstriyel Tasarımda Hacim/Ağırlık Hesabı
Bir vazonun, bir bilyanın, bir mermi çekirdeğinin (torna ile üretilen
her simetrik parçanın) hacmini ve dolayısıyla ağırlığını hesaplamada
kullanılır.
2. Tıbbi Görüntülemede Organ Hacmi Tahmini
BT/MR taramalarından elde edilen kesit görüntülerinden bir organın
(yaklaşık simetrik) hacmini tahmin etmek bu prensiplere dayanır.
""")

_add("Calculus 2", ["Centroids of plane regions", "Moments and center of mass of the system",
                                    "Theorem of Pappus"], """
Ağırlık merkezi (centroid), düzensiz bir şeklin "dengeye geldiği" tek
noktadır — bir parmağın ucunda o şekli dengelemeye çalışsan, tam o
noktadan tutman gerekir.

Nedir?
Ağırlık merkezinin koordinatları, şeklin momentlerinin (her nokta ×
uzaklık) toplamının alana bölünmesiyle bulunur. Pappus Teoremi, bir
düzlemsel bölgeyi kesişmeyen bir eksen etrafında döndürdüğünde oluşan
CİSMİN HACMİNİN, bölgenin alanı ile ağırlık merkezinin kat ettiği çevre
uzunluğunun ÇARPIMINA eşit olduğunu söyleyen şaşırtıcı bir kısayoldur.

Ne İçin Kullanılır?
1. Yapısal Mühendislikte Denge ve Kararlılık
Bir köprü ayağının, bir binanın ağırlık merkezinin nerede olduğunu
bilmek, yapının deprem/rüzgâr altında devrilip devrilmeyeceğini
belirler.
2. Karmaşık Dönel Cisimlerin Hacmini Hızlıca Bulmak
Pappus Teoremi, tekerlek, halka gibi karmaşık dönel cisimlerin hacmini,
tam integral almadan, sadece alan ve mesafe çarparak bulmayı sağlar.

📜 Tarih ve Biyografi
Teorem, MS 4. yüzyılda İskenderiyeli Yunan matematikçi Pappus tarafından
"Mathematical Collection" adlı eserinde formüle edildi — antik Yunan
geometrisinin kalkülüsten yaklaşık 1300 yıl önce ulaştığı en ileri
sonuçlardan biri kabul edilir.
""")

_add("Calculus 2", ["Work done by a variable force", "Work done on elastic springs",
                                    "Work done to empty a tank", "Work done to lift a mass or weight"], """
İş (work) hesaplamaları, DEĞİŞKEN bir kuvvetin bir cismi hareket
ettirmek için yaptığı toplam işi, sabit kuvvet formülünün ($İş = Kuvvet
\\times Mesafe$) integral yoluyla genelleştirilmiş hâlidir.

Nedir?
$W = \\int_a^b F(x)\\,dx$; kuvvet sabit değilse (bir yayı germek gibi,
Hooke Yasası $F=kx$), her sonsuz küçük mesafede kuvvet farklıdır ve
integral bunları toplar. Bir tankı boşaltmak veya bir ağırlığı halatla
çekmek gibi problemlerde, her "dilimin" ne kadar mesafe kat ettiği de
hesaba katılır (mesafe konuma göre değişir).

Ne İçin Kullanılır?
1. Yay ve Esnek Malzeme Tasarımı
Bir yayı belirli bir mesafeye sıkıştırmak/germek için gereken enerjiyi
hesaplamak, yay tasarımının (araba süspansiyonundan saat mekanizmasına)
temelidir.
2. Pompalama ve Kaldırma Sistemleri Mühendisliği
Bir su tankını boşaltmak, bir asansörün ağırlığı kaldırmak için gereken
toplam enerjiyi hesaplamak bu tekniklerle yapılır.
""")

_add("Calculus 2", ["Hydrostatic pressure and force"], """
Hidrostatik basınç ve kuvvet, bir sıvının derinlikle DEĞİŞEN basıncının,
bir yüzeye (bir barajın duvarı gibi) uyguladığı toplam kuvveti hesaplar.

Nedir?
Basınç derinlikle DOĞRUSAL artar ($P=\\rho g h$); bir yüzeye uygulanan
toplam kuvvet, bu değişen basıncın yüzey üzerinde integral alınmasıyla
bulunur — sabit basınç varsayımıyla hesaplamak (yüzeyin en üstündeki
basınçla) hataya yol açar.

Ne İçin Kullanılır?
1. Baraj ve Tank Duvarı Mühendisliği
Bir baraj duvarının, bir akvaryumun camının su basıncına dayanıp
dayanamayacağını hesaplamak bu integrale dayanır.
2. Denizaltı ve Dalış Güvenliği
Belirli bir derinlikteki basıncın bir yapıya (denizaltı gövdesi, dalış
ekipmanı) uyguladığı toplam kuvveti hesaplamada kullanılır.

📜 Tarih ve Biyografi
Basıncın derinlikle nasıl arttığının ilk sistematik incelemesi, Fransız
matematikçi ve fizikçi Blaise Pascal'ın 1653'teki hidrostatik
çalışmalarına dayanır ("Pascal İlkesi").
""")

_add("Calculus 2", ["Rectilinear motion", "Vertical motion"], """
Doğrusal (rectilinear) hareket problemleri, bir cismin TEK BOYUTTA
(bir doğru üzerinde) konum, hız ve ivmesini türev/integral ilişkisiyle
analiz eder — Kalkülüs 1'deki hareket fikrinin integral yönünden
tamamlanmasıdır.

Nedir?
Hız, konumun; ivme, hızın türevidir — TERSİNE, ivmenin integrali hızı,
hızın integrali konumu verir. Bir cismin toplam ALDIĞI YOL (mesafe),
hızın MUTLAK DEĞERİNİN integralidir; yer değiştirme ise hızın (işaretli)
integralidir — cisim geri dönerse bu ikisi FARKLI olur.

Ne İçin Kullanılır?
1. Hız Verisinden Konum/Mesafeyi Geri Hesaplamak
Bir aracın hız sensöründen topladığı veriden toplam kat edilen mesafeyi
(entegre ederek) hesaplamak mühendislikte standart bir uygulamadır.
2. Yer Değiştirme ile Toplam Yol Arasındaki Farkı Ayırt Etmek
Bir cismin ileri-geri hareket ettiği durumlarda "nereye vardı" (yer
değiştirme) ile "ne kadar yürüdü" (toplam yol) sorularını doğru
ayırmayı sağlar.
""")

_add("Calculus 2", ["Find f given f'' or f'''", "Initial value problems"], """
Başlangıç değer problemleri, bir fonksiyonun türevinden (veya ikinci/
üçüncü türevinden) ve BİLİNEN bir başlangıç koşulundan yola çıkarak
orijinal fonksiyonu YENİDEN İNŞA eder.

Nedir?
Ters türev alma (integral), her zaman bir "+C" belirsizliği bırakır;
$f(0)=5$ gibi bir başlangıç koşulu bu $C$'yi TEK bir değere sabitler.
$f''$'den $f$'i bulmak için bu işlem İKİ KEZ (iki farklı sabitle)
tekrarlanır.

Ne İçin Kullanılır?
1. Fizikte İvmeden Hız ve Konumu Bulmak
Bir roketin ivmesi (motor gücünden) biliniyorsa, başlangıç hızı ve
konumuyla birlikte, roketin HER ANDAKİ tam konumunu bu yöntemle
hesaplarsın.
2. Diferansiyel Denklemlerin Temelini Oluşturmak
Mühendislik ve fizikteki hemen her diferansiyel denklem çözümü, bu
"türevden orijinali bulma + başlangıç koşuluyla sabitleme" mantığını
kullanır.
""")

_add("Calculus 2", ["Net Change Theorem", "Mean value theorem for integrals", "Comparison Theorem"], """
Net Değişim Teoremi, bir büyüklüğün DEĞİŞİM HIZININ integralinin, o
büyüklükteki TOPLAM NET DEĞİŞİME eşit olduğunu söyler — Kalkülüsün Temel
Teoremi'nin en sezgisel yorumudur.

Nedir?
$\\int_a^b f'(x)\\,dx = f(b)-f(a)$; yani "hızın integrali, konumdaki net
değişimdir". İntegraller için Ortalama Değer Teoremi, bir fonksiyonun
belirli integralinin, o aralıktaki ORTALAMA değeri ile aralık uzunluğunun
çarpımına eşit olduğu bir $c$ noktasının var olduğunu söyler.

Ne İçin Kullanılır?
1. Toplam Değişimi Anlık Verilerden Hesaplamak
Bir şirketin günlük gelir DEĞİŞİM hızından, bir yıllık toplam net gelir
değişimini hesaplamak bu teoremin doğrudan uygulamasıdır.
2. Bir Fonksiyonun "Tipik" Değerini Bulmak
Bir günün ortalama sıcaklığını, anlık sıcaklık ölçümlerinden (integral
yoluyla) hesaplamak, integraller için ortalama değer teoremini kullanır.
""")

_add("Calculus 2", ["Converting summation notation to the integral", "Summation notation"], """
Sigma (toplam) notasyonu, uzun bir toplamı KOMPAKT bir sembolle ifade
eder; bu notasyonun integral ile ilişkisi, Riemann toplamlarının
integralin TANIMI olmasından gelir.

Nedir?
$\\sum_{i=1}^n a_i$, $a_1+a_2+\\cdots+a_n$'nin kısa yazımıdır. $n$ sonsuza
giderken bir Riemann toplamı ($\\sum f(x_i)\\Delta x$), tam olarak bir
belirli integrale ($\\int f(x)\\,dx$) dönüşür — toplam notasyonu ile
integral notasyonu aslında AYNI FİKRİN iki farklı (ayrık ve sürekli)
görünümüdür.

Ne İçin Kullanılır?
1. Ayrık Veriden Sürekli Modele Geçiş Yapmak
Bilgisayarların ayrık (örneklenmiş) verilerle yaptığı toplamların,
sürekli integrale nasıl yaklaştığını anlamak sayısal analizin temelidir.
2. İstatistik ve Veri Bilimi Formüllerini Okumak
Ortalama, varyans gibi neredeyse tüm istatistik formülleri sigma
notasyonuyla yazılır; bu notasyonu okuyabilmek istatistiğin ön koşuludur.
""")

_add("Calculus 2", ["Probability density functions"], """
Olasılık yoğunluk fonksiyonu (PDF), SÜREKLİ bir rastgele değişkenin
belirli bir ARALIKTA değer alma olasılığını, o aralık üzerindeki
integral ile verir.

Nedir?
Sürekli bir değişken için TEK bir noktanın olasılığı her zaman sıfırdır;
anlamlı olan, $f(x)$ eğrisinin bir aralık ($[a,b]$) altındaki alanıdır:
$P(a\\le X\\le b)=\\int_a^b f(x)\\,dx$. Tüm gerçek sayılar üzerindeki
toplam alan her zaman TAM OLARAK 1'dir.

Ne İçin Kullanılır?
1. Sürekli Verilerle Olasılık Hesaplamak
Bir insanın boyunun 170-180 cm arasında olma olasılığı gibi sürekli
ölçümlerle ilgili her olasılık sorusu bu integral fikrine dayanır.
2. Normal Dağılım ve İstatistiksel Çıkarımın Matematiksel Temeli
İstatistikteki normal dağılım "çan eğrisi" tam olarak bir olasılık
yoğunluk fonksiyonudur; altındaki alan olasılıkları verir.
""")

_add("Calculus 2", ["Economics", "Consumer and producer surplus"], """
Tüketici ve üretici fazlası, bir piyasadaki ALIŞVERİŞTEN doğan toplam
"kazancı" (tüketicilerin ödemeye razı olduğu ile gerçekte ödediği
arasındaki fark, ve üreticiler için tersi) integral ile ölçer.

Nedir?
Tüketici fazlası, talep eğrisi ile denge fiyatı arasındaki ALAN
(integral); üretici fazlası ise denge fiyatı ile arz eğrisi arasındaki
alandır. Bu alanlar, piyasanın toplam "refah" katkısını sayısallaştırır.

Ne İçin Kullanılır?
1. Ekonomi Politikalarının Etkisini Ölçmek
Bir verginin veya sübvansiyonun piyasadaki toplam refahı ne kadar
azalttığını/artırdığını hesaplamak bu alanları karşılaştırmayı
gerektirir.
2. Fiyatlandırma Stratejilerini Değerlendirmek
Bir şirketin fiyat değişikliğinin tüketiciler ve kendisi üzerindeki net
etkisini nicel olarak göstermeyi sağlar.
""")

_add("Calculus 2", ["Area under or enclosed by the curve", "Area between curves",
                                    "Average value of a function"], """
İki eğri arasındaki alan ve bir fonksiyonun ortalama değeri, belirli
integralin en doğrudan iki uygulamasıdır.

Nedir?
İki eğri arasındaki alan $\\int_a^b [f(x)-g(x)]\\,dx$ ile (üstteki eksi
alttaki fonksiyon) bulunur. Bir fonksiyonun $[a,b]$ aralığındaki ortalama
değeri $\\dfrac{1}{b-a}\\int_a^b f(x)\\,dx$'tir — sonsuz sayıda noktanın
"ortalamasını almanın" integral karşılığıdır.

Ne İçin Kullanılır?
1. İki Senaryo Arasındaki Net Farkı Ölçmek
İki farklı üretim/talep tahmininin arasındaki toplam farkı (örn. gelir
kaybı/kazancı) hesaplamak iki eğri arasındaki alanla yapılır.
2. Değişken Bir Büyüklüğün "Tipik" Değerini Bulmak
Bir günün ortalama sıcaklığı, bir yılın ortalama gelir akışı gibi sürekli
değişen büyüklüklerin tek bir "temsilci" değerini bulmayı sağlar.
""")

# ---------------------------------------------------------------------------
# Calculus 3 — round 2 (part 1: vectors, curvature, lines/planes)
# ---------------------------------------------------------------------------
_add("Calculus 3", ["Combinations of vectors", "Sum of two vectors"], """
Vektör toplama, iki (veya daha fazla) vektörün BİRLEŞİK etkisini bulur —
bir uçağın kendi hızı ile rüzgârın hızının toplamı, gerçek yer hızını
verir.

Nedir?
Vektörler bileşen bileşen toplanır: $(a_1,a_2,a_3)+(b_1,b_2,b_3) =
(a_1{+}b_1, a_2{+}b_2, a_3{+}b_3)$. Geometrik olarak, uç uca eklenen
oklar zincirinin başlangıcından bitişine giden ok, toplam vektördür.

Ne İçin Kullanılır?
1. Birden Fazla Kuvvetin Net Etkisini Bulmak
Bir cisme aynı anda etki eden birden fazla kuvvetin (yerçekimi, sürtünme,
itme) toplam (bileşke) etkisini bulmak vektör toplamadır.
2. Navigasyon ve Rota Planlamada
Bir geminin kendi rotası ile akıntının etkisini toplayarak gerçek
rotasını hesaplamak bu ilkeye dayanır.
""")

_add("Calculus 3", ["Domain of a vector function", "Limit of a vector function",
                                    "Derivative of a vector function", "Integral of a vector function",
                                    "Arc length of a vector function"], """
Vektör değerli fonksiyonlar, her $t$ değeri için bir SAYI yerine bir
VEKTÖR üreten fonksiyonlardır — uzayda hareket eden bir noktanın konumunu
zamanla tarif eder.

Nedir?
$\\vec{r}(t) = \\langle f(t), g(t), h(t)\\rangle$ biçimindedir; türevi,
limiti, integrali BİLEŞEN BİLEŞEN alınır (her bileşen ayrı bir tek
değişkenli fonksiyon gibi işlenir). Yay uzunluğu, hız vektörünün
büyüklüğünün integralidir: $\\int\\|\\vec{r}'(t)\\|\\,dt$.

Ne İçin Kullanılır?
1. Uzayda Hareket Eden Cisimleri Tam Olarak Tarif Etmek
Bir uydunun, bir dronun 3B uzaydaki tam yörüngesini (konum, hız, ivme)
tarif etmenin standart matematiksel dilidir.
2. Bilgisayar Animasyonunda Kamera/Nesne Yollarını Tanımlamak
3B animasyon yazılımlarında bir kameranın veya nesnenin izleyeceği
yumuşak yol, vektör değerli fonksiyonlarla tanımlanır.
""")

_add("Calculus 3", ["Unit tangent vector", "Unit tangent and unit normal vectors", "Curvature",
                                    "Maximum curvature", "Normal and osculating planes",
                                    "Tangential and normal components of acceleration"], """
Eğrilik (curvature), bir eğrinin bir noktada NE KADAR KESKİN büküldüğünü
sayısallaştırır — düz bir yol eğriliği sıfırdır, sıkı bir viraj yüksek
eğriliğe sahiptir.

Nedir?
Birim teğet vektör $\\vec{T}$, eğrinin yönünü (büyüklüğü her zaman 1
olacak şekilde) gösterir; birim normal vektör $\\vec{N}$ ise eğrinin
BÜKÜLME yönünü gösterir ve $\\vec{T}$'ye diktir. Eğrilik $\\kappa$,
$\\vec{T}$'nin yönünün ne kadar hızlı değiştiğini ölçer. İvme, teğet
yöndeki (hız değişimi) ve normal yöndeki (yön değişimi/merkezcil) iki
bileşene ayrıştırılabilir.

Ne İçin Kullanılır?
1. Yol ve Ray Tasarımında Güvenli Viraj Hesabı
Bir otoyol virajının veya tren rayının eğriliği, aracın o virajı güvenli
hızda alıp alamayacağını (merkezcil kuvvet limiti) belirler.
2. Roller Coaster ve Uçuş Rotası Tasarımı
Bir roller coaster'ın veya uçağın hissettirdiği "G kuvveti", doğrudan
rotanın eğriliğiyle ilişkilidir.

📜 Tarih ve Biyografi
Bir eğrinin her noktadaki teğet, normal ve eğrilik davranışını tam
tanımlayan formüller (Frenet-Serret formülleri), Fransız matematikçi
Jean Frédéric Frenet (1847) ve Joseph Alfred Serret (1851) tarafından
birbirinden bağımsız olarak geliştirildi.
""")

_add("Calculus 3", ["Velocity and acceleration vectors", "Velocity acceleration and speed given position"], """
Hız ve ivme vektörleri, uzaydaki bir hareketin YÖNÜNÜ VE BÜYÜKLÜĞÜNÜ tek
seferde taşır — Kalkülüs 1'deki tek boyutlu hız/ivme fikrinin 3B'ye
genelleştirilmiş hâlidir.

Nedir?
Konum $\\vec{r}(t)$'nin türevi hız $\\vec{v}(t)$'yi, hızın türevi ivme
$\\vec{a}(t)$'yi verir. Sürat (speed), hız VEKTÖRÜNÜN büyüklüğüdür (yönsüz,
tek bir sayı): $\\|\\vec{v}(t)\\|$.

Ne İçin Kullanılır?
1. Uzay Aracı ve Uydu Yörünge Hesapları
Bir uydunun konumundan hızını ve ivmesini (dolayısıyla üzerine etki eden
net kuvveti, Newton'un ikinci yasasıyla) hesaplamak bu türevlere
dayanır.
2. Spor Bilimi ve Hareket Analizi
Bir sporcunun 3B hareketini (GPS/sensör verisinden) analiz ederek anlık
hız ve ivmesini hesaplamak bu yöntemi kullanır.
""")

_add("Calculus 3", ["Equation of a plane", "Scalar equation of a plane", "Equation of the tangent plane"], """
Düzlem denklemi, 3B uzayda düz, sonsuz bir yüzeyi tarif eder — bir
düzlemi tam olarak tanımlamak için ona DİK olan bir vektör (normal
vektör) ve üzerindeki BİR nokta yeterlidir.

Nedir?
$(x_0,y_0,z_0)$ noktasından geçen ve $\\langle a,b,c\\rangle$ normal
vektörüne sahip düzlemin denklemi $a(x{-}x_0){+}b(y{-}y_0){+}c(z{-}z_0)=0$'dır.
Bir yüzeye teğet düzlem, o yüzeyin gradyan vektörünü normal vektör olarak
kullanır.

Ne İçin Kullanılır?
1. 3B Grafiklerde Yüzey Tanımlamak ve Işıklandırmak
Bir 3B modelin her düz yüzü bir düzlem denklemiyle temsil edilir; bu
yüzeyin ışığa nasıl tepki vereceği normal vektörden hesaplanır.
2. Bir Fonksiyonu Bir Noktada Doğrusal Yaklaşıklamak
Çok değişkenli bir fonksiyonu, bir noktadaki teğet düzlemiyle (tek
değişkenli teğet doğru fikrinin genellemesi) yaklaşık ifade etmeyi
sağlar.
""")

_add("Calculus 3", ["Scalar equation of a line", "Vector and parametric equations of a line segment",
                                    "Vector, parametric, and symmetric equations of the line",
                                    "Parametric equations of the tangent line"], """
Uzayda bir doğrunun denklemi, düzlemdekinden farklı olarak TEK bir
denklemle değil, bir NOKTA ve bir YÖN vektörüyle (genelde parametrik
biçimde) ifade edilir.

Nedir?
$\\vec{r}(t) = \\vec{r_0} + t\\vec{v}$ (vektörel form), bileşenlere
ayrılırsa $x=x_0{+}ta, y=y_0{+}tb, z=z_0{+}tc$ (parametrik form) olur;
$t$ her denklemden çekilip eşitlenirse simetrik form elde edilir.

Ne İçin Kullanılır?
1. Işın İzleme (Ray Tracing) Grafik Render Motorlarında
Bilgisayar grafiklerinde gerçekçi ışıklandırma üreten "ray tracing"
algoritması, milyonlarca ışık ışınını TAM OLARAK bu parametrik doğru
formuyla temsil eder.
2. Robot Kolu ve Drone Yol Planlaması
Bir robotun bir noktadan diğerine düz bir yolla hareketini tanımlamak bu
formülle yapılır.
""")

_add("Calculus 3", ["Intersection of a line and a plane", "Parallel, intersecting, skew, and perpendicular lines",
                                    "Parallel perpendicular and angle between planes", "Orthogonal parallel or neither",
                                    "Acute angle between the curves", "Acute angle between the lines"], """
Doğru ve düzlem ilişkileri, 3B uzayda iki geometrik nesnenin BİRBİRİNE
göre nasıl konumlandığını (paralel, dik, kesişen, ya da "aylak" —
skew) sınıflandırır.

Nedir?
İki doğru, yön vektörleri paralelse PARALEL; kesişiyorsa KESİŞEN; ne
paralel ne kesişiyorsa (3B'ye özgü bir durum) AYLAK (skew)'tir. İki
düzlem arasındaki açı, normal vektörleri arasındaki açıdan bulunur. Bir
doğru ile düzlemin kesişimi, doğrunun parametrik denklemi düzlem
denkleminde yerine konularak bulunur.

Ne İçin Kullanılır?
1. Yapısal Mühendislikte Kiriş/Boru Çakışma Kontrolü
İki borunun veya kirişin 3B uzayda gerçekten kesişip kesişmediğini
(yoksa sadece 2B izdüşümde mi kesişiyor görünüyor) doğrulamak "aylak
doğru" kavramını kullanır.
2. Bilgisayar Grafiklerinde Işın-Yüzey Kesişimi
Bir ışığın bir yüzeye çarpıp çarpmadığını (gölge, yansıma hesapları)
belirlemek doğru-düzlem kesişim formülünü kullanır.
""")

_add("Calculus 3", ["Parametric equations for the line of intersection of two planes",
                                    "Symmetric equations for the line of intersection of two planes"], """
İki düzlemin kesişim doğrusu, iki düz yüzeyin uzayda BULUŞTUĞU çizgiyi
bulur — iki duvarın birleştiği köşe çizgisi gibi.

Nedir?
İki düzlemin kesişim doğrusunun YÖNÜ, iki düzlemin normal vektörlerinin
ÇAPRAZ ÇARPIMIYLA bulunur (bu doğru her iki düzleme de paralel olmalı,
yani her iki normale de dik olmalıdır); doğru üzerindeki bir nokta ise
iki düzlem denklemini birlikte çözerek bulunur.

Ne İçin Kullanılır?
1. Mimari ve Yapısal Tasarımda Kesişim Çizgilerini Bulmak
İki çatı yüzeyinin birleştiği mahya çizgisini hesaplamak bu yöntemle
yapılır.
2. Bilgisayar Destekli Tasarımda (CAD) Yüzey Kesişimleri
Karmaşık 3B modellerde iki yüzeyin kesiştiği sınırı bulmak, modelleme
yazılımlarının temel işlemlerinden biridir.
""")

_add("Calculus 3", ["Direction cosines and direction angles"], """
Yön kosinüsleri, bir vektörün UZAYDAKİ üç eksenle (x, y, z) yaptığı
açıların kosinüslerini vererek vektörün yönünü tam olarak tarif eder.

Nedir?
Bir $\\vec{v}=\\langle a,b,c\\rangle$ vektörü için yön kosinüsleri
$\\cos\\alpha=a/\\|\\vec{v}\\|$ (ve $y,z$ için benzer) şeklindedir;
bu üç kosinüsün kareleri toplamı HER ZAMAN 1'dir.

Ne İçin Kullanılır?
1. Uçuş ve Uzay Aracı Yönelim Sistemleri
Bir uçağın veya uydunun uzaydaki tam yönelimini (hangi ekseni hangi
yöne bakıyor) tanımlamak için kullanılır.
2. Kristalografi ve Malzeme Biliminde
Bir kristal yapısındaki atomik düzlemlerin yönünü tanımlamak yön
kosinüsleri ile yapılır.
""")

_add("Calculus 3", ["Distance between points in three dimensions", "Plotting points in three dimensions",
                                    "Center radius and equation of the sphere"], """
3B'de nokta, mesafe ve küre, iki boyutlu koordinat geometrisinin ÜÇÜNCÜ
bir eksen (derinlik, $z$) eklenerek genelleştirilmesidir.

Nedir?
Mesafe formülü $d=\\sqrt{(x_2{-}x_1)^2+(y_2{-}y_1)^2+(z_2{-}z_1)^2}$
(Pisagor'un üçüncü kez uygulanmış hâli). Kürenin denklemi
$(x{-}h)^2+(y{-}k)^2+(z{-}l)^2=r^2$'dir — çemberin 3B karşılığı.

Ne İçin Kullanılır?
1. 3B Modelleme ve Oyun Motorlarının Temeli
Her 3B nesnenin konumu, iki nesne arası mesafe (çarpışma tespiti) bu
temel formüllerle hesaplanır.
2. GPS ve Uydu Konumlandırma
Bir GPS alıcısının konumu, birden fazla uyduya olan mesafelerin (küre
denklemlerinin) KESİŞİMİ olarak hesaplanır.
""")

_add("Calculus 3", ["Vector orthogonal to the plane", "Scalar triple product to prove vectors are coplanar",
                                    "Volume of the parallelpiped from vectors", "Volume of the parallelpiped from adjacent edges",
                                    "Magnitude and angle of the resultant force", "Scalar and vector projections"], """
Üçlü çarpım ve paralelyüzler, üç vektörün birlikte oluşturduğu 3B
"kutunun" (paralelyüzün) hacmini ve bu vektörlerin AYNI DÜZLEMDE olup
olmadığını tek bir sayıyla ölçer.

Nedir?
Skaler üçlü çarpım $\\vec{u}\\cdot(\\vec{v}\\times\\vec{w})$, üç
vektörün oluşturduğu paralelyüzün HACMİNİ verir; bu değer SIFIRSA üç
vektör aynı düzlemdedir (coplanar — 3B'de "düzleşmişlerdir"). İzdüşüm
(projection), bir vektörün başka bir vektör üzerine düşen "gölgesini"
skaler (uzunluk) veya vektör (yönlü) olarak verir.

Ne İçin Kullanılır?
1. Bilgisayar Grafiklerinde Hacim ve Çarpışma Hesabı
3B nesnelerin kapladığı hacmi veya üç noktanın aynı düzlemde olup
olmadığını (dejenere üçgen kontrolü) hızlıca test etmek için kullanılır.
2. Fizikte Kuvvetleri Bileşenlerine Ayırmak
Eğik bir düzlemdeki bir kuvveti, düzleme paralel ve dik bileşenlerine
ayırmak (izdüşüm alarak) mekanik problemlerinin standart ilk adımıdır.
""")

_add("Calculus 3", ["Implicit differentiation for multivariable functions", "Linear approximation in two variables",
                                    "Differential of the function"], """
Çok değişkenli fonksiyonlarda örtük türev ve doğrusal yaklaşıklık, tek
değişkenli kalkülüsteki aynı fikirlerin İKİ (veya daha fazla) değişkene
genelleştirilmiş hâlidir.

Nedir?
$F(x,y,z)=0$ biçimindeki bir denklemde $z$'nin $x$ veya $y$'ye göre
kısmi türevi, kısmi türevlerin oranıyla ($-F_x/F_z$ gibi) bulunur. Toplam
diferansiyel $dz = f_x\\,dx + f_y\\,dy$, fonksiyondaki KÜÇÜK bir
değişimi, her değişkendeki küçük değişimlerin toplam etkisi olarak
yaklaşık ifade eder.

Ne İçin Kullanılır?
1. Ölçüm Hatalarının Sonuca Nasıl Yayıldığını Hesaplamak
Bir silindirin yarıçap ve yüksekliğindeki küçük ölçüm hatalarının,
hesaplanan hacimdeki toplam hatayı ne kadar etkileyeceğini diferansiyel
ile tahmin edersin.
2. Çok Değişkenli Sistemlerde Hızlı Yaklaşık Hesap
Birden fazla girdinin birlikte değiştiği mühendislik sistemlerinde,
çıktıdaki değişimi tam hesaplamadan hızlıca tahmin etmeyi sağlar.
""")

_add("Calculus 3", ["Second derivative test"], """
Çok değişkenli İkinci Türev Testi, tek değişkenli versiyonun İKİ
BOYUTA genelleştirilmiş hâlidir — bir yüzeyin bir noktada tepe mi, çukur
mu, yoksa "eyer noktası" mı olduğunu belirler.

Nedir?
Kısmi türevlerden oluşan Hessian determinantı $D=f_{xx}f_{yy}-(f_{xy})^2$
hesaplanır: $D>0$ ve $f_{xx}>0$ ise minimum, $D>0$ ve $f_{xx}<0$ ise
maksimum, $D<0$ ise eyer noktasıdır (bazı yönlerde tepe, bazı yönlerde
çukur).

Ne İçin Kullanılır?
1. Çok Değişkenli Optimizasyon Problemlerini Sınıflandırmak
Kritik bir noktanın gerçek bir maksimum/minimum mu yoksa yanıltıcı bir
eyer noktası mı olduğunu ayırt etmeden, o noktayı "en iyi" sanmak ciddi
mühendislik/ekonomi hatalarına yol açabilir.
2. Makine Öğrenmesinde Kayıp Fonksiyonu Analizi
Derin öğrenme modellerinin eğitiminde "eyer noktalarına" takılma sorunu,
tam olarak bu testin incelediği geometriden kaynaklanır.
""")

_add("Calculus 3", ["Independence of path", "Line integral of a curve"], """
Çizgi integrali, bir integrali DÜZ bir eksen yerine EĞRİ bir yol boyunca
alır; yoldan bağımsızlık ise bazı özel (korunumlu) kuvvet alanlarında bu
integralin sadece BAŞLANGIÇ ve BİTİŞ noktasına bağlı olduğunu, izlenen
yola bağlı OLMADIĞINI söyler.

Nedir?
$\\int_C f(x,y)\\,ds$, bir eğri boyunca bir fonksiyonu "toplar" (örn. bir
telin toplam kütlesini, yoğunluk eğri boyunca değişiyorsa). Bir kuvvet
alanı gradyan alanıysa (bir potansiyel fonksiyonun gradyanıysa), bu alan
boyunca yapılan iş yoldan BAĞIMSIZDIR.

Ne İçin Kullanılır?
1. Fizikte "Korunumlu Kuvvetleri" Tanımak
Yerçekimi gibi korunumlu kuvvetlerde yapılan işin sadece başlangıç/bitiş
yüksekliğine bağlı olması (izlenen yola değil), enerjinin korunumu
ilkesinin matematiksel temelidir.
2. Değişken Yoğunluklu Nesnelerin Toplam Kütlesini Bulmak
Yoğunluğu boyunca değişen bir telin veya kablonun toplam kütlesini/
merkezini hesaplamak çizgi integrali gerektirir.
""")

_add("Calculus 3", ["Chain rule for multivariable functions"], """
Çok değişkenli zincir kuralı, bir değişkenin BAŞKA değişkenler
ÜZERİNDEN dolaylı olarak bir fonksiyonu nasıl etkilediğini hesaplar —
tek değişkenli zincir kuralının, birden fazla "yol" üzerinden
genelleştirilmiş hâlidir.

Nedir?
Eğer $z=f(x,y)$ ve $x,y$ kendileri $t$'nin fonksiyonuysa,
$\\dfrac{dz}{dt} = \\dfrac{\\partial z}{\\partial x}\\dfrac{dx}{dt} +
\\dfrac{\\partial z}{\\partial y}\\dfrac{dy}{dt}$ — her "yoldan" gelen
katkı ayrı ayrı hesaplanıp toplanır.

Ne İçin Kullanılır?
1. Birbirine Bağlı Çok Değişkenli Sistemlerde Değişim Oranı
Bir ürünün kârının hem fiyata hem üretim maliyetine bağlı olduğu ve
ikisinin de zamanla değiştiği durumlarda kârın zamana göre değişim
hızını bulmak bu kuralı gerektirir.
2. Makine Öğrenmesinde Geri Yayılımın Matematiksel Temeli
Derin sinir ağlarındaki geri yayılım algoritması, bu çok değişkenli
zincir kuralının binlerce kez otomatik uygulanmasından ibarettir.
""")

# ---------------------------------------------------------------------------
# Calculus 3 — round 2 (part 2: cylindrical/spherical, numeric)
# ---------------------------------------------------------------------------
_add("Calculus 3", ["Cylindrical coordinates", "Spherical coordinates",
                                    "Changing iterated and double integrals to polar coordinates",
                                    "Changing triple integrals to cylindrical coordinates",
                                    "Finding volume in cylindrical coordinates", "Finding volume in spherical coordinates"], """
Silindirik ve küresel koordinatlar, 3B uzayda DAİRESEL/KÜRESEL simetrisi
olan bölgeleri (bir boru, bir gezegen gibi) Kartezyen $(x,y,z)$'den çok
daha DOĞAL biçimde tarif eder.

Nedir?
Silindirik koordinatlar $(r,\\theta,z)$, taban düzlemini kutupsal
koordinatlarla, yüksekliği ise düz $z$ ile tarif eder ($dV=r\\,dr\\,
d\\theta\\,dz$). Küresel koordinatlar $(\\rho,\\theta,\\phi)$, bir
noktayı merkeze uzaklık ($\\rho$) ve iki açıyla tarif eder
($dV=\\rho^2\\sin\\phi\\,d\\rho\\,d\\theta\\,d\\phi$) — bu ek çarpanlar,
Jacobian'ın bu koordinat sistemlerine uyarlanmış hâlleridir.

Ne İçin Kullanılır?
1. Boru, Tank ve Silindirik Yapıların Hacim/Isı Analizi
Bir borudaki akışkanın hacmini veya ısı dağılımını hesaplamak, silindirik
koordinatlarda ÇOK DAHA KOLAYDIR.
2. Gezegen, Yıldız ve Manyetik Alan Modellemesi
Gökbilimde ve elektromanyetizmada küresel simetrili sistemlerin (bir
yıldızın iç sıcaklık dağılımı gibi) hemen tamamı küresel koordinatlarla
modellenir.
""")

_add("Calculus 3", ["Average value of a double integral", "Average value of a triple integral",
                                    "Midpoint rule for double integrals", "Midpoint rule for triple integrals"], """
Çoklu integral sayısal yöntemleri, tek değişkenli Riemann toplamı/orta
nokta kuralının, YÜZEY ve HACİM integrallerine genelleştirilmiş hâlidir.

Nedir?
Bir bölgedeki ortalama değer, integralin bölgenin alanına/hacmine
bölünmesiyle bulunur. Orta nokta kuralı, bölgeyi küçük dikdörtgen/kutucuklara
bölüp her birinin TAM ORTASINDAKİ değeri kullanarak integrali sayısal
olarak (elle çözülemediğinde) yaklaşık hesaplar.

Ne İçin Kullanılır?
1. Kapalı Formda Çözülemeyen Çoklu İntegralleri Tahmin Etmek
Mühendislik yazılımları, analitik çözümü olmayan karmaşık 2B/3B
integralleri bu tür sayısal yöntemlerle (bilgisayarla) yaklaşık
hesaplar.
2. Bir Bölgenin "Tipik" Sıcaklık/Yoğunluk Değerini Bulmak
Bir odanın veya bir cismin ortalama sıcaklığını, o bölge üzerindeki
sıcaklık fonksiyonunun integralinden hesaplamak bu tekniği kullanır.
""")

# ---------------------------------------------------------------------------
# Kapanış turu — son birkaç eksik (gerçek ağaçta %98 -> %100'e yakın kapsam)
# ---------------------------------------------------------------------------
_add("Calculus 2", ["Absolute and conditional convergence"], """
Mutlak ve koşullu yakınsaklık, bir alternatif serinin YAKINSAMASININ
"ne kadar sağlam" olduğunu ayırt eder — bazı seriler terimlerin
işaretini görmezden gelsen bile yakınsar, bazıları sadece işaretler
sayesinde ayakta durur.

Nedir?
Bir seri $\\sum|a_n|$ (mutlak değerleriyle) yakınsıyorsa MUTLAK yakınsaktır.
$\\sum a_n$ yakınsıyor ama $\\sum|a_n|$ ıraksıyorsa, seri KOŞULLU
yakınsaktır — bu durumda terimlerin sırasını değiştirmek serinin toplamını
DEĞİŞTİREBİLİR (Riemann'ın yeniden sıralama teoremi).

Ne İçin Kullanılır?
1. Hangi Yakınsaklık Testinin Daha Güçlü Olduğunu Anlamak
Mutlak yakınsaklık, koşullu yakınsaklıktan daha güçlü bir garantidir;
hangi testin ne söylediğini doğru yorumlamak için bu ayrım gereklidir.
2. Sayısal Hesaplamalarda Sıralama Hassasiyetini Bilmek
Bilgisayarların sonsuz toplamları yaklaşık hesaplarken, koşullu yakınsak
serilerde toplama SIRASININ sonucu etkileyebileceğini bilmek, sayısal
analizde kritik bir uyarıdır.
""")

_add("Calculus 3", ["Cross product of two vectors", "Dot product of two vectors"], """
İki vektörün nokta ve çapraz çarpımı, üç boyutlu uzayda vektörler
arasındaki en temel iki ilişkiyi (hizalanma derecesi ve dik yön) verir
— Lineer Cebir dersindeki aynı işlemlerin, somut 3B geometri
bağlamındaki uygulamasıdır.

Nedir?
Nokta çarpım $\\vec{u}\\cdot\\vec{v}=u_1v_1{+}u_2v_2{+}u_3v_3$ bir SAYI
verir (iki vektör arasındaki açıyla ilişkilidir). Çapraz çarpım
$\\vec{u}\\times\\vec{v}$ ise HER İKİSİNE de dik yeni bir VEKTÖR üretir;
büyüklüğü, iki vektörün oluşturduğu paralelkenarın alanına eşittir.

Ne İçin Kullanılır?
1. Bir Yüzeyin Normal Vektörünü Bulmak
Bir düzlemdeki iki vektörün çapraz çarpımı, o düzleme dik (normal)
vektörü verir — düzlem denklemi kurmanın ilk adımıdır.
2. Fizikte Tork ve Açısal Momentum Hesabı
Bir kuvvetin bir cismi ne yönde ve ne kadar döndürdüğü (tork), kuvvet ve
konum vektörlerinin çapraz çarpımıyla hesaplanır.
""")

_add("Calculus 3", ["Normal line to the surface"], """
Bir yüzeye normal doğru, o yüzeye teğet düzleme DİK olan, yüzeyden
"dışarı doğru" çıkan doğrudur.

Nedir?
Bir $F(x,y,z)=0$ yüzeyinin bir noktadaki normal doğrusu, gradyan vektörü
$\\nabla F$'yi yön vektörü olarak kullanan parametrik bir doğrudur —
gradyanın seviye yüzeylerine her zaman dik olması özelliğinden gelir.

Ne İçin Kullanılır?
1. 3B Grafiklerde Işıklandırma Hesabı
Bir yüzeyin bir ışık kaynağına ne kadar "baktığını" (parlaklığını)
hesaplamak, o noktadaki normal doğrunun yönünü bilmeyi gerektirir.
2. Optik Sistemlerde Işın Yansımasını Hesaplamak
Bir ışının eğri bir yüzeyden nasıl yansıyacağını hesaplamak (yansıma
açısı = geliş açısı, normale göre) bu doğruya dayanır.
""")

_add("Calculus 3", ["Projections of the curve", "Reparametrizing the curve",
                                    "Vector function for the curve of intersection of two surfaces"], """
Bir uzay eğrisini yeniden parametrelemek ve izdüşümlerini almak, aynı
geometrik yolu FARKLI bir "hızla" (parametreyle) tarif etmek veya onu
daha basit bir düzleme (xy, xz, yz) düşürerek incelemektir.

Nedir?
Yeniden parametreleme, $t$ yerine başka bir değişken (örn. yay uzunluğu
$s$) kullanarak AYNI eğriyi tarif eder — eğrinin şekli değişmez, sadece
üzerinde "ilerleme hızı" değişir. İki yüzeyin kesişim eğrisi, iki yüzey
denklemi birlikte çözülerek (genelde bir parametre cinsinden) bulunur.
Bir eğrinin bir düzleme izdüşümü, ilgili koordinatı (örn. $z$'yi) göz ardı
ederek elde edilir.

Ne İçin Kullanılır?
1. Eğriyi Yay Uzunluğuna Göre "Doğal" Hızla İncelemek
Eğrilik gibi geometrik özellikleri hesaplarken, eğriyi yay uzunluğu
parametresiyle yeniden yazmak formülleri büyük ölçüde sadeleştirir.
2. Karmaşık 3B Kesişimleri Anlaşılır Kılmak
İki karmaşık yüzeyin (örn. bir küre ile bir silindirin) kesiştiği eğriyi
düzlemlere izdüşürerek daha basit, tanıdık 2B eğriler olarak görselleştirmek
mümkün olur.
""")

_add("Algebra", ["Absolute value equations", "Absolute value inequalities"], """
Mutlak değerli denklem ve eşitsizlikler, $|x|$'in İKİ farklı durumu
(içerideki ifade pozitif VEYA negatif) temsil edebileceği gerçeğinden
yola çıkarak çözülür.

Nedir?
$|x|=a$ ($a>0$) denklemi İKİ ayrı denkleme ayrılır: $x=a$ VEYA $x=-a$.
$|x|<a$ eşitsizliği bir ARALIĞA ($-a<x<a$) karşılık gelirken, $|x|>a$
İKİ AYRI aralığa ($x<-a$ veya $x>a$) karşılık gelir — yön burada kritik
bir farktır.

Ne İçin Kullanılır?
1. Tolerans ve Hata Payı Problemlerini Modellemek
"Ürünün ağırlığı hedeften en fazla 2 gram sapabilir" gibi mühendislik
tolerans koşulları doğrudan mutlak değerli eşitsizliklerle ifade edilir.
2. İki Farklı Senaryoyu Tek Denklemde Yakalamak
Bir büyüklüğün iki yönde de (fazla veya eksik) aynı sınırı aştığı
durumları TEK bir kompakt ifadeyle yazmayı sağlar.
""")

_add("Algebra", ["PEMDAS and order of operations"], """
İşlem önceliği (PEMDAS/BODMAS), bir ifadede HANGİ işlemin ÖNCE
yapılacağını belirleyen evrensel bir anlaşmadır — bu kural olmadan aynı
ifade farklı insanlar tarafından farklı sonuçlara götürülebilirdi.

Nedir?
Sıra: Parantezler → Üsler → Çarpma/Bölme (soldan sağa, EŞİT öncelikli) →
Toplama/Çıkarma (soldan sağa, EŞİT öncelikli). "Önce çarpma sonra bölme"
gibi bir kural YOKTUR — ikisi aynı önceliğe sahiptir ve soldan sağa
hangisi önce gelirse o yapılır.

Ne İçin Kullanılır?
1. Herkesin Aynı İfadeden Aynı Sonucu Almasını Garanti Etmek
Bilimsel makalelerden hesap makinelerine kadar her yerde $3+4\\times2$'nin
HERKES için aynı (11) sonucu vermesini sağlayan anlaşmadır.
2. Programlama Dillerinin Sözdizimi Kurallarının Temeli
Her programlama dilinin derleyicisi, bir ifadeyi tam olarak bu öncelik
kurallarına göre (operatör önceliği) yorumlar.
""")

_add("Calculus 3", ["Expressing the integral six ways", "Finding area", "Finding surface area",
                                    "Sketching area"], """
Bir çoklu integrali "altı farklı şekilde ifade etmek", AYNI hacim/alanı
FARKLI integrasyon SIRALARIYla ($dx\\,dy\\,dz$, $dz\\,dx\\,dy$ gibi tüm
permütasyonlarla) yazabilme becerisidir — hangi sıranın hesaplaması daha
kolaysa o seçilir.

Nedir?
Bir bölgenin sınırları, hangi değişkenin İÇ, hangisinin DIŞ integral
olduğuna bağlı olarak farklı görünür; bölgeyi doğru ÇİZEBİLMEK (sketching),
doğru sınırları (integral limitlerini) belirlemenin ön koşuludur.

Ne İçin Kullanılır?
1. Zor Bir İntegrali Kolay Bir Sıraya Çevirmek
Bazı integrasyon sıraları elle çözülemezken, aynı bölgeyi FARKLI bir
sırayla yazmak integrali çözülebilir hâle getirebilir (bir integralin
"imkânsız" görünmesi, çoğu zaman yanlış sıra seçildiği içindir).
2. Mühendislik Yazılımlarında Doğru Sınırları Kodlamak
Sayısal integrasyon yazılımlarına doğru sınırları girmek için, bölgeyi
önce doğru zihinsel/görsel olarak anlamak gerekir.
""")
