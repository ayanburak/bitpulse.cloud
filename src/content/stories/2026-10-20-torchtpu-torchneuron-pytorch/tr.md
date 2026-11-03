---
slug: google-amazon-yapay-zeka-cip-yarisi
title: "Google ve Amazon Aynı Gün Aynı Hamleyi Yaptı: Çip Yarışı Kızışıyor"
summary: "İki teknoloji devi, yapay zekâ yazılımlarının kendi çiplerinde daha kolay çalışması için aynı gün sahneye çıktı. Hedef belli: geliştiricileri, yani yapay zekâ dünyasının en değerli müşterilerini kendi tarafına çekmek."
category: technology
date: 2026-10-20
kind: news
sources:
  - name: "Google Cloud Blog: TorchTPU is now open source"
    url: https://cloud.google.com/blog/topics/ai-infrastructure/torchtpu-is-now-open-source-run-native-pytorch-on-tpus
  - name: "PyTorch Blog: Introducing TorchNeuron"
    url: https://pytorch.org/blog/introducing-torchneuron-native-pytorch-backend-for-aws-trainium/
  - name: "Techzine: TorchNeuron brings PyTorch code to AWS Trainium without modifications"
    url: https://www.techzine.eu/news/infrastructure/145105/torchneuron-brings-pytorch-code-to-aws-trainium-without-modifications/
  - name: "The Register: Nvidia's CUDA moat may not be as impenetrable as you think"
    url: https://www.theregister.com/2024/12/17/nvidia_cuda_moat/
  - name: "Wikipedia: Tensor Processing Unit"
    url: https://en.wikipedia.org/wiki/Tensor_Processing_Unit
  - name: "Wikipedia: PyTorch"
    url: https://en.wikipedia.org/wiki/PyTorch
  - name: "Wikipedia: Annapurna Labs"
    url: https://en.wikipedia.org/wiki/Annapurna_Labs
image:
  file: image.jpg
  alt: "Üzerinde çok sayıda renkli mikroçip deseni bulunan parlak bir silikon levhanın yakın çekimi."
  credit: "DrHughManning"
  license: "CC BY-SA 4.0"
  licenseUrl: https://creativecommons.org/licenses/by-sa/4.0/
  source: https://commons.wikimedia.org/wiki/File:Semiconductor_Wafer_of_Microelectronics.jpg
---
Teknoloji dünyasında bazı yarışlar büyük reklamlarla değil, dışarıdan bakınca sıkıcı görünen duyurularla kızışır. 20 Ekim'de de böyle oldu. Google ve Amazon, geliştiricilerin bir araya geldiği PyTorch Konferansı'nda neredeyse aynı mesajı verdi: Yapay zekâ yazılımlarınızı artık bizim çiplerimizde de kolayca çalıştırabilirsiniz.

Bu cümle ilk bakışta sıradan bir ürün tanıtımı gibi görünebilir. Ama arkasında yapay zekâ çağının en pahalı rekabetlerinden biri var. Bugün yapay zekâ sistemlerini eğitmek ve çalıştırmak çok güçlü çipler gerektiriyor. Bu alanın en bilinen ismi Nvidia. Google ve Amazon ise yıllardır kendi çözümlerini geliştiriyor.

## Şirketler neden kendi çipini yapıyor?

Google, kendi yapay zekâ çipi TPU'yu 2015'ten beri veri merkezlerinde kullanıyor ve Mayıs 2016'da dünyaya tanıttı. Amazon ise 2015'te satın aldığı çip şirketi Annapurna Labs'in birikimiyle ilerledi ve Aralık 2020'de Trainium adlı yapay zekâ çipini duyurdu.

Bir şirketin kendi çipini üretmek istemesi şaşırtıcı değil. Yapay zekâ altyapısı bu şirketlerin [en büyük yatırımlarından biri](/tr/stories/alphabet-tarihinin-en-kotu-gunu-google-bulut-arama/). Donanımı kendi tasarlayan şirket, ürünü kendi ihtiyacına göre şekillendirebilir.

Ama güçlü bir çip üretmek hikâyenin yalnızca yarısı. Geliştiriciler o çipi kullanmıyorsa, en iyi donanım bile rafta kalır.

## Oyun konsolu benzetmesi

Bunu oyun konsollarına benzetebiliriz. Bir konsolun gücü kadar, üzerinde hangi oyunların çalıştığı da önemlidir. Herkes aynı konsol için oyun yapıyorsa, yeni bir rakibin daha güçlü olması tek başına yetmez. Oyunların o konsola da gelmesi gerekir.

Yapay zekâ dünyasındaki durum buna oldukça benziyor. PyTorch, yapay zekâ modellerini hazırlamak ve eğitmek için kullanılan yaygın bir yazılım aracı. Meta tarafından geliştirildi, 2016'da yayımlandı ve bugün Linux Vakfı çatısı altındaki bağımsız bir yapı tarafından yönetiliyor. ChatGPT'nin de aralarında bulunduğu birçok tanınmış sistem bu araçla geliştirildi. Amazon'a göre yapay zekâ araştırmacıları ve geliştiricilerinin yüzde 85'i kodunu PyTorch ile yazıyor.

Sorun şu: Bu kodu başka bir çipe taşımak çoğu zaman kolay değil. Teknoloji yayını Techzine'e göre farklı çiplere geçmek isteyenler kodu yeniden yazmak ve doğrulamak için çoğu zaman aylar harcıyordu.

## Google ve Amazon ne yaptı?

İki şirket de işte bu engeli küçültmeye çalışıyor.

Google, Meta ile birlikte geliştirdiği TorchTPU adlı aracı açık kaynak yaptı. Yani kodu artık herkes görebiliyor ve kullanabiliyor. Şirket, bu araçla birlikte kullanılan bir eğitim sisteminin 8 bin çipe kadar test edildiğini söylüyor.

Amazon da kendi çipleri için TorchNeuron'u yayımladı. Şirkete göre bir modeli Trainium'a taşımak için bazı durumlarda yalnızca tek bir ayarı değiştirmek yetebiliyor. Araç şimdilik herkese açık deneme aşamasında.

İki hamlenin hedefi aynı: Geliştiriciye yeni bir dil öğretmeden, alıştığı araçlarla çalışmaya devam etmesini sağlamak. Konsol benzetmesine dönersek, şirketler oyunları tek tek yeniden yazmak yerine yeni konsollarında da çalıştıracak bir yol arıyor.

## Nvidia için ne anlama geliyor?

Nvidia'nın gücü yalnızca çiplerinden gelmiyor. Şirketin yıllar içinde kurduğu yazılım dünyası da önemli bir avantaj sağlıyor. PyTorch da Nvidia çiplerinde bu yazılım altyapısı üzerinden çalışabiliyor.

Yine de tablo değişiyor. Bir Intel yöneticisinin The Register'a söylediğine göre geliştiricilerin çoğu artık doğrudan çipe en yakın seviyede değil, PyTorch gibi daha üst seviyedeki araçlarda çalışıyor. Intel de Nvidia'nın rakibi, bu yüzden bu tek tarafın görüşü. Bu da rakiplere bir fırsat veriyor. PyTorch başka çiplerde de sorunsuz çalışırsa, geçiş daha kolay hale gelebilir.

Bu, Nvidia'nın yerinden kolayca oynatılacağı anlamına gelmiyor. Çip dünyasında yıllarla ölçülen alışkanlıklar ve yatırımlar var. Ama iki büyük rakibin aynı gün aynı kapıya yüklenmesi, savaş alanının nereye kaydığını gösteriyor.

## Neden hemen heyecanlanmamak gerekiyor?

Bu vaatlerin büyük bölümü şimdilik şirketlerin kendi anlatımı. Amazon'un kendi blog yazısına göre ilk sürümde bazı özellikler henüz yok. Şirket, test sonuçlarında yaklaşık 154 bin sonucun 69 bininin atlandığını, bunların 22 bin kadarının henüz desteklenmeyen işlemlerden kaynaklandığını da açıklıyor.

Gerçek sınav ise şirketlerin dışında yaşanacak. Bağımsız geliştiriciler bu araçları kendi projelerinde denediğinde tek ayar vaadinin ne kadar tuttuğu ortaya çıkacak. Yani yarış kızışıyor, ama kimin öne geçtiğini söylemek için henüz erken.
