# Gmail API Setup Guide for Damien-CLI

To use Damien-CLI, you need to authorize it to access your Gmail account. This involves creating a project in Google Cloud Platform, enabling the Gmail API, and obtaining OAuth 2.0 credentials.

## Steps

1. **Go to Google Cloud Console:**
   Navigate to [https://console.cloud.google.com/](https://console.cloud.google.com/) and log in with your Google account.

2. **Create or Select a Project:**
   * If you don't have a project, click "NEW PROJECT" and give it a name (e.g., "Damien-CLI-Access").
   * If you have an existing project you want to use, select it.

3. **Enable the Gmail API:**
   * Use the search bar at the top to search for "Gmail API".
   * Select "Gmail API" from the results.
   * Click the "ENABLE" button.

4. **Configure OAuth Consent Screen:**
   If this is your first time creating credentials for this project, you'll need to configure the consent screen.
   * Go to "Credentials" (usually under "APIs & Services").
   * If prompted, click "CONFIGURE CONSENT SCREEN".
   * **User Type:** Choose "External". Click "CREATE".
   * **App information:**
     * **App name:** `Damien-CLI` (or your preference)
     * **User support email:** Your email address.
     * **Developer contact information:** Your email address.
   * Click "SAVE AND CONTINUE".
   * **Scopes page:** Click "SAVE AND CONTINUE" (Damien will request scopes dynamically).
   * **Test users page:**
     * Click "+ ADD USERS".
     * Enter the Gmail address of the account you want Damien-CLI to manage (this is **your** Gmail address).
     * Click "ADD", then "SAVE AND CONTINUE".
   * Review the summary and click "BACK TO DASHBOARD".

5. **Create OAuth 2.0 Client ID Credentials:**
   * On the "Credentials" page, click "+ CREATE CREDENTIALS".
   * Select "OAuth client ID"
   * **Application type:** Choose "Desktop app".
   * **Name:** You can leave the default or name it (e.g., "Damien-CLI Desktop Client").
   * Click "CREATE".

6. **Download Credentials JSON:**
   * A pop-up will appear showing "Your Client ID" and "Your Client Secret".
   * Click the "DOWNLOAD JSON" button on the right.
   * **Rename the downloaded file to `credentials.json`**.

7. **Place `credentials.json`:**
   * Move the `credentials.json` file into the root directory of your Damien-CLI project (the same folder where `pyproject.toml` is).

## Important Security Note

The `credentials.json` file contains sensitive information that allows your application to request access to Google APIs.
* **DO NOT commit `credentials.json` to public Git repositories.**
* It is already listed in the project's `.gitignore` file to help prevent accidental commits.
* Keep this file secure.

When you first run a Damien-CLI command that requires Gmail access (like `damien login` or `damien emails list`), it will use this `credentials.json` file to initiate the authorization flow, opening a browser window for you to grant permissions. A `token.json` file will then be created in the `data/` directory to store your specific access tokens.
