# DetoxLock language packs

This public repository contains only translation packs downloaded by DetoxLock. It does **not** contain the application source code, signing keys, API keys, or user data.

- `manifest.json`: language versions, paths and SHA-256 hashes
- `locales/*.json`: one downloadable language pack per locale

The app verifies every downloaded pack against the SHA-256 value in the manifest and keeps the last valid local copy for offline use.
