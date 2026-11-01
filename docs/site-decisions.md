# Site decisions

This document records the product, design and language decisions behind Bitpulse, together with their reasons. Editorial rules are in docs/editorial-policy.md and advertising decisions are in docs/advertising.md.

## Publisher

Bitpulse is presented as a PaktLabs venture. The footer, the About page and the Contact page say so. The public contact address is info@paktlabs.com.

## Technology

The site is built with React and Vite. Every public page is generated as static HTML at build time, so that articles and category pages are readable without running JavaScript. Pages use real addresses such as /en/category/economy/ instead of query parameters.

Search runs in the browser against an index generated at build time, so it needs no server code.

React runs only during the build. Readers receive static HTML and a small script, which keeps pages fast and leaves no client side application to load.

Each language has an RSS feed at /en/feed.xml and /tr/feed.xml with the newest stories. Feed readers find it through a link in the page head, so it adds nothing visible to a page. Story pages also carry an image for link previews and NewsArticle structured data, with the site as the author because articles have no personal bylines.

Home page sections appear only when there are enough stories to fill them. There is no most read list until real readership numbers exist, because an invented ranking would mislead readers.

## Launch scope

The newsletter form and its links are not part of the launch, because a real newsletter needs email delivery and the storage of personal data. The contact page shows an email address and has no form. A form that does not deliver data is never published with a success message.

## Design direction

The central idea is a pulse line. A thin line runs along the page and rises like a square wave under the active menu item. While a story is being read, the same rise shows reading progress.

Letter width expresses the pace of the content. News headlines use narrow Archivo, long reads use wide Archivo and body text uses Literata.

There is one color, cobalt #1430d6. Color comes from real photographs, and categories do not get their own colors.

Corners are square. There are no shadows or gradients. Small caps labels and CSS that converts letters to capitals are not used.

The logo is a square cornered letter b inside a cobalt square, next to the word bitpulse. The favicon uses the same drawing.

Long reads have a separate look on a cobalt background.

On screens up to 720 pixels wide the seven menu links do not fit one row, so they open from a button with three lines next to the language switch. The header stays at the top of the screen there, and the pulse line stays under it to show reading progress. The button is a native details element, so it works without JavaScript.

The Last 30 days section on the home page is a flat row of boxes running from left to right, and it does not use the pulse shape.

The calendar on the archive page marks only the days with published stories.

A future newsletter is a single subscription form with no plans to choose from.

Animation is limited to the sliding pulse in the menu and the line under headlines. Transitions are turned off for readers who prefer reduced motion.

Fonts are hosted with the site and their SIL Open Font License files ship next to them.

The site has a light theme and a dark theme. Light is the default for every reader, and the sun and moon button next to Search switches between them. The choice stays in the browser. Dark surfaces use a lighter tint of cobalt, because the original cobalt is too dark to read on them, and long reads keep their cobalt background in both themes.

## Languages

The site is published in Turkish and English at separate addresses, /tr/ and /en/. Each page points to its counterpart with hreflang, and the root address is marked as x-default. The TR and EN switch in the header opens the same page in the other language.

The reader's choice is stored for one year in the bp_lang cookie. Only the root address redirects. Article addresses never redirect.

The server makes the root redirect. It reads the bp_lang cookie first and the browser's Accept-Language header second. A Turkish browser goes to /tr/ and every other browser goes to /en/. The aim is to show Turkish to readers in Turkey and English to everyone else. The language header was chosen over a location lookup because it needs no location database and does not process IP addresses for this purpose.

Separate addresses were chosen because Google recommends them for language versions. Google also advises against changing content by IP address and against automatic redirects between language versions, since its crawler mostly comes from the United States and may otherwise never see the other language. A single address that switches language with a cookie was rejected for this reason.
