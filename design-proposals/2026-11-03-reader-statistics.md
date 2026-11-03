# Proposal: more detailed reader statistics for Bitpulse

Status: open, waiting for review. The crawler part of option A was done on the server on 2026-11-03, and the published days were recalculated.

Branch: none yet. This is a decision proposal. The request was to compare the ways of measuring before anything is built, and the banner's design depends on which consent tool is chosen (see Fit with the AdSense consent tool). Once an option is chosen, the banner, the script and the privacy page change are prepared on proposal/reader-statistics and proposed with screenshots of the current and proposed pages, as the design process requires.

## The reason

The statistics published today can not show reach. They count some crawlers as readers, can not tell one reader from another and say nothing about how far a story is read. More detailed reader statistics were requested, with a cookie notice at the bottom of the page for first time visitors, accept and decline choices, and measurement that starts only after a reader accepts. This proposal compares how that is normally done with ways of measuring that set no cookies. Items marked (unconfirmed) could not be verified from a primary source that was opened.

## What the research found

- Consent for storing or reading information on a reader's device is the normal rule for analytics cookies in the EU. The French regulator CNIL exempts audience measurement only under strict conditions: notice, an objection option, measurement only, no cross-site matching, one publisher, a truncated IP address and a tracker lifetime of at most 13 months. It adds that most large analytics services do not qualify.
- Cookieless does not automatically mean consent-free. No regulator page opened for this work says that a cookieless counter is exempt. Vendor claims (Plausible: no cookie banner needed; GoatCounter: "probably" safe without a notice, author not a lawyer) are not regulator positions.
- Turkey: the data protection authority (KVKK) published its cookie guide on 20 June 2022 and revised it in July 2025. The guide text itself could not be opened (the official page returned an unrelated PDF). Law firm summaries say that only strictly necessary cookies are exempt, that analytics and advertising cookies need explicit consent, that continued browsing is not consent, that pre-ticked boxes are invalid and that consent must be provable. Whether first-party analytics has an exemption is unclear (section 5.9 of the guide, unconfirmed).
- CNIL: refusing must be as easy as accepting, consent must be as easy to withdraw as to give, nothing may be read or written on the device before consent, and scrolling is not consent. Google's EU user consent policy additionally requires records of consent and clear instructions for revoking it.
- Google AdSense: a certified consent tool that supports the IAB Transparency and Consent Framework (TCF) is required for personalized ads in the EEA and UK (since 16 January 2024) and Switzerland (since 31 July 2024). Without it only non-personalized or limited ads are eligible. Google's CMP is offered in AdSense under Privacy & messaging. A self-built dialog is allowed, but it is not a certified tool.
- Google Analytics 4 Consent Mode: if tags are blocked until consent (basic mode), decliners produce no data and no modeling. Advanced mode loads Google tags before a choice and sends cookieless pings, which would break the rule that no measuring code runs before a choice. Using TCF-based consent also prevents modeling.

## Options compared

| Option | Measures | Consent needed | Tool and account | Account holder | How agents read results | Cost |
|---|---|---|---|---|---|---|
| A. Better log job (bot list, only count requests that look like real page loads) | Views, pages, referrers, fewer crawlers | No new processing; logs already exist | None (server job) | Owner (server) | Existing /stats JSON | Free |
| B. Search Console | Impressions, clicks, queries, pages, countries, devices in Google Search | None for readers (Google collects it) | Google Search Console, verified by DNS record or an HTML file or meta tag | Owner's Google account | API needs OAuth, so agents cannot read it without a token; owner exports numbers, or a server job publishes aggregates | Free |
| C. Own first-party beacon on the owner's server, shown after Accept | Views by real JavaScript load, time on page, scroll depth, returning visits (only with a consent-only cookie) | Yes (reads and may store on the device); gated by the banner | Code in this repository plus a small endpoint on the server | Owner (server) | Aggregates added to the existing /stats JSON, no credentials | Free, plus server work |
| D. Cookieless counter: GoatCounter, Umami (self-hosted) | Views, referrers, browsers, screen size, country; no cookie or storage (GoatCounter; Umami says no cookies). Time on page and scroll: unconfirmed | Not settled; vendors say probably not, no regulator source found | Own server, or goatcounter.com (free for reasonable public use) | Owner | API with a token (GoatCounter: bearer key; Umami: login). Public dashboard unconfirmed. A server job could publish aggregates | Free self-hosted |
| E. Plausible or Fathom (hosted) | Views, referrers, devices, country; cookieless, no raw IP stored (Plausible). Time on page: unconfirmed | Vendor says no banner needed; not a regulator position | Paid account. Plausible: $9, $14 or $19 a month, API only on the $19 plan, shared links from $14, EU data. Fathom: from $15 a month, API on all plans, data location unconfirmed | Owner (billing) | Stats API needs a key held outside the repository, again via a server job | $9 to $19 and up |
| F. Cloudflare Web Analytics | Page views, visitors, load speed and Core Web Vitals; works without moving DNS | Cookie behaviour not confirmed | Cloudflare account and a script | Owner | Needs the account; GraphQL API (token) | Free |
| G. Google Analytics 4 with Consent Mode | Users, sessions, engagement, audiences (feature list unconfirmed) | Yes; data goes to Google, so Turkish cross-border transfer rules also apply | Google Analytics property | Owner's Google account | API needs OAuth tokens | Free |

## Recommendation

1. Now, without any banner: fix the log job (option A) and verify Search Console (option B). These answer the open question of how many real readers there are and which language earns search impressions, and they need no consent from readers.
2. Then, if the owner wants depth (time on page, scroll, returning readers): build option C, shown only after Accept. It needs no third-party account, keeps data on the owner's server, and agents continue to read only published aggregate JSON. Readers who decline are still counted by option A.
3. Not recommended: Google Analytics 4 (data leaves the owner's control, extra transfer rules, credentials for agents, and advanced mode conflicts with the no-code-before-choice rule). Ready-made cookieless tools (D, E) are fallbacks if building is not wanted. They could run without a banner, but the request was for opt-in measurement, so they would be loaded only after Accept like option C.

Reasons: the owner's rule (nothing before a choice) is met cleanly by a consent-gated first-party script; accounts held by the owner stay few; secrets stay off agents. The cost is that depth metrics cover only readers who accept. The opt-in rate is unknown and will not represent all readers.

## Banner behavior if chosen

- A bar at the bottom of the page, shown only on a first visit, in the page language.
- Two buttons of the same size, style and weight, "Accept" and "Decline" (Turkish: "Kabul et", "Reddet"). Nothing pre-selected, no pre-ticked boxes, no closing mark that counts as consent, no scroll or continued-browsing consent. Reading and navigation work without a choice.
- Before a choice no measuring code is loaded or run. After Decline it never loads.
- The choice is stored in a small first-party cookie (for example bp_consent), described on the privacy page. Storing the choice itself is generally treated as strictly necessary (law firm sources, unconfirmed against the KVKK guide). A footer link "Cookie settings" reopens the choice, and changing it takes one click. Withdrawal removes the measuring cookie and stops the script.
- The banner is a visible design change, so it goes through the design proposal process. Server and account work waits for the owner.

## Fit with the AdSense consent tool

docs/advertising.md says Google requires a certified consent tool for personalized ads in the EEA, UK and Switzerland, offered under Privacy & messaging. A site-built banner would not be certified, and two banners would annoy readers and invite inconsistent choices. Preferred path: use the Google CMP as the only banner, configured for the regions required, and load the first-party beacon only when that tool reports consent for measurement. Whether Google's CMP can gate a non-Google script, and whether it can show the same banner in Turkey, where its EEA message does not apply, was not confirmed. If it cannot, the choice is a certified third-party CMP that can, or a site-built banner for readers outside the EEA, UK and Switzerland with Google's tool only inside them. This must be settled before building. If AdSense is never approved, the site-built banner alone is enough.

## Privacy page text needed (English)

The privacy page now says that Bitpulse "runs no analytics scripts of its own". If option C is chosen, that sentence is replaced and the page gains the text below, written in the page's existing voice. The Turkish page gets the same content.

> **Information collected.** Bitpulse has no accounts, forms or newsletter. The server keeps technical access logs, and they are turned into daily totals that contain no IP addresses. If a reader presses Accept in the notice at the bottom of the page, a small script that belongs to the site also records which page was read, how long the reader stayed, how far the page was scrolled and whether the browser has visited before. It sends this only to the site's own server, uses no third party and is not combined with other data. After Decline, or before any choice, the script does not run. The choice can be changed at any time through Cookie settings in the footer.
>
> **Cookies.** bp_lang stores the chosen language for one year. bp_consent stores the reader's choice for [period to be decided]. bp_visit is set only after Accept, holds a random number used to recognise a returning browser for [period] and is deleted when consent is withdrawn.
>
> **Legal basis.** Measurement after Accept rests on the reader's consent, which can be withdrawn at any time without affecting earlier processing. Log statistics rest on the legitimate interest in keeping the site secure and understanding how it is used.
>
> **Retention and rights.** Records of choices and measurement data are kept for [period]. Questions and requests about personal data can be sent to info@paktlabs.com. Readers can also complain to their data protection authority, which in Turkey is the Personal Data Protection Authority (KVKK).

The current page also says the aggregated statistics are published in the project's public repository, while they are published at bitpulse.cloud/stats and are not in this repository. The same change should correct that sentence. The Turkish page needs the same text. Legal review of the wording is advisable (not confirmed by any lawyer).

## Work that needs the owner

These are also listed under Waiting for the owner in HANDOFF.md.

- Decide between the steps above and whether depth statistics are wanted at all.
- Server: update the log job (bot list, only count page loads), deploy a beacon endpoint and its aggregation, and publish results in /stats. Agents do not connect to the server.
- Verify the site in Google Search Console with the owner's Google account (DNS TXT record or a file placed in the repository's public folder) and share numbers or approve a server job that publishes them.
- In AdSense, set up Privacy & messaging, or pick a certified CMP, and report back which one and whether it covers Turkey.
- Choose the retention periods for the privacy text and approve it, ideally after legal review.
- Approve the banner through the design proposal process.
- Tokens or API keys for any tool stay on the server and out of the repository.

## Sources opened

- https://www.cnil.fr/en/sheet-ndeg16-use-analytics-your-websites-and-applications
- https://www.cnil.fr/en/dark-patterns-cookie-banners-cnil-issues-formal-notice-website-publishers
- https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-052020-consent-under-regulation-2016679_en (landing page only; PDF returned 404)
- https://kvkk.gov.tr/Icerik/7353/Cerez-Uygulamalari-Hakkinda-Rehber (guide itself not readable); secondary: https://www.erdem-erdem.av.tr/bilgi-bankasi/kisisel-verileri-koruma-kurumu-cerez-uygulamalari-hakkinda-rehberi-guncelledi and web search summaries of law firm sites
- https://support.google.com/adsense/answer/13554116?hl=en
- https://support.google.com/adsense/answer/7670013
- https://www.google.com/about/company/user-consent-policy/
- https://support.google.com/analytics/answer/9976101
- https://support.google.com/webmasters/answer/9008080
- https://support.google.com/webmasters/answer/7576553
- https://developers.google.com/webmaster-tools/v1/how-tos/authorizing
- https://plausible.io/data-policy, https://plausible.io/#pricing, https://plausible.io/docs/stats-api
- https://www.goatcounter.com/help/privacy, /help/gdpr, /help/api, /#pricing
- https://docs.umami.is/docs/faq, https://docs.umami.is/docs/api
- https://usefathom.com/pricing
- https://developers.cloudflare.com/web-analytics/about/, /data-metrics/, /data-metrics/data-origin-and-collection/, /faq/

Not opened or failed: EUR-Lex ePrivacy Directive Article 5(3), CNIL's guidelines page, GoatCounter and Umami public dashboard settings, Plausible/Fathom time-on-page features, GA4 feature and API pages, Google CMP support for non-Google scripts.
