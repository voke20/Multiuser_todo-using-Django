# Solution: OneDrive note upload (MES)

## Proposed approach
Mirror the existing Google Drive pattern on this branch (`feature/onedrive-upload` ← `feat/add-rating`):

1. Add `CustomerModel.onedrive_credentials` (JSON text: access + refresh tokens; **do not** store client_secret on the user row — read from settings).
2. Microsoft identity OAuth (authorization code):
   - `GET /api/auth/onedrive/` → `{ "auth_url": "..." }` (authenticated)
   - `GET /api/auth/onedrive/callback/` → exchange code, save tokens
3. Upload: `POST /api/notes/<id>/onedrive/` — strip HTML, write `Title…Content…` as `.txt` to OneDrive via Microsoft Graph:
   `PUT https://graph.microsoft.com/v1.0/me/drive/root:/EmmaNotes/{title}.txt:/content`
4. Env: `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_REDIRECT_URI`, `MICROSOFT_TENANT_ID` (default `common`).
5. Dependency: `msal` (MES) + existing `requests` for Graph PUT. Scope: `Files.ReadWrite` + `offline_access`.

Keep Google Drive code untouched except optional tiny bugfix only if requested (`{"auth_url:", auth_url}` typo).

## Alternatives rejected
| Option | Why rejected |
|--------|----------------|
| Client-side-only OneDrive upload | Tokens/secrets harder to secure; Google pattern is backend-mediated |
| New abstraction `CloudProvider` plugin layer | YAGNI — two providers; extract later if a third appears |
| SharePoint-site upload | User asked for personal OneDrive, not org libraries |
| Re-implement Google + OneDrive as shared module now | Scope creep; mirror first, refactor after both work |

## Performance impact
Neutral. One OAuth redirect per connect; one Graph HTTP PUT per upload. No list/query hot path changes.

## Performance delta
Not measurable in CI without live Graph. Expect ~200–800ms per upload depending on note size and Graph latency.

## Trade-offs
- Plaintext credential JSON on user (same as Google today) — acceptable for MES; encrypt-at-rest is a follow-up.
- `Files.ReadWrite` is broader than Drive’s `drive.file` equivalent; Graph has no exact “app-created files only” personal-drive scope — document for Azure app consent.
- Branch based on `feat/add-rating`, not `main` — OneDrive ships with Google Drive + rating/download features.

## Dead code audit
None expected. No Google code removed.
