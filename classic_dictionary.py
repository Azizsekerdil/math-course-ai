# -*- coding: utf-8 -*-
"""Math Course AI — klasik gomulu Ingilizce-Turkce sozluk (yedek).

Ana dosyadan (Math_Course_AI.pyw) V48'de mekanik olarak cikarildi.
Asil sozluk language_dictionary.LanguageDictionaryPanel'dir; bu sinif
yalnizca o modul yuklenemezse devreye giren sade yedektir ve *_TERMS
listeleri yeni sozluge tohum olarak da verilir.
"""

import tkinter as tk
from tkinter import ttk

from mca_common import THEME, RoundedButton

class EnglishTurkishDictionary(ttk.Frame):
    """Built-in science dictionary with dictionary-type and category filters."""

    MATH_TERMS = [
        {'en':'absolute value','tr':'mutlak değer','category':'Arithmetic / Aritmetik','tr_explanation':'Bir sayının sıfıra olan uzaklığıdır; sonuç negatif olmaz.','en_explanation':'The distance of a number from zero; it is never negative.','example':'|-7| = 7'},
        {'en':'addition','tr':'toplama','category':'Arithmetic / Aritmetik','tr_explanation':'İki veya daha fazla sayıyı birleştirerek toplam bulma işlemidir.','en_explanation':'Combining numbers to find a sum.','example':'8 + 5 = 13'},
        {'en':'subtraction','tr':'çıkarma','category':'Arithmetic / Aritmetik','tr_explanation':'Bir sayıdan başka bir sayıyı eksiltme işlemidir.','en_explanation':'Taking one number away from another.','example':'10 - 4 = 6'},
        {'en':'fraction','tr':'kesir','category':'Arithmetic / Aritmetik','tr_explanation':'Bir bütünün eş parçalarını gösteren sayıdır.','en_explanation':'A number representing equal parts of a whole.','example':'3/4 bir kesirdir.'},
        {'en':'denominator','tr':'payda','category':'Arithmetic / Aritmetik','tr_explanation':'Kesirde alt tarafta bulunan sayıdır.','en_explanation':'The bottom number in a fraction.','example':'3/5 kesrinde payda 5 tir.'},
        {'en':'numerator','tr':'pay','category':'Arithmetic / Aritmetik','tr_explanation':'Kesirde üst tarafta bulunan sayıdır.','en_explanation':'The top number in a fraction.','example':'3/5 kesrinde pay 3 tür.'},
        {'en':'ratio','tr':'oran','category':'Arithmetic / Aritmetik','tr_explanation':'İki niceliğin karşılaştırılmasıdır.','en_explanation':'A comparison of two quantities.','example':'2:3'},
        {'en':'percent','tr':'yüzde','category':'Arithmetic / Aritmetik','tr_explanation':'Yüzde biriminden oran ifade eder.','en_explanation':'A ratio expressed per hundred.','example':'25% = 25/100'},
        {'en':'algebra','tr':'cebir','category':'Algebra / Cebir','tr_explanation':'Sayılar ve değişkenler arasındaki ilişkileri inceler.','en_explanation':'The study of relationships using numbers and variables.','example':'2x + 3 = 11'},
        {'en':'equation','tr':'denklem','category':'Algebra / Cebir','tr_explanation':'İki ifadenin eşit olduğunu gösteren matematik cümlesidir.','en_explanation':'A mathematical statement that two expressions are equal.','example':'x + 4 = 10'},
        {'en':'coefficient','tr':'katsayı','category':'Algebra / Cebir','tr_explanation':'Bir değişkeni çarpan sayıdır.','en_explanation':'The numerical factor multiplying a variable.','example':'7x ifadesinde katsayı 7 dir.'},
        {'en':'factor','tr':'çarpan','category':'Algebra / Cebir','tr_explanation':'Bir sayıyı kalansız bölen ya da çarpımda yer alan sayıdır.','en_explanation':'A number that divides another exactly or appears in a product.','example':'3 ve 4, 12 nin çarpanlarıdır.'},
        {'en':'polynomial','tr':'polinom','category':'Algebra / Cebir','tr_explanation':'Terimlerin toplamından oluşan cebirsel ifadedir.','en_explanation':'An algebraic expression made of a sum of terms.','example':'x^2 + 3x + 2'},
        {'en':'function','tr':'fonksiyon','category':'Functions / Fonksiyonlar','tr_explanation':'Her girdiye tam bir çıktı eşleyen kuraldır.','en_explanation':'A rule that assigns exactly one output to each input.','example':'f(x)=2x+1'},
        {'en':'domain','tr':'tanım kümesi','category':'Functions / Fonksiyonlar','tr_explanation':'Bir fonksiyona verilebilecek girişler kümesidir.','en_explanation':'The set of allowed inputs of a function.','example':'f(x)=1/x için x=0 tanım kümesinde değildir.'},
        {'en':'range','tr':'değer kümesi','category':'Functions / Fonksiyonlar','tr_explanation':'Fonksiyonun üretebildiği çıktıların kümesidir.','en_explanation':'The set of outputs a function can produce.','example':'f(x)=x^2 için y≥0'},
        {'en':'slope','tr':'eğim','category':'Geometry / Geometri','tr_explanation':'Doğrunun dikey değişiminin yatay değişime oranıdır.','en_explanation':'The ratio of vertical change to horizontal change.','example':'m = Δy/Δx'},
        {'en':'angle','tr':'açı','category':'Geometry / Geometri','tr_explanation':'Aynı noktadan çıkan iki ışının oluşturduğu açıklıktır.','en_explanation':'The opening formed by two rays with the same endpoint.','example':'Dik açı 90 derecedir.'},
        {'en':'area','tr':'alan','category':'Geometry / Geometri','tr_explanation':'Bir düzlemsel şeklin kapladığı yüzey miktarıdır.','en_explanation':'The amount of surface covered by a 2D shape.','example':'Dikdörtgen alanı = uzunluk x genişlik'},
        {'en':'perimeter','tr':'çevre','category':'Geometry / Geometri','tr_explanation':'Bir şeklin etrafındaki toplam uzunluktur.','en_explanation':'The total distance around a shape.','example':'Karenin çevresi = 4a'},
        {'en':'vector','tr':'vektör','category':'Linear Algebra / Lineer Cebir','tr_explanation':'Büyüklüğü ve yönü olan niceliktir.','en_explanation':'A quantity with magnitude and direction.','example':'<3,4>'},
        {'en':'matrix','tr':'matris','category':'Linear Algebra / Lineer Cebir','tr_explanation':'Satır ve sütunlardan oluşan sayısal tablodur.','en_explanation':'A rectangular array of numbers.','example':'[[1,2],[3,4]]'},
        {'en':'determinant','tr':'determinant','category':'Linear Algebra / Lineer Cebir','tr_explanation':'Kare matris için tek bir sayı üreten özettir.','en_explanation':'A scalar summary associated with a square matrix.','example':'2x2 matris için ad-bc'},
        {'en':'derivative','tr':'türev','category':'Calculus / Kalkülüs','tr_explanation':'Fonksiyonun anlık değişim hızını verir.','en_explanation':'The instantaneous rate of change of a function.','example':'d/dx (x^2) = 2x'},
        {'en':'integral','tr':'integral','category':'Calculus / Kalkülüs','tr_explanation':'Toplam birikimi veya alanı temsil eder.','en_explanation':'Represents accumulation or area.','example':'∫x dx = x^2/2 + C'},
        {'en':'limit','tr':'limit','category':'Calculus / Kalkülüs','tr_explanation':'Bir fonksiyonun belli bir noktaya yaklaşırken aldığı değeri ifade eder.','en_explanation':'The value a function approaches near a point.','example':'lim x→0 sinx/x = 1'},
        {'en':'probability','tr':'olasılık','category':'Statistics / İstatistik','tr_explanation':'Bir olayın gerçekleşme ihtimalini ölçer.','en_explanation':'Measures the chance of an event.','example':'Yazı gelme olasılığı 1/2'},
        {'en':'mean','tr':'ortalama','category':'Statistics / İstatistik','tr_explanation':'Verilerin toplamının veri sayısına bölünmesidir.','en_explanation':'The sum of values divided by the number of values.','example':'2,4,6 ortalaması 4'},
        {'en':'standard deviation','tr':'standart sapma','category':'Statistics / İstatistik','tr_explanation':'Verilerin ne kadar yayıldığını gösterir.','en_explanation':'Measures how spread out the values are.','example':'Sapma büyüdükçe veri daha dağınıktır.'},
        {'en':'radical','tr':'köklü ifade','category':'Algebra / Cebir','tr_explanation':'Kök sembolü içeren ifadedir.','en_explanation':'An expression containing a root.','example':'√40 = 2√10'},
    ]

    PHYSICS_TERMS = [
        {'en':'position','tr':'konum','category':'Mechanics / Mekanik','tr_explanation':'Bir cismin referans sistemine göre yeridir.','en_explanation':'The location of an object relative to a reference system.','example':'x(t) ile gösterilebilir.'},
        {'en':'velocity','tr':'hız','category':'Mechanics / Mekanik','tr_explanation':'Konumun zamana göre değişim hızıdır ve yön içerir.','en_explanation':'Rate of change of position with direction.','example':'v = dx/dt'},
        {'en':'acceleration','tr':'ivme','category':'Mechanics / Mekanik','tr_explanation':'Hızın zamana göre değişim oranıdır.','en_explanation':'The rate of change of velocity with respect to time.','example':'a = Δv/Δt'},
        {'en':'force','tr':'kuvvet','category':'Mechanics / Mekanik','tr_explanation':'Bir cisme ivme kazandıran etkidir.','en_explanation':'An interaction that can accelerate an object.','example':'F = ma'},
        {'en':'momentum','tr':'momentum','category':'Mechanics / Mekanik','tr_explanation':'Kütle ile hızın çarpımıdır.','en_explanation':'The product of mass and velocity.','example':'p = mv'},
        {'en':'impulse','tr':'itme','category':'Mechanics / Mekanik','tr_explanation':'Kuvvet-zaman çarpımıdır ve momentum değişimine eşittir.','en_explanation':'Force times time; equal to change in momentum.','example':'J = FΔt'},
        {'en':'energy','tr':'enerji','category':'Mechanics / Mekanik','tr_explanation':'İş yapabilme kapasitesidir.','en_explanation':'The capacity to do work.','example':'Kinetik enerji = 1/2 mv^2'},
        {'en':'power','tr':'güç','category':'Mechanics / Mekanik','tr_explanation':'Bir işin yapılma hızıdır.','en_explanation':'The rate at which work is done.','example':'P = W/t'},
        {'en':'work','tr':'iş','category':'Mechanics / Mekanik','tr_explanation':'Kuvvet ile yer değiştirmenin skaler çarpımıdır.','en_explanation':'The scalar product of force and displacement.','example':'W = Fd cosθ'},
        {'en':'electric field','tr':'elektrik alan','category':'Electricity / Elektrik','tr_explanation':'Uzaydaki her noktaya kuvvet yönü atayan vektör alandır.','en_explanation':'A vector field assigning force direction and magnitude in space.','example':'E = kq/r^2'},
        {'en':'current','tr':'akım','category':'Electricity / Elektrik','tr_explanation':'Birim zamanda geçen yük miktarıdır.','en_explanation':'Charge flow per unit time.','example':'I = Q/t'},
        {'en':'voltage','tr':'gerilim','category':'Electricity / Elektrik','tr_explanation':'Birim yük başına enerji farkıdır.','en_explanation':'Energy difference per unit charge.','example':'V = W/Q'},
        {'en':'resistance','tr':'direnç','category':'Electricity / Elektrik','tr_explanation':'Akıma karşı gösterilen zorluktur.','en_explanation':'Opposition to electric current.','example':'V = IR'},
        {'en':'wave','tr':'dalga','category':'Waves / Dalgalar','tr_explanation':'Enerjinin uzay ve zamanda yayılmasıdır.','en_explanation':'A propagating disturbance carrying energy.','example':'y(x,t)=A sin(kx-ωt)'},
        {'en':'frequency','tr':'frekans','category':'Waves / Dalgalar','tr_explanation':'Birim zamandaki salınım sayısıdır.','en_explanation':'Number of oscillations per unit time.','example':'f = 1/T'},
        {'en':'wavelength','tr':'dalga boyu','category':'Waves / Dalgalar','tr_explanation':'İki ardışık aynı faz noktası arasındaki mesafedir.','en_explanation':'Distance between two successive in-phase points.','example':'v = fλ'},
        {'en':'amplitude','tr':'genlik','category':'Waves / Dalgalar','tr_explanation':'Maksimum sapma miktarıdır.','en_explanation':'Maximum displacement from equilibrium.','example':'A, dalganın yüksekliğini belirler.'},
        {'en':'temperature','tr':'sıcaklık','category':'Thermodynamics / Termodinamik','tr_explanation':'Parçacıkların ortalama kinetik enerjisi ile ilişkili ölçüdür.','en_explanation':'A measure related to average kinetic energy.','example':'Kelvin sıcaklık ölçeğidir.'},
        {'en':'entropy','tr':'entropi','category':'Thermodynamics / Termodinamik','tr_explanation':'Düzensizlik veya mikrodurum sayısı ile ilişkili büyüklüktür.','en_explanation':'A quantity related to disorder or the number of microstates.','example':'ΔS > 0 olabilir.'},
        {'en':'pressure','tr':'basınç','category':'Thermodynamics / Termodinamik','tr_explanation':'Birim alana etki eden kuvvettir.','en_explanation':'Force per unit area.','example':'P = F/A'},
        {'en':'refraction','tr':'kırılma','category':'Optics / Optik','tr_explanation':'Işığın ortam değiştirirken yön değiştirmesidir.','en_explanation':'The bending of light as it enters a new medium.','example':'n1 sinθ1 = n2 sinθ2'},
        {'en':'reflection','tr':'yansıma','category':'Optics / Optik','tr_explanation':'Işığın yüzeyden geri dönmesidir.','en_explanation':'The return of light from a surface.','example':'Gelme açısı = yansıma açısı'},
    ]

    DNA_TERMS = [
        {'en':'DNA','tr':'DNA','category':'Genetics / Genetik','tr_explanation':'Genetik bilgiyi taşıyan çift sarmallı moleküldür.','en_explanation':'The double-helical molecule carrying genetic information.','example':'DNA bazları A, C, G, T dir.'},
        {'en':'gene','tr':'gen','category':'Genetics / Genetik','tr_explanation':'Bir ürün için bilgi taşıyan DNA bölgesidir.','en_explanation':'A DNA region that carries information for a product.','example':'Bir gen birçok kodondan oluşabilir.'},
        {'en':'genome','tr':'genom','category':'Genetics / Genetik','tr_explanation':'Bir canlının tüm genetik materyalidir.','en_explanation':'The complete genetic material of an organism.','example':'İnsan genomu milyarlarca baz içerebilir.'},
        {'en':'chromosome','tr':'kromozom','category':'Genetics / Genetik','tr_explanation':'DNA ve proteinlerden oluşan paketlenmiş yapıdır.','en_explanation':'A packaged structure made of DNA and proteins.','example':'İnsanlarda 23 çift kromozom vardır.'},
        {'en':'allele','tr':'alel','category':'Genetics / Genetik','tr_explanation':'Bir genin alternatif biçimidir.','en_explanation':'An alternative form of a gene.','example':'Göz rengi için farklı aleller olabilir.'},
        {'en':'nucleotide','tr':'nükleotit','category':'Molecular Biology / Moleküler Biyoloji','tr_explanation':'Baz, şeker ve fosfattan oluşan temel yapı taşıdır.','en_explanation':'The basic building block made of base, sugar, and phosphate.','example':'A bir nükleotit bazını temsil eder.'},
        {'en':'base pair','tr':'baz çifti','category':'Molecular Biology / Moleküler Biyoloji','tr_explanation':'Tamamlayıcı iki bazın eşleşmesidir.','en_explanation':'A complementary matched pair of bases.','example':'A-T ve C-G'},
        {'en':'codon','tr':'kodon','category':'Molecular Biology / Moleküler Biyoloji','tr_explanation':'Üç bazdan oluşan bilgi birimidir.','en_explanation':'A three-base information unit.','example':'ATG bir başlangıç kodonudur.'},
        {'en':'replication','tr':'replikasyon','category':'Molecular Biology / Moleküler Biyoloji','tr_explanation':'DNA nın kendini kopyalama sürecidir.','en_explanation':'The process by which DNA copies itself.','example':'Hücre bölünmeden önce gerçekleşir.'},
        {'en':'transcription','tr':'transkripsiyon','category':'Molecular Biology / Moleküler Biyoloji','tr_explanation':'DNA bilgisinin RNA ya aktarılmasıdır.','en_explanation':'Copying DNA information into RNA.','example':'Gen ifadesinin ilk adımıdır.'},
        {'en':'translation','tr':'translasyon','category':'Molecular Biology / Moleküler Biyoloji','tr_explanation':'RNA bilgisinin proteine çevrilmesidir.','en_explanation':'Converting RNA information into protein.','example':'Kodonlar amino asitlere çevrilir.'},
        {'en':'mutation','tr':'mutasyon','category':'Molecular Biology / Moleküler Biyoloji','tr_explanation':'Dizideki kalıcı değişikliktir.','en_explanation':'A lasting change in the sequence.','example':'A dan G ye dönüşüm bir mutasyon olabilir.'},
        {'en':'RNA','tr':'RNA','category':'Molecular Biology / Moleküler Biyoloji','tr_explanation':'Gen ifadesinde rol oynayan tek iplikli nükleik asittir.','en_explanation':'A single-stranded nucleic acid involved in gene expression.','example':'mRNA protein sentezinde kullanılır.'},
        {'en':'amino acid','tr':'amino asit','category':'Molecular Biology / Moleküler Biyoloji','tr_explanation':'Proteinlerin yapı taşıdır.','en_explanation':'The building block of proteins.','example':'20 temel amino asit vardır.'},
        {'en':'k-mer','tr':'k-mer','category':'Bioinformatics / Biyoinformatik','tr_explanation':'Uzunluğu k olan alt dizi parçasıdır.','en_explanation':'A substring of length k.','example':'ACGT dizisinde 2-mer ler AC, CG, GT dir.'},
        {'en':'reverse complement','tr':'ters tamamlayıcı','category':'Bioinformatics / Biyoinformatik','tr_explanation':'Dizinin ters çevrilip tamamlayıcı bazlarla yazılmasıdır.','en_explanation':'The reversed sequence written with complementary bases.','example':'ATGC nin ters tamamlayıcısı GCAT'},
        {'en':'GC content','tr':'GC oranı','category':'Bioinformatics / Biyoinformatik','tr_explanation':'Dizideki G ve C bazlarının oranıdır.','en_explanation':'The fraction of G and C bases in a sequence.','example':'GC içeriği yüzde olarak verilebilir.'},
        {'en':'alignment','tr':'hizalama','category':'Bioinformatics / Biyoinformatik','tr_explanation':'İki veya daha fazla diziyi benzerlik için eşleme işlemidir.','en_explanation':'Matching sequences to compare similarity.','example':'Global ve local hizalama yapılabilir.'},
        {'en':'Hamming distance','tr':'Hamming uzaklığı','category':'Bioinformatics / Biyoinformatik','tr_explanation':'Aynı uzunluktaki iki dizi arasındaki farklı konum sayısıdır.','en_explanation':'The number of differing positions between equal-length strings.','example':'AAC ile AGC arasında uzaklık 1 dir.'},
        {'en':'Shannon entropy','tr':'Shannon entropisi','category':'Bioinformatics / Biyoinformatik','tr_explanation':'Bilgi çeşitliliğini ölçen büyüklüktür.','en_explanation':'A measure of information diversity or uncertainty.','example':'H = -Σ p log2 p'},
    ]

    CHEMISTRY_TERMS = [
        {'en':'atom','tr':'atom','category':'General Chemistry / Genel Kimya','tr_explanation':'Maddenin kimyasal özelliklerini taşıyan en küçük birimidir.','en_explanation':'The smallest unit retaining chemical properties.','example':'Hidrojen bir atom türüdür.'},
        {'en':'molecule','tr':'molekül','category':'General Chemistry / Genel Kimya','tr_explanation':'İki veya daha çok atomun bağlanmasıyla oluşur.','en_explanation':'A group of bonded atoms.','example':'H2O bir moleküldür.'},
        {'en':'ion','tr':'iyon','category':'General Chemistry / Genel Kimya','tr_explanation':'Elektron alıp veren yüklü taneciktir.','en_explanation':'A charged particle formed by gain or loss of electrons.','example':'Na+ bir katyondur.'},
        {'en':'compound','tr':'bileşik','category':'General Chemistry / Genel Kimya','tr_explanation':'Farklı elementlerin belirli oranlarda birleşmesiyle oluşur.','en_explanation':'A substance made of different elements in fixed ratios.','example':'CO2 bir bileşiktir.'},
        {'en':'mole','tr':'mol','category':'General Chemistry / Genel Kimya','tr_explanation':'Belirli sayıda taneciği temsil eden miktar birimidir.','en_explanation':'A unit representing a specific number of particles.','example':'1 mol ≈ 6.022×10^23 tanecik'},
        {'en':'molar mass','tr':'molar kütle','category':'General Chemistry / Genel Kimya','tr_explanation':'Bir mol maddenin gram cinsinden kütlesidir.','en_explanation':'The mass of one mole of a substance.','example':'H2O için yaklaşık 18 g/mol'},
        {'en':'solution','tr':'çözelti','category':'Solutions / Çözeltiler','tr_explanation':'Çözücü ve çözünenin homojen karışımıdır.','en_explanation':'A homogeneous mixture of solute and solvent.','example':'Tuzlu su bir çözeltidir.'},
        {'en':'concentration','tr':'derişim','category':'Solutions / Çözeltiler','tr_explanation':'Birim hacimdeki çözünen miktarıdır.','en_explanation':'Amount of solute per unit volume.','example':'0.5 M NaCl'},
        {'en':'molarity','tr':'molarite','category':'Solutions / Çözeltiler','tr_explanation':'Litre başına mol sayısıdır.','en_explanation':'Moles of solute per liter of solution.','example':'M = n/V'},
        {'en':'solubility','tr':'çözünürlük','category':'Solutions / Çözeltiler','tr_explanation':'Bir maddenin çözünebileceği maksimum miktardır.','en_explanation':'The maximum amount of a substance that can dissolve.','example':'Sıcaklık çözünürlüğü etkileyebilir.'},
        {'en':'reaction rate','tr':'reaksiyon hızı','category':'Kinetics / Kinetik','tr_explanation':'Derişimin zamana göre değişim hızıdır.','en_explanation':'The rate at which concentration changes with time.','example':'r = -d[A]/dt'},
        {'en':'catalyst','tr':'katalizör','category':'Kinetics / Kinetik','tr_explanation':'Reaksiyonu hızlandırır ama kalıcı olarak tüketilmez.','en_explanation':'Speeds up a reaction without being permanently consumed.','example':'Enzimler biyolojik katalizörlerdir.'},
        {'en':'activation energy','tr':'aktivasyon enerjisi','category':'Kinetics / Kinetik','tr_explanation':'Reaksiyonun başlaması için gereken minimum enerjidir.','en_explanation':'The minimum energy needed for a reaction to start.','example':'Katalizör bu bariyeri düşürür.'},
        {'en':'equilibrium','tr':'denge','category':'Equilibrium / Denge','tr_explanation':'İleri ve geri hızların eşitlendiği durumdur.','en_explanation':'The state where forward and reverse rates are equal.','example':'K = ürünler/girenler'},
        {'en':'Le Chatelier principle','tr':'Le Chatelier ilkesi','category':'Equilibrium / Denge','tr_explanation':'Dengede sistem dış etkiye karşı koyacak yönde tepki verir.','en_explanation':'A system at equilibrium shifts to oppose an external change.','example':'Basınç artarsa denge kayabilir.'},
        {'en':'pH','tr':'pH','category':'Acid-Base / Asit-Baz','tr_explanation':'Asitlik bazlık ölçüsüdür.','en_explanation':'A measure of acidity or basicity.','example':'pH = -log10[H+]'},
        {'en':'acid','tr':'asit','category':'Acid-Base / Asit-Baz','tr_explanation':'Proton verebilen veya suda H+ oluşturan türdür.','en_explanation':'A species that donates protons or forms H+ in water.','example':'HCl kuvvetli asittir.'},
        {'en':'base','tr':'baz','category':'Acid-Base / Asit-Baz','tr_explanation':'Proton alabilen veya OH- oluşturan türdür.','en_explanation':'A species that accepts protons or forms OH- in water.','example':'NaOH kuvvetli bazdır.'},
        {'en':'buffer','tr':'tampon çözelti','category':'Acid-Base / Asit-Baz','tr_explanation':'pH değişimine direnç gösteren çözelti türüdür.','en_explanation':'A solution that resists pH changes.','example':'pH = pKa + log([A-]/[HA])'},
        {'en':'ideal gas law','tr':'ideal gaz yasası','category':'Physical Chemistry / Fizikokimya','tr_explanation':'Gaz değişkenleri arasındaki temel ilişkidir.','en_explanation':'The basic relation among gas variables.','example':'PV = nRT'},
        {'en':'diffusion','tr':'difüzyon','category':'Physical Chemistry / Fizikokimya','tr_explanation':'Taneciklerin derişim farkı nedeniyle yayılmasıdır.','en_explanation':'The spreading of particles due to concentration differences.','example':'J = -D dc/dx'},
        {'en':'enthalpy','tr':'entalpi','category':'Physical Chemistry / Fizikokimya','tr_explanation':'Sabit basınçta ısı değişimiyle ilişkili büyüklüktür.','en_explanation':'A quantity related to heat change at constant pressure.','example':'ΔH < 0 ekzotermik olabilir.'},
        {'en':'stoichiometry','tr':'stokiyometri','category':'Stoichiometry / Stokiyometri','tr_explanation':'Reaksiyonlardaki nicel oranları inceler.','en_explanation':'The quantitative relationships in reactions.','example':'2H2 + O2 -> 2H2O'},
        {'en':'limiting reagent','tr':'sınırlayıcı madde','category':'Stoichiometry / Stokiyometri','tr_explanation':'Ürünün miktarını sınırlayan girendir.','en_explanation':'The reactant that limits the amount of product formed.','example':'Önce tükenen girendir.'},
        {'en':'yield','tr':'verim','category':'Stoichiometry / Stokiyometri','tr_explanation':'Gerçek ürün miktarının teorik ürüne oranıdır.','en_explanation':'The ratio of actual product to theoretical product.','example':'% verim = gerçek / teorik × 100'},
    ]

    DICT_TYPES = {
        'Mathematics': ('Mathematics / Matematik', MATH_TERMS),
        'Physics': ('Physics / Fizik', PHYSICS_TERMS),
        'DNA': ('DNA / Genetik', DNA_TERMS),
        'Chemistry': ('Chemistry / Kimya', CHEMISTRY_TERMS),
    }

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.query_var = tk.StringVar()
        self.dict_type_var = tk.StringVar(value='Mathematics')
        self.category_var = tk.StringVar(value='All / Tümü')
        self.filtered_terms = list(self.current_terms())
        self._build()

    def _t(self, key):
        return self.app.t(key) if hasattr(self.app, 't') else key

    def current_terms(self):
        return list(self.DICT_TYPES.get(self.dict_type_var.get(), self.DICT_TYPES['Mathematics'])[1])

    def type_label(self, key):
        return self.DICT_TYPES.get(key, self.DICT_TYPES['Mathematics'])[0]

    def category_options(self):
        cats = sorted({item['category'] for item in self.current_terms()})
        return ['All / Tümü'] + cats

    def _build(self):
        top = ttk.Frame(self, style='Panel.TFrame')
        top.pack(fill='x', padx=10, pady=10)
        self.title_label = ttk.Label(top, text=self._t('dictionary_full'), style='Header.TLabel')
        self.title_label.pack(side='left', padx=(0, 10))
        self.type_combo = ttk.Combobox(top, textvariable=self.dict_type_var, values=list(self.DICT_TYPES.keys()), width=14, state='readonly')
        self.type_combo.pack(side='left', padx=4)
        self.type_combo.bind('<<ComboboxSelected>>', lambda e: self.on_type_change())
        self.category_combo = ttk.Combobox(top, textvariable=self.category_var, values=self.category_options(), width=28, state='readonly')
        self.category_combo.pack(side='left', padx=4)
        self.category_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_terms())
        entry = ttk.Entry(top, textvariable=self.query_var, width=40)
        entry.pack(side='left', fill='x', expand=True, padx=5)
        entry.bind('<Return>', lambda e: self.lookup())
        entry.bind('<KeyRelease>', lambda e: self.filter_terms())
        self.lookup_button = RoundedButton(top, text=self._t('lookup'), command=self.lookup)
        self.lookup_button.pack(side='left', padx=4)
        self.hint_label = ttk.Label(self, text=self.build_hint_text(), style='Muted.TLabel')
        self.hint_label.pack(fill='x', padx=12, pady=(0, 8))

        body = ttk.Panedwindow(self, orient='horizontal')
        body.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        left = ttk.Frame(body, style='Panel.TFrame')
        right = ttk.Frame(body, style='Panel.TFrame')
        body.add(left, weight=1)
        body.add(right, weight=2)

        self.listbox = tk.Listbox(left, bg=THEME["surface"], fg=THEME['text'], selectbackground=THEME['accent'], relief='flat', font=('Segoe UI', 10))
        self.listbox.pack(fill='both', expand=True, padx=8, pady=8)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)

        self.output = tk.Text(right, wrap='word', bg=THEME["surface"], fg=THEME['text'], insertbackground=THEME["text"], relief='flat', font=('Consolas', 11))
        self.output.pack(fill='both', expand=True, padx=8, pady=8)
        self.populate_list(self.current_terms())
        self.show_welcome()

    def build_hint_text(self):
        if getattr(self.app, 'language', 'en') == 'tr':
            return 'Önce sözlük türünü ve kategori filtresini seç; sonra İngilizce ya da Türkçe terimi ara. Açıklamalar programın içine gömülüdür, offline çalışır ve AI kullanmaz.'
        return 'Choose the dictionary type and category filter, then search in English or Turkish. Explanations are embedded in the program, work offline, and do not call AI.'

    def refresh_ui(self):
        self.title_label.config(text=self._t('dictionary_full'))
        self.lookup_button.config(text=self._t('lookup'))
        self.hint_label.config(text=self.build_hint_text())
        self.category_combo['values'] = self.category_options()
        if self.category_var.get() not in self.category_options():
            self.category_var.set('All / Tümü')
        self.show_welcome()

    def term_label(self, item):
        return f"{item['en']}  →  {item['tr']}"

    def filtered_source_terms(self):
        items = self.current_terms()
        cat = self.category_var.get()
        if cat and cat != 'All / Tümü':
            items = [item for item in items if item['category'] == cat]
        return items

    def populate_list(self, items):
        self.filtered_terms = list(items)
        self.listbox.delete(0, 'end')
        for item in self.filtered_terms:
            self.listbox.insert('end', self.term_label(item))

    def on_type_change(self):
        self.query_var.set('')
        self.category_var.set('All / Tümü')
        self.category_combo['values'] = self.category_options()
        self.populate_list(self.current_terms())
        self.show_welcome()

    def filter_terms(self):
        q = (self.query_var.get() or '').strip().lower()
        items = self.filtered_source_terms()
        if not q:
            self.populate_list(items)
            return
        results = []
        for item in items:
            haystack = ' '.join([item['en'], item['tr'], item['category'], item['tr_explanation'], item['en_explanation'], item['example']]).lower()
            if q in haystack:
                results.append(item)
        self.populate_list(results)

    def find_term(self, query):
        q = (query or '').strip().lower()
        if not q:
            return None
        exact = []
        partial = []
        for item in self.filtered_source_terms():
            en = item['en'].lower(); tr = item['tr'].lower()
            if q == en or q == tr:
                exact.append(item)
            elif q in en or q in tr or q in item['tr_explanation'].lower() or q in item['en_explanation'].lower() or q in item['category'].lower():
                partial.append(item)
        return exact[0] if exact else (partial[0] if partial else None)

    def show_welcome(self):
        self.output.delete('1.0', 'end')
        type_key = self.dict_type_var.get()
        label = self.type_label(type_key)
        count = len(self.current_terms())
        visible_count = len(self.filtered_source_terms())
        if getattr(self.app, 'language', 'en') == 'tr':
            self.output.insert('end', f"Seçili sözlük: {label}\n")
            self.output.insert('end', f"Kategori filtresi: {self.category_var.get()}\n\n")
            self.output.insert('end', 'Listeden bir terim seç veya arama kutusuna yaz.\n\n')
            self.output.insert('end', f'Toplam hazır terim sayısı: {count}\n')
            self.output.insert('end', f'Filtre sonrası görünür terim sayısı: {visible_count}\n')
            self.output.insert('end', 'Tüm açıklamalar programın içine yerleştirilmiştir; bu bölüm offline çalışır ve AI kullanmaz.\n')
        else:
            self.output.insert('end', f"Selected dictionary: {label}\n")
            self.output.insert('end', f"Category filter: {self.category_var.get()}\n\n")
            self.output.insert('end', 'Choose a term from the list or type in the search box.\n\n')
            self.output.insert('end', f'Total built-in terms: {count}\n')
            self.output.insert('end', f'Visible terms after filter: {visible_count}\n')
            self.output.insert('end', 'All explanations are embedded in the program; this section works offline and does not call AI.\n')

    def lookup(self):
        q = (self.query_var.get() or '').strip()
        if not q:
            self.show_welcome()
            return
        found = self.find_term(q)
        self.output.delete('1.0', 'end')
        if found:
            label = self.type_label(self.dict_type_var.get())
            if getattr(self.app, 'language', 'en') == 'tr':
                self.output.insert('end', f"Sözlük Türü: {label}\n")
                self.output.insert('end', f"Kategori: {found['category']}\n")
                self.output.insert('end', f"Terim: {found['en']}\n")
                self.output.insert('end', f"Türkçe Karşılığı: {found['tr']}\n\n")
                self.output.insert('end', f"Açıklama:\n{found['tr_explanation']}\n\n")
                self.output.insert('end', f"İngilizce Açıklama:\n{found['en_explanation']}\n\n")
                self.output.insert('end', f"Örnek:\n{found['example']}\n")
            else:
                self.output.insert('end', f"Dictionary Type: {label}\n")
                self.output.insert('end', f"Category: {found['category']}\n")
                self.output.insert('end', f"Term: {found['en']}\n")
                self.output.insert('end', f"Turkish: {found['tr']}\n\n")
                self.output.insert('end', f"Explanation:\n{found['en_explanation']}\n\n")
                self.output.insert('end', f"Turkish Explanation:\n{found['tr_explanation']}\n\n")
                self.output.insert('end', f"Example:\n{found['example']}\n")
        else:
            if getattr(self.app, 'language', 'en') == 'tr':
                self.output.insert('end', 'Bu terim seçili yerleşik sözlükte bulunamadı.\n')
                self.output.insert('end', 'Daha kısa bir arama deneyebilir, kategori filtresini kaldırabilir veya sözlük türünü değiştirebilirsin.\n')
            else:
                self.output.insert('end', 'This term was not found in the selected built-in dictionary.\n')
                self.output.insert('end', 'Try a shorter query, clear the category filter, or switch to a different dictionary type.\n')

    def on_select(self, event=None):
        sel = self.listbox.curselection()
        if sel:
            item = self.filtered_terms[sel[0]]
            self.query_var.set(item['en'])
            self.lookup()


