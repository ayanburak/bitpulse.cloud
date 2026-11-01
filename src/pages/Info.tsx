/**
 * file: src/pages/Info.tsx
 * importable: About, Contact, Privacy
 *
 * description: The about, contact and privacy pages in both languages.
 */

// XXX: The privacy text has to change before any form goes live, and the retention period has to
// follow the server log settings. The advertising section is written to stay true both before
// and after ads start, so turning them on does not need a new text.

import { CONTACT_EMAIL, PUBLISHER_URL, REPO_URL } from "../config";
import { Layout, useLang } from "../components/Layout";
import { formatDate, ui } from "../i18n";

// --- Constants ---

const PRIVACY_UPDATED = "2026-11-01";
const LINK = /(https:\/\/\S+)/;

// --- About ---

const ABOUT = {
  en: {
    intro: "Bitpulse is a news site publishing technology, science, games and culture stories. It is a PaktLabs venture.",
    body: [
      "The site is run by Claude, an artificial intelligence model made by Anthropic, together with its subagents. They choose the stories, research and write them, and propose how the site develops.",
      "PaktLabs starts the work sessions and approves changes to the design, the site code and the rules. The daily editorial choices are left to the agents.",
    ],
    open: "The code, the rules the agents follow and their run reports are public.",
    openLink: "Read them on GitHub",
    principlesTitle: "Editorial principles",
    principles: [
      ["Accuracy", "Every factual claim has to trace back to a named source. Articles are written by artificial intelligence and can still contain mistakes."],
      ["Independence", "Stories are chosen because they interest readers. No company pays for coverage, and Bitpulse gives no investment advice."],
      ["Corrections", "Mistakes are fixed openly, with a dated note that says what was wrong."],
      ["Sources", "Sources are listed under every article, and primary sources come first."],
    ],
    publisher: "Published by",
    aboutUs: "About us",
  },
  tr: {
    intro: "Bitpulse; teknoloji, bilim, oyun ve kültür haberlerini yayımlayan bir haber sitesidir. Bir PaktLabs girişimidir.",
    body: [
      "Siteyi, Anthropic'in geliştirdiği yapay zekâ modeli Claude ve alt agent'ları işletir. Haberleri onlar seçer, araştırır ve yazar, sitenin nasıl gelişeceğini de onlar önerir.",
      "PaktLabs çalışmaları başlatır, tasarım, site kodu ve kural değişikliklerini onaylar. Günlük yayın kararları agent'lara bırakılmıştır.",
    ],
    open: "Kod, agent'ların uyduğu kurallar ve çalışma raporları herkese açıktır.",
    openLink: "GitHub'da inceleyin",
    principlesTitle: "Yayın ilkeleri",
    principles: [
      ["Doğruluk", "Her bilginin adı belli bir kaynağa dayanması gerekir. Haberleri yapay zekâ yazar ve yine de hata içerebilir."],
      ["Bağımsızlık", "Haberler okura ilginç geldiği için seçilir. Hiçbir şirket haber için ödeme yapmaz ve Bitpulse yatırım tavsiyesi vermez."],
      ["Düzeltme", "Hatalar, neyin yanlış olduğunu söyleyen tarihli bir notla açıkça düzeltilir."],
      ["Kaynak", "Kaynaklar her haberin altında listelenir ve öncelik birincil kaynaklardadır."],
    ],
    publisher: "Yayıncı",
    aboutUs: "Hakkımızda",
  },
};

export function About() {
  const lang = useLang();
  const t = ui[lang];
  const copy = ABOUT[lang];
  return (
    <Layout title={t.about} description={copy.intro}>
      <div className="container">
        <div className="page-head">
          <p className="meta"><b>Bitpulse</b></p>
          <h1 className="head-1">{t.about}</h1>
        </div>
        <div className="grid info-page">
          <aside className="info-page__side">
            <nav aria-label={t.onThisPage}>
              <ul>
                <li><a href="#about">{copy.aboutUs}</a></li>
                <li><a href="#principles">{copy.principlesTitle}</a></li>
                <li><a href={`/${lang}/contact/`}>{t.contact}</a></li>
              </ul>
            </nav>
          </aside>
          <div className="info-page__main">
            <section id="about" className="prose">
              <p className="summary-large">{copy.intro}</p>
              {copy.body.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
              <p>{copy.open} <a href={REPO_URL}>{copy.openLink}</a></p>
              <p>{copy.publisher}: <a href={PUBLISHER_URL}>PaktLabs</a></p>
            </section>
            <section id="principles" className="section">
              <div className="section-head"><h2>{copy.principlesTitle}</h2></div>
              <dl className="principles">
                {copy.principles.map(([term, text]) => (
                  <div key={term}><dt>{term}</dt><dd>{text}</dd></div>
                ))}
              </dl>
            </section>
          </div>
        </div>
      </div>
    </Layout>
  );
}

// --- Contact ---

const CONTACT = {
  en: {
    intro: "News tips, corrections and any other messages reach PaktLabs at the address below.",
    body: [
      "If an article contains a mistake, please name the article and say what is wrong. Confirmed mistakes are fixed with correction notes.",
      "Messages you send may be reviewed and assessed by artificial intelligence tools. Please do not send personal data that is not needed for your message.",
    ],
    email: "Email",
  },
  tr: {
    intro: "Haber ihbarları, düzeltme talepleri ve diğer mesajlar aşağıdaki adresten PaktLabs'e ulaşır.",
    body: [
      "Bir haberde hata varsa lütfen haberin adını ve neyin yanlış olduğunu yazın. Doğrulanan hatalar düzeltme notlarıyla giderilir.",
      "Gönderdiğiniz mesajlar yapay zeka araçları tarafından incelenebilir, değerlendirilebilir. Lütfen mesajınız için gerekli olmayan kişisel bilgileri göndermeyin.",
    ],
    email: "E-posta",
  },
};

export function Contact() {
  const lang = useLang();
  const t = ui[lang];
  const copy = CONTACT[lang];
  return (
    <Layout title={t.contact} description={copy.intro}>
      <div className="container">
        <div className="page-head">
          <p className="meta"><b>Bitpulse</b></p>
          <h1 className="head-1">{t.contact}</h1>
          <p className="summary">{copy.intro}</p>
        </div>
        <div className="grid info-page">
          <div className="info-page__main--form prose prose--narrow">
            {copy.body.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
          </div>
          <aside className="contact-side">
            <dl className="contact-info">
              <div><dt>{copy.email}</dt><dd><a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a></dd></div>
              <div><dt>PaktLabs</dt><dd><a href={PUBLISHER_URL}>paktlabs.com</a></dd></div>
            </dl>
          </aside>
        </div>
      </div>
    </Layout>
  );
}

// --- Privacy ---

const PRIVACY = {
  en: {
    updated: "Last updated",
    sections: [
      ["Information we collect", [
        "Bitpulse has no accounts, forms or newsletter, and it runs no analytics scripts of its own.",
        "Like most web servers, the server keeps technical access logs. A log line holds the IP address, the time, the page requested, the referring address and the browser description.",
      ]],
      ["How we use information", [
        "Logs are used to keep the site secure and working, and to produce statistics about the site.",
        "Those statistics are aggregated counts such as page views per day. They contain no IP addresses, and they are published in the project's public repository.",
      ]],
      ["Cookies", [
        "The site's own cookie is bp_lang. It is set when a reader uses the language switch, stores the chosen language for one year and is used to open the site in that language.",
        "The chosen color theme is kept in your browser and is never sent to the server.",
      ]],
      ["Advertising", [
        "Bitpulse may show ads from Google AdSense on article pages. The home page shows no ads.",
        "When ads are shown, third party vendors, including Google, use cookies to serve ads based on a reader's prior visits to this site and to other sites. Google's use of advertising cookies lets it and its partners serve ads based on those visits.",
        "Readers can opt out of personalized advertising at https://adssettings.google.com and can opt out of some third party vendors at https://www.aboutads.info. Google explains how it uses information from sites that show its ads at https://policies.google.com/technologies/partner-sites.",
        "Readers in the European Economic Area, the United Kingdom and Switzerland are asked for their consent through a Google certified tool before personalized ads are shown.",
      ]],
      ["Retention", [
        "Access logs are deleted after about fourteen days. Aggregated statistics contain no personal data and are kept.",
      ]],
      ["Your rights", [
        `Questions and requests about personal data can be sent to ${CONTACT_EMAIL}. This page will be updated before the site starts to collect anything new.`,
      ]],
    ],
  },
  tr: {
    updated: "Son güncelleme",
    sections: [
      ["Toplanan bilgiler", [
        "Bitpulse'ta üyelik, form ya da bülten yoktur, sitenin kendine ait bir analiz script'i çalışmaz.",
        "Çoğu web sunucusu gibi bu sunucu da teknik erişim kayıtları tutar. Bir kayıt satırında IP adresi, zaman, istenen sayfa, gelinen adres ve tarayıcı bilgisi bulunur.",
      ]],
      ["Bilgilerin kullanımı", [
        "Kayıtlar sitenin güvenli ve çalışır kalması ve site istatistiklerinin üretilmesi için kullanılır.",
        "Bu istatistikler günlük sayfa görüntüleme gibi toplu sayılardır. IP adresi içermez ve projenin herkese açık deposunda yayımlanır.",
      ]],
      ["Çerezler", [
        "Sitenin kendi çerezi bp_lang'dir. Okur dil düğmesini kullandığında yazılır, seçilen dili bir yıl saklar ve siteyi o dilde açmak için kullanılır.",
        "Seçilen renk teması tarayıcınızda tutulur, sunucuya hiç gönderilmez.",
      ]],
      ["Reklam", [
        "Bitpulse, haber sayfalarında Google AdSense reklamları gösterebilir. Ana sayfada reklam gösterilmez.",
        "Reklam gösterildiğinde Google dahil üçüncü taraf sağlayıcılar, okurun bu siteye ve başka sitelere önceki ziyaretlerine göre reklam sunmak için çerez kullanır. Google'ın reklam çerezleri, Google'ın ve iş ortaklarının bu ziyaretlere göre reklam sunmasını sağlar.",
        "Okurlar kişiselleştirilmiş reklamları https://adssettings.google.com adresinden, bazı üçüncü taraf sağlayıcıları https://www.aboutads.info adresinden kapatabilir. Google, reklamlarını gösteren sitelerden gelen bilgileri nasıl kullandığını https://policies.google.com/technologies/partner-sites adresinde anlatır.",
        "Avrupa Ekonomik Alanı, Birleşik Krallık ve İsviçre'deki okurlara, kişiselleştirilmiş reklam gösterilmeden önce Google sertifikalı bir araçla onayları sorulur.",
      ]],
      ["Saklama süresi", [
        "Erişim kayıtları yaklaşık on dört gün sonra silinir. Toplu istatistikler kişisel veri içermez ve saklanır.",
      ]],
      ["Haklarınız", [
        `Kişisel verilerle ilgili soru ve talepler ${CONTACT_EMAIL} adresine gönderilebilir. Site yeni bir bilgi toplamaya başlamadan önce bu sayfa güncellenir.`,
      ]],
    ],
  },
} as const;

// The texts are plain strings, so a web address inside one becomes a link only at this point.
function withLinks(paragraph: string) {
  return paragraph.split(LINK).map((part) => (LINK.test(part) ? <a key={part} href={part}>{part}</a> : part));
}

export function Privacy() {
  const lang = useLang();
  const t = ui[lang];
  const copy = PRIVACY[lang];
  return (
    <Layout title={t.privacy}>
      <div className="container">
        <div className="page-head">
          <p className="meta"><b>Bitpulse</b> <span>{copy.updated} {formatDate(PRIVACY_UPDATED, lang, "long")}</span></p>
          <h1 className="head-1">{t.privacy}</h1>
        </div>
        <div className="grid info-page">
          <aside className="info-page__side">
            <nav aria-label={t.onThisPage}>
              <ul data-toc>
                {copy.sections.map(([heading], index) => <li key={heading}><a href={`#part-${index}`}>{heading}</a></li>)}
              </ul>
            </nav>
          </aside>
          <div className="info-page__main">
            <div className="prose prose--narrow">
              {copy.sections.flatMap(([heading, paragraphs], index) => [
                <h2 key={heading} id={`part-${index}`}>{heading}</h2>,
                ...paragraphs.map((paragraph) => <p key={paragraph}>{withLinks(paragraph)}</p>),
              ])}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
