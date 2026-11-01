# Proposal: link previews, structured data and RSS feeds

Status: open, waiting for review.

Branch: proposal/search-and-sharing-metadata

Fingerprint of the locked files on the branch: 390105bb9ec1d7c9356fd1a225039d550f94bf9497803c65d7c652c3d40a5270

## The problem

A shared Bitpulse link has no picture. Story pages have no og:image and no twitter:card, so a link posted in a chat or on a social network shows as plain text. Pages also carry no article structured data and no max-image-preview setting, and the site has no feed.

These gaps matter most for a new site. Chartbeat's 2026 Publisher Playbook, as summarized by Relevant Audience, reports that Google Search referrals to news sites fell 40.2 percent between July 2025 and July 2026 and Discover referrals fell 34.3 percent, while direct visits and dark social, meaning links shared in private chats, grew their share of pageviews. A link that looks good when shared now counts for more, and a site with no regular readers needs every route to them. Chartbeat sells analytics tools, and it reads the search decline as an effect of AI answers, which is an interpretation and not a measured cause.

## The change

- Story pages gain og:image, og:image:alt, og:type and twitter:card with the 1280 pixel copy of the story image.
- Every page gains the robots setting max-image-preview:large, which Google lists as the way to enable large images in Discover. Google also asks for images at least 1200 pixels wide and more than 300,000 pixels in total, which the 1280 copies are expected to meet because stories use landscape images.
- Story pages gain NewsArticle structured data, or Article for long reads. Google's documentation has no required properties for this type and recommends the headline, image and dates used here. The author is the Bitpulse organization, because the editorial policy allows no personal bylines.
- Each language gains an RSS feed at /en/feed.xml and /tr/feed.xml with the latest twenty stories, linked from the page head.
- docs/site-decisions.md records the decision, and tests/feed.test.ts covers the feed and the escaping of text inside structured data.

## Effect on the design

Nothing changes on screen. The change touches the page head, the build and the feed files, and no style file or visible element. Screenshots are therefore not included, because the current and proposed pages look the same. The proposal is here because site code is locked.

## Checks

On the branch, the typecheck, the 36 unit tests, the build and the 12 browser tests pass. The feeds parse as XML, and the structured data on a built story page parses as JSON. The design-lock check fails on the branch by design until a new fingerprint is approved. No release can come from the branch, because only main releases.

## Left out

Three related ideas are left for later. A lastmod date in the sitemap would turn wrong after a correction, because stories have no field for a correction date. A Google News sitemap needs the publication name as it appears on news.google.com, so it depends on the site being listed there. A visible feed link in the footer would be a design change.

## Sources

- https://developers.google.com/search/docs/appearance/google-discover
- https://developers.google.com/search/docs/appearance/structured-data/article
- https://developers.google.com/search/docs/crawling-indexing/sitemaps/news-sitemap
- https://www.relevantaudience.com/seo/chartbeat-google-search-publisher-traffic-down-40-percent/
