# Setup Guide

This guide walks you through registering an Azure App and configuring the toolkit so every tool can authenticate with Microsoft Fabric and Power BI on your behalf.

The process takes about five minutes and only needs to be done once.

---

## What you need

- A Microsoft account with access to at least one Fabric or Power BI workspace
- Access to the Azure portal (portal.azure.com)
- Python 3.8 or later installed locally

If you belong to an organisation, you may need your IT administrator to grant admin consent for the API permissions in Step 2. Everything else you can do yourself.

---

## Step 1: Register an Azure App

1. Go to [portal.azure.com](https://portal.azure.com) and sign in with your Microsoft account

2. In the top search bar, type **App registrations** and click the result

3. Click **New registration**

4. Fill in the form:
   - **Name:** `fabric-toolkit` (or any name you prefer)
   - **Supported account types:** Select _Accounts in any organizational directory (Any Microsoft Entra ID tenant)_
   - **Redirect URI:** Leave blank for now

5. Click **Register**

6. You are taken to the app overview page. Copy the **Application (client) ID** shown near the top.

   The value looks like this: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`

   This is the value you will paste into `config.py` in Step 4.

---

## Step 2: Add API permissions

Still on your app registration page:

1. Click **API permissions** in the left sidebar

2. Click **Add a permission**

3. Add each of the following permissions:

   **Microsoft Fabric API**

   | Permission | Type |
   |---|---|
   | `user_impersonation` | Delegated |

   To find this: click _APIs my organization uses_, search for **Microsoft Fabric**, select it, choose _Delegated permissions_, and tick `user_impersonation`.

   **Power BI Service**

   | Permission | Type |
   |---|---|
   | `Dataset.ReadWrite.All` | Delegated |
   | `Workspace.Read.All` | Delegated |
   | `Pipeline.ReadWrite.All` | Delegated |

   To find this: click _APIs my organization uses_, search for **Power BI Service**, select it, choose _Delegated permissions_, and tick each permission above.

4. Once all permissions are added, click **Grant admin consent for [your organisation]**

   If you do not have admin rights, send this page URL to your IT admin and ask them to grant consent. The tools will not be able to authenticate until consent is granted.

---

## Step 3: Set the redirect URI

Still on your app registration page:

1. Click **Authentication** in the left sidebar
2. Click **Add a platform**
3. Choose **Mobile and desktop applications**
4. Tick the checkbox for `https://login.microsoftonline.com/common/oauth2/nativeclient`
5. Click **Configure**

This allows the toolkit to open a browser window for sign-in and receive the token back.

---

## Step 4: Configure the toolkit

In your local copy of `fabric-toolkit`:

1. Copy the config template:
   ```bash
   cp config.example.py config.py
   ```
   On Windows:
   ```powershell
   Copy-Item config.example.py config.py
   ```

2. Open `config.py` in any text editor and paste in your Client ID:
   ```python
   CLIENT_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
   ```

3. Save the file. `config.py` is listed in `.gitignore` and will not be committed.

---

## Step 5: Install dependencies

```bash
pip install -r requirements.txt
```

This installs `msal`, `requests`, `openpyxl`, and `rich`.

---

## Step 6: Run a tool

```bash
python tools/schedule_extractor.py
```

On the first run a browser window opens and asks you to sign in with your Microsoft account. After you sign in, your token is cached locally in a file called `token_cache.bin`. Subsequent runs skip the sign-in step unless the token expires.

---

## Sharing within your organisation

If colleagues at the same organisation want to use the toolkit, they can all share the same `CLIENT_ID`. The Client ID identifies the registered app, not the user. Each person signs in with their own Microsoft account and gets their own token.

Steps for a colleague:
1. Clone the repo
2. Copy `config.example.py` to `config.py`
3. Paste the shared `CLIENT_ID`
4. Run `pip install -r requirements.txt`
5. Run any tool

---

## Troubleshooting

**"AADSTS50011: The redirect URI is not registered"**

Go back to Step 3 and make sure the native client redirect URI is added to your app registration.

**"AADSTS65001: The user or administrator has not consented to the application"**

Admin consent has not been granted. Ask your IT administrator to grant consent on the App registrations page for your app.

**"No module named 'msal'"**

Run `pip install -r requirements.txt` to install dependencies.

**Token cache prompts for sign-in every time**

The `token_cache.bin` file stores your session. If it is missing or deleted, sign-in is required again on the next run. This is expected behaviour.

**"MSAL: invalid_client"**

The Client ID in `config.py` is incorrect. Double-check it matches exactly what is shown on the App registrations overview page.

---

## Removing access

To revoke the toolkit's access to your account:

1. Go to [myapps.microsoft.com](https://myapps.microsoft.com)
2. Find `fabric-toolkit` in the list of apps
3. Click the three-dot menu and select **Remove**

You can also delete `token_cache.bin` from your local folder to clear the cached session without going through the portal.
