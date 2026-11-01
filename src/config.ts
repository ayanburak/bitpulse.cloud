/**
 * file: src/config.ts
 * importable: SITE_URL, CONTACT_EMAIL, REPO_URL, PUBLISHER_URL, ADS_ENABLED, IMAGE_WIDTHS
 *
 * description: Fixed site settings shared by pages, the build and tests.
 */

export const SITE_URL = "https://bitpulse.cloud";
export const CONTACT_EMAIL = "info@paktlabs.com";
export const REPO_URL = "https://github.com/ayanburak/bitpulse.cloud";
export const PUBLISHER_URL = "https://paktlabs.com";

// Stays false until the advertising account is approved, so no empty ad box reaches a reader.
export const ADS_ENABLED = false;

// The build writes one copy of every story image per width, and browsers pick the closest one.
export const IMAGE_WIDTHS = [640, 1280, 2000];
