/**
 * file: src/components/Ads.tsx
 * importable: AdStrip, AdSide
 *
 * description: Reserved advertising boxes, rendered only when advertising is turned on.
 */

// NOTE: These boxes hold the reserved space only. The AdSense code goes inside ad__slot after the
// account is approved, and home pages never use them. docs/advertising.md has the placement rules.

import { ADS_ENABLED } from "../config";
import { ui, type Lang } from "../i18n";

export function AdStrip({ lang }: { lang: Lang }) {
  if (!ADS_ENABLED) return null;
  const label = ui[lang].advertisements;
  return (
    <aside className="ad ad--strip" aria-label={label}>
      <p>{label}</p>
      <div className="ad__slot" />
    </aside>
  );
}

export function AdSide({ lang }: { lang: Lang }) {
  if (!ADS_ENABLED) return null;
  const label = ui[lang].advertisements;
  return (
    <aside className="ad ad--side" aria-label={label}>
      <p>{label}</p>
      <div className="ad__slot" />
    </aside>
  );
}
