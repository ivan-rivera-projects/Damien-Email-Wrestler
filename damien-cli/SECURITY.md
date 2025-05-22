# Security Policy for Damien-CLI

## Reporting a Vulnerability

If you discover a security vulnerability within Damien-CLI, please report it by creating an Issue on the GitHub repository. We appreciate your efforts to disclose your findings responsibly.

Please include the following details with your report:
* A description of the vulnerability and its potential impact.
* Steps to reproduce the vulnerability.
* Any relevant code snippets or configuration details.

We will acknowledge your report and work to address the issue promptly.

## Sensitive Data Handling

Damien-CLI interacts with your Gmail account and handles sensitive authentication tokens.

* **`credentials.json`**: This file, downloaded from Google Cloud Console, contains your OAuth 2.0 client ID and client secret. It allows Damien-CLI to initiate the authorization process.
  * **It is critical that you DO NOT commit your `credentials.json` file to any public Git repository.** The project's `.gitignore` file includes `credentials.json` to help prevent this.
  * Store this file securely in the root directory of your local project.
* **`data/token.json`**: This file is created after you successfully authorize Damien-CLI with your Gmail account. It contains your access and refresh tokens, which allow Damien-CLI to make authenticated API calls to Gmail on your behalf.
  * **This file is also highly sensitive and should NOT be shared or committed to public repositories.** It is included in the project's `.gitignore`.
  * It is stored locally within the `data/` directory of your project.
* **Gmail API Scopes**: Damien-CLI requests permissions (scopes) to access your Gmail data.
  * For full functionality, including permanent deletion of emails, the `https://mail.google.com/` scope is used. This grants broad access to read, compose, send, and permanently delete all your email from Gmail.
  * Be aware of the permissions you grant during the OAuth 2.0 authorization flow. Only authorize applications you trust.

## Best Practices for Users

* Always download `credentials.json` directly from your Google Cloud Console.
* Keep your `credentials.json` and `data/token.json` files in a secure location, not accessible to others.
* Use the `--dry-run` option extensively to understand what actions Damien-CLI will take before applying them.
* Be especially cautious with the `damien emails delete` command, as it permanently removes emails.
* Regularly review the permissions granted to applications in your Google Account settings: [https://myaccount.google.com/permissions](https://myaccount.google.com/permissions)
