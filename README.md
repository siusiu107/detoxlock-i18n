# DetoxLock language packs

This public repository contains only translation packs downloaded by DetoxLock. It does **not** contain the application source code, signing keys, API keys, or user data.

## Fully supported product languages

- `en` — English
- `ko` — 한국어 (Korean)
- `id` — Bahasa Indonesia (Indonesian)

Unsupported device/app locales fall back to English in DetoxLock. The Android protection layer is designed to prefer language-independent evidence such as package/activity names, view roles, resource IDs and exact DetoxLock-row geometry; translated Settings text is used only as a fallback.

- `manifest.json`: language versions, paths and SHA-256 hashes
- `locales/*.json.gz`: one downloadable language pack per supported locale
- `legal/html/*.ko.html`: Korean remote legal documents
- `legal/html/*.id.html`: Indonesian remote legal documents

English legal HTML is the only legal fallback bundled in the app. Korean and
Indonesian legal pages are downloaded remotely and safely fall back to English if
the remote document is unavailable.

The app verifies every downloaded pack against the SHA-256 value in the manifest and keeps the last valid local copy for offline use.

Language packs are gzip-compressed. The app verifies the compressed file hash before decompressing it.
