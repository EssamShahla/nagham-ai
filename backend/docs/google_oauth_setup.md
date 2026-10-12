# Setting up Google Sign-In for local development

This is the one part of the Google authentication feature that only you
can do -- it requires your own Google account and creates real credentials
scoped to your project. Everything else (the code) is already implemented
and tested; this guide gets you from zero to a working "Continue with
Google" button on `http://localhost:3000`.

## 1. Create (or choose) a Google Cloud project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Top bar → project picker → **New Project**.
3. Name it something like `nagham-ai-dev`. You don't need an organization
   or billing account for OAuth sign-in -- it's free and doesn't require
   enabling billing.
4. Wait for the project to finish creating, then make sure it's selected
   in the top bar before continuing.

## 2. Configure the OAuth consent screen

1. Left sidebar → **APIs & Services** → **OAuth consent screen**.
2. **User Type**: choose **External** (unless you have a Google Workspace
   organization and only ever want to sign in with accounts from it, in
   which case **Internal** is simpler and skips verification entirely).
3. Fill in the required fields:
   - **App name**: `Nagham AI` (or anything recognizable -- this is what
     users see on the Google consent screen).
   - **User support email**: your own email.
   - **Developer contact information**: your own email.
4. **Scopes** step: you don't need to add anything here. The app only
   requests `openid`, `email`, and `profile`, which are non-sensitive
   default scopes and don't require explicit configuration or Google's
   app-verification review.
5. **Test users** step (only shown if you kept the app in "Testing"
   publishing status, which is the default and is fine for local dev):
   add the Google account(s) you'll actually sign in with while
   developing. Unlisted accounts will be blocked by Google with an
   "access blocked" screen.
6. Save. You do **not** need to submit the app for verification or move
   it to "Production" status for local development -- "Testing" status
   works indefinitely for the test users you listed, it just shows an
   "unverified app" warning screen (with a "continue anyway" link) during
   sign-in, which is expected and fine for development.

## 3. Create the OAuth client credentials

1. Left sidebar → **APIs & Services** → **Credentials**.
2. **Create Credentials** → **OAuth client ID**.
3. **Application type**: **Web application**.
4. **Name**: `Nagham AI backend (local dev)`.
5. **Authorized JavaScript origins**: you can leave this empty. The app
   never calls Google's JS SDK from the browser -- the whole flow is a
   server-side redirect, so no origin needs to be whitelisted here.
6. **Authorized redirect URIs** -- this is the one field that must be
   exact. Add:
   ```
   http://127.0.0.1:8000/auth/google/callback
   ```
   This must byte-for-byte match the backend's `GOOGLE_REDIRECT_URI`
   environment variable (see step 4). If you run the backend on a
   different host/port, use that instead -- but keep them in sync.
   - If you ever access the backend via `http://localhost:8000` instead
     of `127.0.0.1`, add that as a *second* redirect URI too (Google
     treats them as different origins even though they're the same
     machine) and update `GOOGLE_REDIRECT_URI` to match whichever one you
     actually use.
7. Click **Create**. Google shows you a **Client ID** and **Client
   Secret** -- copy both now (you can always come back to the Credentials
   page later to copy the Client ID again, but the secret is only shown
   in full once; you can regenerate it if lost).

## 4. Configure the backend

Open `backend/.env` (not `.env.example`) and fill in:

```env
GOOGLE_CLIENT_ID=<the client ID from step 3>
GOOGLE_CLIENT_SECRET=<the client secret from step 3>
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/auth/google/callback
```

`FRONTEND_URL` should already be set to `http://localhost:3000` from the
existing setup -- that's where the backend redirects back to after a
successful (or failed) sign-in.

Restart the backend (`uvicorn` needs to reload to pick up the new env
vars):

```bash
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

## 5. Try it

1. Make sure the frontend is running (`npm run dev` in `frontend/`) and
   the backend is running with the env vars from step 4 loaded.
2. Open `http://localhost:3000/login` and click **Continue with Google**.
3. You should land on a real Google sign-in/consent screen (showing an
   "unverified app" notice if you kept the app in Testing status -- click
   **Continue**/"Advanced → Go to Nagham AI (unsafe)" to proceed; this
   notice is expected for an app that hasn't gone through Google's
   verification review, which isn't necessary for local development).
4. After approving, you should land back on `/dashboard`, signed in.
5. Sign out, go to `/register`, and try **Sign up with Google** with the
   *same* Google account -- you should be logged into the *same* account
   again (not a duplicate), since it's already linked by `google_id`.

### Testing the account-linking path specifically

To see the "this email already exists" flow:

1. Register a normal account with email/password using the **same email
   address** as the Google account you tested with (or vice versa: sign
   up with Google first using an email, then try registering that email
   with a password).
2. Sign out, then click **Continue with Google** with that same account.
3. You should land back on `/login` with a banner saying an account
   already exists and asking you to sign in with your password to link
   it.
4. Enter the password for the local account. On success, you'll be
   logged in **and** the Google identity will now be linked -- test this
   by signing out and signing in with Google again; it should go straight
   to the same account without the linking banner the second time.

### Testing cancellation

Click **Continue with Google**, then click **Cancel** (or close the
Google consent popup/tab) instead of approving. You should land back on
`/login` with a "Google sign-in was cancelled" message, not a crash or a
blank page.

## Troubleshooting

- **"Error 400: redirect_uri_mismatch"** from Google -- the
  `GOOGLE_REDIRECT_URI` env var doesn't exactly match an Authorized
  redirect URI on the OAuth client (including the scheme, host, port, and
  trailing slash). Fix one or the other so they match exactly.
- **"Access blocked: this app's request is invalid"** or **"has not
  completed the Google verification process"** and your account isn't
  getting in -- you're signing in with an account that isn't listed under
  **Test users** on the consent screen (step 2.5), and the app is in
  Testing status. Add that account there.
- **503 "Google sign-in is not configured on this server"** -- one of
  `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI` is
  empty in `backend/.env`, or the backend process hasn't been restarted
  since you added them.
- **Nothing happens / CORS error** after Google redirects back -- check
  `FRONTEND_URL` in `backend/.env` matches where your frontend actually
  runs (`http://localhost:3000` by default), and that the frontend's
  `NEXT_PUBLIC_API_URL` points at the backend.
