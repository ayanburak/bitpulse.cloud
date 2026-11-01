# Advertising

This document records the advertising decisions for Bitpulse and the AdSense notes collected so far. Advertising is not active. The application will be made after the site has been live with real content for a reasonable period, and the owner holds the account because it requires a real person.

The notes were compiled from Google's help pages, and the date of those pages could not be confirmed. They are checked against current sources before the application.

## Decisions

The advertising product is AdSense. Automatic ads stay off.

The home page has no ads and does not load ad code. It is also added to the AdSense page exclusions.

Ads appear only on article and long read pages, and there are few of them. All units have a fixed size.

| Page | Screen | Units |
|---|---|---|
| Article | Desktop | One 728×90 inside the text and one 300×250 in the side column |
| Long read | Desktop | One 728×90 inside the text |
| Article and long read | Mobile | One 300×250 inside the text |

The side column unit is shown on screens of 1400 pixels and wider, and its code is not loaded on narrower screens.

Ad space is reserved in advance with min-height. A box that receives no ad stays empty and is not hidden, so the page does not shift. Ad boxes stay switched off in the site code until the account is approved.

Similar sized display ads stays on and is turned off if it breaks the layout. Ad size optimization is checked when mobile ads start and is turned off if it enlarges the box.

The ad label is Reklam on Turkish pages and Advertisements on English pages. The Turkish label is an open question, listed at the end of this document.

Blocked ad categories have not been decided.

## Product and approval

AdSense is the publisher product and Google Ads is the advertiser product. Ad Manager is mainly for large publishers with a direct sales team. AdSense can also be offered through Ad Manager, so a later move is possible.

The approval conditions are original and quality content, the ability to attract an audience, a minimum age of eighteen, compliance with the policies and access to the HTML source of the site.

No minimum traffic or content threshold written by Google was found, but ads are forbidden on screens with low value content.

Turkish is a supported language. Ad code cannot be placed on pages with content in an unsupported language.

## Unit types and appearance

The position of an ad is the place where its code is put.

In a fixed size unit, the publisher sets the width and the height, and the unit does not adapt to screen changes. The sizes 728×90 and 300×250 are within the rules.

A fixed unit can still show another size. Similar sized display ads swaps in an ad of a similar size, fits it inside the unit and shows it horizontally centered at the top. Google's example is a 468×60 ad in a 320×50 unit. What fills the remaining space is not stated.

Similar sized display ads is turned off at Brand safety, Content, Blocking controls, Manage Ad serving. Google says that turning it off can reduce performance and gives no figure.

Ad size optimization adjusts the unit size automatically on mobile. Whether it enlarges the box is not stated. It is turned off at Ads, Global settings, Let Google optimize the size of your mobile ads.

The size of a responsive unit changes with the page and the device, and it can be limited per breakpoint with CSS. Setting the size in an external style sheet is not officially supported.

Responsive code inside a parent box with no explicit width gives the error No slot size for availableWidth=0.

If an ad cannot be filled, the unit usually keeps its size and stays empty. It is collapsed only if that causes no reflow on the page.

An empty unit can be hidden with the CSS selector below. The Fill empty in-page ads setting can place contextual suggestions in empty areas.

```css
ins.adsbygoogle[data-ad-status="unfilled"]
```

The Creative sizes report in AdSense shows which sizes were really served.

## Automatic ads

When Auto ads is on, Google chooses the positions itself on pages that contain the code.

The formats are anchor ads that stick to the screen, full screen vignettes between pages, side rails on wide screens, in-page banners and Multiplex, and ad intent links, anchors and chips inside the text.

Auto ads is turned off with the main switch, and the formats can also be turned off one by one.

Page exclusion is found under Page exclusions. This page only is an exact address match. Addresses with fragments or parameters are not supported, and the change can take up to an hour to apply.

Excluded areas apply only to in-page automatic ads and do not block formats such as anchors.

When Existing ads is on, Auto ads can also optimize units placed by hand.

## Ad content and blocking

The design of a display ad belongs to the advertiser, and the publisher cannot change its color or typeface. Native formats allow limited styling.

Ad images can clash with the single color design of the site, and no setting was found that prevents this.

Blocking controls allow blocking by category, by advertiser and by individual ad. The source notes for this item are cut off, so it is checked again before use.

Google does not guarantee that classification catches every ad, and it recommends blocking little.

Ad review center is used to block and report individual ads.

## Policy and layout

Google states that it accepts only Advertisements and Sponsored Links as ad labels. No official approval or rejection of the Turkish word Reklam was found.

An ad cannot be presented as content or a menu and cannot be placed under a misleading heading.

Layouts that encourage clicks, arrow marks and attention grabbing animation are forbidden.

An ad cannot sit directly next to navigation or action elements, cannot cover content and cannot push content off the screen.

No official pixel distance from news text was found. No specific policy on striped placeholders was found.

Google's code modification policy generally advises against hiding a unit with display:none, while its own page gives a CSS example for unfilled units.

The only guaranteed way to prevent layout shift is to reserve the ad space with CSS, using min-height and min-width. That guidance is written for Google Publisher Tag, and applying the same principle to AdSense is an inference.

The Cumulative Layout Shift target is below 0.1 at the 75th percentile.

## Open questions

These points could not be confirmed.

- Whether the Turkish label Reklam is accepted.
- Whether AdSense has conditions specific to Turkey.
- Whether page exclusion covers anchor and vignette ads.
- Which sizes will really be served in fixed 728×90 and 300×250 units.
- Whether the AdSense crawler sees content added with JavaScript.
- How current Google policy treats content written by artificial intelligence.
- Whether a consent tool is required for readers in Europe, and what it means for the privacy page.
