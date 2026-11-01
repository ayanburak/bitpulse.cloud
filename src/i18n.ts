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
    longRead: "Long read",
    readStory: "Read the story",
    breadcrumb: "Breadcrumb",
    minRead: (n: number) => `${n} min read`,
    minutes: (n: number) => `${n} min`,
    copyLink: "Copy link",
    inThisStory: "In this story",
    contents: "Contents",
    sources: "Sources",
    related: "Related",
    nextStories: "Next stories",
    moreLong: "More long reads",
    photo: "Photo",
    license: "License",
    imageSource: "Source",
    disclosure: "This article was written by artificial intelligence and may contain mistakes.",
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
    footerNote: "A technology and science news site run by Claude. A PaktLabs venture.",
    sourceCode: "Source code",
    onThisPage: "On this page",
    notFoundTitle: "Page not found",
    notFoundText: "The page may have moved or may never have been published.",
    backHome: "Back to top stories",
    searchSite: "Search the site",
    advertisements: "Advertisements",
    metaDescription: "Technology, science, games and culture news, run by Claude and published by PaktLabs.",
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
    longRead: "Uzun okuma",
    readStory: "Yazıyı oku",
    breadcrumb: "Konum",
    minRead: (n: number) => `${n} dakikalık okuma`,
    minutes: (n: number) => `${n} dk`,
    copyLink: "Bağlantıyı kopyala",
    inThisStory: "Bu haberde",
    contents: "İçindekiler",
    sources: "Kaynaklar",
    related: "Bununla ilgili",
    nextStories: "Sonraki haberler",
    moreLong: "Diğer uzun okumalar",
    photo: "Fotoğraf",
    license: "Lisans",
    imageSource: "Kaynak",
    disclosure: "Bu haber yapay zekâ tarafından yazılmıştır ve hata içerebilir.",
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
    footerNote: "Claude tarafından işletilen bir teknoloji ve bilim haberleri sitesi. Bir PaktLabs girişimi.",
    sourceCode: "Kaynak kod",
    onThisPage: "Bu sayfada",
    notFoundTitle: "Bu sayfa bulunamadı",
    notFoundText: "Aradığın sayfa taşınmış ya da hiç yayımlanmamış olabilir.",
    backHome: "Manşete dön",
    searchSite: "Sitede ara",
    advertisements: "Reklam",
    metaDescription: "Claude tarafından işletilen ve PaktLabs tarafından yayımlanan teknoloji, bilim, oyun ve kültür haberleri.",
  },
};

export const categoryNames = {
  en: { economy: "Economy", technology: "Technology", science: "Science", games: "Games", culture: "Culture" },
  tr: { economy: "Ekonomi", technology: "Teknoloji", science: "Bilim", games: "Oyun", culture: "Kültür" },
};

export const categoryIntros = {
  en: {
    economy: "Markets and companies shaping technology, reported without investment advice.",
    technology: "New models, chips, software and the people building them.",
    science: "Discoveries from space, the lab and the natural world.",
    games: "New releases, studios and the hardware they run on.",
    culture: "Film, television, books and fandom.",
  },
  tr: {
    economy: "Teknolojiyi şekillendiren piyasalar ve şirketler, yatırım tavsiyesi vermeden.",
    technology: "Yeni modeller, çipler, yazılımlar ve onları geliştirenler.",
    science: "Uzaydan, laboratuvardan ve doğadan gelen keşifler.",
    games: "Yeni oyunlar, stüdyolar ve onları çalıştıran donanımlar.",
    culture: "Film, dizi, kitap ve hayran kültürü.",
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
} satisfies Record<string, Intl.DateTimeFormatOptions>;

/**
 * Formats a date for one language.
 *
 * @param value Date object or text in the form YYYY-MM-DD.
 * @param lang Language of the result.
 * @param style Name of the date style.
 * @returns The formatted date.
 */
export function formatDate(value: string | Date, lang: Lang, style: keyof typeof STYLES): string {
  // UTC keeps a date such as 2026-10-20 on the same day in every time zone of the build machine.
  const date = typeof value === "string" ? new Date(`${value}T00:00:00Z`) : value;
  return new Intl.DateTimeFormat(LOCALES[lang], { ...STYLES[style], timeZone: "UTC" }).format(date);
}
