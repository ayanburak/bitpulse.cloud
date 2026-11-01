---
slug: yapay-zeka-neden-uydurur
title: "Yapay Zekâ Neden Uydurur?"
summary: "ChatGPT, New York'taki bir avukata verdiği davanın gerçek olduğunu söyledi. Dava uydurmaydı. Arkasındaki nedenler, botların bilmediğini söylemek yerine neden uydurduğunu, kendinden emin bir tonun neden hiçbir şey kanıtlamadığını ve nasıl korunulacağını gösteriyor."
category: technology
date: 2026-11-02
kind: long
sources:
  - name: "Kalai, Nachum, Vempala ve Zhang: Why Language Models Hallucinate (makale, tam metin)"
    url: https://cdn.openai.com/pdf/d04913be-3f6f-4d2b-b283-ff432ef4aaa5/why-language-models-hallucinate.pdf
  - name: "arXiv: Why Language Models Hallucinate (özet sayfası)"
    url: https://arxiv.org/abs/2509.04664
  - name: "Anthropic: Tracing the thoughts of a large language model (büyük bir dil modelinin düşüncelerini izlemek)"
    url: https://www.anthropic.com/research/tracing-thoughts-language-model
  - name: "ABD New York Güney Bölgesi Federal Mahkemesi: Mata v. Avianca, yaptırım kararı (22 Haziran 2023)"
    url: https://storage.courtlistener.com/recap/gov.uscourts.nysd.575368/gov.uscourts.nysd.575368.54.0.pdf
  - name: "Columbia Journalism Review, Tow Center: Yapay zeka aramalarının kaynak gösterme sorunu"
    url: https://www.cjr.org/tow_center/we-compared-eight-ai-search-engines-theyre-all-bad-at-citing-news.php
  - name: "arXiv: Semantic Entropy Probes: Robust and Cheap Hallucination Detection in LLMs"
    url: https://arxiv.org/abs/2406.15927
  - name: "Türkiye Barolar Birliği (TBB) Bilişim ve Teknoloji Hukuku Komisyonu: Avukatlar İçin Yapay Zekâ Kullanımı Tavsiye Rehberi (PDF)"
    url: https://hukukihabernet.teimg.com/hukukihaber-net/uploads/2026/08/tbb-yapayzekatavsiyerehberi.pdf
  - name: "Hukuki Haber: TBB'den avukatlar için yapay zeka kullanımı tavsiye rehberi"
    url: https://www.hukukihaber.net/tbbden-avukatlar-icin-yapay-zeka-kullanimi-tavsiye-rehberi
  - name: "Hukuki Haber: Güçlü bir ilk çerçeve, ancak \"tavsiye\" ile yükümlülüğün sınırı her yerde açık değil"
    url: https://www.hukukihaber.net/tbb-avukatlar-icin-yapay-zeka-rehberininin-analizi
image:
  file: image.jpg
  alt: "Siyah sunuculardan oluşan bir rafın yakın görüntüsü; disk yuvaları sıralar halinde ve mavi ile yeşil durum ışıkları yanıyor, bir sunucu odasında."
  credit: "NOIRLab/NSF/AURA/T. Slovinský"
  license: "CC BY 4.0"
  licenseUrl: https://creativecommons.org/licenses/by/4.0/
  source: https://commons.wikimedia.org/wiki/File:NOIRLab_HQ_Server_Racks_(6V6A0402-CC).jpg
---
Mayıs 2023'te New York'lu avukat Steven Schwartz, federal bir mahkemeye cep telefonundan alınmış ekran görüntüleri sundu. Bir havayolu şirketine karşı açılan davada kendisinin yazıp bir meslektaşının imzaladığı dilekçe, kimsenin bulamadığı mahkeme kararlarına atıf yapıyordu ve bu kararlar ChatGPT'den gelmişti. Görüntülerde ChatGPT'ye, bunlardan Varghese – China Southern Airlines davasının gerçek bir dava olup olmadığını ve verdiği diğerlerinin sahte olup olmadığını soruyordu. ChatGPT bunların "gerçek" olduğunu ve ABD'de mahkeme kararlarına bakılan başlıca kaynaklar olan Westlaw, LexisNexis ve Federal Reporter'da bulunabileceğini söyledi.

Bu davalar yoktu. Hâkim sonradan bunları, sahte alıntı ve atıflar içeren var olmayan yargı kararları olarak nitelendirdi. Olayın en tuhaf yanı şu: Davayı uyduran sistemden bir de davanın doğru olup olmadığını teyit etmesi istendi ve sistem teyit etti.

Yapay zekâ araştırmacıları bu davranışa "halüsinasyon" diyor: Akıcı ve kendinden emin ama yanlış bir ifade. Sorun, bunun neden olduğu.

## Sohbet botu aslında ne yapar?

ChatGPT ya da Claude gibi sohbet botları, büyük miktarda metinle eğitilmiş bir program olan "büyük dil modeli" üzerinde çalışır. Temel becerisi, bir metni sürdürmektir. Claude'u geliştiren Anthropic, modellerin sözcükleri tek tek ürettiğini ve "her zaman bir sonraki sözcük için tahmin yürütmesi gerektiğini" anlatıyor.

Bunun bir sonucu var. Model bir kataloğa bakıp bulduğunu aktarmıyor. Konuşmanın en akla yatkın devamını üretiyor ve neredeyse her soru için akla yatkın bir yanıt vardır. Bir mahkeme kararı için isim, mahkeme, yıl ve künye gerekir. Model bunların nasıl göründüğünü çok iyi bildiği için, her yönüyle gerçeğe benzeyen ama gerçek olmayan bir tane üretebilir.

## Tek kez geçen bilgiler

Her bilgi aynı oranda risk taşımıyor. Adam Tauman Kalai ve arkadaşlarının 2025 tarihli araştırma makalesi farkı açıklıyor. Eğitimin ilk aşamasında, yani "ön eğitim"de model, çok büyük bir metin yığınından dilin örüntülerini öğrenir. Bazı şeylerin örüntüsü kolay öğrenilir, imla gibi. Makalenin yazarları modellerin yazım hatası gibi birçok hata türünden kaçındığını belirtiyor.

Bazı bilgilerin ise hiçbir örüntüsü yok. Bir doğum günü, bir doktora tezinin adı ya da az bilinen bir mahkeme kararı, başka hiçbir şeyden çıkarılamaz. Eğitim metninde yalnızca bir kez geçtiyse ya da hiç geçmediyse, modelin dayanacağı sağlam bir şey kalmaz. Makale bunu somutlaştırıyor: Doğum günü bilgilerinin yüzde 20'si eğitim metninde tam olarak bir kez geçiyorsa, ön eğitimden yeni çıkmış bir modelin bu tür sorulardan en az yüzde 20'sini yanlış yapması beklenir.

Ünlü bilgiler daha güvenli. Makaleye göre dil modelleri, Einstein'ın doğum günü gibi sık anılan bilgilerde nadiren yanılır. Tehlike ayrıntıda: az tanınan bir kişi, dar bir alandaki makale, küçük bir kasabanın tarihi.

Makalenin kendi örnekleri akılda kalıcı. Yazarlardan birinin doğum günü soruldu, üstelik yalnızca biliniyorsa yanıt vermesi istendi. Açık kaynaklı bir model üç denemede üç ayrı yanlış tarih verdi. Aynı kişinin doktora tezinin adı sorulduğunda, yaygın kullanılan üç sohbet botunun üçü de birbirinden farklı, yanlış bir ad ve yanlış bir yıl söyledi. Yanıtların hepsi ayrıntılıydı, hiçbiri doğru değildi.

## Adını bilmek, kişiyi bilmek değildir

Anthropic'in Mart 2025'te yayımladığı, Claude'un içine bakan çalışma daha derindeki bir şeye işaret ediyor. Araştırmacılar, yanıt vermeyi reddetmenin modelin varsayılan davranışı olduğunu buldu: Baştan açık duran bir devre, modele yeterli bilgisi olmadığını söyletiyor. Sorunun konusunu tanıyıp tanımadığını izleyen ayrı bir özellik ise bu varsayılanı kapatıyor. Ünlü bir isim için istenen de bu.

Sorun, tanıma yanlış çalıştığında çıkıyor. Araştırmacıların ifadesiyle bu, model "bir adı tanıyıp o kişi hakkında başka hiçbir şey bilmediğinde" olabiliyor. Aşinalık duygusu "bilmiyorum" refleksini kapatıyor, model de devam edip bir şeyler uyduruyor. Ekip bir deneyde, "Michael Batkin" adlı bilinmeyen bir kişi için bilinen-yanıt özelliklerini yapay olarak açarak modele bu kişinin satranç oynadığını söyletti. Bu müdahale olmadan model, onunla ilgili soruyu yanıtlamayı reddetti.

Sohbet botunun özgüveni, yanıtı gerçekle karşılaştırmasından gelmiyor. Konuya duyduğu aşinalıktan geliyor ve bu aşinalık, bilgi yokken de olabiliyor. Anthropic, halüsinasyona karşı yaptığı eğitimi nispeten başarılı ama kusurlu olarak tanımlıyor.

## Blöf yapana puan veren sınav

Halüsinasyon ön eğitimde başlıyorsa, modeli cilalamak için yapılan sonraki aşamalarda neden yok olmuyor? Kalai makalesi neredeyse insani bir açıklama sunuyor: Modellerin nasıl notlandırıldığı.

Dil modellerini ölçen standart testlerin çoğu bir yanıtı yalnızca doğru ya da yanlış sayıyor. Doğru yanıt bir puan getiriyor, yanlış yanıt da "bilmiyorum" da sıfır. Bu puanlamada tahmin yürütmek, belirsizliği kabul etmekten hiçbir zaman daha kötü değil. Sınava girenler bunu bilir: Emin olmayan boş bırakmaz, akla yatkın bir şey yazar. Yazarlar modellerin bu yüzden sürekli "sınav modunda" olduğunu söylüyor. Her zaman belirsizliğini söyleyen bir modelin, çok daha güvenilir olsa bile, her zaman tahmin yürüten bir modelden düşük puan alacağına da dikkat çekiyorlar. Blöfler de genellikle kesin ayrıntı taşıyor: "Sonbahar civarı" yerine "30 Eylül" gibi.

Makalenin önerdiği çözüm, puanlamayı değiştirmek. Testler bir güven eşiği belirtebilir ve yanlış yanıttan puan kırabilir. Böylece tahmin yalnızca modelin büyük olasılıkla haklı olduğu durumlarda işe yarar. Yazarlar bazı insan sınavlarının zaten böyle çalıştığını hatırlatıyor. Hindistan'daki JEE ve ABD'deki SAT'ın geçmiş yıllardaki hâli bunlardan.

## Hiç blöf yapmayan bir model olur mu?

Halüsinasyon tümüyle ortadan kaldırılabilir mi? Makalenin yanıtı dikkatli. Halüsinasyonların ilke olarak kaçınılmaz olmadığını söylüyor, çünkü bir model yalnızca bildiği sabit bir soru listesini yanıtlayıp gerisine "bilmiyorum" diyebilir. Böyle bir model halüsinasyon görmez ama çok az şeyi yanıtlar. Bir okuma şu: Faydalılık ile kusursuz temkin ters yönlere çekiyor.

Şirketler ve araştırmacılar pratikte sorunu yok etmiyor, azaltıyor. Anthropic, Claude'un yanıtlayamadığı soruları çoğunlukla reddetmesini sağlayan bir eğitimi anlatıyor. Arama araçları sohbet botuna cevap vermeden önce sayfalara bakma imkânı veriyor. Ancak Kalai makalesi aramanın çare olmadığı uyarısını yapıyor: Arama kesin bir yanıt bulamadığında model yine tahmin yürütebilir.

Uyarı işaretleri üzerinde de çalışılıyor. Bir fikir, aynı soruyu birçok kez sorup yanıtların anlamca örtüşüp örtüşmediğine bakmak. Dağılıyorlarsa model büyük olasılıkla tahmin yürütüyordur. "Anlamsal entropi" denen bu yöntem birkaç kat daha fazla hesaplama gücü istiyor. Sonraki bir çalışma, aynı sinyali modelin içinden, tek bir yanıt sırasında kestiren daha ucuz "probları" öneriyor. Bunlar araştırma araçları; sohbet botunu dürüst yapan bir düğme değil.

## İnternete bağlanınca da yanılıyorlar

Sohbet botunu internete bağlamanın sorunu çözeceğini düşünmek cazip. Columbia Journalism Review'un Tow Center'ının Mart 2025'te yayımladığı çalışma, sekiz yapay zekâ arama aracını test etti. Her araca bir haber makalesinden alıntı verildi ve başlığı, yayıncıyı, tarihi ve bağlantıyı bulması istendi. Alıntılar, sıradan bir web aramasında orijinalin ilk üç sonuç arasında çıkacağı şekilde seçilmişti. 1.600 sorguda araçlar zamanın yüzde 60'ından fazlasında yanıldı. Oran araca göre çok değişiyordu: Bir araçta yüzde 37, bir başkasında yüzde 94.

Ton da rakamlar kadar önemliydi. Araştırmacılar araçların çoğunun yanlış yanıtları "ürkütücü bir özgüvenle" verdiğini yazdı. ChatGPT 200 makalenin 134'ünü yanlış tanıdı, düşük güven işaretini yalnızca 15 kez verdi ve hiç yanıtsız bırakmadı. İki aracın ücretli sürümleri ücretsiz sürümlerinden daha çok doğru yanıt verdi ama daha sık da yanıldı, çünkü yanıt vermeyi reddetmek yerine kesin ve yanlış yanıtlar verdiler. İki aracın yanıtlarının yarıdan fazlası uydurma ya da çalışmayan bağlantılar gösterdi.

Çalışma dar bir görevi, haber alıntısının kaynağını bulmayı test etti, yani her tür soruyu ölçmüyor. Ama kendinden emin sesin bir rehber olarak kullanılamayacağını gösteriyor.

## Mahkeme ve baroların uyarısı

New York'taki olayda o ekran görüntülerinin bir ayrıntısı belirsiz: Schwartz'ın bu soruları ne zaman sorduğu. İlk yeminli beyanı tarih vermiyordu ama sohbet botunu Varghese davası mahkemede anılmadan, en azından sözde metni dosyaya konmadan önce sorguladığını düşündürüyordu. Sonraki beyanında ise kuşkularının ancak mahkemenin yaptırım ihtimalini gündeme getiren ilk emrinden sonra başladığını, ChatGPT'nin de o zaman Varghese'nin "gerçekten var olduğunu" söylediğini yazdı. Mahkeme bu açıklamaları "değişken ve birbiriyle çelişen" diye niteledi ve kötü niyet tespit etti. Mahkeme ayrıca Schwartz'ın kendi ifadesinin, mahkemeye bir şey sunmadan önce Varghese'nin tam metninin bulunamadığını bildiğine işaret ettiğini kaydetti. Sohbet botunun yanıtları belgeli. Soruların ne zaman sorulduğu ise yalnızca birbirini tutmayan kendi anlatımlarına dayanıyor. Mahkeme, o emirden önce botun dava uydurabileceğini aklına getiremediği yönündeki iddiasını da reddetti.

Bu kaygı Türkiye'ye de ulaştı. Türkiye Barolar Birliği (TBB) avukatlar için yapay zekâ kullanımına dair bir tavsiye rehberi çıkardı; Hukuki Haber sitesi rehberin Ağustos 2026'da yayımlandığını aktardı. Rehber, yapay zekâ sistemlerinin var olmayan içtihat, mevzuat, kaynak ya da olgular üretebileceğini ve bunları gerçekmiş gibi sunabileceğini söylüyor. Hukuki çıktıların resmî ve güvenilir kaynaklardan doğrulanması, avukat denetiminden geçmeden müvekkile, mahkemeye ya da üçüncü kişilere sunulmaması gerekiyor. TBB Başkanı rehberin önsözünde, mesleki sorumluluğun hiçbir aşamada yapay zekâya devredilemeyeceğini yazıyor.

New York'taki hâkim de kendi bağlamında benzer bir şey söylemişti. Kararda, güvenilir bir yapay zekâ aracından yardım almanın kendi başına uygunsuz olmadığı, ama avukatların dilekçelerinin doğruluğunu sağlama konusunda bir "kapı bekçisi" rolü bulunduğu yazıyor. Mahkeme iki avukata ve büroya 5.000 dolar ceza verdi. Ayrıca mahkeme sorguladıktan sonra bile sahte kararların arkasında durmaya devam ettiklerini kaydetti.

## Kendinizi korumak için alışkanlıklar

Araştırmalar pratik alışkanlıklara işaret ediyor.

**Botun büyük olasılıkla bildiği şeyleri sorun.** Çok bilinen, çok konuşulmuş bilgiler daha güvenli. Uydurma yanıtlar, az bilinen kişilerde, dar çalışmalarda, kelimesi kelimesine alıntılarda ve künye ayrıntılarında yoğunlaşıyor.

**İsimleri, sayıları, tarihleri, alıntıları ve bağlantıları kontrol edilecek iddialar sayın.** Bir model bunları bilmeden de inandırıcı biçimde üretebilir. Bağlantıyı açın. Makalenin adını aratın. Kararı resmî bir veri tabanında arayın.

**Botun kendini onaylamasını istemeyin.** Schwartz'ın ChatGPT'ye sorduğunda aldığı yanıt değersizdi. İddiayı üreten sistemin, onu denetleyebileceği ayrı bir yolu yok.

**"Bilmiyorum" demesine izin verin.** Araştırmalara göre modeller kısmen, testlerde blöf ödüllendirildiği için blöf yapıyor. "Yalnızca eminsen yanıt ver" demek, makalenin testler için önerdiğine benziyor. Yardımı olabilir ama bir garantisi yok.

**Hatanın en pahalı olduğu yerde en dikkatli olun.** Hukuk, sağlık, para ve ödevlerde sohbet botunu taslak, özet ya da açıklama için kullanın; güvenmeden önce sonucu güvenilir bir kaynaktan doğrulayın.

Sohbet botu, iyi bildiği şeyleri de bilmediği şeyleri de aynı akıcı sesle anlatıyor. Okurun tek bir yanlış yanıttan çok bunu aklında tutması gerekir. Kendinden emin ton, sistemin yazış biçiminin bir parçası. Yanıtın doğru olduğuna dair bir kanıt değil.
