# Plan: OneDrive note upload

Branch: `feature/onedrive-upload` (from `origin/feat/add-rating`)

## Steps

1. **Model + migration** — Add `onedrive_credentials` TextField to `authenticate/models.py`; create migration `0004_…`.  
   Complexity: trivial  
   AC: migrate applies; field nullable/blank.

2. **Settings + env** — Add `MICROSOFT_CLIENT_ID/SECRET/REDIRECT_URI/TENANT_ID` in `multiuserapp/settings.py` and `.env.example`.  
   Complexity: trivial  
   AC: settings load when env set; `.env.example` documents keys.

3. **OAuth helpers + views** — In `authenticate/views.py`, add `build_onedrive_auth_url`, `OneDriveAuthView`, `OneDriveCallbackView` (MSAL auth-code flow; persist tokens without client_secret).  
   Complexity: medium  
   AC: authenticated GET returns `auth_url` starting with `https://login.microsoftonline.com/`.

4. **Upload view** — Add `OneDriveUploadView`: owner check, missing-creds → 400 + `auth_url`, refresh token if needed, Graph PUT `.txt`, return `onedrive_link` / `webUrl`.  
   Complexity: medium  
   AC: without creds → 400; with mocked Graph → 200 + link.

5. **Routes** — Wire `authenticate/urls.py` (`onedrive/`, `onedrive/callback/`) and `note/urls.py` (`<id>/onedrive/`).  
   Complexity: trivial  
   AC: `reverse("onedrive-upload", kwargs={"id": 1})` → `/api/notes/1/onedrive/`.

6. **Dependencies** — Add `msal` to `requirements.txt` (pin compatible version).  
   Complexity: low  
   AC: import `msal` succeeds in project env.

7. **Tests** — Mirror Google Drive tests in `note/tests.py` (+ auth tests if needed): URL resolves; upload without connection returns reconnect payload.  
   Complexity: low  
   AC: new tests pass under `python manage.py test`.

## Untested path disclosure
- Live Microsoft OAuth + Graph upload (needs real Azure app + user consent) — manual only.
- Token refresh after expiry — unit-testable with mocks; live refresh not in CI.

## Regression checklist
- `GoogleAuthView` / `GoogleCallbackView` / `GoogleDriveUploadView` / `/api/notes/<id>/drive/`
- JWT login/register/logout
- Note CRUD, share, email, uploads, rate, download

## Definition of Done
- [x] App code paths added for OneDrive connect + upload
- [x] Every AC coded (model, settings, routes, views, tests written)
- [ ] Regression checklist cleared — needs Django test run / manual smoke
- [x] Dead code audit: none left behind
- [x] `msal` justified in solution.md
- [x] Cross-file consistency with Google Drive response shape (`error`, `auth_url`, success `message` + link)
- [x] Changelog written; status remains `implemented` until live test pass → then `done`
