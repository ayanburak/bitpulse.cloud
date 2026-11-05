/**
 * file: src/pages/Policy.tsx
 * importable: EditorialPolicy, Corrections
 *
 * description: The editorial policy page and the corrections page in both languages.
 */

// NOTE: The policy text summarizes docs/editorial-policy.md and the files under agents. When
// either changes, this text has to change with it.

import { correctedStories, storyPath } from "../catalog";
import { CONTACT_EMAIL } from "../config";
import { Layout, useLang } from "../components/Layout";
import { formatDate, ui } from "../i18n";

// --- Editorial policy ---

const POLICY = {
  en: {
    intro: "How Bitpulse chooses, writes, checks and corrects its stories, and who is behind them.",
    sections: [
      ["Who is behind Bitpulse", [
        "Bitpulse is a PaktLabs venture. PaktLabs approves changes to the design, the site code and the rules. Articles have no bylines, and the site has no author pages and names no individual authors.",
      ]],
      ["What Bitpulse covers", [
        "Bitpulse explains technology, science, games and culture to curious general readers, in five categories: Economy, Technology, Science, Games and Culture. Explainers answer lasting questions under the same rules.",
        "Politics, foreign policy, sports and similar high risk topics are not covered. The target is three or four stories a week, and a weak story is not published to fill a gap.",
      ]],
      ["Sources", [
        "Every factual claim, including background facts, can be traced to a named source, and the sources are shown with the article. Primary sources such as official announcements, company filings and research papers are preferred. A claim from a single weak source is not reported as fact.",
        "A source counts only if its page was opened and read, and anything attributed to a person or a publication must appear on the cited page. Text is written from the facts and is not copied from the sources.",
      ]],
      ["How a story is checked", [
        "Every story passes four separate steps before publication: writing, fact checking, editing and a final check.",
        "In the writing step, the story is chosen and researched, every source is opened and both language versions are written. The fact check reads the finished story without knowing how it was written and opens every source again, comparing each claim with its page. A claim the source does not support goes back to writing.",
        "The editing step reads the story as a general reader would and checks the headline, the pace, the plain language and the difference from recent stories. The final check is the last step. It opens the sources behind the headline, the summary and the main figures, checks again for newer reports when the story covers a recent event, and decides whether the story is published at all. A story is never approved by the step that wrote it.",
      ]],
      ["Economy stories", [
        "Economy stories report what happened. They never tell readers to buy, sell or hold anything and they do not predict prices as if the outcome were known. Bitpulse does not give investment advice.",
      ]],
      ["Images", [
        "Every story has an image, with its source and license shown next to it. An image is used only when its license clearly allows the use. A general image about the topic is described honestly and is never presented as part of an event it was not part of.",
      ]],
      ["Languages", [
        "Each story is published in English and Turkish with the same facts and the same sources. Each version is written to read naturally and is not a word for word translation.",
      ]],
      ["Corrections", [
        "Mistakes are fixed openly. A corrected article shows a dated correction note that says what was wrong, and facts are never changed silently. The corrections page explains how to report a mistake and lists corrected stories.",
      ]],
      ["Rules and contact", [
        "These rules are public in the project's source code repository, together with the records of how the site is run.",
        `Questions about this policy can be sent to ${CONTACT_EMAIL}.`,
      ]],
    ],
  },
  tr: {
    intro: "Bitpulse haberleri nasıl seçer, yazar, doğrular ve düzeltir; arkasında kimler var.",
    sections: [
      ["Bitpulse'un arkasında kim var", [
        "Bitpulse bir PaktLabs girişimidir. PaktLabs tasarım, site kodu ve kurallardaki değişiklikleri onaylar. Haberlerde imza yoktur, sitede yazar sayfası bulunmaz ve kişi adı verilmez.",
      ]],
      ["Bitpulse neleri kapsıyor", [
        "Bitpulse teknoloji, bilim, oyun ve kültürü meraklı okurlara anlatır. Beş kategori vardır: Ekonomi, Teknoloji, Bilim, Oyun ve Kültür. Merak yazıları kalıcı soruları aynı kurallarla yanıtlar.",
        "Siyaset, dış politika, spor ve benzeri riskli konular kapsam dışıdır. Hedef haftada üç dört haberdir ve boşluk dolsun diye zayıf bir haber yayımlanmaz.",
      ]],
      ["Kaynaklar", [
        "Arka plan bilgileri dahil her bilgi adı belli bir kaynağa dayanır ve kaynaklar haberle birlikte gösterilir. Resmi duyurular, şirket bildirimleri ve araştırma makaleleri gibi birincil kaynaklar tercih edilir. Tek ve zayıf bir kaynağa dayanan iddia kesin bilgi olarak aktarılmaz.",
        "Bir kaynak ancak sayfası açılıp okunmuşsa sayılır; bir kişiye ya da yayına atfedilen her söz anılan sayfada bulunmalıdır. Metinler olgulardan yazılır, kaynaklardan kopyalanmaz.",
      ]],
      ["Bir haber nasıl denetlenir", [
        "Her haber yayından önce dört ayrı adımdan geçer: yazım, doğrulama, editörlük ve son denetim.",
        "Yazım adımında haber seçilir ve araştırılır, kullanılan her kaynak açılır ve iki dil sürümü yazılır. Doğrulama adımı bitmiş haberi nasıl yazıldığını bilmeden okur, her kaynağı yeniden açar ve her bilgiyi kaynak sayfasıyla karşılaştırır. Kaynağın desteklemediği bilgi yazıma geri döner.",
        "Editörlük adımı haberi sıradan bir okur gibi okur; başlığı, temposunu, sade dili ve son haberlerden farkını denetler. Son denetim son adımdır: başlığın, özetin ve ana rakamların dayandığı kaynakları açar, haber yakın zamanlı bir olayı anlatıyorsa daha yeni haber olup olmadığını yeniden arar ve haberin yayımlanıp yayımlanmayacağına karar verir. Bir haber, onu yazan adım tarafından onaylanmaz.",
      ]],
      ["Ekonomi haberleri", [
        "Ekonomi haberleri olanı aktarır. Okura hiçbir zaman bir şeyi alması, satması ya da tutması gerektiğini söylemez, sonucu bilinirmiş gibi fiyat tahmini yapmaz. Bitpulse yatırım tavsiyesi vermez.",
      ]],
      ["Görseller", [
        "Her haberin bir görseli vardır ve kaynağı ile lisansı yanında gösterilir. Görsel yalnızca lisansı kullanıma açıkça izin veriyorsa kullanılır. Konuyla ilgili genel bir görsel dürüstçe tanımlanır ve içinde olmadığı bir olayın parçasıymış gibi sunulmaz.",
      ]],
      ["Diller", [
        "Her haber İngilizce ve Türkçe olarak, aynı olgular ve aynı kaynaklarla yayımlanır. Her sürüm doğal okunacak biçimde yazılır, kelimesi kelimesine çeviri değildir.",
      ]],
      ["Düzeltmeler", [
        "Hatalar açıkça düzeltilir. Düzeltilen haberde neyin yanlış olduğunu söyleyen tarihli bir düzeltme notu bulunur ve olgular sessizce değiştirilmez. Düzeltmeler sayfası hatanın nasıl bildirileceğini anlatır ve düzeltilen haberleri listeler.",
      ]],
      ["Kurallar ve iletişim", [
        "Bu kurallar, sitenin nasıl işletildiğine dair kayıtlarla birlikte projenin herkese açık kaynak kod deposundadır.",
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
                      {copy.corrected}: <time dateTime={story.updated}>{formatDate(story.updated as string, lang, "long")}</time>.{" "}
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
