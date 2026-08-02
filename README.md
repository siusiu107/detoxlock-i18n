# DetoxLock language packs

This public repository contains only translation packs downloaded by DetoxLock. It does **not** contain the application source code, signing keys, API keys, or user data.

- `manifest.json`: language versions, paths and SHA-256 hashes
- `locales/*.json.gz`: one downloadable language pack per locale

The app verifies every downloaded pack against the SHA-256 value in the manifest and keeps the last valid local copy for offline use.

## Initial installation

Upload `DetoxLock_i18n_GitHub_upload_payload.zip` to the repository root. The included GitHub Actions workflow extracts the language packs, removes the uploaded ZIP, and commits the final files automatically.
