# Damien-CLI

**Damien-CLI: Your Pythonic Gmail Assistant with LLM Superpowers (Under Development)**

Damien helps you manage your Gmail inbox with smarts and power, designed for direct use and future integration with Large Language Models (LLMs).

## Vision

To create a best-in-class, Python-based CLI email management tool for Gmail. Damien aims to empower users to efficiently manage, clean, and automate actions on their email, leveraging both predefined rules and dynamic, LLM-driven intelligence.

## Current Status (as of 2025-05-20)

* **Phase 0: Foundation & Setup - COMPLETE**
  * Google Cloud Project setup & Gmail API authentication (OAuth 2.0).
  * Python project structure using Poetry.
  * Basic CLI structure with Click.
  * Core logging implemented.
* **Phase 1: Core Email Read Operations - COMPLETE**
  * List emails with filtering.
  * Get details of specific emails.
  * Unit tests for read operations.
* **Phase 2: Core Email Write Operations & Basic Rules - COMPLETE**
  * Trash, permanently delete, label, mark read/unread emails (with dry-run & confirmations).
  * Basic rule management (add, list, delete rules from JSON).
  * Initial rule matching logic.
  * Unit tests for write operations and rule management.
* **Phase 3: LLM Integration & Advanced Features - IN PROGRESS**
  * **A3.1: Refine JSON output for all CLI commands - COMPLETE**
  * **A3.2: MCP Server Development - COMPLETE**
    * Developed MCP-compliant server to expose Damien functionality to AI assistants
    * Implemented FastAPI server with proper authentication
    * Created DynamoDB integration for session context
    * Built robust adapter layer connecting MCP to Damien core_api
    * Configured environment-based settings with proper nested model support
    * Created comprehensive test suite for all components
  * **A3.3: Claude Integration - IN PROGRESS**
    * Preparing JSON schemas for Claude integration
    * Setting up testing environment for AI-powered email management

## Features

* Secure Gmail authentication via OAuth 2.0.
* **Email Management:**
  * List emails with various filters.
  * Get detailed information about specific emails.
  * Move emails to Trash.
  * Permanently delete emails (with multiple confirmations).
  * Add/remove labels.
  * Mark emails as read or unread.
  * All modification actions support `--dry-run`.
* **Rule Management:**
  * Define rules in a JSON format.
  * Add, list, and delete rules.
  * Apply rules to emails with various filtering options.
* **AI Assistant Integration:**
  * MCP-compliant server for AI assistant integration.
  * Session context management with DynamoDB.
  * Configurable endpoint with proper authentication.
* **Output Formats:** Human-readable and structured JSON for programmatic use.
* **Logging:** Session activity is logged to `data/damien_session.log`.

## Setup

1. **Prerequisites:**
   * Python 3.13+
   * Poetry (Python dependency manager)
2. **Google Cloud Project & Gmail API:**
   * Follow the detailed instructions in `docs/GMAIL_API_SETUP.md` to enable the Gmail API and download your `credentials.json` file.
   * Place the `credentials.json` file in the root of this project directory.
3. **Clone the Repository (if applicable):**
   ```bash
   git clone https://github.com/YOUR_USERNAME/damien-cli.git # Update this URL
   cd damien-cli
   ```
4. **Install Dependencies:**
   ```bash
   poetry install
   ```
5. **Initial Authentication with Damien:**
   Run any command that requires Gmail access, or `login` explicitly. This will open a browser window for you to authorize Damien with your Gmail account.
   ```bash
   poetry run damien login
   ```
   A `data/token.json` file will be created to store your authentication token.

## Basic Usage

All commands are run via `poetry run damien ...`.

* Show help:
  ```bash
  poetry run damien --help
  poetry run damien emails --help
  poetry run damien rules --help
  ```
* List unread emails:
  ```bash
  poetry run damien emails list --query "is:unread"
  ```
* Get details for an email:
  ```bash
  poetry run damien emails get --id <your_email_id>
  ```
* Trash an email (will ask for confirmation):
  ```bash
  poetry run damien emails trash --ids <your_email_id>
  ```
* List rules:
  ```bash
  poetry run damien rules list
  ```

See `docs/USER_GUIDE.md` for more detailed usage instructions.

## Development

See `docs/DEVELOPER_GUIDE.md`.

## Roadmap & Next Steps

See `docs/ROADMAP.md`.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
