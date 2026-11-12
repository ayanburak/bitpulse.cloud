/**
 * file: src/i18n.ts
 * importable: Lang, langs, otherLang, isLang, ui, categoryNames, categoryIntros, formatDate
 *
 * description: Interface text and date formatting for both site languages.
 */

export const langs = ["en", "tr"] as const;
export type Lang = (typeof langs)[number];

export function isLang(value: string | undefined): value is Lang {
  return value === "en" || value === "tr";
}

export function otherLang(lang: Lang): Lang {
  return lang === "en" ? "tr" : "en";
}

// --- Text ---

export const ui = {
  en: {
    skip: "Skip to content",
    home: "Bitpulse home",
    language: "Language",
    mainMenu: "Main menu",
    topStories: "Top stories",
    archive: "Archive",
    search: "Search",
    darkTheme: "Switch to dark theme",
    lightTheme: "Switch to light theme",
    latest: "Latest stories",
    last30: "Last 30 days",
    all: "All",
    explained: "Explained",
    explainedIntro: "Plain, sourced answers to the questions people wonder about.",
    readStory: "Read the story",
    breadcrumb: "Breadcrumb",
    minRead: (n: number) => `${n} min read`,
    minutes: (n: number) => `${n} min`,
    copyLink: "Copy link",
    updated: "Updated",
    updates: "Updates",
    inThisStory: "In this story",
    contents: "Contents",
    sources: "Sources",
    related: "Related",
    nextStories: "Next stories",
    moreExplained: "More from Explained",
    photo: "Photo",
    license: "License",
    imageSource: "Source",
    noStories: "No stories have been published in this category yet.",
    months: "Months",
    prevMonth: "Previous month",
    nextMonth: "Next month",
    calendarNote: "Underlined days have published stories.",
    monthStories: (label: string) => `${label} stories`,
    searchTerm: "Search term",
    searchPlaceholder: "Search Bitpulse",
    noResults: "No results found",
    noResultsHint: "Try another word.",
    site: "Site",
    categories: "Categories",
    moreCategories: "More categories",
    about: "About",
    contact: "Contact",
    privacy: "Privacy",
    editorialPolicy: "Editorial policy",
    corrections: "Corrections",
    footerNote: "A world news site. A PaktLabs venture.",
    onThisPage: "On this page",
    notFoundTitle: "Page not found",
    notFoundText: "The page may have moved or may never have been published.",
    backHome: "Back to top stories",
    searchSite: "Search the site",
    advertisements: "Advertisements",
    homeTitle: "Bitpulse | The World, Beat by Beat",
    metaDescription: "Follow the world beat by beat: world news, economy, technology, science, health, culture and sports, with every claim sourced.",
  },
  tr: {
    skip: "İçeriğe geç",
    home: "Bitpulse ana sayfa",
    language: "Dil seçimi",
    mainMenu: "Ana menü",
    topStories: "Manşet",
    archive: "Arşiv",
    search: "Ara",
    darkTheme: "Koyu temaya geç",
    lightTheme: "Açık temaya geç",
    latest: "Son haberler",
    last30: "Son 30 gün",
    all: "Tümü",
    explained: "Merak",
    explainedIntro: "Merak edilen soruların sade ve kaynaklı yanıtları.",
    readStory: "Yazıyı oku",
    breadcrumb: "Konum",
    minRead: (n: number) => `${n} dakikalık okuma`,
    minutes: (n: number) => `${n} dk`,
    copyLink: "Bağlantıyı kopyala",
    updated: "Güncellendi",
    updates: "Güncellemeler",
    inThisStory: "Bu haberde",
    contents: "İçindekiler",
    sources: "Kaynaklar",
    related: "Bununla ilgili",
    nextStories: "Sonraki haberler",
    moreExplained: "Merak'tan daha fazlası",
    photo: "Fotoğraf",
    license: "Lisans",
    imageSource: "Kaynak",
    noStories: "Bu kategoride henüz haber yayımlanmadı.",
    months: "Aylar",
    prevMonth: "Önceki ay",
    nextMonth: "Sonraki ay",
    calendarNote: "Alt çizgili günlerde haber yayımlandı.",
    monthStories: (label: string) => `${label} haberleri`,
    searchTerm: "Aranacak kelime",
    searchPlaceholder: "Bitpulse içinde ara",
    noResults: "Sonuç bulunamadı",
    noResultsHint: "Başka bir kelime dene.",
    site: "Site",
    categories: "Kategoriler",
    moreCategories: "Diğer kategoriler",
    about: "Künye",
    contact: "İletişim",
    privacy: "Gizlilik",
    editorialPolicy: "Yayın ilkeleri",
    corrections: "Düzeltmeler",
    footerNote: "Bir dünya haberleri sitesi. Bir PaktLabs girişimi.",
    onThisPage: "Bu sayfada",
    notFoundTitle: "Bu sayfa bulunamadı",
    notFoundText: "Aradığın sayfa taşınmış ya da hiç yayımlanmamış olabilir.",
    backHome: "Manşete dön",
    searchSite: "Sitede ara",
    advertisements: "Reklam",
    homeTitle: "Bitpulse | Dünya, An Be An",
    metaDescription: "Dünyayı an be an izle: dünya, ekonomi, teknoloji, bilim, sağlık, kültür ve spor haberleri, her bilginin kaynağıyla.",
  },
};

export const categoryNames = {
  en: { world: "World", economy: "Economy", technology: "Technology", science: "Science", health: "Health", culture: "Culture", sports: "Sports" },
  tr: { world: "Dünya", economy: "Ekonomi", technology: "Teknoloji", science: "Bilim", health: "Sağlık", culture: "Kültür", sports: "Spor" },
};

export const categoryIntros = {
  en: {
    world: "Politics, diplomacy and events from around the world.",
    economy: "Companies, markets and the wider economy.",
    technology: "Artificial intelligence, devices, chips and the internet.",
    science: "Space, nature and discoveries.",
    health: "Medicine, diseases and public health.",
    culture: "Film, television, music, books and games.",
    sports: "Competitions, results and athletes.",
  },
  tr: {
    world: "Dünyadan siyaset, diplomasi ve gelişmeler.",
    economy: "Şirketler, piyasalar ve genel ekonomi.",
    technology: "Yapay zekâ, cihazlar, çipler ve internet.",
    science: "Uzay, doğa ve keşifler.",
    health: "Tıp, hastalıklar ve halk sağlığı.",
    culture: "Sinema, dizi, müzik, kitap ve oyun.",
    sports: "Müsabakalar, sonuçlar ve sporcular.",
  },
};

// --- Dates ---

const LOCALES = { en: "en-US", tr: "tr-TR" };

const STYLES = {
  full: { weekday: "long", day: "numeric", month: "long", year: "numeric" },
  long: { day: "numeric", month: "long", year: "numeric" },
  day: { day: "numeric", month: "long" },
  tiny: { day: "numeric", month: "short" },
  month: { month: "long", year: "numeric" },
  monthName: { month: "long" },
  weekday: { weekday: "short" },
  stamp: { day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit", hourCycle: "h23" },
  clock: { hour: "2-digit", minute: "2-digit", hourCycle: "h23" },
} satisfies Record<string, Intl.DateTimeFormatOptions>;

/**
 * Formats a date for one language.
 *
 * @param value Date object, text in the form YYYY-MM-DD or a full ISO time in UTC.
 * @param lang Language of the result.
 * @param style Name of the date style.
 * @returns The formatted date.
 */
export function formatDate(value: string | Date, lang: Lang, style: keyof typeof STYLES): string {
  // UTC keeps a date such as 2026-10-20 on the same day in every time zone of the build machine.
  const date = typeof value !== "string" ? value : new Date(value.length === 10 ? `${value}T00:00:00Z` : value);
  return new Intl.DateTimeFormat(LOCALES[lang], { ...STYLES[style], timeZone: "UTC" }).format(date);
}
