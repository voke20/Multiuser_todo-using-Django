# Problem: OneDrive note upload

## Root cause
`main` has no cloud-export APIs; Google Drive exists only on `feat/add-rating`, and there is no Microsoft Graph / OneDrive path to upload a note the same way.

## Symptoms
- Users can connect Google Drive and `POST /api/notes/<id>/drive/` on `feat/add-rating`, but cannot upload notes to OneDrive.
- No `onedrive` / Microsoft Graph code, env vars, or routes exist.
- `main` also lacks Google Drive (feature not merged yet).

## Affected files / functions
- Pattern to mirror: `authenticate/views.py` — `build_google_auth_url`, `GoogleAuthView`, `GoogleCallbackView`, `GoogleDriveUploadView` (~L117–277)
- `authenticate/models.py` — `CustomerModel.google_credentials` (L40)
- `authenticate/urls.py` — `/google/`, `/google/callback/`
- `note/urls.py` — `<id>/drive/` → `GoogleDriveUploadView`
- `multiuserapp/settings.py` — `GOOGLE_*` env settings (~L255–258)
- `authenticate/migrations/0003_customermodel_google_credentials.py`

## Blast radius
- Auth app (new OAuth routes + user credential field)
- Note routes (new upload endpoint)
- Settings / `.env` (Microsoft app registration secrets)
- Dependencies (`msal` or raw OAuth + `requests`)
- Frontend (if any): must call new auth + upload URLs — frontend not in this repo

## Constraints
- Match Google Drive UX: connect once → upload note as `.txt` with stripped HTML
- Keep JWT app auth; Microsoft OAuth is only for OneDrive access
- Do not break existing Google Drive routes on this branch
- No frontend work in this repo (API-only)

## Edge cases
- User not connected to OneDrive → 400 + `auth_url`
- Expired access token → refresh via refresh_token, then upload
- Note not owned by requester → 404
- Microsoft token revoke / invalid grant → clear creds, return reconnect `auth_url`
- Duplicate filename on OneDrive → Graph upsert path should overwrite or create uniquely (decide in plan)
