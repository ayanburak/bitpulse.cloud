---
slug: kuantum-bilgisayarlar-sifrelemeyi-kiracak-mi
title: "Kuantum Bilgisayarlar Şifrelemeyi Kıracak mı?"
summary: "Tarihi kimse bilmiyor, ama hikâye bununla bitmiyor. Tehlike sanıldığından dar, bugün gönderilen sırlar kaydedilip ileride açılabilir ve çözüm tarayıcınızda çoktan çalışıyor."
category: technology
date: 2026-11-04
time: "12:00"
kind: long
sources:
  - name: "Cloudflare: 2025'te kuantum sonrası internetin durumu"
    url: https://blog.cloudflare.com/pq-2025/
  - name: "NIST: İlk 3 kuantum sonrası şifreleme standardı yayımlandı"
    url: https://www.nist.gov/news-events/news/2024/08/nist-releases-first-3-finalized-post-quantum-encryption-standards
  - name: "NIST: Kuantum sonrası kriptografi, sıkça sorulan sorular"
    url: https://csrc.nist.gov/projects/post-quantum-cryptography/faqs
  - name: "NIST: Kuantum sonrası kriptografi standartlarına geçiş (IR 8547, nihai sürüm, Ekim 2026)"
    url: https://csrc.nist.gov/pubs/ir/8547/final
  - name: "NIST: IR 8547, tam rapor (PDF)"
    url: https://nvlpubs.nist.gov/nistpubs/ir/2026/NIST.IR.8547.pdf
  - name: "Gidney (Google Quantum AI): How to factor 2048 bit RSA integers with less than a million noisy qubits (arXiv)"
    url: https://arxiv.org/abs/2505.15917
  - name: "Google Research: Kuantum açıklarını sorumlu biçimde duyurarak kripto paraları korumak"
    url: https://research.google/blog/safeguarding-cryptocurrency-by-disclosing-quantum-vulnerabilities-responsibly/
  - name: "Google: Kuantum sonrası kriptografiye geçiş takvimimiz"
    url: https://blog.google/innovation-and-ai/technology/safety-security/cryptography-migration-timeline/
  - name: "Google: Willow, son teknoloji kuantum çipimiz"
    url: https://blog.google/technology/research/google-willow-quantum-chip/
  - name: "Cain ve ark.: Shor's algorithm is possible with as few as 10,000 reconfigurable atomic qubits (arXiv ön baskısı)"
    url: https://arxiv.org/abs/2603.28627
  - name: "Birleşik Krallık Ulusal Siber Güvenlik Merkezi (NCSC): Kuantum sonrası kriptografiye geçiş takvimi"
    url: https://www.ncsc.gov.uk/guidance/pqc-migration-timelines
  - name: "Signal: Signal Protokolü ve kuantum sonrası mandallar (SPQR)"
    url: https://signal.org/blog/spqr/
  - name: "Apple Güvenlik Araştırması: PQ3 ile iMessage"
    url: https://security.apple.com/blog/imessage-pq3/
image:
  file: image.jpg
  alt: "Beyaz temiz oda tulumları, maskeler ve eldivenler giymiş üç kişi, bir laboratuvarda altın renkli metal plakalardan ve rengârenk kablolardan oluşan bir yapıya, süper iletken bir kuantum bilgisayarın soğutma bölümüne yakından bakıyor."
  credit: "FMNLab"
  license: "CC BY 4.0"
  licenseUrl: https://creativecommons.org/licenses/by/4.0/
  source: https://commons.wikimedia.org/wiki/File:Measuring_a_qubit_leaves_no_room_for_error.jpg
---
Tarayıcınızın adres çubuğundaki asma kilit iki iş yapıyor ve gelecekteki bir kuantum bilgisayar bunlardan birini ötekinden çok daha fazla tehdit ediyor. Hangisi olduğunu görmek için bir sayfa açılmadan önceki saniyeye bakmak gerekir.

Telefonunuz ile bir bankanın sunucusu birbirini hiç tanımıyor. Ortak bir gizli anahtarda anlaşmaları gerekiyor ve bunu, herkesin dinleyebileceği bir ağ üzerinden yapmaları lazım. Bunun aracı, açık anahtarlı şifreleme denen yöntem. Taraflar yapması kolay, geri almak ise pratikte imkânsız bir matematik işlemi yapıyor. Sonunda ikisinin elinde aynı gizli anahtar oluyor; bütün mesajları görmüş bir dinleyici ise bu anahtarı çıkaramıyor. İnternet altyapısı şirketi Cloudflare bu adıma anahtar anlaşması diyor.

İkinci iş kanıt göstermek. Sunucunun, kendisinin gerçekten sizin bankanız olduğunu, sahte biri olmadığını göstermesi gerekiyor. Bunu dijital imzayla yapıyor ve imza da açık anahtarlı matematiğe dayanıyor.

Anahtar belirlendikten sonrası kolay. Mesajlarınız, parolalarınız ve kart numaralarınız bu anahtarla, simetrik şifreleme denen başka bir yöntem ailesiyle karıştırılıyor. Burada tek bir anahtar hem kilitliyor hem açıyor. Yaygın bir örneği AES.

Yani asma kilit iki tür matematiğe dayanıyor. Soru, kuantum bilgisayarın hangisini kırabileceği.

## Kuantum bilgisayar neyi iyi yapar?

Kuantum bilgisayar daha hızlı bir dizüstü bilgisayar değil. Çok küçük şeylerin fiziğini kullanarak bazı sorunları bambaşka bir yoldan çözüyor ve yalnızca birkaç özel sorunda çarpıcı bir hız kazanıyor.

O sorunlardan ikisi, açık anahtarlı şifrelemeyi ayakta tutan sorunların ta kendisi. RSA, çok büyük iki asal sayıyı çarpmanın kolay, çıkan sonucu yeniden o asal sayılara bölmenin ise zor olmasına dayanıyor. Yaygın kullanılan bir başka yöntem olan eliptik eğri şifrelemesi de buna yakın bir zor soruya dayanıyor. Shor algoritması denen bir yöntem, yeterince büyük bir kuantum bilgisayarın ikisine de saldırmasına izin veriyor. Birleşik Krallık Ulusal Siber Güvenlik Merkezi durumu açıkça söylüyor: Kuantum bilgisayarlar, bugünkü açık anahtarlı sistemlerin dayandığı zor matematik problemlerini verimli biçimde çözebilecek.

Tehdit özetle bu. Hem anahtar anlaşması hem imzalar çöker, onlarla birlikte internette birbirini tanımayanların sır kurma ve güvenme yolu da.

## AES neden yerinde kalıyor?

Kilidin öbür yarısı çok daha sağlam. Grover algoritması denen ikinci bir kuantum yöntemi, bir anahtarı deneme yanılmayla bulmayı hızlandırıyor ama yalnızca karekök kadar: bir trilyon adım gerektiren arama yaklaşık bir milyon adıma iniyor. Bu, saldırgana Shor algoritmasının RSA karşısında sağladığından çok daha az yarar sağlıyor.

ABD'nin standart kurumu NIST konuyu yakından inceledi. SSS sayfasına göre Grover algoritması AES'e saldırıda büyük olasılıkla "çok az avantaj veya hiç avantaj" sağlayacak, AES-128 "onlarca yıl güvende kalacak" ve daha uzun AES-192 ile AES-256 "çok uzun süre güvenli olacak". Bu sonuçlar, AES'in kendisinde yeni bir zayıflık bulunmayacağını varsayıyor. Cloudflare pratik sonucu kısaca şöyle söylüyor: AES-GCM gibi simetrik şifreler zaten kuantum sonrası dönem için güvenli.

Dolayısıyla "kuantum bilgisayarlar bütün şifrelemeyi kıracak" cümlesi "bütün" kelimesinde yanlış. Kırılacak olan, yabancıların anahtar üzerinde anlaşmasını ve kim olduklarını kanıtlamasını sağlayan kısım. Verileri sonradan karıştıran kısım ayakta kalacak.

## 105 ile yarım milyon arasındaki mesafe

Böyle bir makine var mı? Yok, hem de uzağız. Google'ın Willow çipinde, kuantum bilgisayarın temel birimi olan 105 kübit var. Başlıca başarısı güvenilirlikle ilgili. Kübitler kırılgan ve hata yapıyor. Willow'da kübitler daha büyük hata düzeltme gruplarına bağlandıkça hatalar artmadı, azaldı. Google buna "eşiğin altına inmek" diyor ve bunu alanın aşılması zor bir sorunu olarak tanımlıyor. Henüz pratikte ticari bir kullanımı olmayan bir deneyde Willow, Google'ın söylediğine göre en güçlü süper bilgisayarın çok uzun sürede yapabileceği bir hesabı beş dakikadan kısa sürede bitirdi. Bu alan için bir dönüm noktası ama şifre kırıcı değil.

RSA'yı kırmak çok daha fazlasını gerektirir ve bu ihtiyacın tahmini düşüyor. Google Quantum AI araştırmacılarından Craig Gidney ve bir meslektaşı 2019'da, 2048 bitlik bir RSA anahtarını kırmak için 20 milyon gürültülü kübit gerekeceğini hesaplamıştı. Gidney Mayıs 2025'te yeni bir tahmin yayımladı: bir milyondan az kübit ve bir haftadan kısa süre. Google araştırmacıları Mart 2026'da, kripto paraları ve başka sistemleri koruyan 256 bitlik eliptik eğri probleminin 500 binden az fiziksel kübitle birkaç dakikada çözülebileceğini bildirdi. Bu, önceki tahminden yaklaşık 20 kat az kübit demek. Bunlar, belirtilen donanım varsayımlarına dayanan kâğıt üzerindeki tahminler.

Başka ekipler başka donanımları inceliyor. Aralarında fizikçi John Preskill'in de olduğu bir grup, Mart 2026'da, resmî incelemeden önce paylaşılan bir ön baskı yayımladı. Buna göre atom tabanlı kübitlerden yapılmış bir makine Shor algoritmasını en az 10 bin kübitle çalıştırabilir ve yaklaşık 26 bin kübit 256 bitlik bir eliptik eğriye birkaç günde saldırabilir. Yazarlar rakamların makul varsayımlara dayandığını ve önemli mühendislik zorluklarının sürdüğünü söylüyor.

Hepsini yan yana koyunca tablo şu: Google'ın Willow çipinde 105 kübit var. Açık anahtarlı şifrelemeyi kırmak için verilen tahminler yaklaşık 10 binden bir milyonun altına uzanıyor ve hepsi henüz var olmayan makineler için. Aradaki fark büyük, ama tahminler birkaç yılda hızla düştü.

## Bugün kaydet, yarın oku

Henüz var olmayan bir makine neden şimdiden önemli? Çünkü şifreli trafiğinizi bugün okuyamayan biri onu yine de kopyalayıp saklayabilir. On ya da yirmi yıl sonra yetenekli bir kuantum bilgisayar çıkarsa, eski dosyaları o zaman açabilir. Buna "harvest now, decrypt later", yani şimdi topla, sonra çöz deniyor. Apple, Signal ve NIST bu adı kullanıyor.

Risk en çok uzun süre hassas kalan bilgilerde: devlet sırları, sağlık kayıtları, iş planları, özel yazışmalar. Önümüzdeki ay geçerliliğini yitirecek bir parolayı yirmi yıl saklamaya değmez. Bir diplomatik yazışma için durum başka olabilir.

Bunun asma kilidin hangi kısmını ilgilendirdiğine dikkat edin: anahtar anlaşmasını. Çünkü kaydedilmiş bir bağlantı ancak o sırada kararlaştırılan anahtar çözülebilirse sonradan açılır. Cloudflare bu yüzden anahtar anlaşmasını şimdiden yenilemenin acil olduğunu söylüyor. İmzalar farklı. Sahte bir imza saldırgana ancak saldırı anında yarar sağlar, yani yeterli bir kuantum bilgisayar gerçekten var olduktan sonra anlam kazanır. Cloudflare ayrıca kuantum sonrası imzalara geçişin çok daha zor olduğunu ekliyor.

## Şimdiden devrede olanlar

Yerine geçecek yöntemler hazır. NIST, Ağustos 2024'te ilk üç kuantum sonrası standardını yayımladı. Biri, ML-KEM adıyla, anahtar anlaşmasını kapsıyor. İkisi imzalar için: ana standart ML-DSA ile, ilkinde bir zayıflık çıkarsa devreye girecek, farklı bir matematiğe dayanan SLH-DSA. NIST bunların kullanıma hazır olduğunu söyledi ve kurumları entegrasyona hemen başlamaya çağırdı.

Geçişin büyük bölümü kimse fark etmeden yapıldı. Chrome, kuantum sonrası bir anahtar anlaşmasını klasik olanla birlikte çalıştıran, saldırganın ikisini birden aşmasını gerektiren hibrit bir yöntemi masaüstünde Mart 2024'ten itibaren varsayılan olarak açtı. Firefox Kasım 2024'te izledi, Apple'ın telefon ve bilgisayarları da 2025 yazılım sürümleriyle kullanmaya başladı. Cloudflare, Ekim 2025 sonunda yönettiği insan kaynaklı trafiğin çoğunun bu şekilde korunduğunu bildirdi.

Mesajlaşma uygulamaları da harekete geçti. Apple, Şubat 2024'te iMessage için PQ3 adlı kuantum sonrası bir tasarım duyurdu ve bunun kuantum bilgisayarlardan gelen bugünkü ve gelecekteki tehditleri karşıladığını söylüyor. Signal, Ekim 2025'te protokolüne kuantum sonrası bir yükseltme getirdi. Signal amacın, kriptografik açıdan geçerli kuantum bilgisayarlar eninde sonunda gerçek olursa konuşmaları korumak olduğunu belirtiyor.

Bu uygulamaların birçoğu hibrit. Örneğin Signal yeni yükseltmesini mevcut protokolün yanında çalıştırıyor ve anahtarları karıştırıyor. Bir parçadaki hata, her şeyi kendiliğinden ortaya dökmüyor.

## Hükümetlerin koyduğu tarihler

Hükümetler çoğunlukla 2030'lu yılları hedef aldı. Birleşik Krallık'ın siber güvenlik kurumu, kuruluşlardan 2028'e kadar geçiş hedeflerini ve planı belirlemelerini, 2031'e kadar en öncelikli işleri bitirmelerini, 2035'e kadar da geçişi tamamlamalarını istiyor. ABD'de NIST'in Ekim 2026'da yayımlanan nihai geçiş raporu, kuantum saldırısına açık, açık anahtarlı kriptografiyi 2030'dan sonra kullanımdan kaldıracağını ve 2035'ten sonra yasaklayacağını söylüyor. Rapor ayrıca federal kurumların uyması gereken bir hedefi de yineliyor: En hassas sistemler 2030 sonuna kadar kuantum sonrası anahtar anlaşmasına, 2031 sonuna kadar da imzalara geçmek zorunda. Rapora göre benzer geçişler daha önce 10 ila 20 yıl sürdü; bu yüzden takvimde pay çok az.

Şirketler de kendi tarihlerini koyuyor. Google, Mart 2026'da kendi geçişi için 2029 hedefi koyduğunu duyurdu. Takvimin kuantum donanımındaki, hata düzeltmedeki ve çarpanlara ayırma kaynak tahminlerindeki ilerlemeyi yansıttığını, verilerin bugün saklanıp ileride çözülebilmesi nedeniyle şifreleme tehdidinin bugün bile geçerli olduğunu söylüyor. İmzaları ise yeterli bir makine ortaya çıkmadan önce çözülmesi gereken gelecekteki bir tehdit olarak görüyor.

## Kimsenin cevaplayamadığı soru

Peki RSA'yı kırabilecek ilk makine ne zaman gelecek? Kimse bilmiyor. NIST'in 2024 duyurusu yalnızca bazı uzmanların böyle bir cihazın on yıl içinde çıkabileceğini öngördüğünü söylüyor, kendisi tarih vermiyor. Cloudflare daha açık konuşuyor: Dürüst cevap, kimsenin kesin bilmediği, çünkü bilinmeyenlerin çok fazla olduğu. Ona göre bu makine 2034'te de gelse 2050'de de gelse, her hâlükârda çok erken gelmiş olacak. Bu yazıdaki her sayı, kimsenin yapmadığı bir makinenin tahmini; her gelecek tarih de bir öngörü değil, bir planlama tercihi.

Daha güvenle söylenebilecek şey küçük ama işe yarar. Şifrelemenin bütünü çökmenin eşiğinde değil. Asma kilidin veriyi karıştıran yarısının ayakta kalması bekleniyor. Risk altındaki yarının ise standartlaşmış, sınanmış ve web trafiğinin önemli bir bölümünde şimdiden açık olan yerine geçecek yöntemleri var. Geriye yavaş ve gösterişsiz bir iş kalıyor: eski açık anahtarlı yöntemlerin kullanıldığı her yeri bulup değiştirmek. Çoğu insan için bu iş güncellemelerle, sizden bir şey beklenmeden yürüyor. Tarayıcınızı, telefonunuzu ve mesajlaşma uygulamalarınızı güncel tutmak, size düşen basit pay.
