---
slug: ram-neden-bu-kadar-pahali
title: "Yapay Zekâ Veri Merkezleri Çip Alırken RAM Neden Bu Kadar Pahalı?"
summary: "Bellek üreticileri hiç olmadığı kadar kazanıyor. Yapay zekâ için üretilen tek bir çip türü dizüstü bilgisayarların ve telefonların belleğini sıkıştırıyor, belleği satan şirketler de bu kıtlığın yıllarca süreceğini bekliyor."
category: economy
date: 2026-11-05
kind: long
sources:
  - name: "Micron: 2026 mali yılı dördüncü çeyrek sonuçları (SEC Form 8-K, ek 99.1)"
    url: https://www.sec.gov/Archives/edgar/data/0000723125/000072312526000018/a2026q4ex991-pressrelease.htm
  - name: "Micron: Crucial tüketici işinden çıkıyoruz"
    url: https://investors.micron.com/news-releases/news-release-details/micron-announces-exit-crucial-consumer-business
  - name: "SK hynix: 2026 üçüncü çeyrek sonuçları"
    url: https://www.placera.se/pressmeddelanden/sk-hynix-announces-3q26-financial-results-20261028
  - name: "TrendForce: SK hynix 3Ç26 sonuçları (haber)"
    url: https://www.trendforce.com/news/?p=65818
  - name: "TrendForce: Samsung 3Ç26 sonuçları (haber)"
    url: https://www.trendforce.com/news/?p=65900
  - name: "TrendForce: Yapay zekâ sunucu talebi 4Ç26'da bellek sözleşme fiyatlarını yükseltmeyi sürdürüyor, tüketici tarafındaki baskı da sürüyor"
    url: https://www.trendforce.com/presscenter/news/20260930-13258.html
  - name: "TrendForce: DRAM fiyatlarının 4Ç26'da çeyreklik yüzde 20 artması bekleniyor"
    url: https://www.trendforce.com/news/2026/10/20/news-dram-prices-seen-rising-20-qoq-in-4q26-despite-slower-gains-ai-demand-tight-supply-support-outlook/
  - name: "TrendForce: Dar DRAM arzı tedarikçilere HBM'de daha fazla fiyat gücü veriyor"
    url: https://www.trendforce.com/presscenter/news/20260602-13074.html
  - name: "TrendForce: Bellek fiyatları fırladı, DRAM ve NAND 2027'de büyük bulut şirketleri yatırımlarının yüzde 68'ini oluşturacak"
    url: https://www.trendforce.com/presscenter/news/20260825-13198.html
  - name: "TrendForce: DRAM Piyasa Bülteni, 23 Eylül 2026"
    url: https://trendforce.com/research/download/RP260923EN
  - name: "Wikimedia Commons: Çift işlemci soketli sunucuda AMD Epyc 9754 (dosya açıklaması)"
    url: https://commons.wikimedia.org/wiki/File:AMD_Epyc_9754_in_Dual-CPU-Socket-Serversystem_(%E6%9E%81%E5%AE%A2%E6%B9%BEGeekerwan)_07.png
  - name: "Wikipedia (İngilizce): Dynamic random-access memory"
    url: https://en.wikipedia.org/wiki/Dynamic_random-access_memory
  - name: "Wikipedia (İngilizce): High Bandwidth Memory"
    url: https://en.wikipedia.org/wiki/High_Bandwidth_Memory
image:
  file: image.jpg
  alt: "Siyah bir ana kartın üzerinde iki büyük AMD Epyc işlemcisi olan bir sunucunun içi. Her işlemcinin çevresinde yuvalara takılı sıra sıra yeşil bellek modülleri var, sol altta sarı-siyah soğutma fanları görünüyor."
  credit: "极客湾Geekerwan"
  license: "CC BY 3.0"
  licenseUrl: https://creativecommons.org/licenses/by/3.0/
  source: https://commons.wikimedia.org/wiki/File:AMD_Epyc_9754_in_Dual-CPU-Socket-Serversystem_(%E6%9E%81%E5%AE%A2%E6%B9%BEGeekerwan)_07.png
---
Bir yıl önce merkezi Boise, Idaho'da bulunan bellek üreticisi Micron, bir çeyrekte yaklaşık 11,3 milyar dolarlık çip sattı. Son çeyrekte sattığı tutar 54,2 milyar dolar oldu. Brüt kâr marjı, yani satış gelirinden çipleri üretme maliyeti düştükten sonra kalan pay, aynı sürede yüzde 44,7'den yüzde 86,8'e çıktı. Bir çip üreticisi için bu olağanüstü bir değişim.

Aynı patlama dizüstü bilgisayarların, telefonların ve bellek kartlarının fiyat etiketlerinde de görülüyor. "RAM neden bu kadar pahalı?" sorusunun kısa yanıtı şu: Belleği üretenler, sizden daha iyi bir müşteri buldu. Uzun yanıt, bu müşteriyle rekabet etmenin neden bu kadar zor olduğunu ve belleği satan hiç kimsenin yakın zamanda bir rahatlama vaat etmediğini anlatıyor.

## RAM nedir ve onu yiyen çip hangisi

RAM, bir cihazın o anda yaptığı iş için kullandığı bellektir: açık uygulamalar, tarayıcı sekmeleri, oyunun o anki bölümü. Büyük kısmı, "dinamik rastgele erişimli bellek" anlamına gelen DRAM adlı türdendir. Veriyi küçücük elektrik yükleri olarak tutar. Bu yükler zamanla sönümlendiği için çipin onları sürekli yenilemesi gerekir. Güç kesilince de her şeyi unutur. Dosyaların ayrı bir diskte durmasının, RAM'in ise yalnızca çalışma masası olmasının nedeni bu.

Dizüstü ve masaüstü bilgisayarlar da telefonlar da DRAM kullanır. Veri merkezlerindeki bilgisayarlar, yani sunucular da öyle.

Yapay zekâ ise HBM adlı özel bir türe talep yarattı. HBM, "yüksek bant genişlikli bellek" demek. Tek ve düz bir çip yerine, taban çipin üzerine genellikle 4 ila 16 DRAM çipini üst üste dizer ve dikey bağlantılarla birbirine bağlar. Bu yığın işlemcinin hemen yanında durur. Çok geniş veri yolu sayesinde işlemci, sıradan belleğin izin verdiğinden çok daha hızlı veri çekebilir. Yapay zekâ işlemcileri bu hızın başlıca müşterisi.

İki ürün de aynı tür fabrikalarda, aynı tür silikon plakalardan, yani çiplerin üzerine basıldığı ince disklerden üretilir. Hikâyenin özü, bu ortak üretim kapasitesi.

## Bir yapay zekâ çipi ne kadar bellek ister

Bir yapay zekâ hızlandırıcısı çok miktarda HBM taşır. Bellek piyasasını izleyen TrendForce'a göre bu yıl özel yapay zekâ çiplerindeki yükseltmeler, çip başına HBM miktarını 96 veya 192 gigabayttan 216 veya 288'e çıkarıyor. Şirket, gelecek yıl Nvidia'nın Rubin Ultra işlemcisinin işlemci başına 384 gigabayta ulaşmasını bekliyor. Karşılaştırma için: Bu sayfanın başındaki fotoğraftaki sunucunun tamamı yaklaşık 825 gigabayt sıradan bellek taşıyor.

Sıradan sunucu belleğine de talep var. TrendForce, sunucu işlemcilerinin daha bol bulunmasının bulut şirketlerinin, kendi deyimiyle "ajan tabanlı yapay zekâ" için, yani görevleri kendi başına yürüten yapay zekâ sistemleri için aldığı bellek miktarını artırdığını bildiriyor. Harcamalar da çok büyük. TrendForce'un tahminine göre büyük bulut şirketlerinin yatırım harcamalarının bu yıl yüzde 47'si, gelecek yıl yüzde 68'i DRAM ve NAND flaşa gidecek. NAND, katı hal disklerinin arkasındaki çip türü.

## Sıkışma sıradan belleğe nasıl ulaşıyor

Daha fazla HBM üreten bir fabrikada geri kalan her şeye daha az yer kalır. TrendForce'un tahminine göre en büyük üç tedarikçinin DRAM plakalarının bu yıl sonunda yaklaşık yüzde 22'si HBM'ye gidiyor, 2027 sonunda bu oran yaklaşık yüzde 30'a çıkacak. Oysa HBM, bit olarak ölçülen bu yılki bellek üretiminin yalnızca yaklaşık yüzde 9'u, 2027'de ise yaklaşık yüzde 13'ü. Yani HBM'ye ayrılan plaka, sıradan çiplere ayrılan plakadan çok daha az bellek veriyor. TrendForce, sonraki HBM kuşaklarında çiplerin büyümesine dikkat çekiyor ve geleneksel DRAM'in kapasiteden dışlanmasının yoğunlaşmasını bekliyor.

Mesele, üretim gücünün nereye yöneldiği de. TrendForce'a göre tedarikçiler en gelişmiş üretim hatlarını sunucu ürünlerine yöneltiyor ve bu, piyasayı arz yetersizliğinde tutuyor. Kapasite sunuculara kaydığı için telefonlara ayrılan bellek arzı dar.

Bu tercih şirket kararlarında görülüyor. Micron 2025 aralık ayında, tüketici markası mağazalarda, çevrimiçi satıcılarda ve distribütörlerde satılan Crucial işinden çıkacağını duyurdu. Baş iş sorumlusu Sumit Sadana, amacın "daha büyük, stratejik müşterilerimiz için arzı ve desteği iyileştirmek" olduğunu söyledi. Açıklama, yapay zekâ veri merkezlerinden gelen bellek ve depolama talebindeki sıçramaya işaret ediyordu.

Bu tercih yalnızca büyük isimlerle sınırlı değil. Tayvanlı çip üreticisi Macronix, [Nintendo Switch oyunlarını](/tr/stories/macronix-rom-switch-kartuslari/) tutan ROM çiplerini kademeli olarak bıraktığını ve kapasiteyi daha hızlı büyüyen bir bellek türü olan NAND'e verdiğini açıkladı. Bu çipler DRAM değil, ama örnek benzer: sınırlı sayıda fabrika hattı ve yapay zekâ ile ilgili bellek için daha fazla ödeyen müşteriler.

## Yüksek fiyatlar neye benziyor

TrendForce, büyük alıcıların, örneğin bilgisayar üreticilerinin tedarikçilerle üzerinde anlaştığı sözleşme fiyatlarını izliyor. Bu maliyetler, insanların satın aldığı cihazlara yansıyor. Kore ve Tayvan basınına dayanan 20 Ekim tarihli bir TrendForce haberine göre DRAM sözleşme fiyatları bu yılın ikinci çeyreğinde yaklaşık yüzde 80, üçüncü çeyreğinde yaklaşık yüzde 40 arttı. TrendForce dördüncü çeyrek için daha küçük bir artış bekliyor, ancak rakamlar ölçüye göre değişiyor. 30 Eylül tarihli bir açıklama, günlük cihazlarda kullanılan geleneksel DRAM için yüzde 10 ila 15 artış öngördü. 20 Ekim tarihli haber ise dördüncü çeyrekteki genel artışı yaklaşık yüzde 20 olarak verdi.

Üreticilerin kendi sonuçları da aynı hikâyeyi anlatıyor. Samsung'un bellek biriminden yönetici Kim Jae-june, TrendForce'un aktardığı News 1 haberine göre DRAM fiyatlarının yaklaşık yüzde 20 arttığını, sevkiyatların ise yalnızca yüzde bir ile orta tek haneli bir oranda yükseldiğini söyledi. Fiyatlar satılan miktardan çok daha hızlı yükseliyor.

Alıcılar bunu hissediyor. TrendForce'a göre yüksek bileşen maliyetleri dizüstü bilgisayar satışlarını zorluyor, artan maliyetler ve tükenen düşük maliyetli bellek stokları akıllı telefon üretimini kısıyor, bilgisayar markaları da maliyeti düşürmek için makinelerindeki depolamayı küçültüyor. Televizyonların, set üstü cihazların ve giyilebilir cihazların da yüksek maliyetleri sindirecek payı az.

## Geleceği kim şimdiden satın aldı

Fiyatların yüksek kalabilmesinin ikinci nedeni, arzın büyük bölümünün çoktan ayrılmış olması. SK hynix, aralarında büyük bulut şirketlerinin de bulunduğu 14 büyük müşteriyle uzun vadeli tedarik anlaşması imzaladığını söylüyor. TrendForce'a göre bu sayı ikinci çeyrekte 10'du. Anlaşmalar genellikle beş yıl sürüyor. Şirkete göre bugüne kadar güvence altına alınan hacim, 2027 ve 2028 için toplam üretim kapasitesinin yarısından fazlasına denk geliyor ve fiyatlar kararlaştırılan aralıklar içinde belirleniyor.

TrendForce, bu anlaşmaların açık piyasada pazarlığa kalan arzı daralttığını söylüyor. Aynı zamanda madalyonun öbür yüzüne de dikkat çekiyor: İkinci çeyrekten bu yana imzalanan bazı anlaşmalarda fiyat tavanı var ve sözleşme mekanizmaları yüzünden bazı tedarikçilerin zamlarının piyasa ortalamasının gerisinde kalması bekleniyor.

## Ne zaman rahatlayabilir?

Bunu kimse bilmiyor ve tahminlerin çoğunu belleği satan şirketler veriyor. İşte onların ve TrendForce'un söyledikleri.

SK hynix sonuç açıklamasında, talebin arzı aştığı yapının 2030'a kadar süreceğini beklediğini söyledi. Şirket, en yeni çip süreçlerinin teknik zorluğuna ve yeni fabrikaların uzun kurulum sürelerine işaret ediyor. TrendForce'un aktardığına göre Koreli Chosun Biz, şirketin DRAM ve HBM üretiminin fiilen 2029'a kadar satıldığını bildirdi. TrendForce'un aktardığı Reuters haberine göre Samsung 2027'de çip arzının daha da sıkışmasını bekliyor. Her iki şirket de satıcı olarak konuşuyor.

Yeni arz geliyor, ama yavaş. SK hynix, M15X adlı tesisin yıl sonuna kadar tam kapasiteye ulaşacağını, Yongin sahasının ilk aşamasının da gelecek yıl tam işletmeye gireceğini söylüyor. TrendForce, sunucu DRAM'i ile HBM'nin birleşik bit arzının 2027'de yüzde 27 artmasını bekliyor, bu artışta o yılın ikinci yarısında devreye girecek yeni fabrika kapasitesi de rol oynuyor. Ancak kapasite sunuculara kaydığı için 2027'de PC belleği arzının düşebileceği uyarısını da yapıyor. Kuruluşa göre bilgisayar üreticileri, sıkıntı bekledikleri için hâlâ agresif biçimde alım yapıyor.

Fiyat artışlarının hızı şimdiden yavaşlıyor. TrendForce'un gerekçeleri, yüksek bir başlangıç noktası, tüketicilerin daha zayıf satın alma gücü ve uzun vadeli sözleşmelerdeki tavanlar. Telefon belleğinde de büyük artışlar zaten fiyatlara yansıdığı için artış yavaşlıyor. Yine de yavaşlayan artış, düşüş demek değil. Burada aktarılan tahminlerin hiçbiri fiyatların gerileyeceğini söylemiyor.

## Tabloyu ne değiştirebilir

Birkaç şey dengeyi kaydırabilir, ama hiçbiri kesin değil.

Tedarikçiler üretimi HBM ile sıradan DRAM arasında kaydırabilir. TrendForce, bu yılın ilk çeyreğinde HBM'nin plaka başına, yaygın bir sunucu bellek modülünden daha az kazandırdığını belirtiyor, çünkü HBM fiyatları yıllık belirleniyor ve sıradan fiyatlardaki hızlı artışları yakalayamamıştı. TrendForce'un aktardığı bir Kore basını haberine göre SK hynix'in HBM ile geleneksel DRAM arasındaki kâr farkının belirgin biçimde daralmasını beklediğini bildiriyor. Sıradan bellek üretmek HBM kadar kazandırırsa, üreticilerin birini öbürüne tercih etmek için daha az nedeni olur.

Talep yumuşayabilir. TrendForce'a göre yüksek bellek maliyetleri bulut şirketlerini sistem başına bellek miktarını azaltmaya ya da başka tasarımlara yönlendirebilir. Ekim raporu ayrıca, yeni bir bellek tasarımı üzerinde çalışan Çinli üretici CXMT'yi anıyor. Rapor, Kore basınına dayanarak bunun spot fiyatlara, yani anında teslimat için ödenen fiyatlara henüz belirgin bir etkisi olmadığını, tam ticari üretimin ise genel olarak 2028'den sonra beklendiğini belirtiyor.

Tahminler de yanılabilir. TrendForce dördüncü çeyrek beklentisini daha önce yukarı yönde revize etti. Micron'un bir sonraki çeyrek için yaklaşık 61,5 milyar dolarlık gelir öngörüsü de şirketin kendi beklentisi, kesinlik değil.

## Sırada bekleyen bellek

Bir telefonun ya da dizüstü bilgisayarın belleği, fiilen bir yapay zekâ sunucusundaki belleğin arkasındaki sırada bekliyor, çünkü her ikisini de aynı fabrikalar besliyor ve yapay zekâ tarafı daha fazla ödüyor. Üreticiler bunun yıllarca süreceğini söylüyor. Analistler fiyat artışlarının yavaşladığını, ama piyasanın arz açısından sıkışık kalacağını görüyor.
