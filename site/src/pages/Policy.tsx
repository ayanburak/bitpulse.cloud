/**
 * file: src/pages/Policy.tsx
 * importable: EditorialPolicy, Corrections
 *
 * description: The editorial policy page and the corrections page in both languages.
 */

// NOTE: The policy text summarizes docs/editorial-policy.md. When that file changes, this text
// has to change with it.

import { correctedStories, storyPath } from "../catalog";
import { CONTACT_EMAIL } from "../config";
import { Layout, useLang } from "../components/Layout";
import { formatDate, ui } from "../i18n";

// --- Editorial policy ---

const POLICY = {
  en: {
    intro: "The principles Bitpulse follows in its reporting.",
    sections: [
      ["About Bitpulse", [
        "Bitpulse is a world news site published in English and Turkish. It is a PaktLabs venture. Articles have no bylines.",
      ]],
      ["What we cover", [
        "Bitpulse covers news from around the world in seven sections: World, Economy, Technology, Science, Health, Culture and Sports.",
      ]],
      ["Impartiality", [
        "Bitpulse takes no side. Claims are attributed to the people who made them, and when sides disagree, each side's position is reported.",
      ]],
      ["Accuracy and sources", [
        "Every factual claim is based on a named source, and the sources are listed under each article. Primary sources come first.",
      ]],
      ["Privacy", [
        "Private individuals in stories about crime, accidents and other sensitive events are named only by their initials. Children are not named.",
      ]],
      ["Economy stories", [
        "Bitpulse does not give investment advice.",
      ]],
      ["Corrections", [
        "Mistakes are fixed openly with a dated note. The corrections page explains how to report a mistake.",
      ]],
      ["Contact", [
        `Questions about this policy can be sent to ${CONTACT_EMAIL}.`,
      ]],
    ],
  },
  tr: {
    intro: "Bitpulse'un habercilikte uyduğu ilkeler.",
    sections: [
      ["Bitpulse hakkında", [
        "Bitpulse, İngilizce ve Türkçe yayımlanan bir dünya haberleri sitesidir. Bir PaktLabs girişimidir. Haberlerde imza yoktur.",
      ]],
      ["Neleri kapsıyoruz", [
        "Bitpulse dünyadan haberleri yedi bölümde yayımlar: Dünya, Ekonomi, Teknoloji, Bilim, Sağlık, Kültür ve Spor.",
      ]],
      ["Tarafsızlık", [
        "Bitpulse taraf tutmaz. İddialar, onları dile getirenlere atfedilir. Tarafların görüş ayrılığında her tarafın görüşü aktarılır.",
      ]],
      ["Doğruluk ve kaynaklar", [
        "Her bilgi adı belli bir kaynağa dayanır ve kaynaklar her haberin altında listelenir. Öncelik birincil kaynaklardadır.",
      ]],
      ["Kişilerin gizliliği", [
        "Suç, kaza ve benzeri hassas olaylarla ilgili haberlerde sıradan kişilerin yalnızca baş harfleri yazılır. Çocukların adı verilmez.",
      ]],
      ["Ekonomi haberleri", [
        "Bitpulse yatırım tavsiyesi vermez.",
      ]],
      ["Düzeltmeler", [
        "Hatalar tarihli bir notla açıkça düzeltilir. Bir hatanın nasıl bildirileceği Düzeltmeler sayfasında anlatılır.",
      ]],
      ["İletişim", [
        `Bu ilkelerle ilgili sorular ${CONTACT_EMAIL} adresine gönderilebilir.`,
      ]],
    ],
  },
} as const;

export function EditorialPolicy() {
  const lang = useLang();
  const t = ui[lang];
  const copy = POLICY[lang];
  return (
    <Layout title={t.editorialPolicy} description={copy.intro}>
      <div className="container">
        <div className="page-head">
          <p className="meta"><b>Bitpulse</b></p>
          <h1 className="head-1">{t.editorialPolicy}</h1>
          <p className="summary">{copy.intro}</p>
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
                ...paragraphs.map((paragraph) => <p key={paragraph}>{paragraph}</p>),
              ])}
              <p><a href={`/${lang}/corrections/`}>{t.corrections}</a></p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}

// --- Corrections ---

const CORRECTIONS = {
  en: {
    intro: "How to report a mistake in a Bitpulse article, and the stories that have been corrected.",
    reportTitle: "Report a mistake",
    report: [
      `Email ${CONTACT_EMAIL} with the name of the article and what is wrong. A link to a source that shows the correct fact helps.`,
      "Messages may be reviewed and assessed by artificial intelligence tools, so please do not send personal data that is not needed.",
    ],
    handlingTitle: "What happens next",
    handling: [
      "A confirmed mistake is fixed openly. The article shows a dated correction note that says what was wrong, and the article's updated date changes. Facts are never changed silently.",
      "The page for each language lists the stories that carry a dated correction.",
    ],
    listTitle: "Corrected stories",
    empty: "No story has carried a dated correction so far. Corrected stories will be listed here with the date of the correction.",
    corrected: "Corrected",
    published: "Published",
  },
  tr: {
    intro: "Bitpulse haberlerindeki bir hatanın nasıl bildirileceği ve düzeltilen haberler.",
    reportTitle: "Hata bildirin",
    report: [
      `${CONTACT_EMAIL} adresine haberin adını ve neyin yanlış olduğunu yazın. Doğru bilgiyi gösteren bir kaynağın bağlantısı işi kolaylaştırır.`,
      "Mesajlar yapay zekâ araçları tarafından incelenebilir, değerlendirilebilir. Bu yüzden gerekli olmayan kişisel bilgileri göndermeyin.",
    ],
    handlingTitle: "Sonra ne olur",
    handling: [
      "Doğrulanan hata açıkça düzeltilir. Haberde neyin yanlış olduğunu söyleyen tarihli bir düzeltme notu görünür ve haberin güncellenme tarihi değişir. Olgular sessizce değiştirilmez.",
      "Her dilin sayfasında, tarihli düzeltme taşıyan haberler listelenir.",
    ],
    listTitle: "Düzeltilen haberler",
    empty: "Şimdiye kadar tarihli düzeltme taşıyan haber olmadı. Düzeltilen haberler düzeltme tarihiyle burada listelenecek.",
    corrected: "Düzeltme",
    published: "Yayın",
  },
} as const;

export function Corrections() {
  const lang = useLang();
  const t = ui[lang];
  const copy = CORRECTIONS[lang];
  const corrected = correctedStories();
  return (
    <Layout title={t.corrections} description={copy.intro}>
      <div className="container">
        <div className="page-head">
          <p className="meta"><b>Bitpulse</b></p>
          <h1 className="head-1">{t.corrections}</h1>
          <p className="summary">{copy.intro}</p>
        </div>
        <div className="grid info-page">
          <aside className="info-page__side">
            <nav aria-label={t.onThisPage}>
              <ul>
                <li><a href="#report">{copy.reportTitle}</a></li>
                <li><a href="#next">{copy.handlingTitle}</a></li>
                <li><a href="#list">{copy.listTitle}</a></li>
                <li><a href={`/${lang}/editorial-policy/`}>{t.editorialPolicy}</a></li>
              </ul>
            </nav>
          </aside>
          <div className="info-page__main">
            <div className="prose prose--narrow">
              <h2 id="report">{copy.reportTitle}</h2>
              <p>{copy.report[0].split(CONTACT_EMAIL)[0]}<a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>{copy.report[0].split(CONTACT_EMAIL)[1]}</p>
              <p>{copy.report[1]}</p>
              <h2 id="next">{copy.handlingTitle}</h2>
              {copy.handling.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
              <h2 id="list">{copy.listTitle}</h2>
              {corrected.length === 0 ? (
                <p data-corrections-empty>{copy.empty}</p>
              ) : (
                <ul data-corrections>
                  {corrected.map((story) => (
                    <li key={story.key}>
                      <a href={storyPath(story, lang)}>{story.versions[lang].title}</a>{" "}
                      {copy.corrected}: <time dateTime={story.corrected}>{formatDate(story.corrected as string, lang, "long")}</time>.{" "}
                      {copy.published}: <time dateTime={story.date}>{formatDate(story.date, lang, "long")}</time>.
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
