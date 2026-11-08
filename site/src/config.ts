/**
 * file: src/config.ts
 * importable: SITE_URL, CONTACT_EMAIL, REPO_URL, PUBLISHER_URL, X_HANDLE, SOCIAL_URLS, ADS_ENABLED, IMAGE_WIDTHS
 *
 * description: Fixed site settings shared by pages, the build and tests.
 */

export const SITE_URL = "https://bitpulse.cloud";
export const CONTACT_EMAIL = "info@paktlabs.com";
export const REPO_URL = "https://github.com/ayanburak/bitpulse.cloud";
export const PUBLISHER_URL = "https://paktlabs.com";

// The owner posts every news story on these accounts. The footer links to them and the home page
// names them in its structured data, so search engines can tie the accounts to the site.
export const X_HANDLE = "bitpulsecloud";
export const SOCIAL_URLS = { X: `https://x.com/${X_HANDLE}`, Instagram: "https://www.instagram.com/bitpulsecloud/" };

// Stays false until the advertising account is approved, so no empty ad box reaches a reader.
export const ADS_ENABLED = false;

// The build writes one copy of every story image per width, and browsers pick the closest one.
export const IMAGE_WIDTHS = [640, 1280, 2000];
