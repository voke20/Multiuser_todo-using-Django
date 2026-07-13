# Credentials to prepare (OneDrive / Microsoft Graph)

You register **one Azure (Entra ID) app**. The Django backend is a **confidential web client** (same pattern as Google Drive).

## 1. Create the app registration

1. Open [Microsoft Entra admin center](https://entra.microsoft.com/) → **Applications** → **App registrations** → **New registration**.
2. Name: e.g. `Emma Note OneDrive`.
3. **Supported account types** (pick one):
   - **Personal Microsoft accounts only** — if users use `@outlook.com` / `@hotmail.com` / personal OneDrive.
   - **Accounts in any org + personal** (`common`) — if you want work/school **and** personal. Recommended for a consumer note app unless you restrict to a company tenant.
4. **Redirect URI** → platform **Web**:
   - Local: `http://localhost:8000/api/auth/onedrive/callback/`
   - If you use ngrok (like Google Drive): `https://<your-ngrok-host>/api/auth/onedrive/callback/`
5. Register.

## 2. Values to copy into `.env`

| Env var | Where to find it | Notes |
|---------|------------------|--------|
| `MICROSOFT_CLIENT_ID` | App registration → **Overview** → Application (client) ID | Public; safe in client configs but still keep in env |
| `MICROSOFT_TENANT_ID` | Overview → Directory (tenant) ID, **or** literal `common` / `consumers` | Use `common` for multi-tenant + personal; `consumers` for personal-only |
| `MICROSOFT_CLIENT_SECRET` | **Certificates & secrets** → **New client secret** → copy **Value** once | Secret expires (set ≤ 12 months); rotate before expiry |
| `MICROSOFT_REDIRECT_URI` | Must **exactly** match the Web redirect URI you registered | Trailing slash must match the Django URL |

Example `.env` block:

```env
MICROSOFT_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MICROSOFT_CLIENT_SECRET=your-secret-value-not-the-secret-id
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/auth/onedrive/callback/
MICROSOFT_TENANT_ID=common
```

## 3. API permissions (delegated)

App registration → **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated**:

| Permission | Why |
|------------|-----|
| `Files.ReadWrite` | Create/update files in the signed-in user’s OneDrive |
| `offline_access` | Refresh token so upload works after the first consent |
| `openid` / `profile` (optional) | Standard OIDC; MSAL often requests these |

Do **not** use Application permissions (`Files.ReadWrite.All` app-only) for this feature — we act **as the user**, same as Google Drive.

For personal Microsoft accounts, admin consent is usually not required; the user consents on first connect. For work/school tenants, an admin may need to grant consent.

## 4. What you do **not** need

- No OneDrive “API key” separate from Entra — Graph uses the OAuth access token.
- No SharePoint site ID for personal OneDrive uploads to `/me/drive`.
- No frontend Microsoft SDK for the MES (backend handles OAuth + Graph PUT).

## 5. Runtime flow (once env is set)

1. Logged-in user: `GET /api/auth/onedrive/` → open `auth_url` → Microsoft login + consent.
2. Callback stores access/refresh tokens on the user (`onedrive_credentials`).
3. `POST /api/notes/<id>/onedrive/` uploads `{title}.txt` under `EmmaNotes/` and returns a `webUrl`.

## 6. Checklist before first live test

- [ ] App registration created with **Web** redirect URI
- [ ] Client secret created and saved (Value, not Secret ID)
- [ ] `.env` has all four `MICROSOFT_*` vars
- [ ] Redirect URI string matches Django route **exactly**
- [ ] Delegated `Files.ReadWrite` + `offline_access` added
- [ ] Test with a personal Microsoft account that has OneDrive
- [ ] If using HTTPS tunnel, add that host to Entra redirect URIs (and `ALLOWED_HOSTS` like Google/ngrok)
