# Changelog: OneDrive note upload

## Layer 1 — System behavior
Authenticated users can connect a Microsoft account and upload a note to their personal OneDrive as a `.txt` file under `EmmaNotes/`, parallel to the existing Google Drive flow. Connect via `GET /api/auth/onedrive/`; upload via `POST /api/notes/<id>/onedrive/`. Tokens are stored on the user row without embedding the app client secret.

## Layer 2 — Files touched

| Path | What changed | Why |
|------|----------------|-----|
| `authenticate/models.py` | Added `CustomerModel.onedrive_credentials` | Persist Graph access/refresh tokens per user |
| `authenticate/migrations/0004_customermodel_onedrive_credentials.py` | New migration | Schema for the new field |
| `authenticate/views.py` | Added MSAL helpers + `OneDriveAuthView`, `OneDriveCallbackView`, `OneDriveUploadView` | OAuth connect + Graph PUT upload |
| `authenticate/urls.py` | `/onedrive/`, `/onedrive/callback/` | Auth entrypoints |
| `note/urls.py` | `<id>/onedrive/` → `OneDriveUploadView` | Upload entrypoint |
| `multiuserapp/settings.py` | `MICROSOFT_*` settings | App registration config |
| `.env.example` | Documented Google + Microsoft vars | Local/prod setup |
| `docker-compose.yml` | Pass Google/Microsoft env into `web` | Docker runtime can load OAuth secrets |
| `requirements.txt` | `msal==1.31.1` | Microsoft identity client |
| `note/tests.py` | URL resolve + not-connected upload tests | Mirror Google Drive coverage |
| `docs/tasks/20260713_onedrive-upload/*` | Problem/solution/plan/credentials | Engineering protocol |

## Verification
- `py_compile` on changed Python modules: passed
- `manage.py test` for OneDrive cases: **not run** — Docker daemon down and project Django not installed in available local venv
